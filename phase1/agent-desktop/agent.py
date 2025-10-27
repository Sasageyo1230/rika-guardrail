# agent-desktop/agent.py
"""
Rika Desktop Agent v0 for Windows
Monitors system activity and communicates with Rika Core
"""

import os
import sys
import time
import json
import asyncio
import threading
import platform
import hashlib
import requests
import psutil
import nats
from datetime import datetime
from pynput import keyboard
from dotenv import load_dotenv
import win32gui
import win32process

# Load environment
load_dotenv()

# Configuration
CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8000")
NATS_URL = os.getenv("NATS_URL", "nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222")
HEARTBEAT_INTERVAL = 5  # seconds
DEVICE_TYPE = "desktop"

# Global state
device_id = None
session_token = None
nc = None
running = True
enrolled = False

class RikaDesktopAgent:
    def __init__(self):
        self.device_id = None
        self.session_token = None
        self.nc = None
        self.running = True
        self.enrolled = False
        self.current_app = None
        self.last_heartbeat = None
        
    def get_device_fingerprint(self):
        """Generate unique device fingerprint"""
        # Combine various hardware/system identifiers
        fingerprint_data = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", "unknown")
        }
        
        # Create hash of the data
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()
        return fingerprint
    
    def get_active_window(self):
        """Get currently active window and application"""
        try:
            window = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(window)
            
            # Get process name
            try:
                _, pid = win32process.GetWindowThreadProcessId(window)
                process = psutil.Process(pid)
                app_name = process.name()
            except:
                app_name = "Unknown"
            
            return app_name, window_title
        except Exception as e:
            return "Unknown", ""
    
    async def enroll(self):
        """Enroll device with Core API"""
        print("🔐 Starting device enrollment...")
        
        # Step 1: Request enrollment token
        device_name = f"{platform.node()}-{os.getenv('USERNAME', 'user')}"
        
        try:
            response = requests.post(
                f"{CORE_API_URL}/enroll",
                json={
                    "device_name": device_name,
                    "device_type": DEVICE_TYPE
                }
            )
            response.raise_for_status()
            enroll_data = response.json()
            token = enroll_data["token"]
            print(f"✅ Got enrollment token: {token[:8]}...")
            
            # Step 2: Complete enrollment with fingerprint
            fingerprint = self.get_device_fingerprint()
            response = requests.post(
                f"{CORE_API_URL}/enroll/complete",
                json={
                    "token": token,
                    "fingerprint": fingerprint
                }
            )
            response.raise_for_status()
            complete_data = response.json()
            
            self.device_id = complete_data["device_id"]
            self.session_token = complete_data["credentials"]["session_token"]
            self.enrolled = True
            
            # Save credentials
            with open(".rika_agent", "w") as f:
                json.dump({
                    "device_id": self.device_id,
                    "session_token": self.session_token,
                    "enrolled_at": datetime.utcnow().isoformat()
                }, f)
            
            print(f"✅ Device enrolled successfully!")
            print(f"   Device ID: {self.device_id}")
            print(f"   NATS subjects: {complete_data['nats_subjects']}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Enrollment failed: {e}")
            return False
    
    def load_credentials(self):
        """Load saved credentials"""
        try:
            if os.path.exists(".rika_agent"):
                with open(".rika_agent", "r") as f:
                    creds = json.load(f)
                    self.device_id = creds["device_id"]
                    self.session_token = creds["session_token"]
                    self.enrolled = True
                    print(f"✅ Loaded saved credentials for device {self.device_id}")
                    return True
        except Exception as e:
            print(f"⚠️ Could not load credentials: {e}")
        return False
    
    async def connect_nats(self):
        """Connect to NATS messaging"""
        try:
            self.nc = await nats.connect(NATS_URL)
            print(f"✅ Connected to NATS")
            
            # Subscribe to device-specific control channel
            await self.nc.subscribe(f"device.{self.device_id}.control", cb=self.handle_control_message)
            await self.nc.subscribe("blackout", cb=self.handle_blackout)
            await self.nc.subscribe("handoff.requested", cb=self.handle_handoff)
            
            print("📡 Subscribed to control channels")
            return True
        except Exception as e:
            print(f"❌ NATS connection failed: {e}")
            return False
    
    async def handle_control_message(self, msg):
        """Handle device control messages"""
        try:
            data = json.loads(msg.data.decode())
            print(f"\n🎮 Control message received: {data}")
            
            # Handle different control commands
            if data.get("action") == "open_url":
                url = data.get("url")
                if url:
                    os.system(f'start {url}')
                    print(f"   Opened URL: {url}")
                    
            elif data.get("action") == "follow_mode":
                print(f"   Follow mode: {data}")
                # Implement follow mode actions
                
        except Exception as e:
            print(f"❌ Error handling control message: {e}")
    
    async def handle_blackout(self, msg):
        """Handle blackout event"""
        data = json.loads(msg.data.decode())
        print(f"\n🚨 BLACKOUT EVENT RECEIVED!")
        print(f"   Reason: {data.get('reason')}")
        print(f"   Triggered by: {data.get('triggered_by')}")
        print("   Shutting down agent...")
        self.running = False
    
    async def handle_handoff(self, msg):
        """Handle handoff request"""
        data = json.loads(msg.data.decode())
        if data.get("to_device") == self.device_id:
            print(f"\n📱 Handoff requested from {data.get('from_device')}")
            context = data.get("context", {})
            
            # Handle handoff based on context
            if "url" in context:
                os.system(f'start {context["url"]}')
                print(f"   Opened handoff URL: {context['url']}")
    
    async def send_heartbeat(self):
        """Send heartbeat to Core API"""
        while self.running:
            try:
                app_name, window_title = self.get_active_window()
                
                response = requests.post(
                    f"{CORE_API_URL}/heartbeat",
                    json={
                        "device_id": self.device_id,
                        "current_app": app_name,
                        "window_title": window_title,
                        "metadata": {
                            "cpu_percent": psutil.cpu_percent(),
                            "memory_percent": psutil.virtual_memory().percent
                        }
                    },
                    headers={"Authorization": f"Bearer {self.session_token}"}
                )
                
                if response.status_code == 200:
                    self.last_heartbeat = datetime.utcnow()
                    print(f"💓 Heartbeat sent - App: {app_name[:30]}", end="\r")
                
            except Exception as e:
                print(f"\n⚠️ Heartbeat failed: {e}")
            
            await asyncio.sleep(HEARTBEAT_INTERVAL)
    
    def setup_hotkeys(self):
        """Setup keyboard hotkeys"""
        def on_hotkey():
            print("\n🔥 Blackout hotkey triggered!")
            try:
                response = requests.post(
                    f"{CORE_API_URL}/blackout",
                    json={
                        "device_id": self.device_id,
                        "reason": "Manual blackout via hotkey"
                    }
                )
                print(f"   Blackout response: {response.status_code}")
            except Exception as e:
                print(f"   Blackout request failed: {e}")
        
        # Setup Ctrl+Shift+R for blackout
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<ctrl>+<shift>+r'),
            on_hotkey
        )
        
        def for_canonical(f):
            return lambda k: f(listener.canonical(k))
        
        listener = keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release)
        )
        listener.start()
        print("⌨️ Hotkey registered: Ctrl+Shift+R for blackout")
        return listener
    
    async def run(self):
        """Main agent loop"""
        print("=" * 50)
        print("🤖 Rika Desktop Agent v0")
        print("=" * 50)
        
        # Load or enroll
        if not self.load_credentials():
            if not await self.enroll():
                print("❌ Failed to enroll device. Exiting.")
                return
        
        # Connect to NATS
        if not await self.connect_nats():
            print("⚠️ Running without NATS connection")
        
        # Setup hotkeys
        hotkey_listener = self.setup_hotkeys()
        
        # Start heartbeat
        print("\n💚 Agent running... Press Ctrl+C to stop")
        print("   Hotkey: Ctrl+Shift+R to trigger blackout\n")
        
        try:
            # Run heartbeat
            await self.send_heartbeat()
        except KeyboardInterrupt:
            print("\n👋 Shutting down agent...")
        finally:
            self.running = False
            if self.nc:
                await self.nc.close()
            hotkey_listener.stop()

async def main():
    agent = RikaDesktopAgent()
    await agent.run()

if __name__ == "__main__":
    # Check if running on Windows
    if platform.system() != "Windows":
        print("❌ This agent is designed for Windows only")
        sys.exit(1)
    
    # Run the agent
    asyncio.run(main())