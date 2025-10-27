// Rika Phase 3.4 Main App Component
import React, { useState, useEffect } from 'react';
import { HUD } from './components/HUD';
import { ChatPanel } from './components/ChatPanel';
import { DesignMode } from './components/DesignMode';
import { chatService } from './services/chat';
import './App.css';

const App: React.FC = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isDesignModeOpen, setIsDesignModeOpen] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);

  useEffect(() => {
    checkServerHealth();
    const interval = setInterval(checkServerHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkServerHealth = async () => {
    try {
      await chatService.getHealth();
      setIsOnline(true);
    } catch (error) {
      setIsOnline(false);
      console.warn('Rika server offline:', error);
    }
  };

  const handleChatToggle = () => {
    setIsChatOpen(!isChatOpen);
    if (showWelcome) {
      setShowWelcome(false);
    }
  };

  const handleDesignModeToggle = () => {
    setIsDesignModeOpen(!isDesignModeOpen);
  };

  const handleKeyboardShortcuts = (e: KeyboardEvent) => {
    // Ctrl+K to open chat
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      setIsChatOpen(true);
    }
    // Ctrl+D to open design mode (dev only)
    if (e.ctrlKey && e.key === 'd') {
      e.preventDefault();
      setIsDesignModeOpen(true);
    }
    // Escape to close panels
    if (e.key === 'Escape') {
      setIsChatOpen(false);
      setIsDesignModeOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('keydown', handleKeyboardShortcuts);
    return () => document.removeEventListener('keydown', handleKeyboardShortcuts);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%239C92AC%22%20fill-opacity%3D%220.1%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%222%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')]"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-8">
        {/* Welcome Screen */}
        {showWelcome && (
          <div className="text-center max-w-4xl mx-auto">
            {/* Logo/Title */}
            <div className="mb-8">
              <h1 className="text-6xl font-bold text-white mb-4">
                <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Rika
                </span>
              </h1>
              <p className="text-xl text-gray-300 mb-2">
                AI-Powered Development Assistant
              </p>
              <div className="text-sm text-gray-400 mb-8">
                Phase 3.4 • Atlas UI • Multi-LLM • Streaming • Tools
              </div>
            </div>

            {/* Status */}
            <div className="mb-8">
              <div className={`inline-flex items-center gap-3 px-6 py-3 rounded-full ${
                isOnline 
                  ? 'bg-green-500 bg-opacity-20 border border-green-500 border-opacity-30' 
                  : 'bg-red-500 bg-opacity-20 border border-red-500 border-opacity-30'
              }`}>
                <div className={`w-3 h-3 rounded-full ${
                  isOnline ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                }`}></div>
                <span className={`text-sm font-medium ${
                  isOnline ? 'text-green-300' : 'text-red-300'
                }`}>
                  {isOnline ? 'Rika is Online' : 'Rika is Offline'}
                </span>
              </div>
            </div>

            {/* Features Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <div className="bg-white bg-opacity-5 backdrop-blur-sm border border-white border-opacity-10 rounded-lg p-6">
                <div className="text-3xl mb-3">💬</div>
                <h3 className="text-white font-semibold mb-2">Multi-Agent Chat</h3>
                <p className="text-gray-400 text-sm">Rika, Rig, Craft, and Scout agents for different tasks</p>
              </div>
              
              <div className="bg-white bg-opacity-5 backdrop-blur-sm border border-white border-opacity-10 rounded-lg p-6">
                <div className="text-3xl mb-3">🔄</div>
                <h3 className="text-white font-semibold mb-2">Streaming</h3>
                <p className="text-gray-400 text-sm">Real-time responses with tool execution feedback</p>
              </div>
              
              <div className="bg-white bg-opacity-5 backdrop-blur-sm border border-white border-opacity-10 rounded-lg p-6">
                <div className="text-3xl mb-3">🧠</div>
                <h3 className="text-white font-semibold mb-2">Multi-LLM</h3>
                <p className="text-gray-400 text-sm">Claude, OpenAI, and local model support</p>
              </div>
              
              <div className="bg-white bg-opacity-5 backdrop-blur-sm border border-white border-opacity-10 rounded-lg p-6">
                <div className="text-3xl mb-3">🔧</div>
                <h3 className="text-white font-semibold mb-2">Tool Integration</h3>
                <p className="text-gray-400 text-sm">n8n workflows and system tools</p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
              <button
                onClick={handleChatToggle}
                disabled={!isOnline}
                className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                Start Chatting
              </button>
              
              {true && (
                <button
                  onClick={handleDesignModeToggle}
                  className="px-8 py-3 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-700 transition-all transform hover:scale-105"
                >
                  AI Designer
                </button>
              )}
            </div>

            {/* Keyboard Shortcuts */}
            <div className="text-center text-gray-400 text-sm">
              <div className="mb-2">Keyboard Shortcuts:</div>
              <div className="flex flex-wrap gap-4 justify-center">
                <span><kbd className="px-2 py-1 bg-gray-700 rounded text-xs">Ctrl+K</kbd> Chat</span>
                {true && (
                  <span><kbd className="px-2 py-1 bg-gray-700 rounded text-xs">Ctrl+D</kbd> Design Mode</span>
                )}
                <span><kbd className="px-2 py-1 bg-gray-700 rounded text-xs">Esc</kbd> Close</span>
              </div>
            </div>
          </div>
        )}

        {/* Minimal view when chat is open */}
        {!showWelcome && (
          <div className="absolute top-8 left-8">
            <h1 className="text-2xl font-bold text-white">
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Rika
              </span>
            </h1>
            <div className={`flex items-center gap-2 mt-1 ${
              isOnline ? 'text-green-400' : 'text-red-400'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isOnline ? 'bg-green-400 animate-pulse' : 'bg-red-400'
              }`}></div>
              <span className="text-xs">
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        )}

        {/* Development Mode Toggle */}
        {true && !showWelcome && (
          <button
            onClick={handleDesignModeToggle}
            className="absolute top-8 right-20 w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-full hover:from-purple-600 hover:to-pink-700 transition-all transform hover:scale-110 shadow-lg"
            title="AI Designer (Ctrl+D)"
          >
            🎨
          </button>
        )}
      </div>

      {/* HUD - Talk to Rika bubble */}
      <HUD 
        onChatToggle={handleChatToggle}
        isChatOpen={isChatOpen}
      />

      {/* Chat Panel */}
      <ChatPanel
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />

      {/* Design Mode (Development Only) */}
      {true && (
        <DesignMode
          isOpen={isDesignModeOpen}
          onClose={() => setIsDesignModeOpen(false)}
        />
      )}

      {/* Offline Banner */}
      {!isOnline && (
        <div className="fixed bottom-0 left-0 right-0 bg-red-600 text-white p-3 text-center text-sm z-50">
          <span className="font-medium">⚠ Rika Server Offline</span>
          <span className="ml-2">Check that the backend is running on port 5317</span>
        </div>
      )}
    </div>
  );
};

export default App;