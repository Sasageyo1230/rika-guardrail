import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface BubbleMessage {
  id: string;
  agent: 'rig' | 'craft' | 'scout' | 'echo' | 'pulse' | 'atlas';
  message: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  timestamp: Date;
  duration?: number; // Auto-dismiss time in ms
  interactive?: boolean;
  voiceEnabled?: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
    style?: 'primary' | 'secondary' | 'danger';
  }>;
  metadata?: {
    task_id?: string;
    progress?: number;
    status?: string;
  };
}

interface EnhancedBubbleProps {
  message: BubbleMessage;
  onDismiss: (id: string) => void;
  position: { x: number; y: number };
  audioContext?: AudioContext;
}

const agentConfig = {
  rig: {
    color: '#2E8B57',
    icon: '🔧',
    name: 'Rig',
    voiceType: 'methodical',
    animationType: 'pulse'
  },
  craft: {
    color: '#4169E1', 
    icon: '⚡',
    name: 'Craft',
    voiceType: 'precise',
    animationType: 'spark'
  },
  scout: {
    color: '#FF6347',
    icon: '🔍', 
    name: 'Scout',
    voiceType: 'curious',
    animationType: 'scan'
  },
  echo: {
    color: '#32CD32',
    icon: '📡',
    name: 'Echo',
    voiceType: 'clear',
    animationType: 'wave'
  },
  pulse: {
    color: '#9370DB',
    icon: '💓',
    name: 'Pulse',
    voiceType: 'analytical',
    animationType: 'heartbeat'
  },
  atlas: {
    color: '#FFD700',
    icon: '🧠',
    name: 'Atlas',
    voiceType: 'authoritative',
    animationType: 'glow'
  }
};

const priorityConfig = {
  low: { opacity: 0.7, scale: 0.9, urgency: 1 },
  normal: { opacity: 0.9, scale: 1.0, urgency: 2 },
  high: { opacity: 1.0, scale: 1.1, urgency: 3 },
  urgent: { opacity: 1.0, scale: 1.2, urgency: 4, glow: true }
};

const EnhancedBubble: React.FC<EnhancedBubbleProps> = ({ 
  message, 
  onDismiss, 
  position,
  audioContext 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [timeLeft, setTimeLeft] = useState(message.duration || 5000);
  const [isHovered, setIsHovered] = useState(false);
  const [hasPlayedVoice, setHasPlayedVoice] = useState(false);
  const bubbleRef = useRef<HTMLDivElement>(null);
  
  const config = agentConfig[message.agent];
  const priority = priorityConfig[message.priority];

  // Auto-dismiss logic
  useEffect(() => {
    if (message.duration && !isHovered) {
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 100) {
            onDismiss(message.id);
            return 0;
          }
          return prev - 100;
        });
      }, 100);
      
      return () => clearInterval(timer);
    }
  }, [message.duration, message.id, onDismiss, isHovered]);

  // Appear animation trigger
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  // Voice synthesis
  useEffect(() => {
    if (message.voiceEnabled && !hasPlayedVoice && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(message.message);
      
      // Configure voice based on agent
      const voices = speechSynthesis.getVoices();
      let preferredVoice = null;
      
      switch (config.voiceType) {
        case 'methodical':
          preferredVoice = voices.find(v => v.name.includes('David') || v.name.includes('Microsoft Mark'));
          utterance.rate = 0.9;
          utterance.pitch = 0.8;
          break;
        case 'precise':
          preferredVoice = voices.find(v => v.name.includes('Microsoft Zira') || v.name.includes('Karen'));
          utterance.rate = 1.1;
          utterance.pitch = 1.0;
          break;
        case 'curious':
          preferredVoice = voices.find(v => v.name.includes('Microsoft Hazel') || v.name.includes('Samantha'));
          utterance.rate = 1.2;
          utterance.pitch = 1.1;
          break;
        case 'clear':
          preferredVoice = voices.find(v => v.name.includes('Microsoft Eva') || v.name.includes('Alex'));
          utterance.rate = 1.0;
          utterance.pitch = 1.0;
          break;
        case 'analytical':
          preferredVoice = voices.find(v => v.name.includes('Microsoft Paul') || v.name.includes('Daniel'));
          utterance.rate = 0.95;
          utterance.pitch = 0.9;
          break;
        case 'authoritative':
          preferredVoice = voices.find(v => v.name.includes('Microsoft George') || v.name.includes('Fred'));
          utterance.rate = 0.85;
          utterance.pitch = 0.7;
          break;
      }
      
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      
      utterance.volume = 0.7;
      speechSynthesis.speak(utterance);
      setHasPlayedVoice(true);
    }
  }, [message.voiceEnabled, hasPlayedVoice, config.voiceType, message.message]);

  const getAnimationVariants = () => {
    const baseVariants = {
      hidden: { 
        opacity: 0, 
        scale: 0.3, 
        x: position.x, 
        y: position.y + 50,
        rotate: 10
      },
      visible: { 
        opacity: priority.opacity, 
        scale: priority.scale, 
        x: position.x, 
        y: position.y,
        rotate: 0,
        transition: { 
          type: "spring", 
          stiffness: 400, 
          damping: 25,
          mass: 0.8
        }
      },
      exit: { 
        opacity: 0, 
        scale: 0.8, 
        x: position.x + 20, 
        y: position.y - 20,
        rotate: -5,
        transition: { 
          duration: 0.3,
          ease: "easeIn"
        }
      }
    };

    // Add agent-specific animation behaviors
    switch (config.animationType) {
      case 'pulse':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            scale: [priority.scale, priority.scale * 1.05, priority.scale],
            transition: { 
              ...baseVariants.visible.transition,
              scale: { 
                repeat: Infinity, 
                duration: 2,
                ease: "easeInOut"
              }
            }
          }
        };
      case 'heartbeat':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            scale: [
              priority.scale, 
              priority.scale * 1.1, 
              priority.scale, 
              priority.scale * 1.05, 
              priority.scale
            ],
            transition: { 
              ...baseVariants.visible.transition,
              scale: { 
                repeat: Infinity, 
                duration: 1.2, 
                times: [0, 0.1, 0.3, 0.4, 1],
                ease: "easeInOut"
              }
            }
          }
        };
      case 'wave':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            y: [position.y, position.y - 3, position.y],
            transition: { 
              ...baseVariants.visible.transition,
              y: { 
                repeat: Infinity, 
                duration: 2.5, 
                ease: "easeInOut" 
              }
            }
          }
        };
      case 'spark':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            rotate: [0, 2, -1, 0],
            scale: [priority.scale, priority.scale * 1.02, priority.scale * 0.98, priority.scale],
            transition: { 
              ...baseVariants.visible.transition,
              rotate: { 
                repeat: Infinity, 
                duration: 1.5,
                ease: "easeInOut"
              },
              scale: { 
                repeat: Infinity, 
                duration: 1.5,
                ease: "easeInOut"
              }
            }
          }
        };
      case 'scan':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            y: [position.y, position.y - 5, position.y],
            scale: [priority.scale, priority.scale * 1.03, priority.scale],
            transition: { 
              ...baseVariants.visible.transition,
              y: { 
                repeat: Infinity, 
                duration: 3,
                ease: "easeInOut"
              },
              scale: { 
                repeat: Infinity, 
                duration: 3,
                ease: "easeInOut"
              }
            }
          }
        };
      case 'glow':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            rotate: [0, 2, 0],
            scale: [priority.scale, priority.scale * 1.03, priority.scale],
            transition: { 
              ...baseVariants.visible.transition,
              rotate: { 
                repeat: Infinity, 
                duration: 4,
                ease: "easeInOut"
              },
              scale: { 
                repeat: Infinity, 
                duration: 4,
                ease: "easeInOut"
              }
            }
          }
        };
      default:
        return baseVariants;
    }
  };

  const getBubbleClassName = () => {
    const classes = [
      'agent-bubble',
      `agent-bubble--${message.agent}`,
      `agent-bubble--priority-${message.priority}`,
      'agent-bubble--active'
    ];
    
    if (isHovered) classes.push('agent-bubble--hovered');
    if (message.metadata?.status === 'error') classes.push('agent-bubble--error');
    
    return classes.join(' ');
  };

  const formatTimeLeft = () => {
    if (!message.duration) return '';
    const seconds = Math.ceil(timeLeft / 1000);
    return seconds > 0 ? `${seconds}s` : '';
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          ref={bubbleRef}
          className={getBubbleClassName()}
          style={{
            position: 'fixed',
            zIndex: 1000 + priority.urgency,
            maxWidth: '320px',
            minWidth: '200px',
            borderRadius: '16px',
            padding: '12px 16px',
            color: 'white',
            fontSize: '14px',
            fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
            cursor: message.interactive ? 'pointer' : 'default',
            userSelect: 'none',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)', // Safari support
            boxShadow: priority.glow ? 
              `0 0 25px ${config.color}66, 0 4px 20px rgba(0,0,0,0.2)` : 
              `0 4px 20px rgba(0,0,0,0.15)`
          }}
          variants={getAnimationVariants()}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={() => message.interactive && onDismiss(message.id)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          whileHover={{ scale: priority.scale * 1.02 }}
          whileTap={{ scale: priority.scale * 0.98 }}
        >
          {/* Header */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            marginBottom: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <motion.span 
                className="agent-icon"
                style={{ fontSize: '18px' }}
                animate={{ rotate: isHovered ? 10 : 0 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                {config.icon}
              </motion.span>
              <span style={{ fontWeight: '600', fontSize: '12px', letterSpacing: '0.5px' }}>
                {config.name.toUpperCase()}
              </span>
              {message.priority === 'urgent' && (
                <motion.span 
                  style={{ 
                    fontSize: '10px', 
                    backgroundColor: 'rgba(255,0,0,0.8)', 
                    padding: '2px 6px', 
                    borderRadius: '4px',
                    fontWeight: '600'
                  }}
                  animate={{ opacity: [1, 0.6, 1] }}
                  transition={{ repeat: Infinity, duration: 1 }}
                >
                  URGENT
                </motion.span>
              )}
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {formatTimeLeft() && (
                <span style={{ fontSize: '10px', opacity: 0.7 }}>
                  {formatTimeLeft()}
                </span>
              )}
              {message.voiceEnabled && (
                <motion.span
                  style={{ fontSize: '12px', opacity: 0.6 }}
                  animate={{ opacity: hasPlayedVoice ? 0.6 : [0.6, 1, 0.6] }}
                  transition={{ repeat: hasPlayedVoice ? 0 : Infinity, duration: 1 }}
                >
                  🔊
                </motion.span>
              )}
              <motion.button
                onClick={(e) => {
                  e.stopPropagation();
                  onDismiss(message.id);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'white',
                  fontSize: '14px',
                  cursor: 'pointer',
                  opacity: 0.7,
                  padding: '2px',
                  borderRadius: '2px'
                }}
                whileHover={{ opacity: 1, scale: 1.2 }}
                whileTap={{ scale: 0.9 }}
              >
                ✕
              </motion.button>
            </div>
          </div>

          {/* Message Content */}
          <div style={{ 
            lineHeight: '1.4', 
            marginBottom: message.actions || message.metadata?.progress !== undefined ? '12px' : '0' 
          }}>
            {message.message}
          </div>

          {/* Progress Bar */}
          {message.metadata?.progress !== undefined && (
            <div style={{
              marginBottom: '8px',
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderRadius: '6px',
              height: '4px',
              overflow: 'hidden'
            }}>
              <motion.div
                style={{
                  height: '100%',
                  backgroundColor: config.color,
                  borderRadius: '6px'
                }}
                initial={{ width: 0 }}
                animate={{ width: `${message.metadata.progress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          )}

          {/* Actions */}
          {message.actions && (
            <div style={{ 
              display: 'flex', 
              gap: '8px', 
              justifyContent: 'flex-end' 
            }}>
              {message.actions.map((action, index) => (
                <motion.button
                  key={index}
                  onClick={(e) => {
                    e.stopPropagation();
                    action.action();
                    if (action.style !== 'secondary') {
                      onDismiss(message.id);
                    }
                  }}
                  style={{
                    background: action.style === 'primary' ? 'rgba(255,255,255,0.25)' : 
                               action.style === 'danger' ? 'rgba(255,0,0,0.25)' : 
                               'transparent',
                    border: '1px solid rgba(255,255,255,0.3)',
                    color: 'white',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    fontWeight: '500'
                  }}
                  whileHover={{ 
                    scale: 1.05, 
                    backgroundColor: action.style === 'primary' ? 'rgba(255,255,255,0.35)' : 
                                    action.style === 'danger' ? 'rgba(255,0,0,0.35)' : 
                                    'rgba(255,255,255,0.15)'
                  }}
                  whileTap={{ scale: 0.95 }}
                >
                  {action.label}
                </motion.button>
              ))}
            </div>
          )}

          {/* Progress bar for timed messages */}
          {message.duration && (
            <div style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: '2px',
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderRadius: '0 0 16px 16px'
            }}>
              <motion.div
                style={{
                  height: '100%',
                  backgroundColor: 'rgba(255,255,255,0.6)',
                  borderRadius: '0 0 16px 16px'
                }}
                initial={{ width: '100%' }}
                animate={{ 
                  width: `${(timeLeft / (message.duration || 1)) * 100}%` 
                }}
                transition={{ duration: 0.1, ease: "linear" }}
              />
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default EnhancedBubble;