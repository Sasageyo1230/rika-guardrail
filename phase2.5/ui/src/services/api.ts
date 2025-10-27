// ui/src/services/api.ts - Phase 2.5
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5317'

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
  // Phase 2.5: Control status
  control_status: string | null // pending, active, revoked
  control_expires_at: string | null
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

// Phase 2.5: New interfaces
export interface StreamInfo {
  device_id: string
  device_name: string
  room_name: string
  participant_token: string
  viewer_token: string
  ws_url: string
  expires_at: string
}

export interface ControlRequest {
  device_id: string
  ttl_minutes: number
  reason?: string
}

export interface ControlResponse {
  request_id: string
  status: string
  expires_at: string
  approval_url: string
}

export interface ControlInputEvent {
  device_id: string
  event_type: 'mouse_move' | 'mouse_click' | 'mouse_scroll' | 'key_press' | 'key_release'
  payload: Record<string, any>
}

export const api = {
  // Phase 1 & 2 endpoints (existing)
  async getPresence(): Promise<Device[]> {
    const response = await apiClient.get('/presence')
    return response.data
  },

  async getLinks(): Promise<DeviceLink[]> {
    const response = await apiClient.get('/links')
    return response.data
  },

  async linkDevice(request: LinkRequest) {
    const response = await apiClient.post('/link', request)
    return response.data
  },

  async unlinkDevice(deviceId?: string) {
    const response = await apiClient.post('/unlink', { 
      device_id: deviceId || null 
    })
    return response.data
  },

  async toggleHandsOn(deviceId: string, enabled: boolean) {
    const response = await apiClient.post('/hands-on', {
      device_id: deviceId,
      enabled
    })
    return response.data
  },

  async triggerBlackout() {
    const response = await apiClient.post('/blackout', {
      device_id: 'atlas-dashboard',
      reason: 'Emergency blackout from Atlas Dashboard'
    })
    return response.data
  },

  // Phase 2.5: Streaming endpoints
  async getStreams(): Promise<StreamInfo[]> {
    const response = await apiClient.get('/streams')
    return response.data
  },

  // Phase 2.5: Control endpoints
  async requestControl(request: ControlRequest): Promise<ControlResponse> {
    const response = await apiClient.post('/control/request', request)
    return response.data
  },

  async revokeControl(deviceId: string) {
    const response = await apiClient.post('/control/revoke', {
      device_id: deviceId,
      reason: 'Manual revoke from Atlas Dashboard'
    })
    return response.data
  },

  async sendControlInput(event: ControlInputEvent) {
    const response = await apiClient.post('/control/input', event)
    return response.data
  },

  // Health check
  async getHealth() {
    const response = await apiClient.get('/health')
    return response.data
  }
}