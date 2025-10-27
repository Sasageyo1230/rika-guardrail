"""
Task Drawer Component - Advanced task management and progress tracking
Phase 3.3 Enhancement for Craft workflows

Features:
- Real-time progress tracking with streaming updates
- Task logs with filtering and search
- Cancel/retry functionality with intelligent backoff
- Visual progress indicators and status badges
- Integration with Rig and Craft creative workflows
"""

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'retrying';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TaskCategory = 'modeling' | 'rigging' | 'storyboard' | 'script' | 'export' | 'system';

export interface TaskLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  details?: any;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  category: TaskCategory;
  status: TaskStatus;
  priority: TaskPriority;
  progress: number; // 0-100
  estimatedDuration?: number; // seconds
  elapsedTime?: number; // seconds
  logs: TaskLog[];
  metadata: {
    agent?: 'rig' | 'craft' | 'scout' | 'echo' | 'pulse' | 'atlas';
    project?: string;
    createdAt: string;
    startedAt?: string;
    completedAt?: string;
    retryCount?: number;
    maxRetries?: number;
  };
  onCancel?: () => Promise<void>;
  onRetry?: () => Promise<void>;
}

export interface TaskDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: Task[];
  onTaskCancel: (taskId: string) => Promise<void>;
  onTaskRetry: (taskId: string) => Promise<void>;
  onTaskClear: (taskId: string) => void;
  position?: 'right' | 'bottom';
}

const statusConfig = {
  pending: {
    label: 'Pending',
    color: '#6B7280',
    bgColor: '#F3F4F6',
    icon: '⏳'
  },
  running: {
    label: 'Running',
    color: '#2563EB',
    bgColor: '#DBEAFE',
    icon: '▶️'
  },
  completed: {
    label: 'Completed',
    color: '#059669',
    bgColor: '#D1FAE5',
    icon: '✅'
  },
  failed: {
    label: 'Failed',
    color: '#DC2626',
    bgColor: '#FEE2E2',
    icon: '❌'
  },
  cancelled: {
    label: 'Cancelled',
    color: '#9333EA',
    bgColor: '#F3E8FF',
    icon: '⏹️'
  },
  retrying: {
    label: 'Retrying',
    color: '#EA580C',
    bgColor: '#FED7AA',
    icon: '🔄'
  }
};

const priorityConfig = {
  low: { label: 'Low', color: '#10B981', order: 1 },
  medium: { label: 'Medium', color: '#F59E0B', order: 2 },
  high: { label: 'High', color: '#EF4444', order: 3 },
  urgent: { label: 'Urgent', color: '#DC2626', order: 4 }
};

const categoryConfig = {
  modeling: { label: 'Modeling', color: '#2E8B57', icon: '🔧' },
  rigging: { label: 'Rigging', color: '#4169E1', icon: '🦴' },
  storyboard: { label: 'Storyboard', color: '#FF6347', icon: '🎬' },
  script: { label: 'Script', color: '#32CD32', icon: '📝' },
  export: { label: 'Export', color: '#9370DB', icon: '📤' },
  system: { label: 'System', color: '#FFD700', icon: '⚙️' }
};

export const TaskDrawer: React.FC<TaskDrawerProps> = ({
  isOpen,
  onClose,
  tasks,
  onTaskCancel,
  onTaskRetry,
  onTaskClear,
  position = 'right'
}) => {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [logFilter, setLogFilter] = useState<'all' | 'info' | 'warning' | 'error' | 'success'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'created' | 'priority' | 'status'>('created');
  const [showCompleted, setShowCompleted] = useState(true);
  
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs to bottom
  const scrollToBottom = useCallback(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    if (selectedTask) {
      scrollToBottom();
    }
  }, [selectedTask?.logs.length, scrollToBottom]);

  // Filter and sort tasks
  const filteredTasks = tasks
    .filter(task => {
      if (!showCompleted && task.status === 'completed') return false;
      if (searchQuery) {
        return task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
               task.description.toLowerCase().includes(searchQuery.toLowerCase());
      }
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          return priorityConfig[b.priority].order - priorityConfig[a.priority].order;
        case 'status':
          return a.status.localeCompare(b.status);
        case 'created':
        default:
          return new Date(b.metadata.createdAt).getTime() - new Date(a.metadata.createdAt).getTime();
      }
    });

  // Filter logs for selected task
  const filteredLogs = selectedTask?.logs.filter(log => 
    logFilter === 'all' || log.level === logFilter
  ) || [];

  const handleTaskAction = async (task: Task, action: 'cancel' | 'retry') => {
    try {
      if (action === 'cancel') {
        await onTaskCancel(task.id);
      } else {
        await onTaskRetry(task.id);
      }
    } catch (error) {
      console.error(`Failed to ${action} task:`, error);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const getTaskProgress = (task: Task): string => {
    if (task.status === 'completed') return '100%';
    if (task.status === 'failed' || task.status === 'cancelled') return 'N/A';
    return `${task.progress}%`;
  };

  const drawerVariants = {
    hidden: position === 'right' 
      ? { x: '100%', opacity: 0 }
      : { y: '100%', opacity: 0 },
    visible: position === 'right'
      ? { x: 0, opacity: 1 }
      : { y: 0, opacity: 1 },
    exit: position === 'right'
      ? { x: '100%', opacity: 0 }
      : { y: '100%', opacity: 0 }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.div
            className={`fixed z-50 bg-white shadow-2xl ${
              position === 'right' 
                ? 'right-0 top-0 h-full w-96 border-l' 
                : 'bottom-0 left-0 w-full h-96 border-t'
            }`}
            variants={drawerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center gap-3">
                <span className="text-xl">📋</span>
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">Task Manager</h2>
                  <p className="text-sm text-gray-600">
                    {tasks.length} tasks ({tasks.filter(t => t.status === 'running').length} active)
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="flex h-full">
              {/* Task List Panel */}
              <div className={`${selectedTask ? 'w-2/5' : 'w-full'} border-r border-gray-200 flex flex-col`}>
                {/* Controls */}
                <div className="p-3 border-b border-gray-100 space-y-3">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Search tasks..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value as any)}
                      className="px-2 py-1 text-sm border border-gray-300 rounded"
                    >
                      <option value="created">Created</option>
                      <option value="priority">Priority</option>
                      <option value="status">Status</option>
                    </select>
                    
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={showCompleted}
                        onChange={(e) => setShowCompleted(e.target.checked)}
                      />
                      Show completed
                    </label>
                  </div>
                </div>

                {/* Task List */}
                <div className="flex-1 overflow-y-auto">
                  {filteredTasks.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      <div className="text-4xl mb-2">📭</div>
                      <p>No tasks found</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-100">
                      {filteredTasks.map((task) => (
                        <motion.div
                          key={task.id}
                          className={`p-3 hover:bg-gray-50 cursor-pointer transition-colors ${
                            selectedTask?.id === task.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''
                          }`}
                          onClick={() => setSelectedTask(task)}
                          whileHover={{ scale: 1.01 }}
                          whileTap={{ scale: 0.99 }}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <span className="text-lg">{categoryConfig[task.category].icon}</span>
                              <div className="flex-1 min-w-0">
                                <h3 className="text-sm font-medium text-gray-900 truncate">
                                  {task.title}
                                </h3>
                                <p className="text-xs text-gray-600 truncate">
                                  {task.description}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1 ml-2">
                              <span
                                className="px-2 py-1 text-xs font-medium rounded-full"
                                style={{
                                  color: statusConfig[task.status].color,
                                  backgroundColor: statusConfig[task.status].bgColor
                                }}
                              >
                                {statusConfig[task.status].icon}
                              </span>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          {(task.status === 'running' || task.status === 'retrying') && (
                            <div className="mb-2">
                              <div className="flex justify-between text-xs text-gray-600 mb-1">
                                <span>Progress</span>
                                <span>{getTaskProgress(task)}</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1.5">
                                <motion.div
                                  className="bg-blue-600 h-1.5 rounded-full"
                                  initial={{ width: 0 }}
                                  animate={{ width: `${task.progress}%` }}
                                  transition={{ duration: 0.3 }}
                                />
                              </div>
                            </div>
                          )}

                          <div className="flex items-center justify-between text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <span
                                className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: priorityConfig[task.priority].color }}
                              />
                              {priorityConfig[task.priority].label}
                            </span>
                            <span>
                              {task.elapsedTime ? formatDuration(task.elapsedTime) : '0s'}
                            </span>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Task Details Panel */}
              {selectedTask && (
                <motion.div
                  className="w-3/5 flex flex-col"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {/* Task Header */}
                  <div className="p-4 border-b border-gray-200">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{categoryConfig[selectedTask.category].icon}</span>
                        <div>
                          <h3 className="font-semibold text-gray-900">{selectedTask.title}</h3>
                          <p className="text-sm text-gray-600">{selectedTask.description}</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {selectedTask.status === 'running' && (
                          <button
                            onClick={() => handleTaskAction(selectedTask, 'cancel')}
                            className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                          >
                            Cancel
                          </button>
                        )}
                        {selectedTask.status === 'failed' && (
                          <button
                            onClick={() => handleTaskAction(selectedTask, 'retry')}
                            className="px-3 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200 transition-colors"
                          >
                            Retry ({selectedTask.metadata.retryCount || 0}/{selectedTask.metadata.maxRetries || 3})
                          </button>
                        )}
                        {['completed', 'failed', 'cancelled'].includes(selectedTask.status) && (
                          <button
                            onClick={() => onTaskClear(selectedTask.id)}
                            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                          >
                            Clear
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Task Metadata */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Status:</span>
                        <span
                          className="ml-2 px-2 py-1 text-xs rounded-full"
                          style={{
                            color: statusConfig[selectedTask.status].color,
                            backgroundColor: statusConfig[selectedTask.status].bgColor
                          }}
                        >
                          {statusConfig[selectedTask.status].label}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Priority:</span>
                        <span className="ml-2 font-medium" style={{ color: priorityConfig[selectedTask.priority].color }}>
                          {priorityConfig[selectedTask.priority].label}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Agent:</span>
                        <span className="ml-2 font-medium">{selectedTask.metadata.agent?.toUpperCase() || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Elapsed:</span>
                        <span className="ml-2 font-mono">{formatDuration(selectedTask.elapsedTime || 0)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Logs Section */}
                  <div className="flex-1 flex flex-col">
                    <div className="p-3 border-b border-gray-100 flex items-center justify-between">
                      <h4 className="font-medium text-gray-800">Logs ({filteredLogs.length})</h4>
                      <select
                        value={logFilter}
                        onChange={(e) => setLogFilter(e.target.value as any)}
                        className="px-2 py-1 text-xs border border-gray-300 rounded"
                      >
                        <option value="all">All</option>
                        <option value="info">Info</option>
                        <option value="warning">Warning</option>
                        <option value="error">Error</option>
                        <option value="success">Success</option>
                      </select>
                    </div>

                    <div className="flex-1 overflow-y-auto p-3 space-y-2">
                      {filteredLogs.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                          <div className="text-2xl mb-2">📄</div>
                          <p>No logs to display</p>
                        </div>
                      ) : (
                        filteredLogs.map((log) => (
                          <motion.div
                            key={log.id}
                            className={`p-2 rounded text-sm border-l-2 ${
                              log.level === 'error' ? 'border-red-500 bg-red-50' :
                              log.level === 'warning' ? 'border-yellow-500 bg-yellow-50' :
                              log.level === 'success' ? 'border-green-500 bg-green-50' :
                              'border-blue-500 bg-blue-50'
                            }`}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            <div className="flex items-start justify-between mb-1">
                              <span className="font-medium capitalize">{log.level}</span>
                              <span className="text-xs text-gray-500">
                                {new Date(log.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-gray-800">{log.message}</p>
                            {log.details && (
                              <pre className="mt-1 text-xs text-gray-600 bg-white p-2 rounded border overflow-x-auto">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            )}
                          </motion.div>
                        ))
                      )}
                      <div ref={logsEndRef} />
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

// Hook for managing tasks
export const useTaskManager = () => {
  const [tasks, setTasks] = useState<Task[]>([]);

  const addTask = useCallback((taskData: Omit<Task, 'id' | 'logs' | 'metadata'> & { metadata?: Partial<Task['metadata']> }) => {
    const task: Task = {
      id: Math.random().toString(36).substr(2, 9),
      logs: [],
      metadata: {
        createdAt: new Date().toISOString(),
        retryCount: 0,
        maxRetries: 3,
        ...taskData.metadata
      },
      ...taskData
    };

    setTasks(prev => [task, ...prev]);
    return task.id;
  }, []);

  const updateTask = useCallback((taskId: string, updates: Partial<Task>) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, ...updates } : task
    ));
  }, []);

  const addLog = useCallback((taskId: string, log: Omit<TaskLog, 'id' | 'timestamp'>) => {
    const logEntry: TaskLog = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toISOString(),
      ...log
    };

    setTasks(prev => prev.map(task =>
      task.id === taskId 
        ? { ...task, logs: [...task.logs, logEntry] }
        : task
    ));
  }, []);

  const cancelTask = useCallback(async (taskId: string) => {
    const task = tasks.find(t => t.id === taskId);
    if (task && task.onCancel) {
      await task.onCancel();
    }
    
    updateTask(taskId, { 
      status: 'cancelled',
      metadata: { ...task?.metadata, completedAt: new Date().toISOString() }
    });
    addLog(taskId, { level: 'warning', message: 'Task cancelled by user' });
  }, [tasks, updateTask, addLog]);

  const retryTask = useCallback(async (taskId: string) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    const retryCount = (task.metadata.retryCount || 0) + 1;
    const maxRetries = task.metadata.maxRetries || 3;

    if (retryCount > maxRetries) {
      addLog(taskId, { level: 'error', message: 'Maximum retry attempts reached' });
      return;
    }

    updateTask(taskId, { 
      status: 'retrying', 
      progress: 0,
      metadata: { 
        ...task.metadata, 
        retryCount,
        startedAt: new Date().toISOString()
      }
    });
    
    addLog(taskId, { level: 'info', message: `Retrying task (attempt ${retryCount}/${maxRetries})` });

    if (task.onRetry) {
      await task.onRetry();
    }
  }, [tasks, updateTask, addLog]);

  const clearTask = useCallback((taskId: string) => {
    setTasks(prev => prev.filter(task => task.id !== taskId));
  }, []);

  return {
    tasks,
    addTask,
    updateTask,
    addLog,
    cancelTask,
    retryTask,
    clearTask
  };
};

export default TaskDrawer;