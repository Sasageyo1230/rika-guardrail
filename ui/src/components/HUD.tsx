// Rika Phase 3.4 HUD Component
import React, { useState } from 'react';

interface HUDProps {
  onChatToggle: () => void;
  isChatOpen: boolean;
}

export const HUD: React.FC<HUDProps> = ({ onChatToggle, isChatOpen }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <>
      {/* Talk to Rika Bubble */}
      <button
        onClick={onChatToggle}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`
          fixed bottom-6 right-6 z-40
          w-16 h-16 rounded-full
          bg-gradient-to-r from-blue-500 to-purple-600
          text-white shadow-lg
          transform transition-all duration-200 ease-out
          hover:scale-110 hover:shadow-xl
          ${isChatOpen ? 'scale-95 opacity-75' : ''}
          ${isHovered ? 'shadow-2xl' : ''}
        `}
        title="Talk to Rika"
      >
        <div className="flex items-center justify-center h-full">
          {isChatOpen ? (
            <span className="text-xl">×</span>
          ) : (
            <span className="text-xl">💬</span>
          )}
        </div>
        
        {/* Pulse Animation */}
        {!isChatOpen && (
          <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 animate-ping opacity-20"></div>
        )}
      </button>
      
      {/* Status Indicator */}
      <div className="fixed bottom-24 right-6 z-40">
        <div className="flex items-center gap-2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span>Rika Online</span>
        </div>
      </div>
    </>
  );
};