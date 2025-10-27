# n8n Control Approval Flow

This n8n workflow handles the approval process for Rika remote control requests.

## Overview

When a control request is made through Atlas UI, the Core API sends a webhook to this n8n flow, which:
1. Validates the request
2. Sends approval notifications via Telegram and/or Email
3. Waits for approval/denial or auto-denies after 5 minutes
4. Sends the decision back to the Core API

## Setup Instructions

### 1. Install n8n (if not already installed)

```powershell
# Install n8n globally
npm install n8n -g

# Or run with Docker
docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
```

### 2. Import the Workflow

1. Start n8n: `n8n start`
2. Open `http://localhost:5678`
3. Go to **Workflows** → **Import from File**
4. Upload `rika-control-approval-flow.json`
5. Save the workflow

### 3. Configure Credentials

#### Telegram Bot (Recommended)

1. Create a Telegram bot:
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Get your bot token

2. In n8n, go to **Credentials** → **Add Credential** → **Telegram API**
   - Name: `Rika Control Bot`
   - Access Token: `your_bot_token`

3. Get your Telegram chat ID:
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat_id` in the response

#### Email (Alternative/Backup)

1. In n8n, go to **Credentials** → **Add Credential** → **SMTP**
   - Name: `Rika SMTP`
   - Host: `smtp.gmail.com` (or your SMTP server)
   - Port: `587`
   - Username: `your_email@gmail.com`
   - Password: `your_app_password`

### 4. Update Webhook URL

In your Core API `.env` file:
```bash
N8N_WEBHOOK_URL=http://localhost:5678/webhook/rika-control-approval
```

### 5. Test the Flow

1. **Activate** the workflow in n8n
2. In Atlas UI, link a device in "control" mode
3. Click "Request Control"
4. Check your Telegram/Email for approval message
5. Approve or deny the request
6. Verify the control session is created/denied in Atlas

## Workflow Details

### Nodes Overview

1. **Control Request Webhook** - Receives POST from Core API
2. **Validate Request** - Ensures required fields are present
3. **Send Telegram Approval** - Sends interactive approval message
4. **Send Email Approval** - Sends email with approve/deny links
5. **Wait 5 Minutes** - Timeout for manual approval
6. **Auto-Deny on Timeout** - Automatically denies if no response
7. **Telegram Callback** - Handles Telegram button presses
8. **Process Approval/Denial** - Processes user decision
9. **Send to Rika API** - Calls Core API with approval result
10. **Confirm Action** - Sends confirmation to user

### Message Format

**Webhook Input (from Core API):**
```json
{
  "request_id": "uuid",
  "device_id": "device_uuid", 
  "device_name": "Desktop-User",
  "reason": "Remote assistance",
  "ttl_minutes": 15,
  "expires_at": "2025-01-15T11:00:00Z",
  "approval_url": "rika://control/approve?request_id=uuid"
}
```

**API Response (to Core API):**
```json
{
  "request_id": "uuid",
  "approved": true/false,
  "approver": "telegram-username"
}
```

### Telegram Interaction

**Approval Message:**
```
🤖 Rika Remote Control Request

📱 Device: Desktop-User (abc123...)
⏰ Duration: 15 minutes
📝 Reason: Remote assistance  
🕒 Expires: 2025-01-15T11:00:00Z

Actions:
• ✅ Reply 'approve' to grant control
• ❌ Reply 'deny' to reject
• ⏰ Will auto-deny in 5 minutes

[✅ Approve] [❌ Deny]
```

## Customization

### Change Timeout Duration

Edit the "Wait 5 Minutes" node:
- Change `amount` from `300` to desired seconds
- Update message text accordingly

### Add More Notification Channels

Add nodes for:
- Discord webhooks
- Slack notifications
- SMS via Twilio
- Custom webhooks

### Custom Approval Logic

Modify the validation node to add:
- Device-specific rules
- Time-based restrictions
- User role requirements
- Approval delegation

### Example Customizations

**Only allow control during business hours:**
```javascript
const now = new Date();
const hour = now.getHours();
const isBusinessHours = hour >= 9 && hour <= 17;

if (!isBusinessHours) {
  return [{ 
    json: { 
      request_id: items[0].json.request_id,
      approved: false, 
      approver: "auto-business-hours" 
    } 
  }];
}
```

**Require manager approval for long sessions:**
```javascript
const ttl = items[0].json.ttl_minutes;
const requiresManagerApproval = ttl > 30;

if (requiresManagerApproval) {
  // Send to manager chat ID instead
  return [{ json: { ...items[0].json, chat_id: "manager_chat_id" } }];
}
```

## Testing

### Manual Testing

1. **Test Webhook Reception:**
   ```powershell
   curl -X POST http://localhost:5678/webhook/rika-control-approval \
     -H "Content-Type: application/json" \
     -d '{"request_id":"test-123","device_id":"device-456","device_name":"Test Device","reason":"Testing","ttl_minutes":15,"expires_at":"2025-01-15T11:00:00Z"}'
   ```

2. **Test Telegram Bot:**
   - Send `/start` to your bot
   - Check bot responds
   - Test button interactions

3. **Test Core API Integration:**
   - Make actual control request through Atlas
   - Verify webhook is triggered
   - Complete approval flow
   - Check control session is created

### Monitoring

**n8n Execution Log:**
- Go to **Executions** in n8n
- Check successful/failed runs
- Debug any errors

**Core API Logs:**
- Check webhook sending: `"Failed to send n8n webhook"`
- Check approval processing: `"Control approved for device"`

## Security Considerations

### Webhook Security

Add authentication to webhook:
```javascript
// Add to validation node
const authToken = items[0].json.auth_token;
if (authToken !== 'your_secret_token') {
  return []; // Reject unauthorized requests
}
```

### Approval Verification

Add request verification:
```javascript
// Verify request hasn't expired
const expiresAt = new Date(items[0].json.expires_at);
const now = new Date();
if (now > expiresAt) {
  return [{ json: { approved: false, reason: "Request expired" } }];
}
```

### Rate Limiting

Add rate limiting logic:
```javascript
// Store recent requests and check frequency
const deviceId = items[0].json.device_id;
const recentRequests = getRecentRequests(deviceId); // Custom function
if (recentRequests.length > 3) {
  return [{ json: { approved: false, reason: "Too many requests" } }];
}
```

## Troubleshooting

### Webhook Not Triggered
- Check Core API logs for webhook sending errors
- Verify n8n is running on port 5678
- Test webhook URL manually with curl
- Check n8n workflow is activated

### Telegram Not Working
- Verify bot token is correct
- Check chat ID is correct
- Ensure bot can send messages to user
- Test bot manually with simple message

### Email Not Working
- Check SMTP credentials
- Verify email server settings
- Check spam folder for emails
- Test SMTP connection outside n8n

### Approval Not Processed
- Check n8n execution logs for errors
- Verify Core API is receiving approval calls
- Check network connectivity between n8n and Core API
- Ensure request IDs match

### Auto-Deny Not Working
- Check "Wait" node configuration
- Verify timeout duration
- Check HTTP request node for API calls
- Monitor Core API logs for denied requests

## Advanced Features

### Multi-Stage Approval

For sensitive devices, implement multi-stage approval:
1. Initial request → Supervisor approval
2. Supervisor approval → Manager approval  
3. Manager approval → Final grant

### Conditional Approval

Implement smart approval based on:
- Device sensitivity level
- Time of day/week
- User requesting control
- Duration of control session
- Reason provided

### Integration with External Systems

Connect to:
- Active Directory for user validation
- Ticketing systems for approval tracking
- Audit systems for compliance logging
- SIEM systems for security monitoring