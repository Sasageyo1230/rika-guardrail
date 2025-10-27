import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export type SystemMode = 'hands-on' | 'control' | 'recording' | 'idle' | 'error';

export interface StatusBannerProps {
  mode: SystemMode;
  agent?: 'rig' | 'craft' | 'scout' | 'echo' | 'pulse' | 'atlas';
  message?: string;
  duration?: number;
  onModeChange?: (mode: SystemMode) => void;
  position?: 'top' | 'bottom';
}

const modeConfig = {
  'hands-on': {
    label: 'HANDS-ON MODE',
    icon: '🔧',
    color: '#2E8B57',
    gradient: 'linear-gradient(90deg, transparent, #2E8B57, #3CB371, transparent)',
    description: 'Direct device control active',
    agent: 'rig',
    animation: 'pulse'
  },
  'control': {
    label: 'CONTROL MODE', 
    icon: '⚡',
    color: '#4169E1',
    gradient: 'linear-gradient(90deg, transparent, #4169E1, #6495ED, transparent)',
    description: 'System automation engaged',
    agent: 'craft',
    animation: 'spark'
  },
  'recording': {
    label: 'RECORDING MODE',
    icon: '📡',
    color: '#32CD32', 
    gradient: 'linear-gradient(90deg, transparent, #32CD32, #00FF7F, transparent)',
    description: 'Activity monitoring active',
    agent: 'echo',
    animation: 'wave'
  },
  'idle': {
    label: 'IDLE',
    icon: '💤',
    color: '#6B7280',
    gradient: 'linear-gradient(90deg, transparent, #6B7280, #9CA3AF, transparent)',
    description: 'System standby',
    agent: 'atlas',
    animation: 'fade'
  },
  'error': {
    label: 'ERROR',
    icon: '⚠️',
    color: '#EF4444',
    gradient: 'linear-gradient(90deg, transparent, #EF4444, #F87171, transparent)',
    description: 'System attention required',
    agent: 'pulse',
    animation: 'flash'
  }
};

const StatusBanner: React.FC<StatusBannerProps> = ({
  mode,
  agent,
  message,
  duration,
  onModeChange,
  position = 'top'
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [currentMode, setCurrentMode] = useState(mode);
  const [timeRemaining, setTimeRemaining] = useState(duration);

  const config = modeConfig[currentMode];
  const displayAgent = agent || config.agent;

  // Handle mode changes
  useEffect(() => {
    if (mode !== currentMode) {
      setCurrentMode(mode);
    }
  }, [mode, currentMode]);

  // Handle auto-dismiss
  useEffect(() => {
    if (duration && timeRemaining) {
      const timer = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev && prev > 1000) {
            return prev - 1000;
          } else {
            setIsVisible(false);
            return 0;
          }
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [duration, timeRemaining]);

  // Notify parent of mode changes
  useEffect(() => {
    if (onModeChange) {
      onModeChange(currentMode);
    }
  }, [currentMode, onModeChange]);

  const getAnimationVariants = () => {
    const baseVariants = {
      hidden: { 
        opacity: 0, 
        y: position === 'top' ? -50 : 50,
        scale: 0.95 
      },
      visible: { 
        opacity: 0.95, 
        y: 0,
        scale: 1,
        transition: { 
          type: "spring", 
          stiffness: 300, 
          damping: 30 
        }
      },
      exit: { 
        opacity: 0, 
        y: position === 'top' ? -30 : 30,
        scale: 0.9,
        transition: { 
          duration: 0.4,
          ease: "easeIn"
        }
      }
    };

    // Add mode-specific animations
    switch (config.animation) {
      case 'pulse':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            scale: [1, 1.02, 1],
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
      case 'wave':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            background: [
              config.gradient,
              config.gradient.replace('90deg', '120deg'),
              config.gradient
            ],
            transition: {
              ...baseVariants.visible.transition,
              background: {
                repeat: Infinity,
                duration: 2,
                ease: "easeInOut"
              }
            }
          }
        };
      case 'flash':
        return {
          ...baseVariants,
          visible: {
            ...baseVariants.visible,
            opacity: [0.95, 1, 0.95],
            transition: {
              ...baseVariants.visible.transition,
              opacity: {
                repeat: Infinity,
                duration: 1,
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
            backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
            transition: {
              ...baseVariants.visible.transition,
              backgroundPosition: {
                repeat: Infinity,
                duration: 3,
                ease: "linear"
              }
            }
          }
        };
      default:
        return baseVariants;
    }
  };

  const formatTimeRemaining = () => {
    if (!timeRemaining) return '';
    const minutes = Math.floor(timeRemaining / 60000);
    const seconds = Math.floor((timeRemaining % 60000) / 1000);
    return minutes > 0 ? `${minutes}:${seconds.toString().padStart(2, '0')}` : `${seconds}s`;
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="status-banner"
          style={{
            position: 'fixed',
            [position]: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1100,
            minWidth: '300px',
            maxWidth: '600px',
            padding: '12px 20px',
            borderRadius: '8px',
            background: config.gradient,
            border: `1px solid ${config.color}`,
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            color: 'white',
            fontSize: '14px',
            fontWeight: '600',
            textAlign: 'center',
            textShadow: '0 1px 2px rgba(0, 0, 0, 0.6)',
            boxShadow: `0 4px 20px ${config.color}40, 0 2px 10px rgba(0, 0, 0, 0.2)`,
            cursor: 'pointer',
            userSelect: 'none'
          }}
          variants={getAnimationVariants()}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={() => setIsVisible(false)}
          whileHover={{ 
            scale: 1.02,
            boxShadow: `0 6px 25px ${config.color}60, 0 3px 15px rgba(0, 0, 0, 0.3)`
          }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px'
          }}>
            {/* Mode Icon */}
            <motion.span
              style={{ 
                fontSize: '18px',
                filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5))'
              }}
              animate={{ 
                rotate: currentMode === 'recording' ? [0, 360] : 0,
                scale: currentMode === 'error' ? [1, 1.1, 1] : 1
              }}
              transition={{ 
                rotate: { repeat: Infinity, duration: 4, ease: "linear" },
                scale: { repeat: Infinity, duration: 0.8, ease: "easeInOut" }
              }}
            >
              {config.icon}
            </motion.span>

            {/* Mode Label */}
            <span style={{ 
              letterSpacing: '0.5px',
              fontSize: '13px'
            }}>
              {config.label}
            </span>

            {/* Separator */}
            <div style={{
              width: '1px',
              height: '16px',
              backgroundColor: 'rgba(255, 255, 255, 0.4)'
            }} />

            {/* Agent Indicator */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              opacity: 0.9
            }}>
              <span>{displayAgent?.toUpperCase()}</span>
            </div>

            {/* Message or Description */}
            <div style={{
              flex: 1,
              textAlign: 'center',
              fontSize: '12px',
              opacity: 0.9,
              fontWeight: '500'
            }}>
              {message || config.description}
            </div>

            {/* Time Remaining */}
            {timeRemaining && timeRemaining > 0 && (
              <>
                <div style={{
                  width: '1px',
                  height: '16px',
                  backgroundColor: 'rgba(255, 255, 255, 0.4)'
                }} />
                <div style={{
                  fontSize: '11px',
                  opacity: 0.8,
                  fontFamily: 'monospace'
                }}>
                  {formatTimeRemaining()}
                </div>
              </>
            )}

            {/* Close Button */}
            <motion.button
              onClick={(e) => {
                e.stopPropagation();
                setIsVisible(false);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                fontSize: '16px',
                cursor: 'pointer',
                opacity: 0.7,
                padding: '2px',
                lineHeight: 1
              }}
              whileHover={{ 
                opacity: 1, 
                scale: 1.2,
                rotate: 90
              }}
              whileTap={{ scale: 0.9 }}
              transition={{ duration: 0.2 }}
            >
              ✕
            </motion.button>
          </div>

          {/* Progress Bar for Timed Banners */}
          {duration && timeRemaining && (
            <motion.div
              style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                height: '2px',
                backgroundColor: 'rgba(255, 255, 255, 0.3)',
                borderRadius: '0 0 8px 8px'
              }}
            >
              <motion.div
                style={{
                  height: '100%',
                  backgroundColor: 'rgba(255, 255, 255, 0.8)',
                  borderRadius: '0 0 8px 8px'
                }}
                initial={{ width: '100%' }}
                animate={{ 
                  width: `${((timeRemaining || 0) / duration) * 100}%`
                }}
                transition={{ duration: 0.5, ease: "linear" }}
              />
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Hook for managing system status
export const useSystemStatus = () => {
  const [mode, setMode] = useState<SystemMode>('idle');
  const [message, setMessage] = useState<string>('');
  const [agent, setAgent] = useState<string>('');

  const activateMode = (newMode: SystemMode, options?: {
    agent?: string;
    message?: string;
    duration?: number;
  }) => {
    setMode(newMode);
    if (options?.agent) setAgent(options.agent);
    if (options?.message) setMessage(options.message);
  };

  const clearStatus = () => {
    setMode('idle');
    setMessage('');
    setAgent('');
  };

  return {
    mode,
    agent,
    message,
    activateMode,
    clearStatus
  };
};

export default StatusBanner;