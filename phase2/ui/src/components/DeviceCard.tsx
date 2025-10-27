// ui/src/components/DeviceCard.tsx
import React from 'react'
import { 
  Monitor, 
  Smartphone, 
  Tablet, 
  Wifi, 
  WifiOff, 
  Link, 
  Unlink, 
  Hand,
  Eye,
  Maximize,
  MousePointer,
  Clock,
  Zap
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Device } from '../services/api'

interface DeviceCardProps {
  device: Device
  onLink: () => void
  onUnlink: () => void
  onHandsOn: (enabled: boolean) => void
  isLinking: boolean
  isUnlinking: boolean
}

const DeviceCard: React.FC<DeviceCardProps> = ({
  device,
  onLink,
  onUnlink,
  onHandsOn,
  isLinking,
  isUnlinking
}) => {
  const getDeviceIcon = () => {
    switch (device.type) {
      case 'desktop':
        return <Monitor className="w-6 h-6" />
      case 'mobile':
        return <Smartphone className="w-6 h-6" />
      case 'tablet':
        return <Tablet className="w-6 h-6" />
      default:
        return <Monitor className="w-6 h-6" />
    }
  }

  const getModeIcon = () => {
    switch (device.link_mode) {
      case 'view':
        return <Eye className="w-4 h-4" />
      case 'extend':
        return <Maximize className="w-4 h-4" />
      case 'control':
        return <MousePointer className="w-4 h-4" />
      default:
        return null
    }
  }

  const getModeColor = () => {
    switch (device.link_mode) {
      case 'view':
        return 'bg-green-100 text-green-800'
      case 'extend':
        return 'bg-blue-100 text-blue-800'
      case 'control':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = () => {
    if (device.linked) return 'border-l-rika-blue'
    if (device.status === 'active') return 'border-l-rika-green'
    if (device.status === 'blackout') return 'border-l-rika-red'
    return 'border-l-gray-300'
  }

  const isOnline = device.status === 'active'
  const hasHandsOn = device.gestures_enabled

  return (
    <div className={`card relative border-l-4 ${getStatusColor()} hover:shadow-md transition-shadow`}>
      {/* Linked Watermark */}
      {device.linked && (
        <div className="absolute top-2 right-2 text-xs text-blue-600 opacity-60">
          Linked by Rika at {new Date().toLocaleTimeString()}
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${isOnline ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
            {getDeviceIcon()}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{device.name}</h3>
            <p className="text-sm text-gray-500 capitalize">{device.type}</p>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center space-x-2">
          {isOnline ? (
            <Wifi className="w-4 h-4 text-green-500" />
          ) : (
            <WifiOff className="w-4 h-4 text-gray-400" />
          )}
          
          <span className={
            device.status === 'active' ? 'status-online' :
            device.status === 'blackout' ? 'status-blackout' :
            'status-offline'
          }>
            {device.status}
          </span>
        </div>
      </div>

      {/* Device Info */}
      <div className="space-y-2 mb-4">
        <div className="text-sm">
          <span className="text-gray-500">Last app: </span>
          <span className="font-medium">{device.last_active_app || 'Unknown'}</span>
        </div>
        <div className="text-sm text-gray-500">
          Last seen: {formatDistanceToNow(new Date(device.last_seen), { addSuffix: true })}
        </div>
      </div>

      {/* Link Status */}
      {device.linked && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              {getModeIcon()}
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getModeColor()}`}>
                {device.link_mode} mode
              </span>
              {device.gestures_enabled && (
                <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">
                  <Hand className="w-3 h-3 inline mr-1" />
                  Gestures
                </span>
              )}
            </div>
          </div>
          
          {device.link_expires_at && (
            <div className="text-xs text-gray-600">
              <Clock className="w-3 h-3 inline mr-1" />
              Expires {formatDistanceToNow(new Date(device.link_expires_at), { addSuffix: true })}
            </div>
          )}

          {/* Thumbnail placeholder for view mode */}
          {device.link_mode === 'view' && (
            <div className="mt-3 bg-gray-100 rounded-lg p-4 text-center">
              <div className="w-full h-20 bg-gray-200 rounded flex items-center justify-center">
                <span className="text-xs text-gray-500">Live thumbnail would appear here</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {device.linked ? (
            <>
              <button
                onClick={onUnlink}
                disabled={isUnlinking || !isOnline}
                className="btn-secondary text-sm flex items-center space-x-1 disabled:opacity-50"
              >
                <Unlink className="w-4 h-4" />
                <span>Unlink</span>
              </button>
              
              {device.linked && (
                <button
                  onClick={() => onHandsOn(!hasHandsOn)}
                  disabled={!isOnline}
                  className={`text-sm flex items-center space-x-1 px-3 py-2 rounded-lg font-medium transition-colors ${
                    hasHandsOn 
                      ? 'bg-purple-100 text-purple-800 hover:bg-purple-200' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  } disabled:opacity-50`}
                >
                  <Hand className="w-4 h-4" />
                  <span>{hasHandsOn ? 'Hands On' : 'Hands Off'}</span>
                </button>
              )}
            </>
          ) : (
            <button
              onClick={onLink}
              disabled={isLinking || !isOnline}
              className="btn-primary text-sm flex items-center space-x-1 disabled:opacity-50"
            >
              <Link className="w-4 h-4" />
              <span>Link</span>
            </button>
          )}
        </div>

        {/* Quick Stats */}
        <div className="text-xs text-gray-500">
          ID: {device.device_id.slice(-6)}
        </div>
      </div>
    </div>
  )
}

export default DeviceCard