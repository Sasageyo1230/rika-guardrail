import React, { useState, useEffect } from 'react';
import { voiceService, VoiceConfig, VoiceService } from '../services/voice';

interface VoiceChatProps {
  selectedAgent: string;
  onTextFromVoice: (text: string) => void;
  onPlayResponse: (text: string, agent: string) => void;
  disabled?: boolean;
}

export const VoiceChat: React.FC<VoiceChatProps> = ({
  selectedAgent,
  onTextFromVoice,
  onPlayResponse,
  disabled = false
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [voiceConfig, setVoiceConfig] = useState<VoiceConfig | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);

  useEffect(() => {
    loadVoiceConfig();
  }, []);

  const loadVoiceConfig = async () => {
    const config = await voiceService.getHealth();
    setVoiceConfig(config);
  };

  const startRecording = async () => {
    if (disabled || isRecording) return;

    const success = await voiceService.startRecording();
    if (success) {
      setIsRecording(true);
    } else {
      alert('Failed to start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = async () => {
    if (!isRecording) return;

    setIsRecording(false);
    const text = await voiceService.stopRecording();
    
    if (text && text.trim()) {
      onTextFromVoice(text.trim());
    }
  };

  const playResponse = async (text: string) => {
    if (!text.trim() || isPlaying) return;

    try {
      setIsPlaying(true);
      
      // Stop any currently playing audio
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }

      const audioUrl = await voiceService.textToSpeech(text, selectedAgent);
      
      if (audioUrl) {
        const audio = new Audio(audioUrl);
        setCurrentAudio(audio);
        
        audio.onended = () => {
          setIsPlaying(false);
          setCurrentAudio(null);
          URL.revokeObjectURL(audioUrl);
        };
        
        audio.onerror = () => {
          setIsPlaying(false);
          setCurrentAudio(null);
          URL.revokeObjectURL(audioUrl);
        };
        
        await audio.play();
      } else {
        setIsPlaying(false);
      }
    } catch (error) {
      console.error('Error playing response:', error);
      setIsPlaying(false);
    }
  };

  const stopAudio = () => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setIsPlaying(false);
      setCurrentAudio(null);
    }
  };

  // Auto-play functionality hook
  useEffect(() => {
    // This will be called by the parent component
    const handlePlayResponse = (text: string, agent: string) => {
      if (agent === selectedAgent) {
        playResponse(text);
      }
    };

    // Update the parent's play function
    onPlayResponse = handlePlayResponse;
  }, [selectedAgent]);

  const voiceSupported = VoiceService.supportsVoice();
  const sttAvailable = voiceConfig?.features?.speech_to_text ?? false;
  const ttsAvailable = voiceConfig?.features?.text_to_speech ?? false;

  if (!voiceSupported) {
    return null; // Don't render if voice is not supported
  }

  return (
    <div className="flex items-center gap-2">
      {/* Speech-to-Text Button */}
      {sttAvailable && (
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={disabled}
          className={`p-2 rounded-full transition-all ${
            isRecording
              ? 'bg-red-500 text-white animate-pulse'
              : disabled
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
          title={isRecording ? 'Stop recording' : 'Start voice recording'}
        >
          {isRecording ? '⏹' : '🎤'}
        </button>
      )}
      
      {/* Text-to-Speech Status */}
      {ttsAvailable && isPlaying && (
        <button
          onClick={stopAudio}
          className="p-2 rounded-full bg-green-500 text-white hover:bg-green-600 animate-pulse"
          title="Stop playback"
        >
          🔊
        </button>
      )}
      
      {/* Voice Status Indicator */}
      <div className="flex items-center gap-1 text-xs text-gray-500">
        {voiceConfig?.test_mode && (
          <span className="text-orange-500" title="Test mode - voice features simulated">
            🧪
          </span>
        )}
        {sttAvailable && (
          <span title="Speech-to-text available">🎤</span>
        )}
        {ttsAvailable && (
          <span title="Text-to-speech available">🔊</span>
        )}
      </div>
    </div>
  );
};