// ui/src/components/LinkModal.tsx
import React, { useState } from 'react'
import { X, Eye, Maximize, MousePointer, Hand, Clock } from 'lucide-react'

interface LinkModalProps {
  isOpen: boolean
  onClose: () => void
  onLink: (params: { mode: string, ttl_minutes: number, gestures: boolean }) => void
  isLoading: boolean
  deviceName: string
}

const LinkModal: React.FC<LinkModalProps> = ({
  isOpen,
  onClose,
  onLink,
  isLoading,
  deviceName
}) => {
  const [mode, setMode] = useState<'view' | 'extend' | 'control'>('view')
  const [ttlMinutes, setTtlMinutes] = useState(30)
  const [gestures, setGestures] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onLink({
      mode,
      ttl_minutes: ttlMinutes,
      gestures
    })
  }

  if (!isOpen) return null

  const modes = [
    {
      value: 'view' as const,
      label: 'View Mode',
      description: 'Upload thumbnails every 5 seconds',
      icon: <Eye className="w-5 h-5" />,
      color: 'text-green-600'
    },
    {
      value: 'extend' as const,
      label: 'Extend Mode',
      description: 'Full LiveKit streaming (coming soon)',
      icon: <Maximize className="w-5 h-5" />,
      color: 'text-blue-600'
    },
    {
      value: 'control' as const,
      label: 'Control Mode',
      description: 'Allow remote input injection',
      icon: <MousePointer className="w-5 h-5" />,
      color: 'text-purple-600'
    }
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Link Device</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Device Info */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-1">{deviceName}</h3>
            <p className="text-sm text-gray-600">
              Configure linking mode and settings for this device
            </p>
          </div>

          {/* Mode Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Link Mode
            </label>
            <div className="space-y-3">
              {modes.map((modeOption) => (
                <label
                  key={modeOption.value}
                  className={`flex items-start space-x-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                    mode === modeOption.value
                      ? 'border-rika-blue bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="mode"
                    value={modeOption.value}
                    checked={mode === modeOption.value}
                    onChange={(e) => setMode(e.target.value as any)}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className={modeOption.color}>
                        {modeOption.icon}
                      </span>
                      <span className="font-medium text-gray-900">
                        {modeOption.label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {modeOption.description}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* TTL Slider */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              <Clock className="w-4 h-4 inline mr-1" />
              Time to Live: {ttlMinutes} minutes
            </label>
            <input
              type="range"
              min="10"
              max="60"
              step="5"
              value={ttlMinutes}
              onChange={(e) => setTtlMinutes(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>10 min</span>
              <span>60 min</span>
            </div>
          </div>

          {/* Gestures Toggle */}
          <div className="mb-6">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={gestures}
                onChange={(e) => setGestures(e.target.checked)}
                className="w-4 h-4 text-rika-blue border-gray-300 rounded focus:ring-rika-blue"
              />
              <div className="flex items-center space-x-2">
                <Hand className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-gray-700">
                  Enable Gesture Controls
                </span>
              </div>
            </label>
            <p className="text-xs text-gray-500 ml-7">
              Allow hands-on gesture commands (grab, throw, swipe)
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary flex items-center space-x-2"
            >
              {isLoading && (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              )}
              <span>Link Device</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default LinkModal