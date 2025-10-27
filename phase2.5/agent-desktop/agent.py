# agent-desktop/agent.py
"""
Rika Desktop Agent v2.5 for Windows
Enhanced with LiveKit streaming and secure remote control
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
from datetime import datetime, timedelta
from pynput import keyboard, mouse
from dotenv import load_dotenv
import win32gui
import win32process
import win32api
import win32con
from PIL import Image, ImageDraw, ImageFont, ImageGrab
from minio import Minio
import io
import tkinter as tk
from tkinter import messagebox
import subprocess

# Phase 2.5: LiveKit imports
try:
    from livekit import rtc, api
    LIVEKIT_AVAILABLE = True
except ImportError:
    print("⚠️ LiveKit not available - streaming will be disabled")
    LIVEKIT_AVAILABLE = False

# Load environment
load_dotenv()

# Configuration
CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8000")
NATS_URL = os.getenv("NATS_URL", "nats://rika_nats:NatsMsg2025RikaCore789@localhost:4222")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "rikaadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "RikaMinIO2025SecureStorage")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "rika-screenshots")

# Phase 2.5: Streaming configuration
LIVEKIT_WS_URL = os.getenv("LIVEKIT_WS_URL", "ws://localhost:7880")
STREAM_FPS = int(os.getenv("STREAM_FPS", "15"))
STREAM_BITRATE = int(os.getenv("STREAM_BITRATE_KBPS", "2000"))
STREAM_RESOLUTION = os.getenv("STREAM_RESOLUTION", "720p")
WATERMARK_ENABLED = os.getenv("WATERMARK_ENABLED", "true").lower() == "true"

HEARTBEAT_INTERVAL = 5  # seconds
THUMBNAIL_INTERVAL = 5  # seconds for view mode
DEVICE_TYPE = "desktop"

class ConsentBanner:
    """On-screen consent banner for streaming and control"""
    
    def __init__(self):
        self.window = None
        self.visible = False
        
    def show(self, mode: str, expires_at: datetime):
        """Show consent banner"""
        if self.visible:
            return
            
        self.visible = True
        
        def create_banner():
            self.window = tk.Tk()
            self.window.title("Rika Control Active")
            self.window.attributes('-topmost', True)
            self.window.attributes('-alpha', 0.9)
            
            # Position at top of screen
            self.window.geometry("400x60+{}+10".format(
                (self.window.winfo_screenwidth() - 400) // 2
            ))
            
            # Configure styling
            self.window.configure(bg='red' if mode == 'control' else 'blue')
            
            # Banner text
            text = f"🤖 Rika {mode.title()} Active"
            if expires_at:
                time_left = expires_at - datetime.utcnow()
                minutes = int(time_left.total_seconds() / 60)
                text += f" ({minutes}m left)"
                
            label = tk.Label(
                self.window, 
                text=text,
                font=('Arial', 12, 'bold'),
                fg='white',
                bg='red' if mode == 'control' else 'blue'
            )
            label.pack(expand=True)
            
            # Auto-hide timer
            def auto_hide():
                time.sleep(300)  # 5 minutes
                if self.window:
                    self.hide()
            
            threading.Thread(target=auto_hide, daemon=True).start()
            self.window.mainloop()
        
        # Run banner in separate thread
        threading.Thread(target=create_banner, daemon=True).start()
    
    def hide(self):
        """Hide consent banner"""
        if self.window:
            try:
                self.window.quit()
                self.window.destroy()
            except:
                pass
            self.window = None
            self.visible = False

class WatermarkOverlay:
    """Watermark overlay for streams"""
    
    @staticmethod
    def add_watermark(image: np.ndarray, device_name: str, timestamp: datetime) -> np.ndarray:
        """Add watermark to image"""
        if not WATERMARK_ENABLED:
            return image
            
        # Convert to PIL for text rendering
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Watermark text
        watermark_text = f"Linked by Rika – {device_name} @ {timestamp.strftime('%H:%M')}"
        
        # Position (bottom-right with padding)
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = pil_image.width - text_width - 20
        y = pil_image.height - text_height - 20
        
        # Semi-transparent background
        draw.rectangle(
            [(x-10, y-5), (x+text_width+10, y+text_height+5)], 
            fill=(0, 0, 0, 128)
        )
        
        # White text
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 255))
        
        # Convert back to OpenCV format
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

class LiveKitStreamer:
    """LiveKit streaming client"""
    
    def __init__(self, device_id: str, device_name: str):
        self.device_id = device_id
        self.device_name = device_name
        self.room = None
        self.local_video_track = None
        self.streaming = False
        self.stream_thread = None
        
    async def start_streaming(self, room_name: str, token: str):
        """Start LiveKit streaming"""
        if not LIVEKIT_AVAILABLE:
            print("⚠️ LiveKit not available - cannot start streaming")
            return False
            
        try:
            self.room = rtc.Room()
            
            # Connect to room
            await self.room.connect(LIVEKIT_WS_URL, token)
            print(f"📡 Connected to LiveKit room: {room_name}")
            
            # Start video capture
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start LiveKit streaming: {e}")
            return False
    
    def _stream_loop(self):
        """Video capture and streaming loop"""
        cap = None
        try:
            # Use screen capture instead of camera
            while self.streaming:
                # Capture screen
                screenshot = ImageGrab.grab()
                
                # Resize based on resolution setting
                if STREAM_RESOLUTION == "720p":
                    screenshot = screenshot.resize((1280, 720), Image.Resampling.LANCZOS)
                elif STREAM_RESOLUTION == "480p":
                    screenshot = screenshot.resize((854, 480), Image.Resampling.LANCZOS)
                
                # Convert to numpy array
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Add watermark
                frame = WatermarkOverlay.add_watermark(
                    frame, 
                    self.device_name, 
                    datetime.utcnow()
                )
                
                # Convert to VideoFrame (simplified - real implementation would use proper VideoFrame)
                # This is a placeholder - actual LiveKit integration would require proper video frame handling
                
                # Limit FPS
                time.sleep(1.0 / STREAM_FPS)
                
        except Exception as e:
            print(f"❌ Error in streaming loop: {e}")
        finally:
            if cap:
                cap.release()
    
    async def stop_streaming(self):
        """Stop LiveKit streaming"""
        self.streaming = False
        if self.room:
            await self.room.disconnect()
        print("📡 Stopped LiveKit streaming")

class RemoteControlHandler:
    """Handles remote control input events"""
    
    def __init__(self):
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.active = False
        
    def process_input_event(self, event_data: dict):
        """Process remote input event"""
        if not self.active:
            return
            
        try:
            event_type = event_data.get("type")
            payload = event_data.get("payload", {})
            
            if event_type == "mouse_move":
                x, y = payload.get("x", 0), payload.get("y", 0)
                self.mouse_controller.position = (x, y)
                
            elif event_type == "mouse_click":
                button_name = payload.get("button", "left")
                pressed = payload.get("pressed", True)
                
                if button_name == "left":
                    button = mouse.Button.left
                elif button_name == "right":
                    button = mouse.Button.right
                elif button_name == "middle":
                    button = mouse.Button.middle
                else:
                    return
                
                if pressed:
                    self.mouse_controller.press(button)
                else:
                    self.mouse_controller.release(button)
                    
            elif event_type == "mouse_scroll":
                dx, dy = payload.get("dx", 0), payload.get("dy", 0)
                self.mouse_controller.scroll(dx, dy)
                
            elif event_type == "key_press":
                key_name = payload.get("key")
                if key_name:
                    # Simple key mapping - extend as needed
                    if len(key_name) == 1:
                        self.keyboard_controller.press(key_name)
                    elif key_name == "enter":
                        self.keyboard_controller.press(keyboard.Key.enter)
                    elif key_name == "space":
                        self.keyboard_controller.press(keyboard.Key.space)
                    # Add more key mappings as needed
                        
            elif event_type == "key_release":
                key_name = payload.get("key")
                if key_name:
                    if len(key_name) == 1:
                        self.keyboard_controller.release(key_name)
                    elif key_name == "enter":
                        self.keyboard_controller.release(keyboard.Key.enter)
                    elif key_name == "space":
                        self.keyboard_controller.release(keyboard.Key.space)
                        
        except Exception as e:
            print(f"❌ Error processing input event: {e}")

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
        
        # Phase 2.5: Streaming and control
        self.livekit_streamer = None
        self.remote_control = RemoteControlHandler()
        self.consent_banner = ConsentBanner()
        self.control_active = False
        
        # MediaPipe for gesture recognition
        self.mp_hands = mp.solutions.hands
        self.hands = None
        self.mp_drawing = mp.solutions.drawing_utils
        self.camera = None
        
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
            
            # Initialize LiveKit streamer
            if LIVEKIT_AVAILABLE:
                self.livekit_streamer = LiveKitStreamer(self.device_id, device_name)
            
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
                    
                    # Initialize LiveKit streamer
                    if LIVEKIT_AVAILABLE:
                        device_name = f"{platform.node()}-{os.getenv('USERNAME', 'user')}"
                        self.livekit_streamer = LiveKitStreamer(self.device_id, device_name)
                    
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
            
            # Phase 2.5: Subscribe to control events
            await self.nc.subscribe("control.granted", cb=self.handle_control_granted)
            await self.nc.subscribe("control.revoked", cb=self.handle_control_revoked)
            await self.nc.subscribe(f"control.input.{self.device_id}", cb=self.handle_control_input)
            
            print("📡 Subscribed to all control channels")
            return True
        except Exception as e:
            print(f"❌ NATS connection failed: {e}")
            return False
    
    # ==================== Phase 2.5: New Event Handlers ====================
    
    async def handle_control_granted(self, msg):
        """Handle control granted event"""
        try:
            data = json.loads(msg.data.decode())
            if data.get("device_id") == self.device_id:
                print(f"\\n🎮 Control granted by {data.get('approver')}")
                print(f"   Expires at: {data.get('expires_at')}")
                
                # Activate remote control
                self.control_active = True
                self.remote_control.active = True
                
                # Show consent banner
                expires_at = datetime.fromisoformat(data.get('expires_at').replace('Z', '+00:00'))
                self.consent_banner.show('control', expires_at)
                
                print("   🔴 Remote control is now ACTIVE - consent banner displayed")
                
        except Exception as e:
            print(f"❌ Error handling control granted: {e}")
    
    async def handle_control_revoked(self, msg):
        """Handle control revoked event"""
        try:
            data = json.loads(msg.data.decode())
            if data.get("device_id") == self.device_id:
                print(f"\\n🔓 Control revoked - {data.get('reason')}")
                
                # Deactivate remote control
                self.control_active = False
                self.remote_control.active = False
                
                # Hide consent banner
                self.consent_banner.hide()
                
        except Exception as e:
            print(f"❌ Error handling control revoked: {e}")
    
    async def handle_control_input(self, msg):
        """Handle remote control input event"""
        try:
            data = json.loads(msg.data.decode())
            if self.control_active:
                self.remote_control.process_input_event(data)
        except Exception as e:
            print(f"❌ Error handling control input: {e}")
    
    # ==================== Enhanced Link Handlers ====================
    
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
                    await self.start_streaming()
                elif self.link_mode == "control":
                    print("   Remote control mode - waiting for approval")
                    
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
                old_mode = self.link_mode
                self.link_mode = None
                self.gestures_enabled = False
                
                # Stop streaming if active
                if old_mode in ["extend", "view"] and self.livekit_streamer:
                    await self.livekit_streamer.stop_streaming()
                
                # Stop hands-on mode
                if self.hands_on_mode:
                    self.hands_on_mode = False
                    if self.camera:
                        self.camera.release()
                        self.camera = None
                
                # Hide consent banner
                self.consent_banner.hide()
                
        except Exception as e:
            print(f"❌ Error handling link removed: {e}")
    
    # ==================== Streaming Functions ====================
    
    async def start_streaming(self):
        """Start LiveKit streaming for extend mode"""
        if not self.livekit_streamer:
            print("⚠️ LiveKit streamer not available")
            return
            
        try:
            # Get streaming token from Core API
            response = requests.get(f"{CORE_API_URL}/streams")
            if response.status_code == 200:
                streams = response.json()
                
                # Find our device stream
                our_stream = None
                for stream in streams:
                    if stream["device_id"] == self.device_id:
                        our_stream = stream
                        break
                
                if our_stream:
                    success = await self.livekit_streamer.start_streaming(
                        our_stream["room_name"],
                        our_stream["participant_token"]
                    )
                    
                    if success:
                        print("📡 LiveKit streaming started successfully")
                        
                        # Show streaming consent banner
                        expires_at = datetime.fromisoformat(our_stream["expires_at"].replace('Z', '+00:00'))
                        self.consent_banner.show('streaming', expires_at)
                    else:
                        print("❌ Failed to start LiveKit streaming")
                else:
                    print("❌ Stream configuration not found")
            else:
                print(f"❌ Failed to get stream configuration: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error starting streaming: {e}")
    
    async def thumbnail_loop(self):
        """Enhanced thumbnail capture with watermarks"""
        print("📸 Starting thumbnail capture loop")
        
        while self.running and self.linked and self.link_mode == "view":
            try:
                # Capture screenshot
                screenshot = ImageGrab.grab()
                screenshot.thumbnail((400, 300), Image.Resampling.LANCZOS)
                
                # Convert to numpy for watermark processing
                img_array = np.array(screenshot)
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                # Add watermark
                device_name = f"{platform.node()}-{os.getenv('USERNAME', 'user')}"
                img_array = WatermarkOverlay.add_watermark(img_array, device_name, datetime.utcnow())
                
                # Convert back to PIL
                watermarked_image = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))
                
                # Convert to bytes
                img_bytes = io.BytesIO()
                watermarked_image.save(img_bytes, format='JPEG', quality=85)
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
                    
                    print(f"📸 Watermarked thumbnail uploaded: {object_name}", end="\\r")
                
            except Exception as e:
                print(f"\\n⚠️ Thumbnail capture failed: {e}")
            
            await asyncio.sleep(THUMBNAIL_INTERVAL)
    
    # ==================== Existing handlers (keep from Phase 2) ====================
    
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
        """Enhanced blackout handling"""
        data = json.loads(msg.data.decode())
        print(f"\\n🚨 BLACKOUT EVENT RECEIVED!")
        print(f"   Reason: {data.get('reason')}")
        print(f"   Triggered by: {data.get('triggered_by')}")
        print("   Shutting down agent...")
        
        # Stop all activities
        self.linked = False
        self.link_mode = None
        self.hands_on_mode = False
        self.control_active = False
        self.remote_control.active = False
        
        # Stop streaming
        if self.livekit_streamer:
            await self.livekit_streamer.stop_streaming()
            
        # Hide consent banner
        self.consent_banner.hide()
        
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
    
    # ==================== Gesture Recognition (keep from Phase 2) ====================
    
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
    
    # ==================== Enhanced Heartbeat ====================
    
    async def send_heartbeat(self):
        """Send enhanced heartbeat with streaming/control status"""
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
                            "hands_on_mode": self.hands_on_mode,
                            "streaming": self.livekit_streamer and self.livekit_streamer.streaming if self.livekit_streamer else False,
                            "control_active": self.control_active,
                            "consent_banner_visible": self.consent_banner.visible
                        }
                    },
                    headers={"Authorization": f"Bearer {self.session_token}"}
                )
                
                if response.status_code == 200:
                    self.last_heartbeat = datetime.utcnow()
                    
                    # Status indicators
                    status_parts = []
                    if self.linked:
                        status_parts.append(f"🔗 {self.link_mode}")
                    if self.control_active:
                        status_parts.append("🎮")
                    if self.livekit_streamer and self.livekit_streamer.streaming:
                        status_parts.append("📡")
                    
                    status_text = " ".join(status_parts) if status_parts else "💓"
                    print(f"{status_text} Heartbeat sent - App: {app_name[:30]}", end="\\r")
                
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
        
        def on_control_revoke_hotkey():
            """Emergency control revoke"""
            if self.control_active:
                print("\\n🔓 Emergency control revoke!")
                try:
                    response = requests.post(
                        f"{CORE_API_URL}/control/revoke",
                        json={
                            "device_id": self.device_id,
                            "reason": "Emergency revoke via hotkey"
                        }
                    )
                    print(f"   Control revoked: {response.status_code}")
                except Exception as e:
                    print(f"   Control revoke failed: {e}")
        
        # Setup hotkeys
        hotkeys = [
            (keyboard.HotKey.parse('<ctrl>+<shift>+r'), on_blackout_hotkey),
            (keyboard.HotKey.parse('<ctrl>+<shift>+h'), on_hands_on_hotkey),
            (keyboard.HotKey.parse('<ctrl>+<shift>+x'), on_control_revoke_hotkey)
        ]
        
        def for_canonical(f):
            return lambda k: f(listener.canonical(k))
        
        def on_press(key):
            for hotkey, _ in hotkeys:
                hotkey.press(listener.canonical(key))
        
        def on_release(key):
            for hotkey, _ in hotkeys:
                hotkey.release(listener.canonical(key))
        
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        
        print("⌨️ Hotkeys registered:")
        print("   Ctrl+Shift+R for blackout")
        print("   Ctrl+Shift+H for hands-on mode")
        print("   Ctrl+Shift+X for emergency control revoke")
        
        return listener
    
    async def run(self):
        """Main agent loop"""
        print("=" * 50)
        print("🤖 Rika Desktop Agent v2.5 - Phase 2.5")
        print("🔧 LiveKit Streaming & Remote Control")
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
        print("   New hotkeys: Ctrl+Shift+X (emergency control revoke)")
        print(f"   Streaming: {'✅ Available' if LIVEKIT_AVAILABLE else '❌ Disabled'}")
        print(f"   Watermarks: {'✅ Enabled' if WATERMARK_ENABLED else '❌ Disabled'}\\n")
        
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
            if self.livekit_streamer:
                await self.livekit_streamer.stop_streaming()
            self.consent_banner.hide()
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