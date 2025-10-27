import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface BubbleMessage {
  id: string;
  agent: 'rig' | 'craft' | 'scout' | 'echo' | 'pulse';
  message: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  timestamp: Date;
  duration?: number; // Auto-dismiss time in ms
  interactive?: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
    style?: 'primary' | 'secondary' | 'danger';
  }>;
}

interface BubbleProps {
  message: BubbleMessage;
  onDismiss: (id: string) => void;
  position: { x: number; y: number };
}

const agentConfig = {
  rig: {
    color: '#2E8B57',
    icon: '🔧',
    animation: 'pulse',
    style: 'solid'
  },
  craft: {
    color: '#4169E1', 
    icon: '⚡',
    animation: 'typewriter',
    style: 'dashed'
  },
  scout: {
    color: '#FF6347',
    icon: '🔍', 
    animation: 'search',
    style: 'dotted'
  },
  echo: {
    color: '#32CD32',
    icon: '📡',
    animation: 'wave',
    style: 'gradient'
  },
  pulse: {
    color: '#9370DB',
    icon: '💓',
    animation: 'heartbeat', 
    style: 'neon'
  }
};

const priorityConfig = {
  low: { opacity: 0.7, scale: 0.9 },
  normal: { opacity: 0.9, scale: 1.0 },
  high: { opacity: 1.0, scale: 1.1 },
  urgent: { opacity: 1.0, scale: 1.2, glow: true }
};

const Bubble: React.FC<BubbleProps> = ({ message, onDismiss, position }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [timeLeft, setTimeLeft] = useState(message.duration || 5000);
  
  const config = agentConfig[message.agent];
  const priority = priorityConfig[message.priority];

  // Auto-dismiss logic
  useEffect(() => {
    if (message.duration) {
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
  }, [message.duration, message.id, onDismiss]);

  // Appear animation trigger
  useEffect(() => {
    setIsVisible(true);
  }, []);

  const getBubbleStyle = () => {
    const baseStyle = {
      backgroundColor: config.color,
      opacity: priority.opacity,
      transform: `scale(${priority.scale})`,
      boxShadow: priority.glow ? `0 0 20px ${config.color}40` : 'none',
    };

    switch (config.style) {
      case 'dashed':
        return { ...baseStyle, border: `2px dashed ${config.color}`, backgroundColor: 'transparent' };
      case 'dotted':
        return { ...baseStyle, border: `2px dotted ${config.color}`, backgroundColor: 'transparent' };
      case 'gradient':
        return { ...baseStyle, background: `linear-gradient(135deg, ${config.color}, ${config.color}80)` };
      case 'neon':
        return { 
          ...baseStyle, 
          backgroundColor: 'rgba(0,0,0,0.8)',
          border: `2px solid ${config.color}`,
          boxShadow: `0 0 10px ${config.color}, inset 0 0 10px ${config.color}20`
        };
      default:
        return baseStyle;
    }
  };

  const getAnimationVariants = () => {
    const baseVariants = {
      hidden: { 
        opacity: 0, 
        scale: 0.3, 
        x: position.x, 
        y: position.y + 50 
      },
      visible: { 
        opacity: priority.opacity, 
        scale: priority.scale, 
        x: position.x, 
        y: position.y,
        transition: { type: "spring", stiffness: 500, damping: 30 }
      },
      exit: { 
        opacity: 0, 
        scale: 0.3, 
        x: position.x + 20, 
        y: position.y - 20,
        transition: { duration: 0.2 }
      }
    };

    // Add specific animation behaviors
    switch (config.animation) {
      case 'pulse':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            scale: [priority.scale, priority.scale * 1.05, priority.scale],
            transition: { 
              ...baseVariants.visible.transition,
              scale: { repeat: Infinity, duration: 2 }
            }
          }
        };
      case 'heartbeat':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            scale: [priority.scale, priority.scale * 1.1, priority.scale, priority.scale * 1.1, priority.scale],
            transition: { 
              ...baseVariants.visible.transition,
              scale: { repeat: Infinity, duration: 1.2, times: [0, 0.1, 0.3, 0.4, 1] }
            }
          }
        };
      case 'wave':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            y: [position.y, position.y - 5, position.y],
            transition: { 
              ...baseVariants.visible.transition,
              y: { repeat: Infinity, duration: 3, ease: "easeInOut" }
            }
          }
        };
      default:
        return baseVariants;
    }
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
          className="hud-bubble"
          style={{
            position: 'fixed',
            zIndex: 1000,
            maxWidth: '320px',
            minWidth: '200px',
            borderRadius: '12px',
            padding: '12px 16px',
            color: 'white',
            fontSize: '14px',
            fontFamily: 'Inter, sans-serif',
            cursor: message.interactive ? 'pointer' : 'default',
            userSelect: 'none',
            backdropFilter: 'blur(10px)',
            ...getBubbleStyle()
          }}
          variants={getAnimationVariants()}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={() => message.interactive && onDismiss(message.id)}
        >
          {/* Header */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            marginBottom: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '16px' }}>{config.icon}</span>
              <span style={{ fontWeight: '600', fontSize: '12px' }}>
                {message.agent.toUpperCase()}
              </span>
              {message.priority === 'urgent' && (
                <span style={{ 
                  fontSize: '10px', 
                  backgroundColor: 'rgba(255,0,0,0.8)', 
                  padding: '2px 6px', 
                  borderRadius: '4px' 
                }}>
                  URGENT
                </span>
              )}
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {formatTimeLeft() && (
                <span style={{ fontSize: '10px', opacity: 0.7 }}>
                  {formatTimeLeft()}
                </span>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDismiss(message.id);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'white',
                  fontSize: '12px',
                  cursor: 'pointer',
                  opacity: 0.7,
                  padding: '0'
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* Message */}
          <div style={{ 
            lineHeight: '1.4', 
            marginBottom: message.actions ? '12px' : '0' 
          }}>
            {message.message}
          </div>

          {/* Actions */}
          {message.actions && (
            <div style={{ 
              display: 'flex', 
              gap: '8px', 
              justifyContent: 'flex-end' 
            }}>
              {message.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={(e) => {
                    e.stopPropagation();
                    action.action();
                    onDismiss(message.id);
                  }}
                  style={{
                    background: action.style === 'primary' ? 'rgba(255,255,255,0.2)' : 
                               action.style === 'danger' ? 'rgba(255,0,0,0.2)' : 'transparent',
                    border: '1px solid rgba(255,255,255,0.3)',
                    color: 'white',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  {action.label}
                </button>
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
              borderRadius: '0 0 12px 12px'
            }}>
              <motion.div
                style={{
                  height: '100%',
                  backgroundColor: 'rgba(255,255,255,0.6)',
                  borderRadius: '0 0 12px 12px'
                }}
                initial={{ width: '100%' }}
                animate={{ width: `${(timeLeft / (message.duration || 1)) * 100}%` }}
                transition={{ duration: 0.1, ease: "linear" }}
              />
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Bubble;