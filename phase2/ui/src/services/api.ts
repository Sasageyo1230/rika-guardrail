// ui/src/services/api.ts
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Device {
  device_id: string
  name: string
  type: string
  last_seen: string
  last_active_app: string | null
  status: string
  linked: boolean
  link_mode: string | null
  link_expires_at: string | null
  gestures_enabled: boolean
}

export interface DeviceLink {
  device_id: string
  device_name: string
  mode: string
  gestures_enabled: boolean
  expires_at: string
  updated_at: string
}

export interface LinkRequest {
  device_id: string
  mode: 'view' | 'extend' | 'control'
  ttl_minutes?: number
  gestures: boolean
}

export const api = {
  // Get all device presence
  async getPresence(): Promise<Device[]> {
    const response = await apiClient.get('/presence')
    return response.data
  },

  // Get active links
  async getLinks(): Promise<DeviceLink[]> {
    const response = await apiClient.get('/links')
    return response.data
  },

  // Link a device
  async linkDevice(request: LinkRequest) {
    const response = await apiClient.post('/link', request)
    return response.data
  },

  // Unlink a device (or all devices if no deviceId provided)
  async unlinkDevice(deviceId?: string) {
    const response = await apiClient.post('/unlink', { 
      device_id: deviceId || null 
    })
    return response.data
  },

  // Toggle hands-on mode
  async toggleHandsOn(deviceId: string, enabled: boolean) {
    const response = await apiClient.post('/hands-on', {
      device_id: deviceId,
      enabled
    })
    return response.data
  },

  // Trigger blackout
  async triggerBlackout() {
    const response = await apiClient.post('/blackout', {
      device_id: 'atlas-dashboard',
      reason: 'Emergency blackout from Atlas Dashboard'
    })
    return response.data
  },

  // Health check
  async getHealth() {
    const response = await apiClient.get('/health')
    return response.data
  }
}