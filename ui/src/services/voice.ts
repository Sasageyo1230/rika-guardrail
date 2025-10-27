// Rika Phase 3.5 Voice Integration
export interface VoiceConfig {
  elevenlabs_configured: boolean;
  whisper_configured: boolean;
  features: {
    text_to_speech: boolean;
    speech_to_text: boolean;
  };
}

export interface VoiceAgent {
  type: string;
  name: string;
  voice_id: string;
  has_voice: boolean;
}

const API_BASE = 'http://localhost:5318';

export class VoiceService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private isRecording = false;

  async getHealth(): Promise<VoiceConfig | null> {
    try {
      const response = await fetch(`${API_BASE}/voice/health`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Voice health check failed:', error);
      return null;
    }
  }

  async getVoiceAgents(): Promise<VoiceAgent[]> {
    try {
      const response = await fetch(`${API_BASE}/voice/agents`);
      if (response.ok) {
        const data = await response.json();
        return data.agents || [];
      }
      return [];
    } catch (error) {
      console.error('Failed to get voice agents:', error);
      return [];
    }
  }

  async textToSpeech(text: string, agent: string = 'rika'): Promise<string | null> {
    try {
      const response = await fetch(`${API_BASE}/voice/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, agent }),
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        return URL.createObjectURL(audioBlob);
      }
      return null;
    } catch (error) {
      console.error('TTS failed:', error);
      return null;
    }
  }

  async startRecording(): Promise<boolean> {
    if (this.isRecording) return false;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      this.audioChunks = [];
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.start(1000); // Collect data every second
      this.isRecording = true;
      return true;
    } catch (error) {
      console.error('Failed to start recording:', error);
      return false;
    }
  }

  async stopRecording(): Promise<string | null> {
    if (!this.mediaRecorder || !this.isRecording) return null;

    return new Promise((resolve) => {
      this.mediaRecorder!.onstop = async () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        
        // Stop all tracks to release microphone
        const stream = this.mediaRecorder!.stream;
        stream.getTracks().forEach(track => track.stop());
        
        this.isRecording = false;
        this.mediaRecorder = null;

        // Convert to text
        const text = await this.speechToText(audioBlob);
        resolve(text);
      };

      this.mediaRecorder.stop();
    });
  }

  private async speechToText(audioBlob: Blob): Promise<string | null> {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await fetch(`${API_BASE}/voice/stt`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        return data.success ? data.text : null;
      }
      return null;
    } catch (error) {
      console.error('STT failed:', error);
      return null;
    }
  }

  isCurrentlyRecording(): boolean {
    return this.isRecording;
  }

  static supportsVoice(): boolean {
    return (
      typeof navigator !== 'undefined' &&
      typeof navigator.mediaDevices !== 'undefined' &&
      typeof navigator.mediaDevices.getUserMedia === 'function' &&
      typeof MediaRecorder !== 'undefined'
    );
  }
}

// Global service instance
export const voiceService = new VoiceService();