import React, { useState, useCallback, useEffect } from 'react';
import Bubble, { BubbleMessage } from './Bubble';

interface BubbleManagerProps {
  maxBubbles?: number;
  defaultDuration?: number;
  spacing?: number;
  edgeMargin?: number;
}

const BubbleManager: React.FC<BubbleManagerProps> = ({
  maxBubbles = 5,
  defaultDuration = 5000,
  spacing = 80,
  edgeMargin = 20
}) => {
  const [bubbles, setBubbles] = useState<BubbleMessage[]>([]);
  const [nextPosition, setNextPosition] = useState(0);

  // Calculate bubble position
  const getBubblePosition = useCallback((index: number) => {
    const x = window.innerWidth - 340 - edgeMargin; // 340px = max bubble width + margin
    const y = edgeMargin + (index * spacing);
    return { x, y };
  }, [spacing, edgeMargin]);

  // Add new bubble
  const addBubble = useCallback((bubble: Omit<BubbleMessage, 'id' | 'timestamp'>) => {
    const newBubble: BubbleMessage = {
      ...bubble,
      id: `bubble_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      duration: bubble.duration ?? defaultDuration
    };

    setBubbles(prev => {
      const updated = [...prev, newBubble];
      // Remove oldest if exceeding max
      if (updated.length > maxBubbles) {
        return updated.slice(-maxBubbles);
      }
      return updated;
    });
  }, [maxBubbles, defaultDuration]);

  // Remove bubble
  const removeBubble = useCallback((id: string) => {
    setBubbles(prev => prev.filter(bubble => bubble.id !== id));
  }, []);

  // Clear all bubbles
  const clearAllBubbles = useCallback(() => {
    setBubbles([]);
  }, []);

  // Expose API to window for external access
  useEffect(() => {
    const rikaHUD = {
      showBubble: addBubble,
      clearBubbles: clearAllBubbles,
      // Convenience methods for each agent
      rig: (message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => 
        addBubble({ agent: 'rig', message, priority, ...options }),
      craft: (message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => 
        addBubble({ agent: 'craft', message, priority, ...options }),
      scout: (message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => 
        addBubble({ agent: 'scout', message, priority, ...options }),
      echo: (message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => 
        addBubble({ agent: 'echo', message, priority, ...options }),
      pulse: (message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => 
        addBubble({ agent: 'pulse', message, priority, ...options })
    };

    // Make available globally
    (window as any).rikaHUD = rikaHUD;

    // Cleanup
    return () => {
      delete (window as any).rikaHUD;
    };
  }, [addBubble, clearAllBubbles]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      // Force re-render to update positions
      setNextPosition(prev => prev + 1);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <>
      {bubbles.map((bubble, index) => (
        <Bubble
          key={bubble.id}
          message={bubble}
          onDismiss={removeBubble}
          position={getBubblePosition(index)}
        />
      ))}
    </>
  );
};

// Hook for using bubble manager in components
export const useBubbleManager = () => {
  const showBubble = useCallback((bubble: Omit<BubbleMessage, 'id' | 'timestamp'>) => {
    if ((window as any).rikaHUD?.showBubble) {
      (window as any).rikaHUD.showBubble(bubble);
    }
  }, []);

  const clearBubbles = useCallback(() => {
    if ((window as any).rikaHUD?.clearBubbles) {
      (window as any).rikaHUD.clearBubbles();
    }
  }, []);

  // Agent-specific methods
  const agents = {
    rig: useCallback((message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => {
      if ((window as any).rikaHUD?.rig) {
        (window as any).rikaHUD.rig(message, priority, options);
      }
    }, []),
    craft: useCallback((message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => {
      if ((window as any).rikaHUD?.craft) {
        (window as any).rikaHUD.craft(message, priority, options);
      }
    }, []),
    scout: useCallback((message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => {
      if ((window as any).rikaHUD?.scout) {
        (window as any).rikaHUD.scout(message, priority, options);
      }
    }, []),
    echo: useCallback((message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => {
      if ((window as any).rikaHUD?.echo) {
        (window as any).rikaHUD.echo(message, priority, options);
      }
    }, []),
    pulse: useCallback((message: string, priority: BubbleMessage['priority'] = 'normal', options?: Partial<BubbleMessage>) => {
      if ((window as any).rikaHUD?.pulse) {
        (window as any).rikaHUD.pulse(message, priority, options);
      }
    }, [])
  };

  return {
    showBubble,
    clearBubbles,
    agents
  };
};

export default BubbleManager;