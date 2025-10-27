import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Command {
  id: string;
  title: string;
  description: string;
  category: 'workflow' | 'device' | 'research' | 'system' | 'navigation';
  agent: 'rig' | 'craft' | 'scout' | 'echo' | 'pulse' | 'atlas';
  keywords: string[];
  action: () => void | Promise<void>;
  shortcut?: string;
  icon: string;
}

interface CommandPaletteProps {
  isVisible: boolean;
  onClose: () => void;
  onExecute?: (command: Command) => void;
}

const commandCategories = {
  workflow: { name: 'Workflows', color: '#3B82F6', icon: '⚙️' },
  device: { name: 'Device Control', color: '#2E8B57', icon: '🔧' },
  research: { name: 'Research', color: '#FF6347', icon: '🔍' },
  system: { name: 'System', color: '#9370DB', icon: '💓' },
  navigation: { name: 'Navigation', color: '#32CD32', icon: '🗺️' }
};

const agentConfig = {
  rig: { color: '#2E8B57', icon: '🔧' },
  craft: { color: '#4169E1', icon: '⚡' },
  scout: { color: '#FF6347', icon: '🔍' },
  echo: { color: '#32CD32', icon: '📡' },
  pulse: { color: '#9370DB', icon: '💓' },
  atlas: { color: '#FFD700', icon: '🧠' }
};

const CommandPalette: React.FC<CommandPaletteProps> = ({
  isVisible,
  onClose,
  onExecute
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Default commands
  const defaultCommands: Command[] = [
    // Workflow commands
    {
      id: 'run-device-controller',
      title: 'Run Device Controller',
      description: 'Execute device control workflow',
      category: 'workflow',
      agent: 'rig',
      keywords: ['device', 'control', 'automation', 'rig'],
      action: () => console.log('Running device controller'),
      icon: '🎮',
      shortcut: 'Ctrl+D'
    },
    {
      id: 'run-notification-sender',
      title: 'Send Notification',
      description: 'Send notification through Echo',
      category: 'workflow', 
      agent: 'echo',
      keywords: ['notification', 'alert', 'message', 'echo'],
      action: () => console.log('Sending notification'),
      icon: '📢'
    },
    {
      id: 'deploy-code',
      title: 'Deploy Code',
      description: 'Deploy latest code changes',
      category: 'workflow',
      agent: 'craft',
      keywords: ['deploy', 'code', 'build', 'craft'],
      action: () => console.log('Deploying code'),
      icon: '🚀',
      shortcut: 'Ctrl+Shift+D'
    },

    // Device commands
    {
      id: 'tv-power',
      title: 'Toggle TV Power',
      description: 'Turn TV on or off',
      category: 'device',
      agent: 'rig',
      keywords: ['tv', 'television', 'power', 'on', 'off'],
      action: () => console.log('Toggling TV power'),
      icon: '📺'
    },
    {
      id: 'pc-sleep',
      title: 'Put PC to Sleep',
      description: 'Put computer into sleep mode',
      category: 'device',
      agent: 'rig',
      keywords: ['pc', 'computer', 'sleep', 'power'],
      action: () => console.log('PC going to sleep'),
      icon: '💻'
    },
    {
      id: 'bluetooth-scan',
      title: 'Scan Bluetooth Devices',
      description: 'Scan for nearby Bluetooth devices',
      category: 'device',
      agent: 'rig',
      keywords: ['bluetooth', 'scan', 'devices', 'wireless'],
      action: () => console.log('Scanning Bluetooth'),
      icon: '📶'
    },

    // Research commands
    {
      id: 'quick-research',
      title: 'Quick Research',
      description: 'Perform quick research on a topic',
      category: 'research',
      agent: 'scout',
      keywords: ['research', 'quick', 'search', 'scout'],
      action: () => console.log('Starting quick research'),
      icon: '⚡',
      shortcut: 'Ctrl+R'
    },
    {
      id: 'deep-research',
      title: 'Deep Research',
      description: 'Perform comprehensive research',
      category: 'research',
      agent: 'scout',
      keywords: ['research', 'deep', 'comprehensive', 'analysis'],
      action: () => console.log('Starting deep research'),
      icon: '🔬'
    },
    {
      id: 'market-analysis',
      title: 'Market Analysis',
      description: 'Analyze market trends and data',
      category: 'research',
      agent: 'scout',
      keywords: ['market', 'analysis', 'trends', 'business'],
      action: () => console.log('Analyzing market'),
      icon: '📈'
    },

    // System commands
    {
      id: 'system-status',
      title: 'System Status',
      description: 'Check overall system health',
      category: 'system',
      agent: 'pulse',
      keywords: ['status', 'health', 'system', 'pulse'],
      action: () => console.log('Checking system status'),
      icon: '💓',
      shortcut: 'Ctrl+S'
    },
    {
      id: 'clear-logs',
      title: 'Clear Logs',
      description: 'Clear system logs and history',
      category: 'system',
      agent: 'pulse',
      keywords: ['clear', 'logs', 'history', 'cleanup'],
      action: () => console.log('Clearing logs'),
      icon: '🧹'
    },
    {
      id: 'restart-services',
      title: 'Restart Services',
      description: 'Restart all Rika services',
      category: 'system',
      agent: 'pulse',
      keywords: ['restart', 'services', 'reboot', 'refresh'],
      action: () => console.log('Restarting services'),
      icon: '🔄'
    },

    // Navigation commands
    {
      id: 'open-chat',
      title: 'Open Chat Panel',
      description: 'Open Atlas chat interface',
      category: 'navigation',
      agent: 'atlas',
      keywords: ['chat', 'atlas', 'communication', 'panel'],
      action: () => console.log('Opening chat'),
      icon: '💬',
      shortcut: 'Ctrl+T'
    },
    {
      id: 'toggle-hud',
      title: 'Toggle HUD',
      description: 'Show/hide HUD bubbles',
      category: 'navigation',
      agent: 'atlas',
      keywords: ['hud', 'bubbles', 'toggle', 'display'],
      action: () => console.log('Toggling HUD'),
      icon: '👁️'
    },
    {
      id: 'open-dashboard',
      title: 'Open Dashboard',
      description: 'Open main Rika dashboard',
      category: 'navigation',
      agent: 'atlas',
      keywords: ['dashboard', 'main', 'overview', 'home'],
      action: () => console.log('Opening dashboard'),
      icon: '🏠',
      shortcut: 'Ctrl+H'
    }
  ];

  // Filter commands based on query
  const filteredCommands = useMemo(() => {
    if (!query.trim()) {
      // Show recent commands first, then all commands
      const recent = defaultCommands.filter(cmd => recentCommands.includes(cmd.id));
      const others = defaultCommands.filter(cmd => !recentCommands.includes(cmd.id));
      return [...recent, ...others];
    }

    const lowerQuery = query.toLowerCase();
    return defaultCommands
      .filter(cmd => 
        cmd.title.toLowerCase().includes(lowerQuery) ||
        cmd.description.toLowerCase().includes(lowerQuery) ||
        cmd.keywords.some(keyword => keyword.toLowerCase().includes(lowerQuery)) ||
        cmd.agent.toLowerCase().includes(lowerQuery) ||
        cmd.category.toLowerCase().includes(lowerQuery)
      )
      .sort((a, b) => {
        // Prioritize title matches
        const aTitle = a.title.toLowerCase().includes(lowerQuery);
        const bTitle = b.title.toLowerCase().includes(lowerQuery);
        if (aTitle && !bTitle) return -1;
        if (!aTitle && bTitle) return 1;
        
        // Then keyword matches
        const aKeyword = a.keywords.some(k => k.toLowerCase().includes(lowerQuery));
        const bKeyword = b.keywords.some(k => k.toLowerCase().includes(lowerQuery));
        if (aKeyword && !bKeyword) return -1;
        if (!aKeyword && bKeyword) return 1;
        
        return 0;
      });
  }, [query, defaultCommands, recentCommands]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isVisible) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < filteredCommands.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : filteredCommands.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            executeCommand(filteredCommands[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isVisible, selectedIndex, filteredCommands, onClose]);

  // Reset state when opened
  useEffect(() => {
    if (isVisible) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isVisible]);

  // Update selected index when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Execute command
  const executeCommand = async (command: Command) => {
    try {
      await command.action();
      
      // Add to recent commands
      setRecentCommands(prev => {
        const updated = [command.id, ...prev.filter(id => id !== command.id)];
        return updated.slice(0, 5); // Keep only 5 recent
      });
      
      if (onExecute) {
        onExecute(command);
      }
      
      onClose();
    } catch (error) {
      console.error('Command execution failed:', error);
    }
  };

  // Group commands by category
  const groupedCommands = useMemo(() => {
    const groups: Record<string, Command[]> = {};
    filteredCommands.forEach(cmd => {
      if (!groups[cmd.category]) {
        groups[cmd.category] = [];
      }
      groups[cmd.category].push(cmd);
    });
    return groups;
  }, [filteredCommands]);

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
          backdropFilter: 'blur(4px)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'center',
          paddingTop: '20vh'
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          style={{
            width: '600px',
            maxWidth: '90vw',
            maxHeight: '60vh',
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            backdropFilter: 'blur(16px)',
            borderRadius: '12px',
            border: '1px solid rgba(75, 85, 99, 0.3)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
          }}
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Search Input */}
          <div style={{ padding: '20px 20px 16px' }}>
            <div style={{ position: 'relative' }}>
              <span style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                fontSize: '16px',
                color: '#9CA3AF'
              }}>
                🔍
              </span>
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search commands... (try 'device', 'research', 'deploy')"
                style={{
                  width: '100%',
                  padding: '12px 12px 12px 40px',
                  backgroundColor: 'rgba(55, 65, 81, 0.8)',
                  border: '1px solid rgba(75, 85, 99, 0.5)',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '16px',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          {/* Results */}
          <div
            ref={listRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              paddingBottom: '8px'
            }}
          >
            {filteredCommands.length === 0 ? (
              <div style={{
                padding: '40px 20px',
                textAlign: 'center',
                color: '#9CA3AF'
              }}>
                No commands found for "{query}"
              </div>
            ) : (
              Object.entries(groupedCommands).map(([category, commands]) => (
                <div key={category} style={{ marginBottom: '8px' }}>
                  {/* Category Header */}
                  <div style={{
                    padding: '8px 20px 4px',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: commandCategories[category as keyof typeof commandCategories].color,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    {commandCategories[category as keyof typeof commandCategories].icon} {commandCategories[category as keyof typeof commandCategories].name}
                  </div>

                  {/* Commands */}
                  {commands.map((command, index) => {
                    const globalIndex = filteredCommands.indexOf(command);
                    const isSelected = globalIndex === selectedIndex;
                    const agentConf = agentConfig[command.agent];

                    return (
                      <motion.div
                        key={command.id}
                        style={{
                          padding: '12px 20px',
                          backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                          borderLeft: isSelected ? '3px solid #3B82F6' : '3px solid transparent',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px'
                        }}
                        whileHover={{ backgroundColor: 'rgba(55, 65, 81, 0.3)' }}
                        onClick={() => executeCommand(command)}
                      >
                        <span style={{ fontSize: '20px' }}>{command.icon}</span>
                        
                        <div style={{ flex: 1 }}>
                          <div style={{
                            color: 'white',
                            fontSize: '14px',
                            fontWeight: '500',
                            marginBottom: '2px'
                          }}>
                            {command.title}
                          </div>
                          <div style={{
                            color: '#9CA3AF',
                            fontSize: '12px'
                          }}>
                            {command.description}
                          </div>
                        </div>

                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}>
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            color: agentConf.color,
                            fontSize: '12px'
                          }}>
                            <span>{agentConf.icon}</span>
                            <span>{command.agent}</span>
                          </div>
                          
                          {command.shortcut && (
                            <div style={{
                              padding: '2px 6px',
                              backgroundColor: 'rgba(75, 85, 99, 0.3)',
                              borderRadius: '4px',
                              fontSize: '10px',
                              color: '#D1D5DB'
                            }}>
                              {command.shortcut}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div style={{
            padding: '12px 20px',
            borderTop: '1px solid rgba(75, 85, 99, 0.3)',
            backgroundColor: 'rgba(55, 65, 81, 0.3)',
            fontSize: '12px',
            color: '#9CA3AF',
            display: 'flex',
            justifyContent: 'space-between'
          }}>
            <span>↑↓ Navigate • Enter Execute • Esc Close</span>
            <span>{filteredCommands.length} commands</span>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default CommandPalette;