# NATS Protocols for Rika Phase 2.5

## Overview

NATS messaging is used for real-time communication between Atlas Dashboard, Core API, and Desktop Agents. This document outlines the message protocols, topics, and security considerations.

## Message Topics

### 1. Control Session Management

#### `rika.control.request`
**Publisher:** Core API  
**Subscriber:** Desktop Agent  
**Purpose:** Notify agent of new control request

```json
{
  "type": "control_request",
  "request_id": "req_abc123",
  "device_id": "device_456",
  "requester": "atlas-user-1",
  "ttl_minutes": 15,
  "reason": "Remote assistance required",
  "approval_required": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### `rika.control.approved`
**Publisher:** n8n Workflow  
**Subscriber:** Core API, Desktop Agent  
**Purpose:** Notify all parties that control was approved

```json
{
  "type": "control_approved",
  "request_id": "req_abc123",
  "device_id": "device_456",
  "session_id": "sess_xyz789",
  "expires_at": "2024-01-15T10:45:00Z",
  "approved_by": "admin@company.com",
  "approved_at": "2024-01-15T10:32:00Z"
}
```

#### `rika.control.denied`
**Publisher:** n8n Workflow  
**Subscriber:** Core API, Desktop Agent  
**Purpose:** Notify that control request was denied

```json
{
  "type": "control_denied",
  "request_id": "req_abc123",
  "device_id": "device_456",
  "reason": "Outside business hours",
  "denied_by": "auto-timeout",
  "denied_at": "2024-01-15T10:37:00Z"
}
```

#### `rika.control.revoked`
**Publisher:** Core API  
**Subscriber:** Desktop Agent, Atlas UI  
**Purpose:** Immediately terminate control session

```json
{
  "type": "control_revoked",
  "session_id": "sess_xyz789",
  "device_id": "device_456",
  "reason": "Session expired",
  "revoked_by": "system",
  "revoked_at": "2024-01-15T10:45:00Z"
}
```

### 2. Input Event Streaming

#### `rika.control.input.{device_id}`
**Publisher:** Atlas UI  
**Subscriber:** Desktop Agent  
**Purpose:** Send real-time input events during control session

```json
{
  "type": "mouse_move",
  "session_id": "sess_xyz789",
  "timestamp": "2024-01-15T10:35:00Z",
  "payload": {
    "x": 50.5,
    "y": 30.2
  }
}
```

```json
{
  "type": "mouse_click",
  "session_id": "sess_xyz789",
  "timestamp": "2024-01-15T10:35:01Z",
  "payload": {
    "button": "left",
    "pressed": true
  }
}
```

```json
{
  "type": "key_press",
  "session_id": "sess_xyz789",
  "timestamp": "2024-01-15T10:35:02Z",
  "payload": {
    "key": "a",
    "modifiers": ["ctrl"]
  }
}
```

### 3. Streaming Management

#### `rika.stream.start`
**Publisher:** Atlas UI  
**Subscriber:** Desktop Agent  
**Purpose:** Request stream initiation

```json
{
  "type": "stream_start",
  "device_id": "device_456",
  "room_name": "room_abc123",
  "mode": "view",
  "quality": "720p",
  "fps": 30,
  "requester": "atlas-user-1"
}
```

#### `rika.stream.stop`
**Publisher:** Atlas UI / Core API  
**Subscriber:** Desktop Agent  
**Purpose:** Request stream termination

```json
{
  "type": "stream_stop",
  "device_id": "device_456",
  "room_name": "room_abc123",
  "reason": "User requested",
  "stopped_by": "atlas-user-1"
}
```

#### `rika.stream.status`
**Publisher:** Desktop Agent  
**Subscriber:** Core API, Atlas UI  
**Purpose:** Report streaming status

```json
{
  "type": "stream_status",
  "device_id": "device_456",
  "room_name": "room_abc123",
  "status": "active",
  "participants": 2,
  "quality": "720p",
  "fps": 30,
  "bandwidth_mbps": 2.5,
  "updated_at": "2024-01-15T10:35:00Z"
}
```

### 4. Policy Enforcement

#### `rika.policy.update`
**Publisher:** Core API  
**Subscriber:** All Desktop Agents  
**Purpose:** Push policy updates

```json
{
  "type": "policy_update",
  "policy_version": "1.2",
  "updated_policies": {
    "control_max_sessions": 5,
    "stream_max_quality": "1080p",
    "approval_required_roles": ["admin", "it_support"]
  },
  "effective_at": "2024-01-15T11:00:00Z"
}
```

#### `rika.policy.violation`
**Publisher:** Desktop Agent  
**Subscriber:** Core API  
**Purpose:** Report policy violations

```json
{
  "type": "policy_violation",
  "device_id": "device_456",
  "violation_type": "max_session_duration_exceeded",
  "session_id": "sess_xyz789",
  "details": {
    "max_allowed": 30,
    "actual_duration": 35,
    "action_taken": "force_disconnect"
  },
  "timestamp": "2024-01-15T11:05:00Z"
}
```

### 5. Audit and Security

#### `rika.audit.log`
**Publisher:** All Components  
**Subscriber:** Core API (Audit Service)  
**Purpose:** Centralized audit logging

```json
{
  "type": "audit_log",
  "event_type": "control_session_started",
  "user_id": "atlas-user-1",
  "device_id": "device_456",
  "session_id": "sess_xyz789",
  "metadata": {
    "ip_address": "192.168.1.100",
    "user_agent": "Atlas-Dashboard/2.5",
    "approval_time_seconds": 45
  },
  "timestamp": "2024-01-15T10:32:00Z"
}
```

## Security Considerations

### Message Encryption
- All NATS traffic should use TLS encryption in production
- Consider using NATS JWT authentication for component authentication
- Implement message signing for critical commands (control, policy)

### Topic Access Control
```yaml
# Example NATS authorization config
authorization:
  users:
    - user: "atlas-dashboard"
      permissions:
        publish:
          - "rika.control.input.*"
          - "rika.stream.start"
          - "rika.stream.stop"
        subscribe:
          - "rika.stream.status"
          - "rika.control.approved"
          - "rika.control.denied"
    
    - user: "desktop-agent"
      permissions:
        publish:
          - "rika.stream.status"
          - "rika.policy.violation"
          - "rika.audit.log"
        subscribe:
          - "rika.control.*"
          - "rika.stream.start"
          - "rika.stream.stop"
          - "rika.policy.update"
    
    - user: "core-api"
      permissions:
        publish:
          - "rika.control.request"
          - "rika.control.revoked"
          - "rika.policy.update"
        subscribe:
          - "rika.stream.status"
          - "rika.policy.violation"
          - "rika.audit.log"
```

### Rate Limiting
- Control input events: Max 60/second per session
- Stream status updates: Max 1/second per device
- Audit logs: Max 100/minute per component

### Message Retention
- Control events: 24 hours (compliance)
- Audit logs: 90 days (security)
- Stream status: 1 hour (operational)

## Error Handling

### Connection Loss
```python
# Desktop Agent NATS reconnection logic
async def handle_nats_disconnect():
    logger.warning("NATS connection lost, attempting reconnect...")
    while not nats_client.is_connected:
        try:
            await nats_client.connect()
            logger.info("NATS reconnected successfully")
            # Re-subscribe to all topics
            await subscribe_to_topics()
            break
        except Exception as e:
            logger.error(f"NATS reconnect failed: {e}")
            await asyncio.sleep(5)
```

### Message Validation
```python
# Example message validation
def validate_control_input(message):
    required_fields = ['type', 'session_id', 'timestamp', 'payload']
    if not all(field in message for field in required_fields):
        raise ValueError("Invalid control input message")
    
    if message['type'] not in ['mouse_move', 'mouse_click', 'key_press', 'key_release']:
        raise ValueError("Invalid control input type")
    
    # Validate session is active
    if not is_session_active(message['session_id']):
        raise ValueError("Control session not active")
```

## Testing NATS Integration

### Local Testing Setup
```bash
# Start NATS server locally
nats-server --port 4222 --config nats-dev.conf

# Test message publishing
nats pub rika.test "Hello World"

# Test message subscription
nats sub rika.control.*
```

### Integration Tests
```python
# Example integration test
async def test_control_approval_flow():
    # 1. Publish control request
    await nats_client.publish("rika.control.request", control_request_msg)
    
    # 2. Wait for approval
    approval_msg = await wait_for_message("rika.control.approved", timeout=10)
    assert approval_msg['request_id'] == control_request_msg['request_id']
    
    # 3. Send test input
    await nats_client.publish(f"rika.control.input.{device_id}", mouse_move_msg)
    
    # 4. Verify input processed
    # Check that mouse moved on target device
```

This NATS protocol documentation provides the foundation for secure, real-time communication in Rika Phase 2.5.