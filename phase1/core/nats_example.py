# core/nats_example.py
"""
NATS Publisher/Subscriber Example
Shows how messages flow through the system
"""

import asyncio
import nats
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

NATS_URL = os.getenv("NATS_URL", "nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222")

async def message_handler(msg):
    """Handle incoming messages"""
    subject = msg.subject
    data = json.loads(msg.data.decode())
    print(f"\n📨 Received on '{subject}':")
    print(f"   Data: {json.dumps(data, indent=2)}")

async def run_subscriber():
    """Subscribe to all Rika subjects"""
    nc = await nats.connect(NATS_URL)
    print(f"✅ Subscriber connected to NATS")
    
    # Subscribe to all subjects
    subjects = [
        "presence.updated",
        "handoff.requested", 
        "control.granted",
        "blackout",
        "enrollment.>",  # Wildcard for all enrollment events
        "device.>"       # Wildcard for all device events
    ]
    
    for subject in subjects:
        await nc.subscribe(subject, cb=message_handler)
        print(f"   Subscribed to: {subject}")
    
    print("\n👂 Listening for messages... (Press Ctrl+C to stop)\n")
    
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        pass
    finally:
        await nc.close()

async def run_publisher():
    """Publish test messages"""
    nc = await nats.connect(NATS_URL)
    print(f"✅ Publisher connected to NATS\n")
    
    # Test messages
    messages = [
        ("presence.updated", {
            "device_id": "test-device-001",
            "device_name": "Test Desktop",
            "current_app": "Visual Studio Code",
            "timestamp": datetime.utcnow().isoformat()
        }),
        ("handoff.requested", {
            "from_device": "desktop-001",
            "to_device": "mobile-001",
            "context": {"url": "https://example.com", "action": "open_browser"},
            "timestamp": datetime.utcnow().isoformat()
        }),
        ("control.granted", {
            "from_device": "mobile-001",
            "to_device": "desktop-001",
            "timestamp": datetime.utcnow().isoformat()
        }),
        ("blackout", {
            "triggered_by": "admin",
            "reason": "Security check",
            "timestamp": datetime.utcnow().isoformat()
        })
    ]
    
    for subject, data in messages:
        await nc.publish(subject, json.dumps(data).encode())
        print(f"📤 Published to '{subject}':")
        print(f"   Data: {json.dumps(data, indent=2)}\n")
        await asyncio.sleep(1)
    
    await nc.close()
    print("✅ All test messages published")

async def main():
    """Run both subscriber and publisher"""
    print("=" * 50)
    print("NATS Messaging Example for Rika Core")
    print("=" * 50)
    
    print("\nChoose mode:")
    print("1. Subscriber (listen for messages)")
    print("2. Publisher (send test messages)")
    print("3. Both (run subscriber, then publish)")
    
    choice = input("\nEnter choice (1/2/3): ")
    
    if choice == "1":
        await run_subscriber()
    elif choice == "2":
        await run_publisher()
    elif choice == "3":
        # Run subscriber in background
        subscriber_task = asyncio.create_task(run_subscriber())
        await asyncio.sleep(2)  # Let subscriber connect
        
        # Publish messages
        await run_publisher()
        
        # Keep subscriber running
        print("\n👂 Subscriber still listening... (Press Ctrl+C to stop)")
        try:
            await subscriber_task
        except KeyboardInterrupt:
            pass
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())