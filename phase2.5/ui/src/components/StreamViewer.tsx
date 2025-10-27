// ui/src/components/StreamViewer.tsx - Phase 2.5
import React, { useEffect, useRef, useState } from 'react'
import { Room, RoomEvent, Track } from 'livekit-client'
import { 
  X, 
  Volume2, 
  VolumeX, 
  Maximize, 
  Minimize, 
  MousePointer,
  Square,
  AlertCircle
} from 'lucide-react'
import { StreamInfo, ControlInputEvent } from '../services/api'

interface StreamViewerProps {
  streamInfo: StreamInfo
  isOpen: boolean
  onClose: () => void
  onSendInput?: (event: ControlInputEvent) => void
  canControl?: boolean
}

const StreamViewer: React.FC<StreamViewerProps> = ({
  streamInfo,
  isOpen,
  onClose,
  onSendInput,
  canControl = false
}) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const roomRef = useRef<Room | null>(null)
  
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [controlActive, setControlActive] = useState(false)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

  useEffect(() => {
    if (!isOpen) return

    const connectToRoom = async () => {
      try {
        const room = new Room()
        roomRef.current = room

        // Handle room events
        room.on(RoomEvent.Connected, () => {
          setIsConnected(true)
          setError(null)
        })

        room.on(RoomEvent.Disconnected, () => {
          setIsConnected(false)
        })

        room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
          if (track.kind === Track.Kind.Video && videoRef.current) {
            track.attach(videoRef.current)
          }
        })

        room.on(RoomEvent.TrackUnsubscribed, (track) => {
          if (track.kind === Track.Kind.Video) {
            track.detach()
          }
        })

        // Connect to room
        await room.connect(streamInfo.ws_url, streamInfo.viewer_token)
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to connect to stream')
        console.error('LiveKit connection error:', err)
      }
    }

    connectToRoom()

    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect()
        roomRef.current = null
      }
      setIsConnected(false)
    }
  }, [isOpen, streamInfo])

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canControl || !controlActive || !onSendInput) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 100
    const y = ((e.clientY - rect.top) / rect.height) * 100

    setMousePosition({ x: e.clientX - rect.left, y: e.clientY - rect.top })

    onSendInput({
      device_id: streamInfo.device_id,
      event_type: 'mouse_move',
      payload: { x: Math.round(x), y: Math.round(y) }
    })
  }

  const handleMouseClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canControl || !controlActive || !onSendInput) return

    const button = e.button === 0 ? 'left' : e.button === 2 ? 'right' : 'middle'
    
    onSendInput({
      device_id: streamInfo.device_id,
      event_type: 'mouse_click',
      payload: { button, pressed: true }
    })

    // Send release after short delay
    setTimeout(() => {
      onSendInput({
        device_id: streamInfo.device_id,
        event_type: 'mouse_click',
        payload: { button, pressed: false }
      })
    }, 100)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLCanvasElement>) => {
    if (!canControl || !controlActive || !onSendInput) return

    e.preventDefault()
    
    onSendInput({
      device_id: streamInfo.device_id,
      event_type: 'key_press',
      payload: { key: e.key }
    })

    // Send release after short delay
    setTimeout(() => {
      onSendInput({
        device_id: streamInfo.device_id,
        event_type: 'key_release',
        payload: { key: e.key }
      })
    }, 100)
  }

  const toggleFullscreen = () => {
    const container = document.getElementById('stream-container')
    if (!container) return

    if (!isFullscreen) {
      container.requestFullscreen?.()
    } else {
      document.exitFullscreen?.()
    }
    setIsFullscreen(!isFullscreen)
  }

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const toggleControl = () => {
    setControlActive(!controlActive)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
      <div 
        id="stream-container"
        className={`relative ${isFullscreen ? 'w-full h-full' : 'w-4/5 h-4/5 max-w-6xl'} bg-black rounded-lg overflow-hidden`}
      >
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/80 to-transparent p-4 z-10">
          <div className="flex items-center justify-between text-white">
            <div>
              <h3 className="font-semibold">{streamInfo.device_name}</h3>
              <div className="text-sm opacity-75">
                {isConnected ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span>Live Stream</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span>Connecting...</span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={toggleMute}
                className="p-2 bg-black/50 hover:bg-black/70 rounded-lg transition-colors"
              >
                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </button>
              
              {canControl && (
                <button
                  onClick={toggleControl}
                  className={`p-2 rounded-lg transition-colors ${
                    controlActive 
                      ? 'bg-red-600 hover:bg-red-700' 
                      : 'bg-black/50 hover:bg-black/70'
                  }`}
                  title={controlActive ? 'Disable Control' : 'Enable Control'}
                >
                  <MousePointer className="w-5 h-5" />
                </button>
              )}
              
              <button
                onClick={toggleFullscreen}
                className="p-2 bg-black/50 hover:bg-black/70 rounded-lg transition-colors"
              >
                {isFullscreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
              </button>
              
              <button
                onClick={onClose}
                className="p-2 bg-black/50 hover:bg-black/70 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Video Stream */}
        <div className="relative w-full h-full">
          <video
            ref={videoRef}
            className="w-full h-full object-contain"
            autoPlay
            playsInline
            muted={isMuted}
          />
          
          {/* Control Overlay Canvas */}
          {canControl && (
            <canvas
              ref={canvasRef}
              className={`absolute inset-0 w-full h-full ${
                controlActive ? 'cursor-none' : 'cursor-pointer'
              }`}
              onMouseMove={handleMouseMove}
              onClick={handleMouseClick}
              onContextMenu={(e) => e.preventDefault()}
              onKeyDown={handleKeyPress}
              tabIndex={controlActive ? 0 : -1}
              style={{ 
                pointerEvents: controlActive ? 'all' : 'none',
                background: controlActive ? 'rgba(255, 0, 0, 0.1)' : 'transparent'
              }}
            />
          )}

          {/* Control Active Indicator */}
          {controlActive && (
            <>
              <div className="absolute top-1/2 left-4 transform -translate-y-1/2 bg-red-600 text-white px-3 py-2 rounded-lg">
                <div className="flex items-center space-x-2">
                  <MousePointer className="w-4 h-4" />
                  <span className="font-medium">Remote Control Active</span>
                </div>
                <div className="text-xs opacity-75 mt-1">
                  Click to control • Press ESC to disable
                </div>
              </div>
              
              {/* Mouse Cursor */}
              <div 
                className="absolute w-4 h-4 pointer-events-none z-20"
                style={{
                  left: mousePosition.x,
                  top: mousePosition.y,
                  transform: 'translate(-2px, -2px)'
                }}
              >
                <MousePointer className="w-4 h-4 text-red-500 drop-shadow-lg" />
              </div>
            </>
          )}

          {/* Error Message */}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80">
              <div className="text-center text-white">
                <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
                <h3 className="text-lg font-semibold mb-2">Stream Error</h3>
                <p className="text-sm opacity-75 mb-4">{error}</p>
                <button
                  onClick={onClose}
                  className="bg-white text-black px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* Loading State */}
          {!isConnected && !error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80">
              <div className="text-center text-white">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                <h3 className="text-lg font-semibold mb-2">Connecting to Stream</h3>
                <p className="text-sm opacity-75">{streamInfo.device_name}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
          <div className="flex items-center justify-between text-white text-sm">
            <div className="flex items-center space-x-4">
              <span>Room: {streamInfo.room_name}</span>
              {controlActive && (
                <div className="flex items-center space-x-1 bg-red-600 px-2 py-1 rounded">
                  <Square className="w-3 h-3" />
                  <span>CONTROLLING</span>
                </div>
              )}
            </div>
            
            <div className="opacity-75">
              Rika Atlas • Stream expires {new Date(streamInfo.expires_at).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* ESC to exit control mode */}
      {controlActive && (
        <div 
          className="fixed inset-0 z-40"
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              setControlActive(false)
            }
          }}
          tabIndex={0}
          autoFocus
        />
      )}
    </div>
  )
}

export default StreamViewer