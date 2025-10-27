import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatMessage {
  id: string;
  agent: 'user' | 'rig' | 'craft' | 'scout' | 'echo' | 'pulse' | 'atlas';
  message: string;
  timestamp: Date;
  type?: 'message' | 'command' | 'result' | 'error';
  metadata?: {
    execution_id?: string;
    workflow?: string;
    status?: string;
  };
}

interface ChatPanelProps {
  isVisible: boolean;
  onToggle: () => void;
  position?: 'left' | 'right' | 'bottom';
  width?: number;
  height?: number;
}

const agentConfig = {
  user: { color: '#6B7280', icon: '👤', name: 'User' },
  rig: { color: '#2E8B57', icon: '🔧', name: 'Rig' },
  craft: { color: '#4169E1', icon: '⚡', name: 'Craft' },
  scout: { color: '#FF6347', icon: '🔍', name: 'Scout' },
  echo: { color: '#32CD32', icon: '📡', name: 'Echo' },
  pulse: { color: '#9370DB', icon: '💓', name: 'Pulse' },
  atlas: { color: '#FFD700', icon: '🧠', name: 'Atlas' }
};

const ChatPanel: React.FC<ChatPanelProps> = ({
  isVisible,
  onToggle,
  position = 'right',
  width = 400,
  height = 600
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      agent: 'atlas',
      message: 'Atlas Chat Panel active. All agents connected and ready.',
      timestamp: new Date(),
      type: 'message'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(true);
  const [activeAgents, setActiveAgents] = useState<string[]>(['rig', 'craft', 'scout', 'echo', 'pulse']);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isVisible && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isVisible]);

  // Add message to chat
  const addMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  };

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

  // Handle slash commands
  const handleCommand = async (command: string) => {
    const [cmd, ...args] = command.slice(1).split(' ');
    
    switch (cmd.toLowerCase()) {
      case 'help':
        addMessage({
          agent: 'atlas',
          message: `Available commands:
/help - Show this help
/status - Show system status  
/agents - List active agents
/clear - Clear chat history
/run <workflow> - Execute n8n workflow
/device <action> - Control device via Rig
/research <query> - Start Scout research
/deploy <project> - Deploy code via Craft`,
          type: 'result'
        });
        break;

      case 'status':
        addMessage({
          agent: 'pulse',
          message: `System Status: ✅ Operational
Active Agents: ${activeAgents.length}/5
Connection: ${isConnected ? 'Connected' : 'Disconnected'}
Uptime: ${Math.floor(Date.now() / 1000 / 60)} minutes`,
          type: 'result'
        });
        break;

      case 'agents':
        addMessage({
          agent: 'atlas',
          message: `Active Agents:
${activeAgents.map(agent => `${agentConfig[agent as keyof typeof agentConfig].icon} ${agentConfig[agent as keyof typeof agentConfig].name} - Online`).join('\n')}`,
          type: 'result'
        });
        break;

      case 'clear':
        setMessages([{
          id: 'welcome_new',
          agent: 'atlas',
          message: 'Chat history cleared.',
          timestamp: new Date(),
          type: 'message'
        }]);
        break;

      case 'run':
        if (args.length === 0) {
          addMessage({
            agent: 'atlas',
            message: 'Usage: /run <workflow_name>',
            type: 'error'
          });
          break;
        }
        
        addMessage({
          agent: 'atlas',
          message: `Executing workflow: ${args[0]}`,
          type: 'command'
        });
        
        // Simulate workflow execution
        setTimeout(() => {
          addMessage({
            agent: 'atlas',
            message: `Workflow ${args[0]} completed successfully.`,
            type: 'result',
            metadata: { execution_id: `exec_${Date.now()}`, workflow: args[0], status: 'success' }
          });
        }, 2000);
        break;

      case 'device':
        if (args.length === 0) {
          addMessage({
            agent: 'rig',
            message: 'Usage: /device <action> [device]',
            type: 'error'
          });
          break;
        }
        
        addMessage({
          agent: 'rig',
          message: `Executing device command: ${args.join(' ')}`,
          type: 'command'
        });
        
        setTimeout(() => {
          addMessage({
            agent: 'rig',
            message: `Device command completed. Status: ${args[0]} executed successfully.`,
            type: 'result'
          });
        }, 1500);
        break;

      case 'research':
        if (args.length === 0) {
          addMessage({
            agent: 'scout',
            message: 'Usage: /research <query>',
            type: 'error'
          });
          break;
        }
        
        addMessage({
          agent: 'scout',
          message: `Starting research: "${args.join(' ')}"`,
          type: 'command'
        });
        
        setTimeout(() => {
          addMessage({
            agent: 'scout',
            message: `Research completed. Found 12 relevant sources. Key insight: ${args.join(' ')} shows strong growth trend.`,
            type: 'result'
          });
        }, 3000);
        break;

      case 'deploy':
        if (args.length === 0) {
          addMessage({
            agent: 'craft',
            message: 'Usage: /deploy <project>',
            type: 'error'
          });
          break;
        }
        
        addMessage({
          agent: 'craft',
          message: `Deploying project: ${args[0]}`,
          type: 'command'
        });
        
        setTimeout(() => {
          addMessage({
            agent: 'craft',
            message: `Deployment successful. Project ${args[0]} is now live.`,
            type: 'result'
          });
        }, 4000);
        break;

      default:
        addMessage({
          agent: 'atlas',
          message: `Unknown command: /${cmd}. Type /help for available commands.`,
          type: 'error'
        });
    }
  };

  // Handle natural language messages
  const handleMessage = async (message: string) => {
    // Simulate processing time
    setTimeout(() => {
      // Simple keyword-based routing
      let responseAgent: ChatMessage['agent'] = 'atlas';
      let responseMessage = '';

      if (message.toLowerCase().includes('device') || message.toLowerCase().includes('control')) {
        responseAgent = 'rig';
        responseMessage = 'I can help with device control. What would you like me to do?';
      } else if (message.toLowerCase().includes('code') || message.toLowerCase().includes('deploy')) {
        responseAgent = 'craft';
        responseMessage = 'Ready to assist with code and deployment tasks.';
      } else if (message.toLowerCase().includes('research') || message.toLowerCase().includes('find')) {
        responseAgent = 'scout';
        responseMessage = 'I can help research that topic. What specific information do you need?';
      } else if (message.toLowerCase().includes('status') || message.toLowerCase().includes('system')) {
        responseAgent = 'pulse';
        responseMessage = 'All systems are running optimally. Is there something specific you\'d like me to check?';
      } else if (message.toLowerCase().includes('notify') || message.toLowerCase().includes('alert')) {
        responseAgent = 'echo';
        responseMessage = 'I can handle notifications and alerts. What would you like me to broadcast?';
      } else {
        responseAgent = 'atlas';
        responseMessage = 'I understand. How would you like me to help with that?';
      }

      addMessage({
        agent: responseAgent,
        message: responseMessage,
        type: 'message'
      });
    }, 1000);
  };

  const getMessageStyle = (message: ChatMessage) => {
    const config = agentConfig[message.agent];
    const isUser = message.agent === 'user';
    
    return {
      alignSelf: isUser ? 'flex-end' : 'flex-start',
      backgroundColor: isUser ? '#3B82F6' : config.color,
      opacity: message.type === 'error' ? 0.8 : 1,
      borderLeft: message.type === 'command' ? '4px solid #FFD700' : 'none'
    };
  };

  const panelStyles = {
    position: 'fixed' as const,
    top: position === 'bottom' ? 'auto' : '50px',
    bottom: position === 'bottom' ? '20px' : 'auto',
    left: position === 'left' ? '20px' : 'auto',
    right: position === 'right' ? '20px' : 'auto',
    width: position === 'bottom' ? 'calc(100% - 40px)' : `${width}px`,
    height: position === 'bottom' ? '300px' : `${height}px`,
    backgroundColor: 'rgba(17, 24, 39, 0.95)',
    backdropFilter: 'blur(16px)',
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
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '20px' }}>🧠</span>
              <span style={{ color: 'white', fontWeight: '600' }}>Atlas Chat</span>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: isConnected ? '#10B981' : '#EF4444'
              }} />
            </div>
            
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
                    maxWidth: '80%',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    color: 'white',
                    fontSize: '14px',
                    lineHeight: '1.4',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '6px',
                    marginBottom: '4px',
                    fontSize: '12px',
                    opacity: 0.8
                  }}>
                    <span>{config.icon}</span>
                    <span>{config.name}</span>
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                  </div>
                  <div>{message.message}</div>
                </motion.div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

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
              placeholder="Type a message or /command..."
              style={{
                flex: 1,
                padding: '8px 12px',
                backgroundColor: 'rgba(55, 65, 81, 0.8)',
                border: '1px solid rgba(75, 85, 99, 0.5)',
                borderRadius: '6px',
                color: 'white',
                fontSize: '14px',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              style={{
                padding: '8px 16px',
                backgroundColor: inputValue.trim() ? '#3B82F6' : 'rgba(75, 85, 99, 0.5)',
                border: 'none',
                borderRadius: '6px',
                color: 'white',
                fontSize: '14px',
                cursor: inputValue.trim() ? 'pointer' : 'not-allowed'
              }}
            >
              Send
            </button>
          </form>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ChatPanel;