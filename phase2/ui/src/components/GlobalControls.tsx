// ui/src/components/GlobalControls.tsx
import React from 'react'
import { UnlinkAll, Power, AlertTriangle, Zap } from 'lucide-react'

interface GlobalControlsProps {
  linkedCount: number
  onUnlinkAll: () => void
  onBlackout: () => void
  isUnlinkingAll: boolean
  isBlackout: boolean
}

const GlobalControls: React.FC<GlobalControlsProps> = ({
  linkedCount,
  onUnlinkAll,
  onBlackout,
  isUnlinkingAll,
  isBlackout
}) => {
  return (
    <div className="card">
      <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
        <Zap className="w-5 h-5 mr-2 text-rika-orange" />
        Global Controls
      </h3>
      
      <div className="space-y-3">
        {/* Unlink All Button */}
        <button
          onClick={onUnlinkAll}
          disabled={isUnlinkingAll || linkedCount === 0}
          className="w-full btn-secondary flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          {isUnlinkingAll ? (
            <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <UnlinkAll className="w-4 h-4" />
          )}
          <span>Unlink All Devices</span>
        </button>
        
        {linkedCount > 0 && (
          <p className="text-xs text-gray-500 text-center">
            Will unlink {linkedCount} device{linkedCount !== 1 ? 's' : ''}
          </p>
        )}

        {/* Blackout Button */}
        <div className="pt-3 border-t border-gray-200">
          <button
            onClick={onBlackout}
            disabled={isBlackout}
            className="w-full btn-danger flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {isBlackout ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Power className="w-4 h-4" />
            )}
            <span>🚨 EMERGENCY BLACKOUT</span>
          </button>
          
          <div className="mt-2 p-3 bg-red-50 rounded-lg">
            <div className="flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-red-700">
                <p className="font-medium mb-1">Warning:</p>
                <p>This will immediately shut down all Rika agents and revoke all sessions.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GlobalControls