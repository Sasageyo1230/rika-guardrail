// ui/src/App.tsx
import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Monitor, 
  Smartphone, 
  Tablet, 
  Wifi, 
  WifiOff, 
  Link, 
  Unlink, 
  Power, 
  Hand,
  Clock,
  Settings,
  AlertTriangle
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { api } from './services/api'
import DeviceCard from './components/DeviceCard'
import LinkModal from './components/LinkModal'
import GlobalControls from './components/GlobalControls'
import StatusBanner from './components/StatusBanner'

function App() {
  const queryClient = useQueryClient()
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null)
  const [linkModalOpen, setLinkModalOpen] = useState(false)

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

  // Link device mutation
  const linkMutation = useMutation({
    mutationFn: api.linkDevice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
      queryClient.invalidateQueries({ queryKey: ['links'] })
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
    }
  })

  // Unlink all devices mutation
  const unlinkAllMutation = useMutation({
    mutationFn: () => api.unlinkDevice(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
      queryClient.invalidateQueries({ queryKey: ['links'] })
    }
  })

  // Blackout mutation
  const blackoutMutation = useMutation({
    mutationFn: api.triggerBlackout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presence'] })
      queryClient.invalidateQueries({ queryKey: ['links'] })
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

  const handleLinkDevice = (deviceId: string) => {
    setSelectedDevice(deviceId)
    setLinkModalOpen(true)
  }

  const handleUnlinkDevice = (deviceId: string) => {
    unlinkMutation.mutate(deviceId)
  }

  const handleLink = (params: { mode: string, ttl_minutes: number, gestures: boolean }) => {
    if (selectedDevice) {
      linkMutation.mutate({
        device_id: selectedDevice,
        ...params
      })
    }
  }

  const linkedDevices = devices.filter(device => device.linked)
  const unlinkedDevices = devices.filter(device => !device.linked)
  const onlineDevices = devices.filter(device => device.status === 'active')

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
                Phase 2 - Device Linking & Management
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                {onlineDevices.length} online • {linkedDevices.length} linked
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </header>

      {/* Status Banner */}
      <StatusBanner 
        linkedCount={linkedDevices.length}
        onlineCount={onlineDevices.length}
        totalCount={devices.length}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Main Content */}
          <div className="lg:col-span-3">
            
            {/* Linked Devices Section */}
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
                      isLinking={linkMutation.isPending}
                      isUnlinking={unlinkMutation.isPending}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Available Devices Section */}
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
                      isLinking={linkMutation.isPending}
                      isUnlinking={unlinkMutation.isPending}
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
          </div>
        </div>
      </div>

      {/* Link Modal */}
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
    </div>
  )
}

export default App