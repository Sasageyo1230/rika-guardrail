// ui/src/components/StatusBanner.tsx
import React from 'react'
import { Link, Monitor, Wifi, AlertCircle } from 'lucide-react'

interface StatusBannerProps {
  linkedCount: number
  onlineCount: number
  totalCount: number
}

const StatusBanner: React.FC<StatusBannerProps> = ({
  linkedCount,
  onlineCount,
  totalCount
}) => {
  const getStatusColor = () => {
    if (linkedCount > 0) return 'bg-blue-50 border-blue-200 text-blue-800'
    if (onlineCount > 0) return 'bg-green-50 border-green-200 text-green-800'
    return 'bg-gray-50 border-gray-200 text-gray-800'
  }

  const getStatusMessage = () => {
    if (linkedCount > 0) {
      return `${linkedCount} device${linkedCount !== 1 ? 's' : ''} actively linked`
    }
    if (onlineCount > 0) {
      return `${onlineCount} device${onlineCount !== 1 ? 's' : ''} online and ready to link`
    }
    return 'No devices online'
  }

  const getStatusIcon = () => {
    if (linkedCount > 0) return <Link className="w-5 h-5" />
    if (onlineCount > 0) return <Wifi className="w-5 h-5" />
    return <AlertCircle className="w-5 h-5" />
  }

  return (
    <div className={`border-b border-t px-4 py-3 ${getStatusColor()}`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <p className="font-medium">{getStatusMessage()}</p>
            <p className="text-sm opacity-75">
              {totalCount} total device{totalCount !== 1 ? 's' : ''} enrolled in Rika ecosystem
            </p>
          </div>
        </div>

        {linkedCount > 0 && (
          <div className="flex items-center space-x-4 text-sm">
            <div className="flex items-center space-x-1">
              <Monitor className="w-4 h-4" />
              <span>Atlas Dashboard Active</span>
            </div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StatusBanner