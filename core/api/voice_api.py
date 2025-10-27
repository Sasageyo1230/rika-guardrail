"""
Voice API endpoints for TTS and STT
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
import logging

from ..voice import voice_service
from ..agents import AgentType

logger = logging.getLogger(__name__)

voice_router = APIRouter(prefix="/voice", tags=["voice"])

class TTSRequest(BaseModel):
    text: str
    agent: Optional[str] = "rika"

class TTSResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class STTResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    message: Optional[str] = None

@voice_router.post("/tts", response_class=StreamingResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        # Validate agent type
        agent_type = AgentType(request.agent)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {request.agent}")
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        audio_data = await voice_service.text_to_speech(request.text, agent_type)
        
        if audio_data is None:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
        
        # Return audio as streaming response
        audio_stream = io.BytesIO(audio_data)
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@voice_router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(..., description="Audio file to transcribe")
):
    """Convert speech to text"""
    
    # Validate file type
    if not audio.content_type or not audio.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        # Read audio data
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        # Transcribe audio
        text = await voice_service.speech_to_text(audio_data, audio.content_type)
        
        if text is None:
            return STTResponse(success=False, message="Failed to transcribe audio")
        
        return STTResponse(success=True, text=text.strip())
        
    except Exception as e:
        logger.error(f"STT error: {e}")
        return STTResponse(success=False, message="Internal server error")

@voice_router.get("/voices")
async def list_voices():
    """List available voices from ElevenLabs"""
    try:
        voices = await voice_service.get_available_voices()
        
        if voices is None:
            raise HTTPException(status_code=500, detail="Failed to retrieve voices")
        
        return {"voices": voices}
        
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@voice_router.get("/agents")
async def list_agent_voices():
    """List agent voice configurations"""
    try:
        agent_registry = voice_service.agent_registry
        agents = []
        
        for agent_type in AgentType:
            agent_info = agent_registry.get_agent(agent_type)
            if agent_info:
                agents.append({
                    "type": agent_type.value,
                    "name": agent_info.name,
                    "voice_id": agent_info.voice_id,
                    "has_voice": agent_info.voice_id is not None
                })
        
        return {"agents": agents}
        
    except Exception as e:
        logger.error(f"Error listing agent voices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@voice_router.get("/health")
async def voice_health():
    """Voice service health check"""
    elevenlabs_configured = voice_service.config.elevenlabs_api_key is not None
    whisper_configured = voice_service.config.whisper_api_key is not None
    
    return {
        "status": "healthy",
        "elevenlabs_configured": elevenlabs_configured,
        "whisper_configured": whisper_configured,
        "features": {
            "text_to_speech": elevenlabs_configured,
            "speech_to_text": whisper_configured
        }
    }