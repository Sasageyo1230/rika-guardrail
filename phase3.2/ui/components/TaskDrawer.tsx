import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number; // 0-100
  agent: 'rig' | 'craft' | 'scout' | 'echo' | 'pulse' | 'atlas';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  created_at: Date;
  updated_at: Date;
  estimated_duration?: number; // seconds
  actual_duration?: number; // seconds
  subtasks?: Task[];
  metadata?: {
    workflow_id?: string;
    execution_id?: string;
    error_message?: string;
    logs?: string[];
  };
}

interface TaskDrawerProps {
  isVisible: boolean;
  onToggle: () => void;
  position?: 'left' | 'right';
  width?: number;
}

const agentConfig = {
  rig: { color: '#2E8B57', icon: '🔧', name: 'Rig' },
  craft: { color: '#4169E1', icon: '⚡', name: 'Craft' },
  scout: { color: '#FF6347', icon: '🔍', name: 'Scout' },
  echo: { color: '#32CD32', icon: '📡', name: 'Echo' },
  pulse: { color: '#9370DB', icon: '💓', name: 'Pulse' },
  atlas: { color: '#FFD700', icon: '🧠', name: 'Atlas' }
};

const statusConfig = {
  pending: { color: '#6B7280', icon: '⏳', label: 'Pending' },
  in_progress: { color: '#3B82F6', icon: '⚡', label: 'In Progress' },
  completed: { color: '#10B981', icon: '✅', label: 'Completed' },
  failed: { color: '#EF4444', icon: '❌', label: 'Failed' }
};

const priorityConfig = {
  low: { color: '#6B7280', weight: 1 },
  normal: { color: '#3B82F6', weight: 2 },
  high: { color: '#F59E0B', weight: 3 },
  urgent: { color: '#EF4444', weight: 4 }
};

const TaskDrawer: React.FC<TaskDrawerProps> = ({
  isVisible,
  onToggle,
  position = 'right',
  width = 400
}) => {
  const [tasks, setTasks] = useState<Task[]>([
    {
      id: 'task_1',
      title: 'Device Controller Setup',
      description: 'Initialize smart device automation system',
      status: 'completed',
      progress: 100,
      agent: 'rig',
      priority: 'high',
      created_at: new Date(Date.now() - 300000),
      updated_at: new Date(Date.now() - 60000),
      estimated_duration: 120,
      actual_duration: 95
    },
    {
      id: 'task_2', 
      title: 'Code Deployment Pipeline',
      description: 'Deploy latest changes to production',
      status: 'in_progress',
      progress: 65,
      agent: 'craft',
      priority: 'urgent',
      created_at: new Date(Date.now() - 180000),
      updated_at: new Date(),
      estimated_duration: 300
    },
    {
      id: 'task_3',
      title: 'Market Research Analysis',
      description: 'Research AI automation trends Q1 2025',
      status: 'in_progress',
      progress: 30,
      agent: 'scout',
      priority: 'normal',
      created_at: new Date(Date.now() - 120000),
      updated_at: new Date(Date.now() - 30000),
      estimated_duration: 600
    },
    {
      id: 'task_4',
      title: 'System Health Check',
      description: 'Monitor all services and performance metrics',
      status: 'pending',
      progress: 0,
      agent: 'pulse',
      priority: 'normal',
      created_at: new Date(),
      updated_at: new Date()
    }
  ]);

  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');
  const [sortBy, setSortBy] = useState<'created' | 'priority' | 'status'>('priority');

  // Filter and sort tasks
  const filteredTasks = tasks
    .filter(task => {
      switch (filter) {
        case 'active': return task.status === 'in_progress' || task.status === 'pending';
        case 'completed': return task.status === 'completed';
        default: return true;
      }
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          return priorityConfig[b.priority].weight - priorityConfig[a.priority].weight;
        case 'status':
          const statusOrder = { in_progress: 3, pending: 2, failed: 1, completed: 0 };
          return statusOrder[b.status] - statusOrder[a.status];
        case 'created':
          return b.created_at.getTime() - a.created_at.getTime();
        default:
          return 0;
      }
    });

  // Simulate task updates
  useEffect(() => {
    const interval = setInterval(() => {
      setTasks(prev => prev.map(task => {
        if (task.status === 'in_progress') {
          const newProgress = Math.min(100, task.progress + Math.random() * 5);
          const newStatus = newProgress >= 100 ? 'completed' : 'in_progress';
          
          return {
            ...task,
            progress: newProgress,
            status: newStatus,
            updated_at: new Date(),
            actual_duration: newStatus === 'completed' ? 
              Math.floor((Date.now() - task.created_at.getTime()) / 1000) : 
              task.actual_duration
          };
        }
        return task;
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimeElapsed = (task: Task) => {
    const elapsed = Math.floor((Date.now() - task.created_at.getTime()) / 1000);
    return formatDuration(elapsed);
  };

  const drawerStyles = {
    position: 'fixed' as const,
    top: '0',
    bottom: '0',
    [position]: '0',
    width: `${width}px`,
    backgroundColor: 'rgba(17, 24, 39, 0.95)',
    backdropFilter: 'blur(16px)',
    borderLeft: position === 'right' ? '1px solid rgba(75, 85, 99, 0.3)' : 'none',
    borderRight: position === 'left' ? '1px solid rgba(75, 85, 99, 0.3)' : 'none',
    zIndex: 1500,
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden'
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          style={drawerStyles}
          initial={{ x: position === 'right' ? width : -width }}
          animate={{ x: 0 }}
          exit={{ x: position === 'right' ? width : -width }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          {/* Header */}
          <div style={{
            padding: '20px',
            borderBottom: '1px solid rgba(75, 85, 99, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>📋</span>
              <div>
                <h2 style={{ 
                  color: 'white', 
                  fontSize: '18px', 
                  fontWeight: '600', 
                  margin: 0 
                }}>
                  Task Manager
                </h2>
                <p style={{
                  color: '#9CA3AF',
                  fontSize: '12px',
                  margin: '2px 0 0'
                }}>
                  {filteredTasks.filter(t => t.status === 'in_progress').length} active • {filteredTasks.filter(t => t.status === 'completed').length} completed
                </p>
              </div>
            </div>
            
            <button
              onClick={onToggle}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                fontSize: '20px',
                cursor: 'pointer',
                opacity: 0.7
              }}
            >
              ✕
            </button>
          </div>

          {/* Filters */}
          <div style={{
            padding: '16px 20px',
            borderBottom: '1px solid rgba(75, 85, 99, 0.3)',
            display: 'flex',
            gap: '12px',
            alignItems: 'center'
          }}>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              style={{
                backgroundColor: 'rgba(55, 65, 81, 0.8)',
                border: '1px solid rgba(75, 85, 99, 0.5)',
                borderRadius: '6px',
                color: 'white',
                fontSize: '12px',
                padding: '4px 8px'
              }}
            >
              <option value="all">All Tasks</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              style={{
                backgroundColor: 'rgba(55, 65, 81, 0.8)',
                border: '1px solid rgba(75, 85, 99, 0.5)',
                borderRadius: '6px',
                color: 'white',
                fontSize: '12px',
                padding: '4px 8px'
              }}
            >
              <option value="priority">Priority</option>
              <option value="status">Status</option>
              <option value="created">Created</option>
            </select>
          </div>

          {/* Task List */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '8px 0'
          }}>
            {filteredTasks.map((task) => {
              const agentConf = agentConfig[task.agent];
              const statusConf = statusConfig[task.status];
              
              return (
                <motion.div
                  key={task.id}
                  style={{
                    padding: '16px 20px',
                    borderBottom: '1px solid rgba(75, 85, 99, 0.2)',
                    cursor: 'pointer'
                  }}
                  whileHover={{ backgroundColor: 'rgba(55, 65, 81, 0.3)' }}
                  layout
                >
                  {/* Task Header */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    marginBottom: '8px'
                  }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{
                        color: 'white',
                        fontSize: '14px',
                        fontWeight: '500',
                        margin: '0 0 4px',
                        lineHeight: '1.2'
                      }}>
                        {task.title}
                      </h3>
                      {task.description && (
                        <p style={{
                          color: '#9CA3AF',
                          fontSize: '12px',
                          margin: 0,
                          lineHeight: '1.3'
                        }}>
                          {task.description}
                        </p>
                      )}
                    </div>

                    <div style={{
                      padding: '2px 8px',
                      backgroundColor: `${priorityConfig[task.priority].color}20`,
                      border: `1px solid ${priorityConfig[task.priority].color}40`,
                      borderRadius: '12px',
                      fontSize: '10px',
                      color: priorityConfig[task.priority].color,
                      textTransform: 'uppercase',
                      fontWeight: '600',
                      marginLeft: '8px'
                    }}>
                      {task.priority}
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {task.status !== 'pending' && (
                    <div style={{
                      marginBottom: '8px',
                      backgroundColor: 'rgba(75, 85, 99, 0.3)',
                      borderRadius: '6px',
                      height: '4px',
                      overflow: 'hidden'
                    }}>
                      <motion.div
                        style={{
                          height: '100%',
                          backgroundColor: statusConf.color,
                          borderRadius: '6px'
                        }}
                        initial={{ width: 0 }}
                        animate={{ width: `${task.progress}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  )}

                  {/* Task Footer */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '11px'
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        color: agentConf.color
                      }}>
                        <span>{agentConf.icon}</span>
                        <span>{agentConf.name}</span>
                      </div>
                      
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        color: statusConf.color
                      }}>
                        <span>{statusConf.icon}</span>
                        <span>{statusConf.label}</span>
                      </div>
                    </div>

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      color: '#9CA3AF'
                    }}>
                      {task.status === 'in_progress' && (
                        <span>⏱️ {getTimeElapsed(task)}</span>
                      )}
                      {task.actual_duration && (
                        <span>✓ {formatDuration(task.actual_duration)}</span>
                      )}
                      {task.progress > 0 && task.progress < 100 && (
                        <span>{task.progress.toFixed(0)}%</span>
                      )}
                    </div>
                  </div>

                  {/* Error Message */}
                  {task.status === 'failed' && task.metadata?.error_message && (
                    <div style={{
                      marginTop: '8px',
                      padding: '8px',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.2)',
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: '#FCA5A5'
                    }}>
                      Error: {task.metadata.error_message}
                    </div>
                  )}
                </motion.div>
              );
            })}

            {filteredTasks.length === 0 && (
              <div style={{
                padding: '40px 20px',
                textAlign: 'center',
                color: '#9CA3AF'
              }}>
                <span style={{ fontSize: '48px', display: 'block', marginBottom: '12px' }}>📭</span>
                <p style={{ margin: 0, fontSize: '14px' }}>
                  No {filter !== 'all' ? filter : ''} tasks found
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div style={{
            padding: '16px 20px',
            borderTop: '1px solid rgba(75, 85, 99, 0.3)',
            backgroundColor: 'rgba(55, 65, 81, 0.3)'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '12px',
              color: '#9CA3AF'
            }}>
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
              <span>{filteredTasks.length} tasks</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default TaskDrawer;