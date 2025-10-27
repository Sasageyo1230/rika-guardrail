// Rika Phase 3.4 Chat Types

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
}

export interface ToolCall {
  name: string;
  arguments: Record<string, any>;
  result?: any;
  status?: 'pending' | 'running' | 'completed' | 'failed';
}

export interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface StreamEvent {
  type: 'start' | 'token' | 'tools_start' | 'tool_result' | 'tools_complete' | 'tools_planned' | 'complete' | 'error';
  data: any;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  agent?: 'rika' | 'rig' | 'craft' | 'scout' | 'echo' | 'pulse';
  stream?: boolean;
  guarded?: boolean;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  tool_calls: ToolCall[];
  finished: boolean;
}