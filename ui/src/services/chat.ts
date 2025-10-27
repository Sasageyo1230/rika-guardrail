// Rika Phase 3.4 Chat Service
import { ChatRequest, ChatResponse, StreamEvent } from '../types/chat';

const API_BASE = 'http://localhost:5318';

export class ChatService {
  
  async sendMessage(request: ChatRequest): Promise<ChatResponse | AsyncGenerator<StreamEvent, void, unknown>> {
    if (request.stream !== false) {
      return this.sendStreamingMessage(request);
    } else {
      return this.sendNonStreamingMessage(request);
    }
  }
  
  private async *sendStreamingMessage(request: ChatRequest): AsyncGenerator<StreamEvent, void, unknown> {
    const url = `${API_BASE}/chat/`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...request, stream: true }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      if (!response.body) {
        throw new Error('No response body');
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('event: ') || line.startsWith('data: ')) {
              continue;
            }
            
            if (line.trim() === '') continue;
            
            try {
              // Parse SSE format: "event: type\ndata: json\n\n"
              const eventMatch = chunk.match(/event: (\w+)\ndata: (.*?)\n\n/s);
              if (eventMatch) {
                const [, eventType, data] = eventMatch;
                const parsedData = JSON.parse(data);
                yield { type: eventType as StreamEvent['type'], data: parsedData };
              }
            } catch (e) {
              // Continue parsing other events if one fails
              console.warn('Failed to parse SSE event:', e);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      yield {
        type: 'error',
        data: { error: error instanceof Error ? error.message : 'Unknown error' }
      };
    }
  }
  
  private async sendNonStreamingMessage(request: ChatRequest): Promise<ChatResponse> {
    const url = `${API_BASE}/chat/`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...request, stream: false }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    return response.json();
  }
  
  async getSessions(): Promise<string[]> {
    const response = await fetch(`${API_BASE}/chat/sessions`);
    if (!response.ok) {
      throw new Error(`Failed to get sessions: ${response.statusText}`);
    }
    const data = await response.json();
    return data.sessions || [];
  }
  
  async clearSession(sessionId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to clear session: ${response.statusText}`);
    }
  }
  
  async getHealth(): Promise<any> {
    const response = await fetch(`${API_BASE}/chat/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }
  
  // Fallback for browsers that don't support streaming
  async sendMessageWithPolling(request: ChatRequest): Promise<string> {
    // Send non-streaming request and return result
    const response = await this.sendNonStreamingMessage({ ...request, stream: false });
    return response.response;
  }
  
  // Test streaming support
  static supportsStreaming(): boolean {
    return typeof EventSource !== 'undefined' && typeof fetch !== 'undefined' && 'body' in Response.prototype;
  }
}

// Design Mode Service
export class DesignModeService {
  async createPatch(request: string, targetFiles?: string[]): Promise<any> {
    const response = await fetch(`${API_BASE}/ui/patch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        request,
        target_files: targetFiles,
        preview_only: true
      }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to create patch: ${errorText}`);
    }
    
    return response.json();
  }
  
  async applyPatch(patchId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/ui/patch/${patchId}/apply`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to apply patch: ${errorText}`);
    }
    
    return response.json();
  }
  
  async listPatches(): Promise<any> {
    const response = await fetch(`${API_BASE}/ui/patches`);
    if (!response.ok) {
      throw new Error(`Failed to list patches: ${response.statusText}`);
    }
    return response.json();
  }
}

// Global service instances
export const chatService = new ChatService();
export const designModeService = new DesignModeService();