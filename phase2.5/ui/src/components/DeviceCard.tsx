// ui/src/components/DeviceCard.tsx - Phase 2.5
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
  Zap,
  Play,
  Square,
  Shield,
  ShieldCheck,
  ShieldX,
  Timer
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Device } from '../services/api'

interface DeviceCardProps {
  device: Device
  onLink: () => void
  onUnlink: () => void
  onHandsOn: (enabled: boolean) => void
  onStartStream: () => void
  onStopStream: () => void
  onRequestControl: () => void
  onRevokeControl: () => void
  isLinking: boolean
  isUnlinking: boolean
  isStreamActive: boolean
}

const DeviceCard: React.FC<DeviceCardProps> = ({
  device,
  onLink,
  onUnlink,
  onHandsOn,
  onStartStream,
  onStopStream,
  onRequestControl,
  onRevokeControl,
  isLinking,
  isUnlinking,
  isStreamActive
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

  const getControlStatusIcon = () => {
    switch (device.control_status) {
      case 'pending':
        return <Timer className="w-4 h-4 text-yellow-600" />
      case 'active':
        return <ShieldCheck className="w-4 h-4 text-green-600" />
      case 'revoked':
        return <ShieldX className="w-4 h-4 text-red-600" />
      default:
        return <Shield className="w-4 h-4 text-gray-400" />
    }
  }

  const getControlStatusColor = () => {
    switch (device.control_status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'revoked':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = () => {
    if (device.control_status === 'active') return 'border-l-red-500'
    if (device.linked && device.link_mode === 'extend' && isStreamActive) return 'border-l-blue-500'
    if (device.linked) return 'border-l-rika-blue'
    if (device.status === 'active') return 'border-l-rika-green'
    if (device.status === 'blackout') return 'border-l-rika-red'
    return 'border-l-gray-300'
  }

  const isOnline = device.status === 'active'
  const hasHandsOn = device.gestures_enabled
  const canStream = device.linked && (device.link_mode === 'view' || device.link_mode === 'extend')
  const canControl = device.linked && device.link_mode === 'control'

  return (
    <div className={`card relative border-l-4 ${getStatusColor()} hover:shadow-md transition-shadow`}>
      {/* Enhanced Status Indicators */}
      <div className="absolute top-2 right-2 flex items-center space-x-1">
        {isStreamActive && (
          <div className="flex items-center space-x-1 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
            <span>LIVE</span>
          </div>
        )}
        {device.control_status === 'active' && (
          <div className="flex items-center space-x-1 text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
            <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
            <span>CONTROL</span>
          </div>
        )}
        {device.linked && (
          <div className="text-xs text-blue-600 opacity-60">
            Linked at {new Date().toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-4 pr-16">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${isOnline ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
            {getDeviceIcon()}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{device.name}</h3>
            <p className="text-sm text-gray-500 capitalize">{device.type}</p>
          </div>
        </div>

        {/* Network Status */}
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
            <div className="text-xs text-gray-600 mb-2">
              <Clock className="w-3 h-3 inline mr-1" />
              Link expires {formatDistanceToNow(new Date(device.link_expires_at), { addSuffix: true })}
            </div>
          )}

          {/* Control Status */}
          {device.link_mode === 'control' && (
            <div className="mb-2">
              <div className="flex items-center space-x-2">
                {getControlStatusIcon()}
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getControlStatusColor()}`}>
                  Control {device.control_status || 'inactive'}
                </span>
              </div>
              
              {device.control_expires_at && device.control_status === 'active' && (
                <div className="text-xs text-gray-600 mt-1">
                  <Timer className="w-3 h-3 inline mr-1" />
                  Control expires {formatDistanceToNow(new Date(device.control_expires_at), { addSuffix: true })}
                </div>
              )}
            </div>
          )}

          {/* Stream Preview */}
          {canStream && (
            <div className="mt-3 bg-gray-100 rounded-lg p-4">
              {isStreamActive ? (
                <div className="text-center">
                  <div className="w-full h-20 bg-blue-200 rounded flex items-center justify-center mb-2">
                    <Play className="w-8 h-8 text-blue-600" />
                  </div>
                  <div className="text-xs text-blue-600 font-medium">Live Stream Active</div>
                  <div className="text-xs text-gray-500">Click "View Stream" to watch</div>
                </div>
              ) : (
                <div className="text-center">
                  <div className="w-full h-20 bg-gray-200 rounded flex items-center justify-center mb-2">
                    <Square className="w-6 h-6 text-gray-400" />
                  </div>
                  <div className="text-xs text-gray-500">Stream inactive</div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="space-y-2">
        {/* Primary Actions */}
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

          {/* Device ID */}
          <div className="text-xs text-gray-500">
            ID: {device.device_id.slice(-6)}
          </div>
        </div>

        {/* Phase 2.5: Streaming Actions */}
        {canStream && (
          <div className="flex items-center space-x-2 pt-2 border-t border-gray-200">
            {isStreamActive ? (
              <button
                onClick={onStopStream}
                className="flex-1 bg-red-100 hover:bg-red-200 text-red-800 text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center space-x-1"
              >
                <Square className="w-4 h-4" />
                <span>Stop Stream</span>
              </button>
            ) : (
              <button
                onClick={onStartStream}
                disabled={!isOnline}
                className="flex-1 bg-blue-100 hover:bg-blue-200 text-blue-800 text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center space-x-1 disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                <span>Start Stream</span>
              </button>
            )}
            
            <button className="bg-blue-100 hover:bg-blue-200 text-blue-800 text-sm font-medium py-2 px-3 rounded-lg flex items-center space-x-1">
              <Eye className="w-4 h-4" />
              <span>View</span>
            </button>
          </div>
        )}

        {/* Phase 2.5: Control Actions */}
        {canControl && (
          <div className="flex items-center space-x-2 pt-2 border-t border-gray-200">
            {device.control_status === 'active' ? (
              <button
                onClick={onRevokeControl}
                className="flex-1 bg-red-100 hover:bg-red-200 text-red-800 text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center space-x-1"
              >
                <ShieldX className="w-4 h-4" />
                <span>Revoke Control</span>
              </button>
            ) : device.control_status === 'pending' ? (
              <div className="flex-1 bg-yellow-100 text-yellow-800 text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center space-x-1">
                <Timer className="w-4 h-4 animate-spin" />
                <span>Approval Pending...</span>
              </div>
            ) : (
              <button
                onClick={onRequestControl}
                disabled={!isOnline}
                className="flex-1 bg-purple-100 hover:bg-purple-200 text-purple-800 text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center space-x-1 disabled:opacity-50"
              >
                <MousePointer className="w-4 h-4" />
                <span>Request Control</span>
              </button>
            )}
            
            {device.control_status === 'active' && (
              <button className="bg-purple-100 hover:bg-purple-200 text-purple-800 text-sm font-medium py-2 px-3 rounded-lg flex items-center space-x-1">
                <MousePointer className="w-4 h-4" />
                <span>Control</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default DeviceCard