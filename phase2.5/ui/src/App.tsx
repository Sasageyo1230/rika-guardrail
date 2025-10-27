// ui/src/App.tsx - Phase 2.5
import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Monitor, 
  Wifi, 
  WifiOff, 
  Link, 
  Unlink, 
  Power, 
  Hand,
  Clock,
  Settings,
  AlertTriangle,
  Play,
  Square,
  Shield
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { api, StreamInfo } from './services/api'
import DeviceCard from './components/DeviceCard'
import LinkModal from './components/LinkModal'
import ControlRequestModal from './components/ControlRequestModal'
import StreamViewer from './components/StreamViewer'
import GlobalControls from './components/GlobalControls'
import StatusBanner from './components/StatusBanner'

function App() {
  const queryClient = useQueryClient()
  
  // Modal states
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null)
  const [linkModalOpen, setLinkModalOpen] = useState(false)
  const [controlModalOpen, setControlModalOpen] = useState(false)
  const [streamViewerOpen, setStreamViewerOpen] = useState(false)
  
  // Stream states
  const [activeStreams, setActiveStreams] = useState<Set<string>>(new Set())
  const [selectedStream, setSelectedStream] = useState<StreamInfo | null>(null)

  // Fetch device presence data
  const { data: devices = [], isLoading } = useQuery({
    queryKey: ['presence'],
    queryFn: api.getPresence,
    refetchInterval: 5000,
  })

  // Fetch current links
  const { data: links = [] } = useQuery({
    queryKey: ['links'],
    queryFn: api.getLinks,
    refetchInterval: 5000,
  })

  // Fetch stream info
  const { data: streams = [] } = useQuery({
    queryKey: ['streams'],
    queryFn: api.getStreams,
    refetchInterval: 10000,
  })

  // Link device mutation
  const linkMutation = useMutation({
    mutationFn: api.linkDevice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
      queryClient.invalidateQueries({ queryKey: ['links'] })
      queryClient.invalidateQueries({ queryKey: ['streams'] })
      setLinkModalOpen(false)
      setSelectedDevice(null)
    }
  })

  // Unlink device mutation
  const unlinkMutation = useMutation({
    mutationFn: api.unlinkDevice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
      queryClient.invalidateQueries({ queryKey: ['links'] })
      queryClient.invalidateQueries({ queryKey: ['streams'] })
    }
  })

  // Unlink all devices mutation
  const unlinkAllMutation = useMutation({
    mutationFn: () => api.unlinkDevice(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
      queryClient.invalidateQueries({ queryKey: ['links'] })
      queryClient.invalidateQueries({ queryKey: ['streams'] })
    }
  })

  // Blackout mutation
  const blackoutMutation = useMutation({
    mutationFn: api.triggerBlackout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
      queryClient.invalidateQueries({ queryKey: ['links'] })
      queryClient.invalidateQueries({ queryKey: ['streams'] })
      setActiveStreams(new Set())
    }
  })

  // Hands-on mode mutation
  const handsOnMutation = useMutation({
    mutationFn: ({ deviceId, enabled }: { deviceId: string, enabled: boolean }) =>
      api.toggleHandsOn(deviceId, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
    }
  })

  // Phase 2.5: Control request mutation
  const controlRequestMutation = useMutation({
    mutationFn: api.requestControl,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
      setControlModalOpen(false)
      setSelectedDevice(null)
    }
  })

  // Phase 2.5: Control revoke mutation
  const controlRevokeMutation = useMutation({
    mutationFn: api.revokeControl,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
    }
  })

  // Phase 2.5: Send control input mutation
  const controlInputMutation = useMutation({
    mutationFn: api.sendControlInput
  })

  const handleLinkDevice = (deviceId: string) => {
    setSelectedDevice(deviceId)
    setLinkModalOpen(true)
  }

  const handleUnlinkDevice = (deviceId: string) => {
    unlinkMutation.mutate(deviceId)
    // Stop stream if active
    setActiveStreams(prev => {
      const newSet = new Set(prev)
      newSet.delete(deviceId)
      return newSet
    })
  }

  const handleLink = (params: { mode: string, ttl_minutes: number, gestures: boolean }) => {
    if (selectedDevice) {
      linkMutation.mutate({
        device_id: selectedDevice,
        ...params
      })
    }
  }

  const handleRequestControl = (deviceId: string) => {
    setSelectedDevice(deviceId)
    setControlModalOpen(true)
  }

  const handleControlRequest = (params: { ttl_minutes: number, reason: string }) => {
    if (selectedDevice) {
      controlRequestMutation.mutate({
        device_id: selectedDevice,
        ...params
      })
    }
  }

  const handleRevokeControl = (deviceId: string) => {
    controlRevokeMutation.mutate(deviceId)
  }

  const handleStartStream = (deviceId: string) => {
    setActiveStreams(prev => new Set(prev).add(deviceId))
  }

  const handleStopStream = (deviceId: string) => {
    setActiveStreams(prev => {
      const newSet = new Set(prev)
      newSet.delete(deviceId)
      return newSet
    })
  }

  const handleViewStream = (deviceId: string) => {
    const streamInfo = streams.find(s => s.device_id === deviceId)
    if (streamInfo) {
      setSelectedStream(streamInfo)
      setStreamViewerOpen(true)
    }
  }

  const handleSendControlInput = (event: any) => {
    controlInputMutation.mutate(event)
  }

  const linkedDevices = devices.filter(device => device.linked)
  const unlinkedDevices = devices.filter(device => !device.linked)
  const onlineDevices = devices.filter(device => device.status === 'active')
  const controlledDevices = devices.filter(device => device.control_status === 'active')
  const streamingDevices = devices.filter(device => 
    device.linked && 
    (device.link_mode === 'view' || device.link_mode === 'extend') &&
    activeStreams.has(device.device_id)
  )

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rika-blue mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Atlas Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-rika-blue rounded-lg flex items-center justify-center">
                  <Monitor className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900">Rika Atlas</h1>
              </div>
              <div className="text-sm text-gray-500">
                Phase 2.5 - Streaming & Remote Control
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="text-sm text-gray-600">
                {onlineDevices.length} online • {linkedDevices.length} linked
              </div>
              
              {streamingDevices.length > 0 && (
                <div className="flex items-center space-x-1 text-sm text-blue-600">
                  <Play className="w-4 h-4" />
                  <span>{streamingDevices.length} streaming</span>
                </div>
              )}
              
              {controlledDevices.length > 0 && (
                <div className="flex items-center space-x-1 text-sm text-red-600">
                  <Shield className="w-4 h-4" />
                  <span>{controlledDevices.length} controlled</span>
                </div>
              )}
              
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </header>

      {/* Enhanced Status Banner */}
      <StatusBanner 
        linkedCount={linkedDevices.length}
        onlineCount={onlineDevices.length}
        totalCount={devices.length}
        streamingCount={streamingDevices.length}
        controlledCount={controlledDevices.length}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Main Content */}
          <div className="lg:col-span-3">
            
            {/* Active Control Sessions */}
            {controlledDevices.length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Shield className="w-5 h-5 mr-2 text-red-600" />
                  Active Control Sessions ({controlledDevices.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {controlledDevices.map(device => (
                    <DeviceCard
                      key={device.device_id}
                      device={device}
                      onLink={() => handleLinkDevice(device.device_id)}
                      onUnlink={() => handleUnlinkDevice(device.device_id)}
                      onHandsOn={(enabled) => handsOnMutation.mutate({ 
                        deviceId: device.device_id, 
                        enabled 
                      })}
                      onStartStream={() => handleStartStream(device.device_id)}
                      onStopStream={() => handleStopStream(device.device_id)}
                      onRequestControl={() => handleRequestControl(device.device_id)}
                      onRevokeControl={() => handleRevokeControl(device.device_id)}
                      isLinking={linkMutation.isPending}
                      isUnlinking={unlinkMutation.isPending}
                      isStreamActive={activeStreams.has(device.device_id)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Streaming Devices */}
            {streamingDevices.length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Play className="w-5 h-5 mr-2 text-blue-600" />
                  Live Streams ({streamingDevices.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {streamingDevices.map(device => (
                    <div key={device.device_id} className="relative">
                      <DeviceCard
                        device={device}
                        onLink={() => handleLinkDevice(device.device_id)}
                        onUnlink={() => handleUnlinkDevice(device.device_id)}
                        onHandsOn={(enabled) => handsOnMutation.mutate({ 
                          deviceId: device.device_id, 
                          enabled 
                        })}
                        onStartStream={() => handleStartStream(device.device_id)}
                        onStopStream={() => handleStopStream(device.device_id)}
                        onRequestControl={() => handleRequestControl(device.device_id)}
                        onRevokeControl={() => handleRevokeControl(device.device_id)}
                        isLinking={linkMutation.isPending}
                        isUnlinking={unlinkMutation.isPending}
                        isStreamActive={activeStreams.has(device.device_id)}
                      />
                      <button
                        onClick={() => handleViewStream(device.device_id)}
                        className="absolute top-2 left-2 bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs font-medium flex items-center space-x-1"
                      >
                        <Play className="w-3 h-3" />
                        <span>Watch</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Linked Devices */}
            {linkedDevices.length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Link className="w-5 h-5 mr-2 text-rika-blue" />
                  Linked Devices ({linkedDevices.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {linkedDevices.map(device => (
                    <DeviceCard
                      key={device.device_id}
                      device={device}
                      onLink={() => handleLinkDevice(device.device_id)}
                      onUnlink={() => handleUnlinkDevice(device.device_id)}
                      onHandsOn={(enabled) => handsOnMutation.mutate({ 
                        deviceId: device.device_id, 
                        enabled 
                      })}
                      onStartStream={() => handleStartStream(device.device_id)}
                      onStopStream={() => handleStopStream(device.device_id)}
                      onRequestControl={() => handleRequestControl(device.device_id)}
                      onRevokeControl={() => handleRevokeControl(device.device_id)}
                      isLinking={linkMutation.isPending}
                      isUnlinking={unlinkMutation.isPending}
                      isStreamActive={activeStreams.has(device.device_id)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Available Devices */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Monitor className="w-5 h-5 mr-2 text-gray-600" />
                Available Devices ({unlinkedDevices.length})
              </h2>
              
              {unlinkedDevices.length === 0 ? (
                <div className="card text-center py-12">
                  <Monitor className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Available Devices</h3>
                  <p className="text-gray-600">All devices are currently linked or offline.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {unlinkedDevices.map(device => (
                    <DeviceCard
                      key={device.device_id}
                      device={device}
                      onLink={() => handleLinkDevice(device.device_id)}
                      onUnlink={() => handleUnlinkDevice(device.device_id)}
                      onHandsOn={(enabled) => handsOnMutation.mutate({ 
                        deviceId: device.device_id, 
                        enabled 
                      })}
                      onStartStream={() => handleStartStream(device.device_id)}
                      onStopStream={() => handleStopStream(device.device_id)}
                      onRequestControl={() => handleRequestControl(device.device_id)}
                      onRevokeControl={() => handleRevokeControl(device.device_id)}
                      isLinking={linkMutation.isPending}
                      isUnlinking={unlinkMutation.isPending}
                      isStreamActive={activeStreams.has(device.device_id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <GlobalControls
              linkedCount={linkedDevices.length}
              streamingCount={streamingDevices.length}
              controlledCount={controlledDevices.length}
              onUnlinkAll={() => unlinkAllMutation.mutate()}
              onBlackout={() => blackoutMutation.mutate()}
              isUnlinkingAll={unlinkAllMutation.isPending}
              isBlackout={blackoutMutation.isPending}
            />

            {/* Active Links Summary */}
            {links.length > 0 && (
              <div className="card mt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Active Links</h3>
                <div className="space-y-3">
                  {links.map(link => (
                    <div key={link.device_id} className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-sm">{link.device_name}</div>
                        <div className="text-xs text-gray-500 capitalize">
                          {link.mode} mode
                          {link.gestures_enabled && ' • Gestures'}
                        </div>
                      </div>
                      <div className="text-xs text-gray-500">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {formatDistanceToNow(new Date(link.expires_at), { addSuffix: true })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Stream Status */}
            {streams.length > 0 && (
              <div className="card mt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Stream Status ({streams.length})
                </h3>
                <div className="space-y-2">
                  {streams.map(stream => (
                    <div key={stream.device_id} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                      <div>
                        <div className="font-medium text-sm">{stream.device_name}</div>
                        <div className="text-xs text-blue-600">Room: {stream.room_name}</div>
                      </div>
                      <button
                        onClick={() => handleViewStream(stream.device_id)}
                        className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                      >
                        View
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <LinkModal
        isOpen={linkModalOpen}
        onClose={() => {
          setLinkModalOpen(false)
          setSelectedDevice(null)
        }}
        onLink={handleLink}
        isLoading={linkMutation.isPending}
        deviceName={devices.find(d => d.device_id === selectedDevice)?.name || ''}
      />

      <ControlRequestModal
        isOpen={controlModalOpen}
        onClose={() => {
          setControlModalOpen(false)
          setSelectedDevice(null)
        }}
        onRequest={handleControlRequest}
        isLoading={controlRequestMutation.isPending}
        deviceName={devices.find(d => d.device_id === selectedDevice)?.name || ''}
      />

      {selectedStream && (
        <StreamViewer
          streamInfo={selectedStream}
          isOpen={streamViewerOpen}
          onClose={() => {
            setStreamViewerOpen(false)
            setSelectedStream(null)
          }}
          onSendInput={handleSendControlInput}
          canControl={devices.find(d => d.device_id === selectedStream.device_id)?.control_status === 'active'}
        />
      )}
    </div>
  )
}

export default App