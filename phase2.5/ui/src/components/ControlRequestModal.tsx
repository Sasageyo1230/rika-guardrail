// ui/src/components/ControlRequestModal.tsx - Phase 2.5
import React, { useState } from 'react'
import { X, Shield, Clock, AlertTriangle, MousePointer } from 'lucide-react'

interface ControlRequestModalProps {
  isOpen: boolean
  onClose: () => void
  onRequest: (params: { ttl_minutes: number, reason: string }) => void
  isLoading: boolean
  deviceName: string
}

const ControlRequestModal: React.FC<ControlRequestModalProps> = ({
  isOpen,
  onClose,
  onRequest,
  isLoading,
  deviceName
}) => {
  const [ttlMinutes, setTtlMinutes] = useState(15)
  const [reason, setReason] = useState('Remote assistance')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onRequest({
      ttl_minutes: ttlMinutes,
      reason
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <Shield className="w-6 h-6 text-red-600" />
            <h2 className="text-xl font-semibold text-gray-900">Request Remote Control</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Warning Banner */}
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="text-red-800 font-medium mb-1">Security Notice:</p>
              <p className="text-red-700">
                Remote control grants full access to mouse and keyboard input on the target device. 
                This request requires approval and will be logged for security purposes.
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Device Info */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <MousePointer className="w-4 h-4 text-gray-600" />
              <span className="font-medium text-gray-900">Target Device</span>
            </div>
            <p className="text-sm text-gray-600">{deviceName}</p>
            <p className="text-xs text-gray-500 mt-1">
              Device must be linked in "control" mode for remote access
            </p>
          </div>

          {/* Reason Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason for Control Request
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={3}
              placeholder="Explain why you need remote control access..."
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              This reason will be shown to the approver
            </p>
          </div>

          {/* TTL Slider */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              <Clock className="w-4 h-4 inline mr-1" />
              Control Duration: {ttlMinutes} minutes
            </label>
            <input
              type="range"
              min="5"
              max="30"
              step="5"
              value={ttlMinutes}
              onChange={(e) => setTtlMinutes(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>5 min</span>
              <span>15 min</span>
              <span>30 min</span>
            </div>
            <p className="text-xs text-gray-600 mt-2">
              Control session will automatically expire after {ttlMinutes} minutes
            </p>
          </div>

          {/* Approval Process Info */}
          <div className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Approval Process:</h4>
            <ol className="text-sm text-blue-800 space-y-1">
              <li>1. Request sent to system administrator</li>
              <li>2. Approval notification via Telegram/Email</li>
              <li>3. Admin has 5 minutes to approve or deny</li>
              <li>4. Auto-deny if no response within timeout</li>
            </ol>
          </div>

          {/* Terms Acknowledgment */}
          <div className="mb-6">
            <label className="flex items-start space-x-2 cursor-pointer">
              <input 
                type="checkbox" 
                required
                className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                I acknowledge that this remote control session will be logged and monitored 
                for security purposes. I will use this access only for legitimate business purposes.
              </span>
            </label>
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
              disabled={isLoading || reason.length < 10}
              className="btn-danger flex items-center space-x-2"
            >
              {isLoading && (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              )}
              <Shield className="w-4 h-4" />
              <span>Request Control Access</span>
            </button>
          </div>
        </form>

        {/* Footer Notice */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            By requesting control, you agree to follow your organization's remote access policies.
            Unauthorized or malicious use may result in disciplinary action.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ControlRequestModal