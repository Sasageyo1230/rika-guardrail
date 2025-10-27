# agent-desktop/agent.py
"""
Rika Desktop Agent v2 for Windows
Monitors system activity, communicates with Rika Core, and handles linking modes
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
import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime
from pynput import keyboard, mouse
from dotenv import load_dotenv
import win32gui
import win32process
import win32api
import win32con
from PIL import ImageGrab
from minio import Minio
import io

# Load environment
load_dotenv()

# Configuration
CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8000")
NATS_URL = os.getenv("NATS_URL", "nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "rikaadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "RikaMinIO2025SecureStorage")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "rika-screenshots")

HEARTBEAT_INTERVAL = 5  # seconds
THUMBNAIL_INTERVAL = 5  # seconds for view mode
DEVICE_TYPE = "desktop"

class RikaDesktopAgent:
    def __init__(self):
        self.device_id = None
        self.session_token = None
        self.nc = None
        self.minio_client = None
        self.running = True
        self.enrolled = False
        self.current_app = None
        self.last_heartbeat = None
        
        # Phase 2: Linking state
        self.linked = False
        self.link_mode = None
        self.gestures_enabled = False
        self.hands_on_mode = False
        
        # MediaPipe for gesture recognition
        self.mp_hands = mp.solutions.hands
        self.hands = None
        self.mp_drawing = mp.solutions.drawing_utils
        self.camera = None
        
        # Input control
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
    def get_device_fingerprint(self):
        """Generate unique device fingerprint"""
        fingerprint_data = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", "unknown")
        }
        
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()
        return fingerprint
    
    def get_active_window(self):
        """Get currently active window and application"""
        try:
            window = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(window)
            
            try:
                _, pid = win32process.GetWindowThreadProcessId(window)
                process = psutil.Process(pid)
                app_name = process.name()
            except:
                app_name = "Unknown"
            
            return app_name, window_title
        except Exception as e:
            return "Unknown", ""
    
    async def init_minio(self):
        """Initialize MinIO client"""
        try:
            self.minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )
            
            # Create bucket if it doesn't exist
            if not self.minio_client.bucket_exists(MINIO_BUCKET):
                self.minio_client.make_bucket(MINIO_BUCKET)
                
            print(f"✅ Connected to MinIO at {MINIO_ENDPOINT}")
            return True
        except Exception as e:
            print(f"⚠️ MinIO connection failed: {e}")
            return False
    
    async def enroll(self):
        """Enroll device with Core API"""
        print("🔐 Starting device enrollment...")
        
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
            
            # Subscribe to control channels
            await self.nc.subscribe(f"device.{self.device_id}.control", cb=self.handle_control_message)
            await self.nc.subscribe("blackout", cb=self.handle_blackout)
            await self.nc.subscribe("handoff.requested", cb=self.handle_handoff)
            
            # Phase 2: Subscribe to link events
            await self.nc.subscribe("link.added", cb=self.handle_link_added)
            await self.nc.subscribe("link.removed", cb=self.handle_link_removed)
            await self.nc.subscribe("hands_on.enabled", cb=self.handle_hands_on_enabled)
            await self.nc.subscribe("hands_on.disabled", cb=self.handle_hands_on_disabled)
            
            print("📡 Subscribed to control channels")
            return True
        except Exception as e:
            print(f"❌ NATS connection failed: {e}")
            return False
    
    async def handle_control_message(self, msg):
        """Handle device control messages"""
        try:
            data = json.loads(msg.data.decode())
            print(f"\\n🎮 Control message received: {data}")
            
            if data.get("action") == "open_url":
                url = data.get("url")
                if url:
                    os.system(f'start {url}')
                    print(f"   Opened URL: {url}")
                    
            elif data.get("action") == "follow_mode":
                print(f"   Follow mode: {data}")
                    
        except Exception as e:
            print(f"❌ Error handling control message: {e}")
    
    async def handle_blackout(self, msg):
        """Handle blackout event"""
        data = json.loads(msg.data.decode())
        print(f"\\n🚨 BLACKOUT EVENT RECEIVED!")
        print(f"   Reason: {data.get('reason')}")
        print(f"   Triggered by: {data.get('triggered_by')}")
        print("   Shutting down agent...")
        
        # Stop all linking activities
        self.linked = False
        self.link_mode = None
        self.hands_on_mode = False
        if self.camera:
            self.camera.release()
        
        self.running = False
    
    async def handle_handoff(self, msg):
        """Handle handoff request"""
        data = json.loads(msg.data.decode())
        if data.get("to_device") == self.device_id:
            print(f"\\n📱 Handoff requested from {data.get('from_device')}")
            context = data.get("context", {})
            
            if "url" in context:
                os.system(f'start {context["url"]}')
                print(f"   Opened handoff URL: {context['url']}")
    
    # ==================== Phase 2: Link Event Handlers ====================
    
    async def handle_link_added(self, msg):
        """Handle device link added event"""
        try:
            data = json.loads(msg.data.decode())
            if data.get("device_id") == self.device_id:
                self.linked = True
                self.link_mode = data.get("mode")
                self.gestures_enabled = data.get("gestures_enabled", False)
                
                print(f"\\n🔗 Device linked in {self.link_mode} mode")
                print(f"   Gestures enabled: {self.gestures_enabled}")
                print(f"   Expires at: {data.get('expires_at')}")
                
                # Start mode-specific activities
                if self.link_mode == "view":
                    asyncio.create_task(self.thumbnail_loop())
                elif self.link_mode == "extend":
                    print("   LiveKit streaming would start here")
                elif self.link_mode == "control":
                    print("   Remote control enabled")
                    
        except Exception as e:
            print(f"❌ Error handling link added: {e}")
    
    async def handle_link_removed(self, msg):
        """Handle device link removed event"""
        try:
            data = json.loads(msg.data.decode())
            if data.get("device_id") == self.device_id:
                print(f"\\n🔓 Device unlinked - {data.get('reason')}")
                
                # Stop all linking activities
                self.linked = False
                self.link_mode = None
                self.gestures_enabled = False
                
                # Stop hands-on mode if active
                if self.hands_on_mode:
                    self.hands_on_mode = False
                    if self.camera:
                        self.camera.release()
                        self.camera = None
                    
        except Exception as e:
            print(f"❌ Error handling link removed: {e}")
    
    async def handle_hands_on_enabled(self, msg):
        """Handle hands-on mode enabled"""
        try:
            data = json.loads(msg.data.decode())
            if data.get("device_id") == self.device_id:
                self.hands_on_mode = True
                print(f"\\n👋 Hands-on mode enabled")
                
                # Initialize camera and gesture recognition
                self.camera = cv2.VideoCapture(0)
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.7,
                    min_tracking_confidence=0.5
                )
                
                # Start gesture recognition loop
                asyncio.create_task(self.gesture_loop())
                
        except Exception as e:
            print(f"❌ Error enabling hands-on mode: {e}")
    
    async def handle_hands_on_disabled(self, msg):
        """Handle hands-on mode disabled"""
        try:
            data = json.loads(msg.data.decode())
            if data.get("device_id") == self.device_id:
                self.hands_on_mode = False
                print(f"\\n🚫 Hands-on mode disabled")
                
                # Clean up camera resources
                if self.camera:
                    self.camera.release()
                    self.camera = None
                if self.hands:
                    self.hands.close()
                    
        except Exception as e:
            print(f"❌ Error disabling hands-on mode: {e}")
    
    # ==================== Phase 2: Linking Behaviors ====================
    
    async def thumbnail_loop(self):
        """Capture and upload thumbnails in view mode"""
        print("📸 Starting thumbnail capture loop")
        
        while self.running and self.linked and self.link_mode == "view":
            try:
                # Capture screenshot
                screenshot = ImageGrab.grab()
                screenshot.thumbnail((400, 300), resample=Image.LANCZOS)
                
                # Convert to bytes
                img_bytes = io.BytesIO()
                screenshot.save(img_bytes, format='JPEG', quality=85)
                img_bytes.seek(0)
                
                # Upload to MinIO
                if self.minio_client:
                    object_name = f"thumbnails/{self.device_id}/latest.jpg"
                    self.minio_client.put_object(
                        MINIO_BUCKET,
                        object_name,
                        img_bytes,
                        length=img_bytes.getbuffer().nbytes,
                        content_type="image/jpeg"
                    )
                    
                    print(f"📸 Thumbnail uploaded: {object_name}", end="\\r")
                
            except Exception as e:
                print(f"\\n⚠️ Thumbnail capture failed: {e}")
            
            await asyncio.sleep(THUMBNAIL_INTERVAL)
    
    async def gesture_loop(self):
        """Process gestures in hands-on mode"""
        print("👋 Starting gesture recognition loop")
        
        while self.running and self.hands_on_mode and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    continue
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        gesture = self.recognize_gesture(hand_landmarks)
                        if gesture:
                            await self.handle_gesture(gesture)
                
                # Small delay to prevent excessive processing
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"\\n⚠️ Gesture processing error: {e}")
                await asyncio.sleep(1)
    
    def recognize_gesture(self, landmarks):
        """Recognize gestures from hand landmarks"""
        try:
            # Get landmark positions
            thumb_tip = landmarks.landmark[4]
            index_tip = landmarks.landmark[8]
            middle_tip = landmarks.landmark[12]
            ring_tip = landmarks.landmark[16]
            pinky_tip = landmarks.landmark[20]
            
            # Simple gesture recognition
            # Closed fist (grab)
            if (thumb_tip.y > landmarks.landmark[3].y and
                index_tip.y > landmarks.landmark[6].y and
                middle_tip.y > landmarks.landmark[10].y):
                return "grab"
            
            # Open hand (throw/release)
            if (thumb_tip.y < landmarks.landmark[3].y and
                index_tip.y < landmarks.landmark[6].y and
                middle_tip.y < landmarks.landmark[10].y):
                return "throw"
            
            # Swipe down (blackout)
            if (index_tip.y > 0.7 and middle_tip.y > 0.7):
                return "swipe_down"
                
        except Exception as e:
            print(f"Gesture recognition error: {e}")
        
        return None
    
    async def handle_gesture(self, gesture):
        """Handle recognized gestures"""
        try:
            if gesture == "grab":
                print("\\n👊 Grab gesture detected")
                
            elif gesture == "throw":
                print("\\n🤚 Throw gesture detected - triggering handoff")
                # TODO: Implement handoff to nearest linked device
                
            elif gesture == "swipe_down":
                print("\\n👇 Swipe down gesture - triggering blackout")
                response = requests.post(
                    f"{CORE_API_URL}/blackout",
                    json={
                        "device_id": self.device_id,
                        "reason": "Gesture-triggered blackout"
                    }
                )
                
        except Exception as e:
            print(f"❌ Error handling gesture: {e}")
    
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
                            "memory_percent": psutil.virtual_memory().percent,
                            "linked": self.linked,
                            "link_mode": self.link_mode,
                            "hands_on_mode": self.hands_on_mode
                        }
                    },
                    headers={"Authorization": f"Bearer {self.session_token}"}
                )
                
                if response.status_code == 200:
                    self.last_heartbeat = datetime.utcnow()
                    status_icon = "🔗" if self.linked else "💓"
                    mode_text = f" ({self.link_mode})" if self.linked else ""
                    print(f"{status_icon} Heartbeat sent{mode_text} - App: {app_name[:30]}", end="\\r")
                
            except Exception as e:
                print(f"\\n⚠️ Heartbeat failed: {e}")
            
            await asyncio.sleep(HEARTBEAT_INTERVAL)
    
    def setup_hotkeys(self):
        """Setup keyboard hotkeys"""
        def on_blackout_hotkey():
            print("\\n🔥 Blackout hotkey triggered!")
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
        
        def on_hands_on_hotkey():
            print("\\n👋 Hands-on mode toggle!")
            try:
                new_state = not self.hands_on_mode
                response = requests.post(
                    f"{CORE_API_URL}/hands-on",
                    json={
                        "device_id": self.device_id,
                        "enabled": new_state
                    }
                )
                print(f"   Hands-on mode {'enabled' if new_state else 'disabled'}")
            except Exception as e:
                print(f"   Hands-on toggle failed: {e}")
        
        # Setup Ctrl+Shift+R for blackout
        blackout_hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<ctrl>+<shift>+r'),
            on_blackout_hotkey
        )
        
        # Setup Ctrl+Shift+H for hands-on mode
        hands_on_hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<ctrl>+<shift>+h'),
            on_hands_on_hotkey
        )
        
        def for_canonical(f):
            return lambda k: f(listener.canonical(k))
        
        def on_press(key):
            blackout_hotkey.press(listener.canonical(key))
            hands_on_hotkey.press(listener.canonical(key))
        
        def on_release(key):
            blackout_hotkey.release(listener.canonical(key))
            hands_on_hotkey.release(listener.canonical(key))
        
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        
        print("⌨️ Hotkeys registered:")
        print("   Ctrl+Shift+R for blackout")
        print("   Ctrl+Shift+H for hands-on mode")
        
        return listener
    
    async def run(self):
        """Main agent loop"""
        print("=" * 50)
        print("🤖 Rika Desktop Agent v2 - Phase 2")
        print("=" * 50)
        
        # Load or enroll
        if not self.load_credentials():
            if not await self.enroll():
                print("❌ Failed to enroll device. Exiting.")
                return
        
        # Initialize MinIO
        await self.init_minio()
        
        # Connect to NATS
        if not await self.connect_nats():
            print("⚠️ Running without NATS connection")
        
        # Setup hotkeys
        hotkey_listener = self.setup_hotkeys()
        
        # Start heartbeat
        print("\\n💚 Agent running... Press Ctrl+C to stop")
        print("   Hotkeys: Ctrl+Shift+R (blackout), Ctrl+Shift+H (hands-on)\\n")
        
        try:
            # Run heartbeat
            await self.send_heartbeat()
        except KeyboardInterrupt:
            print("\\n👋 Shutting down agent...")
        finally:
            self.running = False
            if self.nc:
                await self.nc.close()
            if self.camera:
                self.camera.release()
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