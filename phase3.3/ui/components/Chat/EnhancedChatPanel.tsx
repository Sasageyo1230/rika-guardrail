import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatMessage {
  id: string;
  agent: 'user' | 'rig' | 'craft' | 'scout' | 'echo' | 'pulse' | 'atlas';
  message: string;
  timestamp: Date;
  type?: 'message' | 'command' | 'result' | 'error' | 'streaming';
  metadata?: {
    execution_id?: string;
    workflow?: string;
    status?: string;
    citations?: Array<{
      title: string;
      url: string;
      excerpt: string;
    }>;
  };
  isStreaming?: boolean;
}

interface EnhancedChatPanelProps {
  isVisible: boolean;
  onToggle: () => void;
  position?: 'left' | 'right' | 'bottom';
  width?: number;
  height?: number;
  enableVoice?: boolean;
  enableCitations?: boolean;
}

const agentConfig = {
  user: { color: '#6B7280', icon: '👤', name: 'You' },
  rig: { color: '#2E8B57', icon: '🔧', name: 'Rig' },
  craft: { color: '#4169E1', icon: '⚡', name: 'Craft' },
  scout: { color: '#FF6347', icon: '🔍', name: 'Scout' },
  echo: { color: '#32CD32', icon: '📡', name: 'Echo' },
  pulse: { color: '#9370DB', icon: '💓', name: 'Pulse' },
  atlas: { color: '#FFD700', icon: '🧠', name: 'Atlas' }
};

const EnhancedChatPanel: React.FC<EnhancedChatPanelProps> = ({
  isVisible,
  onToggle,
  position = 'right',
  width = 400,
  height = 600,
  enableVoice = false,
  enableCitations = true
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      agent: 'atlas',
      message: 'Enhanced Atlas Chat Panel active. All agents connected and ready for advanced interactions.',
      timestamp: new Date(),
      type: 'message'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(true);
  const [activeAgents, setActiveAgents] = useState<string[]>(['rig', 'craft', 'scout', 'echo', 'pulse']);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [showCitations, setShowCitations] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<ChatMessage | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const citationsTrayRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isVisible && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isVisible]);

  // Add message to chat
  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  }, []);

  // Stream message content (simulates real-time typing)
  const streamMessage = useCallback((agent: ChatMessage['agent'], content: string, delay = 30) => {
    const messageId = addMessage({
      agent,
      message: '',
      type: 'streaming',
      isStreaming: true
    });
    
    setStreamingMessageId(messageId);
    
    let currentContent = '';
    let index = 0;
    
    const streamInterval = setInterval(() => {
      if (index < content.length) {
        currentContent += content[index];
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, message: currentContent }
            : msg
        ));
        index++;
      } else {
        clearInterval(streamInterval);
        setStreamingMessageId(null);
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, isStreaming: false, type: 'message' }
            : msg
        ));
      }
    }, delay);
    
    return messageId;
  }, [addMessage]);

  // Handle input submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Add user message
    addMessage({
      agent: 'user',
      message: inputValue,
      type: 'message'
    });

    const userInput = inputValue;
    setInputValue('');

    // Process command or message
    if (userInput.startsWith('/')) {
      await handleCommand(userInput);
    } else {
      await handleMessage(userInput);
    }
  };

  // Enhanced slash commands
  const handleCommand = async (command: string) => {
    const [cmd, ...args] = command.slice(1).split(' ');
    
    switch (cmd.toLowerCase()) {
      case 'help':
        streamMessage('atlas', `Enhanced commands available:
/help - Show this help
/status - System status with live metrics
/agents - List agents with capabilities
/clear - Clear chat history
/voice on/off - Toggle voice responses
/citations - Toggle citation display
/run <workflow> - Execute n8n workflow
/device <action> - Control device via Rig
/research <query> - Scout research (quick/deep)
/storyboard <script> - Craft storyboard generation
/vault search <query> - Search knowledge vault`);
        break;

      case 'status':
        const statusMessage = `System Status Report:
✅ Core Services: Online
🔧 Rig: ${activeAgents.includes('rig') ? 'Active' : 'Standby'}
⚡ Craft: ${activeAgents.includes('craft') ? 'Active' : 'Standby'}
🔍 Scout: ${activeAgents.includes('scout') ? 'Active' : 'Standby'}
📡 Echo: ${activeAgents.includes('echo') ? 'Active' : 'Standby'}
💓 Pulse: ${activeAgents.includes('pulse') ? 'Active' : 'Standby'}
🧠 Atlas: Always Active
Connection: ${isConnected ? 'Stable' : 'Reconnecting'}
Voice: ${enableVoice ? 'Enabled' : 'Disabled'}
Citations: ${enableCitations ? 'Enabled' : 'Disabled'}`;
        
        streamMessage('pulse', statusMessage, 20);
        break;

      case 'voice':
        if (args[0] === 'on') {
          addMessage({
            agent: 'atlas',
            message: 'Voice responses enabled. Agents will now speak their messages.',
            type: 'result'
          });
        } else if (args[0] === 'off') {
          addMessage({
            agent: 'atlas',
            message: 'Voice responses disabled. Text-only mode active.',
            type: 'result'
          });
        } else {
          addMessage({
            agent: 'atlas',
            message: 'Usage: /voice on|off',
            type: 'error'
          });
        }
        break;

      case 'citations':
        setShowCitations(!showCitations);
        addMessage({
          agent: 'atlas',
          message: `Citations display ${!showCitations ? 'enabled' : 'disabled'}.`,
          type: 'result'
        });
        break;

      case 'research':
        if (args.length === 0) {
          addMessage({
            agent: 'scout',
            message: 'Usage: /research <query> [quick|deep]',
            type: 'error'
          });
          break;
        }
        
        const query = args.join(' ');
        const mode = args[args.length - 1] === 'deep' ? 'deep' : 'quick';
        
        addMessage({
          agent: 'scout',
          message: `Starting ${mode} research: "${query}"`,
          type: 'command'
        });
        
        // Simulate research with citations
        setTimeout(() => {
          const mockCitations = [
            {
              title: `${query} - Latest Developments`,
              url: 'https://example.com/research1',
              excerpt: 'Recent advances show promising trends...'
            },
            {
              title: `Industry Analysis: ${query}`,
              url: 'https://example.com/research2', 
              excerpt: 'Market research indicates significant growth...'
            }
          ];
          
          streamMessage('scout', `Research completed! Found ${mockCitations.length} relevant sources. 

Key insights:
• Trend analysis shows 23% growth in related sectors
• 3 major developments identified in past 30 days
• Expert consensus indicates positive outlook

Citations available in footer. Click to expand details.`, 15);
          
          // Add citations to the last message
          setTimeout(() => {
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1];
              if (lastMessage.agent === 'scout') {
                return [...prev.slice(0, -1), {
                  ...lastMessage,
                  metadata: { ...lastMessage.metadata, citations: mockCitations }
                }];
              }
              return prev;
            });
          }, 500);
        }, 2000);
        break;

      case 'storyboard':
        if (args.length === 0) {
          addMessage({
            agent: 'craft',
            message: 'Usage: /storyboard <script_description>',
            type: 'error'
          });
          break;
        }
        
        streamMessage('craft', `Creating storyboard for: "${args.join(' ')}"

Panel 1: Opening scene setup
Panel 2: Character introduction  
Panel 3: Conflict establishment
Panel 4: Rising action
Panel 5: Climax moment
Panel 6: Resolution begins
Panel 7: Character development
Panel 8: Closing scene

Storyboard panels generated and saved to MinIO. Preview available in Task Drawer.`, 40);
        break;

      default:
        addMessage({
          agent: 'atlas',
          message: `Unknown command: /${cmd}. Type /help for available commands.`,
          type: 'error'
        });
    }
  };

  // Enhanced natural language processing
  const handleMessage = async (message: string) => {
    // Simulate processing time
    setTimeout(() => {
      let responseAgent: ChatMessage['agent'] = 'atlas';
      let responseMessage = '';
      let shouldStream = true;

      // Enhanced keyword detection
      const lowerMessage = message.toLowerCase();
      
      if (lowerMessage.includes('device') || lowerMessage.includes('control') || lowerMessage.includes('bluetooth') || lowerMessage.includes('tv')) {
        responseAgent = 'rig';
        responseMessage = 'I can help with device control and automation. What specific device or action would you like me to handle? I support Bluetooth, HDMI-CEC, IR, and gesture control.';
      } else if (lowerMessage.includes('code') || lowerMessage.includes('deploy') || lowerMessage.includes('storyboard') || lowerMessage.includes('create')) {
        responseAgent = 'craft';
        responseMessage = 'Ready to assist with creative and technical projects. I can help with code deployment, storyboard generation, and automation workflows. What would you like me to create?';
      } else if (lowerMessage.includes('research') || lowerMessage.includes('find') || lowerMessage.includes('search') || lowerMessage.includes('analyze')) {
        responseAgent = 'scout';
        responseMessage = 'I\'m equipped for comprehensive research and analysis. I can perform quick or deep research, search the knowledge vault, and provide detailed insights. What topic would you like me to investigate?';
      } else if (lowerMessage.includes('status') || lowerMessage.includes('health') || lowerMessage.includes('monitor') || lowerMessage.includes('performance')) {
        responseAgent = 'pulse';
        responseMessage = 'System monitoring active. All core services are running optimally. Current metrics show normal performance across all agents. Is there a specific system aspect you\'d like me to examine?';
      } else if (lowerMessage.includes('notify') || lowerMessage.includes('alert') || lowerMessage.includes('message') || lowerMessage.includes('communicate')) {
        responseAgent = 'echo';
        responseMessage = 'Communication systems ready. I can handle notifications, alerts, and inter-agent messaging. What would you like me to broadcast or route?';
      } else {
        responseAgent = 'atlas';
        responseMessage = 'I understand. Let me route this to the most appropriate agent or handle it directly. How can the Rika system assist you today?';
      }

      if (shouldStream) {
        streamMessage(responseAgent, responseMessage, 25);
      } else {
        addMessage({
          agent: responseAgent,
          message: responseMessage,
          type: 'message'
        });
      }
    }, 800);
  };

  // Copy message content
  const copyMessage = useCallback((message: ChatMessage) => {
    navigator.clipboard.writeText(message.message);
    // Could add a toast notification here
  }, []);

  // Toggle citations tray
  const toggleCitations = useCallback((message: ChatMessage) => {
    if (message.metadata?.citations) {
      setSelectedMessage(selectedMessage?.id === message.id ? null : message);
      setShowCitations(selectedMessage?.id !== message.id);
    }
  }, [selectedMessage]);

  const getMessageStyle = (message: ChatMessage) => {
    const config = agentConfig[message.agent];
    const isUser = message.agent === 'user';
    
    return {
      alignSelf: isUser ? 'flex-end' : 'flex-start',
      backgroundColor: isUser ? '#3B82F6' : `${config.color}20`,
      borderColor: config.color,
      borderLeft: isUser ? 'none' : `4px solid ${config.color}`,
      opacity: message.type === 'error' ? 0.8 : 1,
      maxWidth: '80%'
    };
  };

  const panelStyles = {
    position: 'fixed' as const,
    top: position === 'bottom' ? 'auto' : '50px',
    bottom: position === 'bottom' ? '20px' : 'auto',
    left: position === 'left' ? '20px' : 'auto',
    right: position === 'right' ? '20px' : 'auto',
    width: position === 'bottom' ? 'calc(100% - 40px)' : `${width}px`,
    height: position === 'bottom' ? '400px' : `${height}px`,
    backgroundColor: 'rgba(17, 24, 39, 0.95)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    borderRadius: '12px',
    border: '1px solid rgba(75, 85, 99, 0.3)',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden'
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          style={panelStyles}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
        >
          {/* Header */}
          <div style={{
            padding: '16px',
            borderBottom: '1px solid rgba(75, 85, 99, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, rgba(255, 215, 0, 0.1), transparent)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <motion.span 
                style={{ fontSize: '20px' }}
                animate={{ rotate: [0, 10, 0] }}
                transition={{ repeat: Infinity, duration: 4 }}
              >
                🧠
              </motion.span>
              <span style={{ color: 'white', fontWeight: '600' }}>Enhanced Atlas Chat</span>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: isConnected ? '#10B981' : '#EF4444'
              }} />
              {streamingMessageId && (
                <motion.div
                  style={{ 
                    fontSize: '10px', 
                    color: '#10B981',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                  animate={{ opacity: [1, 0.5, 1] }}
                  transition={{ repeat: Infinity, duration: 1 }}
                >
                  <span>●</span> Streaming...
                </motion.div>
              )}
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {/* Voice Toggle */}
              <motion.button
                onClick={() => {/* Toggle voice */}}
                style={{
                  background: 'none',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  color: enableVoice ? '#10B981' : 'white',
                  fontSize: '12px',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                🔊
              </motion.button>
              
              {/* Citations Toggle */}
              <motion.button
                onClick={() => setShowCitations(!showCitations)}
                style={{
                  background: 'none',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  color: showCitations ? '#10B981' : 'white',
                  fontSize: '12px',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                📚
              </motion.button>
              
              <button
                onClick={onToggle}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'white',
                  fontSize: '18px',
                  cursor: 'pointer',
                  opacity: 0.7
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1,
            padding: '16px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {messages.map((message) => {
              const config = agentConfig[message.agent];
              return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    ...getMessageStyle(message),
                    padding: '12px 16px',
                    borderRadius: '12px',
                    color: 'white',
                    fontSize: '14px',
                    lineHeight: '1.4',
                    whiteSpace: 'pre-wrap',
                    position: 'relative'
                  }}
                  whileHover={{ scale: 1.01 }}
                >
                  {/* Message Header */}
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '6px',
                    marginBottom: '6px',
                    fontSize: '12px',
                    opacity: 0.8
                  }}>
                    <span>{config.icon}</span>
                    <span style={{ fontWeight: '600' }}>{config.name}</span>
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    
                    {/* Streaming indicator */}
                    {message.isStreaming && (
                      <motion.span
                        style={{ fontSize: '10px', color: '#10B981' }}
                        animate={{ opacity: [1, 0.5, 1] }}
                        transition={{ repeat: Infinity, duration: 1 }}
                      >
                        ●
                      </motion.span>
                    )}
                  </div>
                  
                  {/* Message Content */}
                  <div style={{ marginBottom: '8px' }}>
                    {message.message}
                    {message.isStreaming && (
                      <motion.span
                        style={{ opacity: 0.5 }}
                        animate={{ opacity: [0.5, 1, 0.5] }}
                        transition={{ repeat: Infinity, duration: 1 }}
                      >
                        |
                      </motion.span>
                    )}
                  </div>
                  
                  {/* Message Actions */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '11px',
                    opacity: 0.7
                  }}>
                    <motion.button
                      onClick={() => copyMessage(message)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'inherit',
                        cursor: 'pointer',
                        fontSize: '11px'
                      }}
                      whileHover={{ scale: 1.1 }}
                    >
                      📋 Copy
                    </motion.button>
                    
                    {message.metadata?.citations && (
                      <motion.button
                        onClick={() => toggleCitations(message)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#10B981',
                          cursor: 'pointer',
                          fontSize: '11px'
                        }}
                        whileHover={{ scale: 1.1 }}
                      >
                        📚 {message.metadata.citations.length} sources
                      </motion.button>
                    )}
                  </div>
                </motion.div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Citations Tray */}
          <AnimatePresence>
            {showCitations && selectedMessage?.metadata?.citations && (
              <motion.div
                ref={citationsTrayRef}
                style={{
                  borderTop: '1px solid rgba(75, 85, 99, 0.3)',
                  backgroundColor: 'rgba(0, 0, 0, 0.2)',
                  padding: '12px',
                  maxHeight: '200px',
                  overflowY: 'auto'
                }}
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
              >
                <div style={{ 
                  fontSize: '12px', 
                  fontWeight: '600', 
                  color: '#10B981',
                  marginBottom: '8px'
                }}>
                  Citations & Sources
                </div>
                {selectedMessage.metadata.citations.map((citation, index) => (
                  <motion.div
                    key={index}
                    style={{
                      padding: '8px',
                      marginBottom: '8px',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      borderRadius: '6px',
                      borderLeft: '3px solid #10B981'
                    }}
                    whileHover={{ backgroundColor: 'rgba(255, 255, 255, 0.1)' }}
                  >
                    <div style={{ fontSize: '12px', fontWeight: '600', color: 'white', marginBottom: '4px' }}>
                      {citation.title}
                    </div>
                    <div style={{ fontSize: '11px', color: '#9CA3AF', marginBottom: '4px' }}>
                      {citation.url}
                    </div>
                    <div style={{ fontSize: '11px', color: '#D1D5DB' }}>
                      {citation.excerpt}
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input */}
          <form onSubmit={handleSubmit} style={{
            padding: '16px',
            borderTop: '1px solid rgba(75, 85, 99, 0.3)',
            display: 'flex',
            gap: '8px'
          }}>
            <input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Enhanced chat • /help for commands • Voice enabled"
              style={{
                flex: 1,
                padding: '10px 14px',
                backgroundColor: 'rgba(55, 65, 81, 0.8)',
                border: '1px solid rgba(75, 85, 99, 0.5)',
                borderRadius: '8px',
                color: 'white',
                fontSize: '14px',
                outline: 'none',
                fontFamily: 'inherit'
              }}
              disabled={!!streamingMessageId}
            />
            <motion.button
              type="submit"
              disabled={!inputValue.trim() || !!streamingMessageId}
              style={{
                padding: '10px 18px',
                backgroundColor: inputValue.trim() && !streamingMessageId ? '#3B82F6' : 'rgba(75, 85, 99, 0.5)',
                border: 'none',
                borderRadius: '8px',
                color: 'white',
                fontSize: '14px',
                cursor: inputValue.trim() && !streamingMessageId ? 'pointer' : 'not-allowed',
                fontWeight: '600'
              }}
              whileHover={inputValue.trim() && !streamingMessageId ? { scale: 1.05 } : {}}
              whileTap={inputValue.trim() && !streamingMessageId ? { scale: 0.95 } : {}}
            >
              Send
            </motion.button>
          </form>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default EnhancedChatPanel;