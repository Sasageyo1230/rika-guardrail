# phase3.2/agents/desktop/desktop_agent.py
# Desktop Agent - Environment & Device Control

import asyncio
import json
import logging
import struct
import subprocess
import time
from typing import Dict, List, Optional, Any
import platform
import threading

# Core imports
import bleak
import cv2
import mediapipe as mp
import numpy as np
from pycec import CECAdapter
import asyncpg
import httpx
import structlog

# Local imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'subagents', 'sdk'))
from n8n_client import RigAgentN8nClient

logger = structlog.get_logger()

class BluetoothManager:
    """Manages Bluetooth device discovery and connections"""
    
    def __init__(self):
        self.discovered_devices = {}
        self.connected_devices = {}
        self.scan_duration = 10
        
    async def scan_devices(self, timeout: int = 10) -> List[Dict]:
        """Scan for nearby Bluetooth devices"""
        try:
            logger.info("Starting Bluetooth device scan")
            devices = []
            
            def detection_callback(device, advertisement_data):
                device_info = {
                    "address": device.address,
                    "name": device.name or "Unknown Device",
                    "rssi": advertisement_data.rssi,
                    "services": list(advertisement_data.service_uuids),
                    "manufacturer_data": dict(advertisement_data.manufacturer_data),
                    "local_name": advertisement_data.local_name
                }
                
                if device.address not in self.discovered_devices:
                    self.discovered_devices[device.address] = device_info
                    devices.append(device_info)
                    logger.info(f"Discovered device: {device.name} ({device.address})")
            
            async with bleak.BleakScanner(detection_callback) as scanner:
                await asyncio.sleep(timeout)
                
            logger.info(f"Scan complete. Found {len(devices)} devices")
            return devices
            
        except Exception as e:
            logger.error(f"Bluetooth scan failed: {e}")
            return []
    
    async def connect_device(self, address: str) -> bool:
        """Connect to a Bluetooth device"""
        try:
            if address in self.connected_devices:
                logger.warning(f"Already connected to {address}")
                return True
                
            client = bleak.BleakClient(address)
            await client.connect()
            
            if client.is_connected:
                self.connected_devices[address] = client
                logger.info(f"Connected to device: {address}")
                return True
            else:
                logger.error(f"Failed to connect to {address}")
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect_device(self, address: str) -> bool:
        """Disconnect from a Bluetooth device"""
        try:
            if address not in self.connected_devices:
                logger.warning(f"Not connected to {address}")
                return True
                
            client = self.connected_devices[address]
            await client.disconnect()
            del self.connected_devices[address]
            
            logger.info(f"Disconnected from device: {address}")
            return True
            
        except Exception as e:
            logger.error(f"Disconnection failed: {e}")
            return False
    
    async def get_device_services(self, address: str) -> List[Dict]:
        """Get services from connected device"""
        try:
            if address not in self.connected_devices:
                logger.error(f"Not connected to {address}")
                return []
                
            client = self.connected_devices[address]
            services = []
            
            for service in client.services:
                service_info = {
                    "uuid": service.uuid,
                    "description": service.description,
                    "characteristics": []
                }
                
                for char in service.characteristics:
                    char_info = {
                        "uuid": char.uuid,
                        "properties": char.properties,
                        "descriptors": [desc.uuid for desc in char.descriptors]
                    }
                    service_info["characteristics"].append(char_info)
                
                services.append(service_info)
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return []

class HDMICECController:
    """Controls devices via HDMI-CEC"""
    
    def __init__(self):
        self.adapter = None
        self.devices = {}
        
    async def initialize(self) -> bool:
        """Initialize CEC adapter"""
        try:
            # Try to find CEC adapter
            self.adapter = CECAdapter()
            await asyncio.sleep(1)  # Give adapter time to initialize
            
            logger.info("HDMI-CEC adapter initialized")
            await self.scan_devices()
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize CEC: {e}")
            return False
    
    async def scan_devices(self):
        """Scan for CEC devices"""
        try:
            if not self.adapter:
                return
                
            # Scan logical addresses 0-15
            for addr in range(16):
                try:
                    # Send ping to check if device exists
                    response = self.adapter.ping(addr)
                    if response:
                        device_info = {
                            "address": addr,
                            "name": f"CEC Device {addr}",
                            "type": self._get_device_type(addr),
                            "active": True
                        }
                        
                        # Try to get device name
                        try:
                            osd_name = self.adapter.get_osd_name(addr)
                            if osd_name:
                                device_info["name"] = osd_name
                        except:
                            pass
                            
                        self.devices[addr] = device_info
                        logger.info(f"Found CEC device: {device_info}")
                        
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"CEC device scan failed: {e}")
    
    def _get_device_type(self, address: int) -> str:
        """Get device type from logical address"""
        device_types = {
            0: "TV",
            1: "Recording Device",
            2: "Reserved",
            3: "Tuner", 
            4: "Playback Device",
            5: "Audio System",
            6: "Tuner",
            7: "Tuner",
            8: "Playback Device",
            9: "Recording Device",
            10: "Tuner",
            11: "Playback Device",
            14: "Free Use",
            15: "Unregistered/Broadcast"
        }
        return device_types.get(address, "Unknown")
    
    async def power_on(self, address: int) -> bool:
        """Power on CEC device"""
        try:
            if not self.adapter:
                return False
                
            self.adapter.power_on(address)
            logger.info(f"Sent power ON to CEC device {address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to power on device {address}: {e}")
            return False
    
    async def power_off(self, address: int) -> bool:
        """Power off CEC device"""
        try:
            if not self.adapter:
                return False
                
            self.adapter.standby(address)
            logger.info(f"Sent STANDBY to CEC device {address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to power off device {address}: {e}")
            return False
    
    async def set_active_source(self, address: int) -> bool:
        """Set device as active source"""
        try:
            if not self.adapter:
                return False
                
            self.adapter.set_active_source(address)
            logger.info(f"Set CEC device {address} as active source")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set active source {address}: {e}")
            return False

class IRController:
    """Controls devices via infrared (requires LIRC or similar)"""
    
    def __init__(self):
        self.remote_configs = {}
        self.lirc_available = False
        
    async def initialize(self) -> bool:
        """Initialize IR controller"""
        try:
            # Check if LIRC is available
            result = subprocess.run(['which', 'irsend'], capture_output=True, text=True)
            self.lirc_available = result.returncode == 0
            
            if self.lirc_available:
                logger.info("LIRC IR controller available")
                await self.load_remote_configs()
            else:
                logger.warning("LIRC not available - IR control disabled")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize IR: {e}")
            return False
    
    async def load_remote_configs(self):
        """Load available remote configurations"""
        try:
            result = subprocess.run(['irsend', 'LIST', '', ''], capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        remote_name = parts[1]
                        self.remote_configs[remote_name] = {"name": remote_name, "commands": []}
            
            # Get commands for each remote
            for remote in self.remote_configs:
                result = subprocess.run(['irsend', 'LIST', remote, ''], capture_output=True, text=True)
                commands = []
                
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            commands.append(parts[1])
                            
                self.remote_configs[remote]["commands"] = commands
                
            logger.info(f"Loaded {len(self.remote_configs)} IR remote configurations")
            
        except Exception as e:
            logger.error(f"Failed to load IR configs: {e}")
    
    async def send_command(self, remote: str, command: str) -> bool:
        """Send IR command"""
        try:
            if not self.lirc_available:
                logger.error("LIRC not available")
                return False
                
            if remote not in self.remote_configs:
                logger.error(f"Remote {remote} not found")
                return False
                
            result = subprocess.run(['irsend', 'SEND_ONCE', remote, command], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Sent IR command: {remote} {command}")
                return True
            else:
                logger.error(f"IR command failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send IR command: {e}")
            return False

class GestureController:
    """MediaPipe-based gesture recognition"""
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = None
        self.camera = None
        self.running = False
        self.gesture_callbacks = {}
        
    async def initialize(self) -> bool:
        """Initialize gesture recognition"""
        try:
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            
            # Try to open camera
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                logger.error("Failed to open camera for gesture recognition")
                return False
                
            logger.info("Gesture recognition initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize gesture recognition: {e}")
            return False
    
    def register_gesture_callback(self, gesture: str, callback):
        """Register callback for gesture events"""
        self.gesture_callbacks[gesture] = callback
    
    async def start_recognition(self):
        """Start gesture recognition loop"""
        self.running = True
        
        def recognition_loop():
            while self.running:
                try:
                    ret, frame = self.camera.read()
                    if not ret:
                        continue
                        
                    # Flip frame horizontally for mirror effect
                    frame = cv2.flip(frame, 1)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Process frame
                    results = self.hands.process(rgb_frame)
                    
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Detect gestures
                            gesture = self._detect_gesture(hand_landmarks)
                            if gesture and gesture in self.gesture_callbacks:
                                try:
                                    self.gesture_callbacks[gesture]()
                                except Exception as e:
                                    logger.error(f"Gesture callback error: {e}")
                    
                    # Small delay to prevent overwhelming CPU
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Gesture recognition error: {e}")
                    time.sleep(1)
        
        # Run in background thread
        recognition_thread = threading.Thread(target=recognition_loop)
        recognition_thread.daemon = True
        recognition_thread.start()
        
        logger.info("Gesture recognition started")
    
    def _detect_gesture(self, landmarks) -> Optional[str]:
        """Detect gesture from hand landmarks"""
        try:
            # Get landmark positions
            thumb_tip = landmarks.landmark[4]
            thumb_ip = landmarks.landmark[3]
            index_tip = landmarks.landmark[8]
            index_pip = landmarks.landmark[6]
            middle_tip = landmarks.landmark[12]
            middle_pip = landmarks.landmark[10]
            ring_tip = landmarks.landmark[16]
            ring_pip = landmarks.landmark[14]
            pinky_tip = landmarks.landmark[20]
            pinky_pip = landmarks.landmark[18]
            
            # Count extended fingers
            fingers_up = 0
            
            # Thumb (check if tip is to the right of IP joint)
            if thumb_tip.x > thumb_ip.x:
                fingers_up += 1
                
            # Other fingers (check if tip is above PIP joint)
            if index_tip.y < index_pip.y:
                fingers_up += 1
            if middle_tip.y < middle_pip.y:
                fingers_up += 1
            if ring_tip.y < ring_pip.y:
                fingers_up += 1
            if pinky_tip.y < pinky_pip.y:
                fingers_up += 1
            
            # Gesture recognition
            if fingers_up == 0:
                return "grab"  # Closed fist
            elif fingers_up == 1 and index_tip.y < index_pip.y:
                return "point"  # Pointing
            elif fingers_up == 5:
                return "open_palm"  # Open hand
            elif fingers_up == 2 and index_tip.y < index_pip.y and middle_tip.y < middle_pip.y:
                return "peace"  # Peace sign / V
            
            return None
            
        except Exception as e:
            logger.error(f"Gesture detection error: {e}")
            return None
    
    async def stop_recognition(self):
        """Stop gesture recognition"""
        self.running = False
        if self.camera:
            self.camera.release()
        logger.info("Gesture recognition stopped")

class DesktopAgent:
    """Main desktop agent for environment and device control"""
    
    def __init__(self, gateway_url: str = "http://localhost:5324"):
        self.bluetooth = BluetoothManager()
        self.hdmi_cec = HDMICECController()
        self.ir_controller = IRController()
        self.gesture_controller = GestureController()
        self.n8n_client = RigAgentN8nClient(gateway_url)
        
        self.capabilities = {
            "bluetooth": False,
            "hdmi_cec": False,
            "ir_control": False,
            "gesture_recognition": False
        }
        
    async def initialize(self) -> bool:
        """Initialize all controllers"""
        logger.info("Initializing desktop agent...")
        
        # Initialize Bluetooth
        try:
            # Bluetooth is always available if bleak works
            self.capabilities["bluetooth"] = True
            logger.info("Bluetooth capability enabled")
        except Exception as e:
            logger.error(f"Bluetooth initialization failed: {e}")
        
        # Initialize HDMI-CEC
        self.capabilities["hdmi_cec"] = await self.hdmi_cec.initialize()
        
        # Initialize IR
        self.capabilities["ir_control"] = await self.ir_controller.initialize()
        
        # Initialize gesture recognition
        self.capabilities["gesture_recognition"] = await self.gesture_controller.initialize()
        
        # Set up gesture callbacks
        if self.capabilities["gesture_recognition"]:
            self.gesture_controller.register_gesture_callback("grab", self._on_grab_gesture)
            self.gesture_controller.register_gesture_callback("point", self._on_point_gesture)
            self.gesture_controller.register_gesture_callback("open_palm", self._on_open_palm_gesture)
            await self.gesture_controller.start_recognition()
        
        enabled_count = sum(self.capabilities.values())
        logger.info(f"Desktop agent initialized - {enabled_count}/4 capabilities enabled")
        
        return enabled_count > 0
    
    async def scan_environment(self) -> Dict:
        """Scan for all available devices"""
        environment = {
            "bluetooth_devices": [],
            "hdmi_cec_devices": {},
            "ir_remotes": {},
            "capabilities": self.capabilities,
            "timestamp": time.time()
        }
        
        # Scan Bluetooth devices
        if self.capabilities["bluetooth"]:
            environment["bluetooth_devices"] = await self.bluetooth.scan_devices()
        
        # Get CEC devices
        if self.capabilities["hdmi_cec"]:
            environment["hdmi_cec_devices"] = self.hdmi_cec.devices
        
        # Get IR remotes
        if self.capabilities["ir_control"]:
            environment["ir_remotes"] = self.ir_controller.remote_configs
        
        return environment
    
    async def control_device(self, device_type: str, device_id: str, action: str, parameters: Dict = None) -> Dict:
        """Control a device"""
        if parameters is None:
            parameters = {}
            
        logger.info(f"Controlling device: {device_type}:{device_id} - {action}")
        
        try:
            if device_type == "bluetooth":
                return await self._control_bluetooth_device(device_id, action, parameters)
            elif device_type == "hdmi_cec":
                return await self._control_cec_device(device_id, action, parameters)
            elif device_type == "ir":
                return await self._control_ir_device(device_id, action, parameters)
            else:
                return {"success": False, "error": f"Unknown device type: {device_type}"}
                
        except Exception as e:
            logger.error(f"Device control failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _control_bluetooth_device(self, device_id: str, action: str, parameters: Dict) -> Dict:
        """Control Bluetooth device"""
        if action == "connect":
            success = await self.bluetooth.connect_device(device_id)
            return {"success": success, "action": "connect", "device": device_id}
        elif action == "disconnect":
            success = await self.bluetooth.disconnect_device(device_id)
            return {"success": success, "action": "disconnect", "device": device_id}
        elif action == "services":
            services = await self.bluetooth.get_device_services(device_id)
            return {"success": True, "services": services, "device": device_id}
        else:
            return {"success": False, "error": f"Unknown Bluetooth action: {action}"}
    
    async def _control_cec_device(self, device_id: str, action: str, parameters: Dict) -> Dict:
        """Control HDMI-CEC device"""
        try:
            address = int(device_id)
        except ValueError:
            return {"success": False, "error": "Invalid CEC address"}
            
        if action == "power_on":
            success = await self.hdmi_cec.power_on(address)
            return {"success": success, "action": "power_on", "device": address}
        elif action == "power_off":
            success = await self.hdmi_cec.power_off(address)
            return {"success": success, "action": "power_off", "device": address}
        elif action == "set_active":
            success = await self.hdmi_cec.set_active_source(address)
            return {"success": success, "action": "set_active", "device": address}
        else:
            return {"success": False, "error": f"Unknown CEC action: {action}"}
    
    async def _control_ir_device(self, device_id: str, action: str, parameters: Dict) -> Dict:
        """Control IR device"""
        command = parameters.get("command")
        if not command:
            return {"success": False, "error": "IR command required"}
            
        success = await self.ir_controller.send_command(device_id, command)
        return {"success": success, "action": f"ir_{command}", "device": device_id}
    
    def _on_grab_gesture(self):
        """Handle grab gesture"""
        logger.info("Grab gesture detected")
        # Could trigger device selection or power toggle
        asyncio.create_task(self.n8n_client.send_notification(
            "Grab gesture detected - Device ready for control",
            channels=["gesture"],
            urgency="normal"
        ))
    
    def _on_point_gesture(self):
        """Handle point gesture"""
        logger.info("Point gesture detected")
        # Could trigger navigation or selection
        asyncio.create_task(self.n8n_client.send_notification(
            "Point gesture detected - Navigation active",
            channels=["gesture"],
            urgency="normal"
        ))
    
    def _on_open_palm_gesture(self):
        """Handle open palm gesture"""
        logger.info("Open palm gesture detected")
        # Could trigger stop or reset
        asyncio.create_task(self.n8n_client.send_notification(
            "Open palm gesture detected - Stop command",
            channels=["gesture"],
            urgency="normal"
        ))

# FastAPI integration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Desktop Agent", version="3.2.0")

# Global agent instance
agent = None

class DeviceControlRequest(BaseModel):
    device_type: str
    device_id: str
    action: str
    parameters: Dict = {}

@app.on_event("startup")
async def startup():
    global agent
    agent = DesktopAgent()
    await agent.initialize()

@app.get("/environment/scan")
async def scan_environment():
    """Scan for all available devices"""
    if not agent:
        raise HTTPException(500, "Agent not initialized")
    
    return await agent.scan_environment()

@app.post("/device/control")
async def control_device(request: DeviceControlRequest):
    """Control a device"""
    if not agent:
        raise HTTPException(500, "Agent not initialized")
    
    result = await agent.control_device(
        request.device_type,
        request.device_id, 
        request.action,
        request.parameters
    )
    
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Control failed"))
    
    return result

@app.get("/capabilities")
async def get_capabilities():
    """Get agent capabilities"""
    if not agent:
        raise HTTPException(500, "Agent not initialized")
    
    return {
        "capabilities": agent.capabilities,
        "bluetooth_devices": len(agent.bluetooth.discovered_devices),
        "cec_devices": len(agent.hdmi_cec.devices),
        "ir_remotes": len(agent.ir_controller.remote_configs)
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "desktop-agent",
        "version": "3.2.0",
        "platform": platform.system()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5325)