import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface Command {
  id: string;
  title: string;
  description: string;
  category: 'workflow' | 'device' | 'research' | 'creative' | 'system' | 'navigation' | 'vault';
  agent: 'rig' | 'craft' | 'scout' | 'echo' | 'pulse' | 'atlas';
  keywords: string[];
  action: () => void | Promise<void>;
  shortcut?: string;
  icon: string;
  enabled?: boolean;
  params?: Array<{
    name: string;
    type: 'string' | 'number' | 'boolean' | 'select';
    required?: boolean;
    options?: string[];
    default?: any;
  }>;
}

interface EnhancedCommandPaletteProps {
  isVisible: boolean;
  onClose: () => void;
  onExecute?: (command: Command) => void;
  customCommands?: Command[];
}

const commandCategories = {
  workflow: { name: 'Workflows', color: '#3B82F6', icon: '⚙️' },
  device: { name: 'Device Control', color: '#2E8B57', icon: '🔧' },
  research: { name: 'Research', color: '#FF6347', icon: '🔍' },
  creative: { name: 'Creative Tools', color: '#9370DB', icon: '🎨' },
  system: { name: 'System', color: '#6B7280', icon: '💓' },
  navigation: { name: 'Navigation', color: '#32CD32', icon: '🗺️' },
  vault: { name: 'Knowledge Vault', color: '#F59E0B', icon: '📚' }
};

const agentConfig = {
  rig: { color: '#2E8B57', icon: '🔧' },
  craft: { color: '#4169E1', icon: '⚡' },
  scout: { color: '#FF6347', icon: '🔍' },
  echo: { color: '#32CD32', icon: '📡' },
  pulse: { color: '#9370DB', icon: '💓' },
  atlas: { color: '#FFD700', icon: '🧠' }
};

const EnhancedCommandPalette: React.FC<EnhancedCommandPaletteProps> = ({
  isVisible,
  onClose,
  onExecute,
  customCommands = []
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const [showParameters, setShowParameters] = useState(false);
  const [selectedCommand, setSelectedCommand] = useState<Command | null>(null);
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({});
  
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Enhanced command registry with Phase 3.3 additions
  const defaultCommands: Command[] = [
    // Workflow commands
    {
      id: 'run-device-controller',
      title: 'Run Device Controller',
      description: 'Execute device control workflow with safety checks',
      category: 'workflow',
      agent: 'rig',
      keywords: ['device', 'control', 'automation', 'rig', 'bluetooth', 'cec'],
      action: () => console.log('Running device controller'),
      icon: '🎮',
      shortcut: 'Ctrl+D'
    },
    {
      id: 'run-notification-sender',
      title: 'Send Notification',
      description: 'Send notification through Echo agent',
      category: 'workflow', 
      agent: 'echo',
      keywords: ['notification', 'alert', 'message', 'echo', 'broadcast'],
      action: () => console.log('Sending notification'),
      icon: '📢',
      params: [
        { name: 'message', type: 'string', required: true },
        { name: 'priority', type: 'select', options: ['low', 'normal', 'high', 'urgent'], default: 'normal' }
      ]
    },
    {
      id: 'deploy-code',
      title: 'Deploy Code',
      description: 'Deploy latest code changes through Craft',
      category: 'workflow',
      agent: 'craft',
      keywords: ['deploy', 'code', 'build', 'craft', 'production'],
      action: () => console.log('Deploying code'),
      icon: '🚀',
      shortcut: 'Ctrl+Shift+D'
    },

    // Device commands (Enhanced)
    {
      id: 'bluetooth-scan',
      title: 'Scan Bluetooth Devices',
      description: 'Discover and list nearby Bluetooth devices',
      category: 'device',
      agent: 'rig',
      keywords: ['bluetooth', 'scan', 'discover', 'devices', 'wireless'],
      action: () => console.log('Scanning Bluetooth devices'),
      icon: '📶'
    },
    {
      id: 'tv-control',
      title: 'Control TV (HDMI-CEC)',
      description: 'Control TV power and input via HDMI-CEC',
      category: 'device',
      agent: 'rig',
      keywords: ['tv', 'television', 'cec', 'hdmi', 'power', 'input'],
      action: () => console.log('Controlling TV'),
      icon: '📺',
      params: [
        { name: 'action', type: 'select', options: ['power_on', 'power_off', 'set_input'], required: true },
        { name: 'input', type: 'select', options: ['HDMI1', 'HDMI2', 'HDMI3', 'USB'], required: false }
      ]
    },
    {
      id: 'gesture-toggle',
      title: 'Toggle Gesture Recognition',
      description: 'Enable/disable MediaPipe gesture control',
      category: 'device',
      agent: 'rig',
      keywords: ['gesture', 'hand', 'camera', 'mediapipe', 'recognition'],
      action: () => console.log('Toggling gesture recognition'),
      icon: '👋'
    },

    // Research commands (Enhanced)
    {
      id: 'research-quick',
      title: 'Quick Research',
      description: 'Perform rapid research with 5 sources',
      category: 'research',
      agent: 'scout',
      keywords: ['research', 'quick', 'fast', 'scout', 'search'],
      action: () => console.log('Starting quick research'),
      icon: '⚡',
      shortcut: 'Ctrl+R',
      params: [
        { name: 'query', type: 'string', required: true },
        { name: 'sources', type: 'number', default: 5 }
      ]
    },
    {
      id: 'research-deep',
      title: 'Deep Research',
      description: 'Comprehensive research with up to 15 sources',
      category: 'research',
      agent: 'scout',
      keywords: ['research', 'deep', 'comprehensive', 'analysis', 'thorough'],
      action: () => console.log('Starting deep research'),
      icon: '🔬',
      params: [
        { name: 'query', type: 'string', required: true },
        { name: 'sources', type: 'number', default: 15 },
        { name: 'analysis_depth', type: 'select', options: ['basic', 'detailed', 'expert'], default: 'detailed' }
      ]
    },

    // Creative Tools (NEW Phase 3.3)
    {
      id: 'rig-apply-template',
      title: 'Rig: Apply Template',
      description: 'Apply Blender template for modeling/rigging',
      category: 'creative',
      agent: 'rig',
      keywords: ['rig', 'blender', 'template', 'model', 'character', '3d'],
      action: () => console.log('Applying Rig template'),
      icon: '🎭',
      params: [
        { name: 'template', type: 'select', options: ['character-base', 'vehicle-setup', 'camera-rig', 'lighting-setup'], required: true },
        { name: 'apply_materials', type: 'boolean', default: true }
      ]
    },
    {
      id: 'craft-storyboard',
      title: 'Craft: Storyboard Draft',
      description: 'Generate visual storyboard panels from script',
      category: 'creative',
      agent: 'craft',
      keywords: ['craft', 'storyboard', 'panels', 'script', 'visual', 'scene'],
      action: () => console.log('Generating storyboard'),
      icon: '🎬',
      params: [
        { name: 'script_text', type: 'string', required: true },
        { name: 'panels', type: 'number', default: 8 },
        { name: 'style', type: 'select', options: ['sketch', 'detailed', 'minimalist'], default: 'sketch' }
      ]
    },
    {
      id: 'craft-scene-breakdown',
      title: 'Craft: Scene Breakdown',
      description: 'Extract scenes and beats from script',
      category: 'creative',
      agent: 'craft',
      keywords: ['craft', 'scene', 'script', 'breakdown', 'beats', 'analysis'],
      action: () => console.log('Breaking down script'),
      icon: '📋',
      params: [
        { name: 'script_file', type: 'string', required: true }
      ]
    },

    // Knowledge Vault (NEW Phase 3.3)
    {
      id: 'vault-search',
      title: 'Vault: Search Knowledge',
      description: 'Search the knowledge vault with semantic matching',
      category: 'vault',
      agent: 'scout',
      keywords: ['vault', 'search', 'knowledge', 'semantic', 'vector', 'find'],
      action: () => console.log('Searching knowledge vault'),
      icon: '🔍',
      shortcut: 'Ctrl+K',
      params: [
        { name: 'query', type: 'string', required: true },
        { name: 'limit', type: 'number', default: 10 },
        { name: 'similarity_threshold', type: 'number', default: 0.7 }
      ]
    },
    {
      id: 'vault-import',
      title: 'Vault: Import Documents',
      description: 'Import PDFs and documents into knowledge vault',
      category: 'vault',
      agent: 'scout',
      keywords: ['vault', 'import', 'pdf', 'documents', 'upload', 'index'],
      action: () => console.log('Importing documents'),
      icon: '📚',
      params: [
        { name: 'file_path', type: 'string', required: true },
        { name: 'tags', type: 'string', required: false }
      ]
    },
    {
      id: 'vault-digest',
      title: 'Vault: Generate Digest',
      description: 'Create daily/weekly knowledge digest',
      category: 'vault',
      agent: 'scout',
      keywords: ['vault', 'digest', 'summary', 'weekly', 'daily', 'report'],
      action: () => console.log('Generating vault digest'),
      icon: '📰',
      params: [
        { name: 'period', type: 'select', options: ['daily', 'weekly', 'monthly'], default: 'weekly' }
      ]
    },

    // System commands (Enhanced)
    {
      id: 'system-status',
      title: 'System Status',
      description: 'Check comprehensive system health',
      category: 'system',
      agent: 'pulse',
      keywords: ['status', 'health', 'system', 'pulse', 'monitor', 'check'],
      action: () => console.log('Checking system status'),
      icon: '💓',
      shortcut: 'Ctrl+S'
    },
    {
      id: 'overseer-verify',
      title: 'Overseer: Verify Audit',
      description: 'Verify audit chain integrity',
      category: 'system',
      agent: 'pulse',
      keywords: ['overseer', 'audit', 'verify', 'security', 'integrity'],
      action: () => console.log('Verifying audit chain'),
      icon: '🔒'
    },
    {
      id: 'chaos-scenario',
      title: 'Chaos: Run Scenario',
      description: 'Execute chaos testing scenario',
      category: 'system',
      agent: 'pulse',
      keywords: ['chaos', 'test', 'scenario', 'fault', 'resilience'],
      action: () => console.log('Running chaos scenario'),
      icon: '⚡',
      params: [
        { name: 'scenario', type: 'select', options: ['service-kill', 'network-partition', 'high-latency'], required: true }
      ]
    },

    // Navigation commands (Enhanced)
    {
      id: 'open-enhanced-chat',
      title: 'Open Enhanced Chat',
      description: 'Open Atlas enhanced chat with voice and citations',
      category: 'navigation',
      agent: 'atlas',
      keywords: ['chat', 'atlas', 'communication', 'panel', 'enhanced'],
      action: () => console.log('Opening enhanced chat'),
      icon: '💬',
      shortcut: 'Ctrl+T'
    },
    {
      id: 'toggle-status-banner',
      title: 'Toggle Status Banner',
      description: 'Show/hide system status banner',
      category: 'navigation',
      agent: 'atlas',
      keywords: ['status', 'banner', 'toggle', 'display', 'mode'],
      action: () => console.log('Toggling status banner'),
      icon: '📊'
    },
    {
      id: 'open-task-drawer',
      title: 'Open Task Drawer',
      description: 'View task progress with logs and controls',
      category: 'navigation',
      agent: 'atlas',
      keywords: ['task', 'drawer', 'progress', 'logs', 'jobs'],
      action: () => console.log('Opening task drawer'),
      icon: '📋',
      shortcut: 'Ctrl+J'
    }
  ];

  // Combine default and custom commands
  const allCommands = useMemo(() => {
    return [...defaultCommands, ...customCommands].filter(cmd => cmd.enabled !== false);
  }, [customCommands]);

  // Filter commands based on query
  const filteredCommands = useMemo(() => {
    if (!query.trim()) {
      // Show recent commands first, then all commands
      const recent = allCommands.filter(cmd => recentCommands.includes(cmd.id));
      const others = allCommands.filter(cmd => !recentCommands.includes(cmd.id));
      return [...recent, ...others];
    }

    const lowerQuery = query.toLowerCase();
    return allCommands
      .filter(cmd => 
        cmd.title.toLowerCase().includes(lowerQuery) ||
        cmd.description.toLowerCase().includes(lowerQuery) ||
        cmd.keywords.some(keyword => keyword.toLowerCase().includes(lowerQuery)) ||
        cmd.agent.toLowerCase().includes(lowerQuery) ||
        cmd.category.toLowerCase().includes(lowerQuery)
      )
      .sort((a, b) => {
        // Prioritize exact matches in title
        const aExactTitle = a.title.toLowerCase() === lowerQuery;
        const bExactTitle = b.title.toLowerCase() === lowerQuery;
        if (aExactTitle && !bExactTitle) return -1;
        if (!aExactTitle && bExactTitle) return 1;
        
        // Then title startsWith matches
        const aTitleStarts = a.title.toLowerCase().startsWith(lowerQuery);
        const bTitleStarts = b.title.toLowerCase().startsWith(lowerQuery);
        if (aTitleStarts && !bTitleStarts) return -1;
        if (!aTitleStarts && bTitleStarts) return 1;
        
        // Then keyword matches
        const aKeywordExact = a.keywords.some(k => k.toLowerCase() === lowerQuery);
        const bKeywordExact = b.keywords.some(k => k.toLowerCase() === lowerQuery);
        if (aKeywordExact && !bKeywordExact) return -1;
        if (!aKeywordExact && bKeywordExact) return 1;
        
        // Finally by relevance score
        const getRelevance = (cmd: Command) => {
          let score = 0;
          if (cmd.title.toLowerCase().includes(lowerQuery)) score += 3;
          if (cmd.description.toLowerCase().includes(lowerQuery)) score += 2;
          if (cmd.keywords.some(k => k.toLowerCase().includes(lowerQuery))) score += 1;
          return score;
        };
        
        return getRelevance(b) - getRelevance(a);
      });
  }, [query, allCommands, recentCommands]);

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
            handleCommandSelect(filteredCommands[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          if (showParameters) {
            setShowParameters(false);
            setSelectedCommand(null);
            setParameterValues({});
          } else {
            onClose();
          }
          break;
        case 'Tab':
          e.preventDefault();
          if (filteredCommands[selectedIndex]?.params?.length) {
            handleCommandSelect(filteredCommands[selectedIndex]);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isVisible, selectedIndex, filteredCommands, showParameters, onClose]);

  // Reset state when opened
  useEffect(() => {
    if (isVisible) {
      setQuery('');
      setSelectedIndex(0);
      setShowParameters(false);
      setSelectedCommand(null);
      setParameterValues({});
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isVisible]);

  // Update selected index when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Handle command selection
  const handleCommandSelect = (command: Command) => {
    if (command.params?.length && !showParameters) {
      // Show parameter form
      setSelectedCommand(command);
      setShowParameters(true);
      
      // Initialize parameter values with defaults
      const initialValues: Record<string, any> = {};
      command.params.forEach(param => {
        if (param.default !== undefined) {
          initialValues[param.name] = param.default;
        }
      });
      setParameterValues(initialValues);
    } else {
      // Execute command directly
      executeCommand(command);
    }
  };

  // Execute command
  const executeCommand = async (command: Command, params?: Record<string, any>) => {
    try {
      if (params) {
        // Command with parameters - could pass params to action
        console.log('Executing command with params:', command.id, params);
      }
      
      await command.action();
      
      // Add to recent commands
      setRecentCommands(prev => {
        const updated = [command.id, ...prev.filter(id => id !== command.id)];
        return updated.slice(0, 8); // Keep only 8 recent
      });
      
      if (onExecute) {
        onExecute(command);
      }
      
      onClose();
    } catch (error) {
      console.error('Command execution failed:', error);
    }
  };

  // Handle parameter form submission
  const handleParameterSubmit = () => {
    if (!selectedCommand) return;
    
    // Validate required parameters
    const missing = selectedCommand.params?.filter(param => 
      param.required && !parameterValues[param.name]
    );
    
    if (missing?.length) {
      console.error('Missing required parameters:', missing.map(p => p.name));
      return;
    }
    
    executeCommand(selectedCommand, parameterValues);
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
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(8px)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'center',
          paddingTop: '15vh'
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={() => {
          if (showParameters) {
            setShowParameters(false);
            setSelectedCommand(null);
          } else {
            onClose();
          }
        }}
      >
        <motion.div
          style={{
            width: showParameters ? '700px' : '650px',
            maxWidth: '90vw',
            maxHeight: '70vh',
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: '16px',
            border: '1px solid rgba(75, 85, 99, 0.3)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 25px 50px rgba(0, 0, 0, 0.4)'
          }}
          initial={{ opacity: 0, scale: 0.95, y: -30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -30 }}
          onClick={(e) => e.stopPropagation()}
          layout
        >
          {!showParameters ? (
            <>
              {/* Search Input */}
              <div style={{ padding: '24px 24px 16px' }}>
                <div style={{ position: 'relative' }}>
                  <motion.span 
                    style={{
                      position: 'absolute',
                      left: '16px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      fontSize: '18px',
                      color: '#9CA3AF'
                    }}
                    animate={{ rotate: query ? 0 : [0, 10, 0] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  >
                    ⚡
                  </motion.span>
                  <input
                    ref={inputRef}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search enhanced commands... (try 'vault search', 'rig template', 'chaos test')"
                    style={{
                      width: '100%',
                      padding: '16px 16px 16px 48px',
                      backgroundColor: 'rgba(55, 65, 81, 0.8)',
                      border: '2px solid rgba(75, 85, 99, 0.3)',
                      borderRadius: '12px',
                      color: 'white',
                      fontSize: '16px',
                      outline: 'none',
                      transition: 'border-color 0.2s'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = 'rgba(59, 130, 246, 0.6)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = 'rgba(75, 85, 99, 0.3)';
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
                    padding: '60px 24px',
                    textAlign: 'center',
                    color: '#9CA3AF'
                  }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                    <div style={{ fontSize: '16px', marginBottom: '8px' }}>No commands found</div>
                    <div style={{ fontSize: '14px' }}>Try "vault", "rig", "craft", or "research"</div>
                  </div>
                ) : (
                  Object.entries(groupedCommands).map(([category, commands]) => (
                    <div key={category} style={{ marginBottom: '8px' }}>
                      {/* Category Header */}
                      <div style={{
                        padding: '12px 24px 8px',
                        fontSize: '12px',
                        fontWeight: '700',
                        color: commandCategories[category as keyof typeof commandCategories].color,
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <span>{commandCategories[category as keyof typeof commandCategories].icon}</span>
                        {commandCategories[category as keyof typeof commandCategories].name}
                        <span style={{ 
                          color: '#6B7280', 
                          fontWeight: '400',
                          fontSize: '11px' 
                        }}>
                          ({commands.length})
                        </span>
                      </div>

                      {/* Commands */}
                      {commands.map((command, index) => {
                        const globalIndex = filteredCommands.indexOf(command);
                        const isSelected = globalIndex === selectedIndex;
                        const agentConf = agentConfig[command.agent];
                        const categoryConf = commandCategories[command.category];

                        return (
                          <motion.div
                            key={command.id}
                            style={{
                              padding: '16px 24px',
                              backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                              borderLeft: isSelected ? '4px solid #3B82F6' : '4px solid transparent',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '16px',
                              transition: 'all 0.2s'
                            }}
                            whileHover={{ 
                              backgroundColor: 'rgba(55, 65, 81, 0.4)',
                              scale: 1.01
                            }}
                            onClick={() => handleCommandSelect(command)}
                          >
                            <motion.span 
                              style={{ fontSize: '24px' }}
                              animate={{ 
                                rotate: isSelected ? [0, 10, 0] : 0,
                                scale: isSelected ? 1.1 : 1
                              }}
                              transition={{ duration: 0.3 }}
                            >
                              {command.icon}
                            </motion.span>
                            
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{
                                color: 'white',
                                fontSize: '15px',
                                fontWeight: '600',
                                marginBottom: '4px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                              }}>
                                {command.title}
                                {command.params?.length && (
                                  <span style={{
                                    fontSize: '10px',
                                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                                    color: '#93C5FD',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    fontWeight: '500'
                                  }}>
                                    {command.params.length} params
                                  </span>
                                )}
                              </div>
                              <div style={{
                                color: '#9CA3AF',
                                fontSize: '13px',
                                marginBottom: '8px',
                                lineHeight: '1.4'
                              }}>
                                {command.description}
                              </div>
                              <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                fontSize: '11px'
                              }}>
                                <div style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                  color: agentConf.color
                                }}>
                                  <span>{agentConf.icon}</span>
                                  <span style={{ fontWeight: '500' }}>{command.agent}</span>
                                </div>
                                
                                <div style={{ color: '#6B7280' }}>•</div>
                                
                                <div style={{
                                  color: categoryConf.color,
                                  fontWeight: '500'
                                }}>
                                  {categoryConf.name}
                                </div>
                              </div>
                            </div>

                            <div style={{
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'flex-end',
                              gap: '4px'
                            }}>
                              {command.shortcut && (
                                <div style={{
                                  padding: '4px 8px',
                                  backgroundColor: 'rgba(75, 85, 99, 0.4)',
                                  borderRadius: '6px',
                                  fontSize: '11px',
                                  color: '#D1D5DB',
                                  fontFamily: 'monospace',
                                  fontWeight: '500'
                                }}>
                                  {command.shortcut}
                                </div>
                              )}
                              
                              {command.params?.length && (
                                <div style={{
                                  fontSize: '10px',
                                  color: '#6B7280'
                                }}>
                                  Tab for params
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
                padding: '16px 24px',
                borderTop: '1px solid rgba(75, 85, 99, 0.3)',
                backgroundColor: 'rgba(55, 65, 81, 0.3)',
                fontSize: '12px',
                color: '#9CA3AF',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <span>↑↓ Navigate</span>
                  <span>Enter Execute</span>
                  <span>Tab Params</span>
                  <span>Esc Close</span>
                </div>
                <span>{filteredCommands.length} commands</span>
              </div>
            </>
          ) : (
            /* Parameter Form */
            selectedCommand && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                style={{ padding: '24px' }}
              >
                <div style={{ marginBottom: '24px' }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    marginBottom: '8px'
                  }}>
                    <span style={{ fontSize: '24px' }}>{selectedCommand.icon}</span>
                    <h2 style={{
                      color: 'white',
                      fontSize: '20px',
                      fontWeight: '600',
                      margin: 0
                    }}>
                      {selectedCommand.title}
                    </h2>
                  </div>
                  <p style={{
                    color: '#9CA3AF',
                    fontSize: '14px',
                    margin: '0 0 0 36px'
                  }}>
                    {selectedCommand.description}
                  </p>
                </div>

                <div style={{ marginBottom: '24px' }}>
                  {selectedCommand.params?.map((param, index) => (
                    <div key={param.name} style={{ marginBottom: '16px' }}>
                      <label style={{
                        display: 'block',
                        color: 'white',
                        fontSize: '14px',
                        fontWeight: '500',
                        marginBottom: '6px'
                      }}>
                        {param.name}
                        {param.required && (
                          <span style={{ color: '#EF4444', marginLeft: '4px' }}>*</span>
                        )}
                      </label>
                      
                      {param.type === 'select' ? (
                        <select
                          value={parameterValues[param.name] || ''}
                          onChange={(e) => setParameterValues(prev => ({
                            ...prev,
                            [param.name]: e.target.value
                          }))}
                          style={{
                            width: '100%',
                            padding: '12px',
                            backgroundColor: 'rgba(55, 65, 81, 0.8)',
                            border: '1px solid rgba(75, 85, 99, 0.5)',
                            borderRadius: '8px',
                            color: 'white',
                            fontSize: '14px'
                          }}
                        >
                          <option value="">Select {param.name}...</option>
                          {param.options?.map(option => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      ) : param.type === 'boolean' ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <input
                            type="checkbox"
                            checked={parameterValues[param.name] || false}
                            onChange={(e) => setParameterValues(prev => ({
                              ...prev,
                              [param.name]: e.target.checked
                            }))}
                            style={{ transform: 'scale(1.2)' }}
                          />
                          <span style={{ color: '#D1D5DB', fontSize: '14px' }}>
                            Enable {param.name}
                          </span>
                        </div>
                      ) : (
                        <input
                          type={param.type === 'number' ? 'number' : 'text'}
                          value={parameterValues[param.name] || ''}
                          onChange={(e) => setParameterValues(prev => ({
                            ...prev,
                            [param.name]: param.type === 'number' ? 
                              parseFloat(e.target.value) || 0 : e.target.value
                          }))}
                          placeholder={`Enter ${param.name}...`}
                          style={{
                            width: '100%',
                            padding: '12px',
                            backgroundColor: 'rgba(55, 65, 81, 0.8)',
                            border: '1px solid rgba(75, 85, 99, 0.5)',
                            borderRadius: '8px',
                            color: 'white',
                            fontSize: '14px'
                          }}
                        />
                      )}
                    </div>
                  ))}
                </div>

                <div style={{
                  display: 'flex',
                  gap: '12px',
                  justifyContent: 'flex-end'
                }}>
                  <motion.button
                    onClick={() => {
                      setShowParameters(false);
                      setSelectedCommand(null);
                      setParameterValues({});
                    }}
                    style={{
                      padding: '12px 20px',
                      backgroundColor: 'transparent',
                      border: '1px solid rgba(75, 85, 99, 0.5)',
                      borderRadius: '8px',
                      color: '#9CA3AF',
                      fontSize: '14px',
                      cursor: 'pointer'
                    }}
                    whileHover={{ backgroundColor: 'rgba(75, 85, 99, 0.2)' }}
                  >
                    Cancel
                  </motion.button>
                  
                  <motion.button
                    onClick={handleParameterSubmit}
                    style={{
                      padding: '12px 24px',
                      backgroundColor: '#3B82F6',
                      border: 'none',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                    whileHover={{ backgroundColor: '#2563EB', scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Execute Command
                  </motion.button>
                </div>
              </motion.div>
            )
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default EnhancedCommandPalette;