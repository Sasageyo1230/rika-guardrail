"""
Rika Phase 3.5 Voice Integration
ElevenLabs TTS + Whisper STT
"""
import os
import asyncio
import aiohttp
import aiofiles
import tempfile
from typing import Optional, BinaryIO
from pathlib import Path
import logging
from pydantic import BaseModel

from .agents import AgentType, get_agent_registry

logger = logging.getLogger(__name__)

class VoiceConfig(BaseModel):
    """Voice configuration"""
    elevenlabs_api_key: Optional[str] = None
    whisper_api_key: Optional[str] = None  # OpenAI API key for Whisper
    elevenlabs_model: str = "eleven_turbo_v2"
    whisper_model: str = "whisper-1"
    voice_stability: float = 0.75
    voice_similarity: float = 0.75
    voice_style: float = 0.0
    voice_use_speaker_boost: bool = True

class VoiceService:
    """Voice service for TTS and STT"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.agent_registry = get_agent_registry()
        self.elevenlabs_base_url = "https://api.elevenlabs.io/v1"
        self.openai_base_url = "https://api.openai.com/v1"
        
    async def text_to_speech(self, text: str, agent_type: AgentType = AgentType.RIKA) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs"""
        if not self.config.elevenlabs_api_key:
            logger.warning("ElevenLabs API key not configured")
            return None
            
        agent_info = self.agent_registry.get_agent(agent_type)
        if not agent_info or not agent_info.voice_id:
            logger.warning(f"No voice ID configured for agent {agent_type}")
            return None
            
        url = f"{self.elevenlabs_base_url}/text-to-speech/{agent_info.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.config.elevenlabs_api_key
        }
        
        data = {
            "text": text,
            "model_id": self.config.elevenlabs_model,
            "voice_settings": {
                "stability": self.config.voice_stability,
                "similarity_boost": self.config.voice_similarity,
                "style": self.config.voice_style,
                "use_speaker_boost": self.config.voice_use_speaker_boost
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs API error {response.status}: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error calling ElevenLabs API: {e}")
            return None
    
    async def speech_to_text(self, audio_data: bytes, content_type: str = "audio/webm") -> Optional[str]:
        """Convert speech to text using OpenAI Whisper"""
        if not self.config.whisper_api_key:
            logger.warning("OpenAI API key not configured for Whisper")
            return None
            
        url = f"{self.openai_base_url}/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {self.config.whisper_api_key}"
        }
        
        # Create temporary file for audio data
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
            
        try:
            async with aiohttp.ClientSession() as session:
                with open(temp_file_path, 'rb') as audio_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field('file', audio_file, filename='audio.webm', content_type=content_type)
                    form_data.add_field('model', self.config.whisper_model)
                    form_data.add_field('response_format', 'text')
                    
                    async with session.post(url, data=form_data, headers=headers) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            error_text = await response.text()
                            logger.error(f"Whisper API error {response.status}: {error_text}")
                            return None
        except Exception as e:
            logger.error(f"Error calling Whisper API: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    async def get_available_voices(self) -> Optional[list]:
        """Get available voices from ElevenLabs"""
        if not self.config.elevenlabs_api_key:
            return None
            
        url = f"{self.elevenlabs_base_url}/voices"
        headers = {"xi-api-key": self.config.elevenlabs_api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("voices", [])
                    else:
                        logger.error(f"Failed to get voices: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return None

def create_voice_service() -> VoiceService:
    """Create voice service with configuration from environment"""
    config = VoiceConfig(
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
        whisper_api_key=os.getenv("OPENAI_API_KEY")
    )
    return VoiceService(config)

# Global voice service instance
voice_service = create_voice_service()