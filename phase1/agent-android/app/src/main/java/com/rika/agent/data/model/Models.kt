// agent-android/app/src/main/java/com/rika/agent/data/model/Models.kt
package com.rika.agent.data.model

import com.google.gson.annotations.SerializedName

// API Request/Response Models
data class EnrollRequest(
    @SerializedName("device_name") val deviceName: String,
    @SerializedName("device_type") val deviceType: String
)

data class EnrollResponse(
    val token: String,
    @SerializedName("expires_at") val expiresAt: String
)

data class EnrollCompleteRequest(
    val token: String,
    val fingerprint: String
)

data class EnrollCompleteResponse(
    @SerializedName("device_id") val deviceId: String,
    val credentials: Credentials,
    @SerializedName("nats_subjects") val natsSubjects: NatsSubjects
)

data class Credentials(
    @SerializedName("session_token") val sessionToken: String
)

data class NatsSubjects(
    val control: String,
    val presence: String
)

data class HeartbeatData(
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("current_app") val currentApp: String,
    @SerializedName("window_title") val windowTitle: String,
    val metadata: Map<String, Any>
)

data class PresenceResponse(
    val devices: List<DevicePresence>
)

data class DevicePresence(
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("device_name") val deviceName: String,
    @SerializedName("device_type") val deviceType: String,
    @SerializedName("current_app") val currentApp: String?,
    @SerializedName("last_seen") val lastSeen: String,
    val online: Boolean
)

data class BlackoutRequest(
    @SerializedName("device_id") val deviceId: String,
    val reason: String
)

// Local Storage Models
data class DeviceCredentials(
    val deviceId: String,
    val sessionToken: String,
    val enrolledAt: String
)

// UI State Models
data class MainUiState(
    val isServiceRunning: Boolean = false,
    val isEnrolled: Boolean = false,
    val isConnected: Boolean = false,
    val deviceId: String = "",
    val coreApiUrl: String = "http://192.168.1.100:8000",
    val lastHeartbeat: String = ""
)

data class NetworkInfo(
    val type: String,
    val isConnected: Boolean
)