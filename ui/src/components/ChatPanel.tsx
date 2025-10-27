import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, StreamEvent } from '../types/chat';
import { chatService } from '../services/chat';
import { VoiceChat } from './VoiceChat';

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Agent {
  type: string;
  name: string;
  description: string;
  color: string;
  emoji: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<'rika' | 'rig' | 'craft' | 'scout' | 'echo' | 'pulse'>('rika');
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamingMessage]);
  
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      loadAgents();
    }
  }, [isOpen]);
  
  const loadAgents = async () => {
    try {
      const response = await fetch('http://localhost:5318/chat/agents');
      const data = await response.json();
      setAgents(data.agents || []);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };
  
  const sendMessage = async () => {
    if (!currentMessage.trim() || isStreaming) return;
    
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: currentMessage.trim(),
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsStreaming(true);
    setCurrentStreamingMessage('');
    
    try {
      const stream = await chatService.sendMessage({
        session_id: sessionId,
        message: userMessage.content,
        agent: selectedAgent,
        stream: true,
      }) as AsyncGenerator<StreamEvent, void, unknown>;
      
      let assistantContent = '';
      
      for await (const event of stream) {
        switch (event.type) {
          case 'token':
            if (event.data.content) {
              assistantContent += event.data.content;
              setCurrentStreamingMessage(assistantContent);
            }
            break;
            
          case 'complete':
            const assistantMessage: ChatMessage = {
              id: `msg-${Date.now()}`,
              role: 'assistant',
              content: assistantContent || event.data.response,
              timestamp: new Date(),
            };
            
            setMessages(prev => [...prev, assistantMessage]);
            setCurrentStreamingMessage('');
            break;
            
          case 'error':
            console.error('Chat error:', event.data.error);
            const errorMessage: ChatMessage = {
              id: `msg-${Date.now()}`,
              role: 'assistant',
              content: `Error: ${event.data.error}`,
              timestamp: new Date(),
            };
            setMessages(prev => [...prev, errorMessage]);
            setCurrentStreamingMessage('');
            break;
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setCurrentStreamingMessage('');
    } finally {
      setIsStreaming(false);
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleVoiceText = (text: string) => {
    setCurrentMessage(text);
    inputRef.current?.focus();
  };

  const handlePlayResponse = (text: string, agent: string) => {
    // This will be handled by the VoiceChat component
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-end">
      <div className="w-96 h-full bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-lg font-semibold">Chat with Rika</h2>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-xl"
            >
              ×
            </button>
          </div>
          
          {/* Agent Selector */}
          <div className="flex gap-1 flex-wrap">
            {agents.length > 0 ? agents.map((agent) => (
              <button
                key={agent.type}
                onClick={() => setSelectedAgent(agent.type as any)}
                className={`px-2 py-1 rounded text-xs transition-all flex items-center gap-1 ${
                  selectedAgent === agent.type
                    ? 'text-white shadow-lg transform scale-105'
                    : 'bg-white bg-opacity-20 text-white hover:bg-opacity-30'
                }`}
                style={selectedAgent === agent.type ? { backgroundColor: agent.color } : {}}
                title={agent.description}
              >
                <span>{agent.emoji}</span>
                <span>{agent.name}</span>
              </button>
            )) : 
            // Fallback if agents haven't loaded
            ['rika', 'rig', 'craft', 'scout', 'echo', 'pulse'].map((agent) => (
              <button
                key={agent}
                onClick={() => setSelectedAgent(agent as any)}
                className={`px-2 py-1 rounded text-xs transition-all ${
                  selectedAgent === agent
                    ? 'bg-blue-500 text-white'
                    : 'bg-white bg-opacity-20 text-white hover:bg-opacity-30'
                }`}
              >
                {agent}
              </button>
            ))}
          </div>
        </div>
        
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-3 py-2 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}
          
          {/* Streaming Message */}
          {currentStreamingMessage && (
            <div className="flex justify-start">
              <div className="max-w-xs lg:max-w-md px-3 py-2 rounded-lg bg-gray-200 text-gray-800">
                {currentStreamingMessage}
                <div className="inline-block w-2 h-4 bg-gray-500 animate-pulse ml-1"></div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input Area */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <input
                ref={inputRef}
                type="text"
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Ask ${selectedAgent}...`}
                disabled={isStreaming}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            
            {/* Voice Chat Integration */}
            <VoiceChat
              selectedAgent={selectedAgent}
              onTextFromVoice={handleVoiceText}
              onPlayResponse={handlePlayResponse}
              disabled={isStreaming}
            />
            
            <button
              onClick={sendMessage}
              disabled={!currentMessage.trim() || isStreaming}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isStreaming ? '⋯' : '→'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};