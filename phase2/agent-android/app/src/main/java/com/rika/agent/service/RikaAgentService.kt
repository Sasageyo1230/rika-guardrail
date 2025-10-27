// agent-android/app/src/main/java/com/rika/agent/service/RikaAgentService.kt
package com.rika.agent.service

import android.app.*
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import com.rika.agent.R
import com.rika.agent.data.RikaRepository
import com.rika.agent.data.model.HeartbeatData
import com.rika.agent.util.DeviceInfoProvider
import com.rika.agent.util.ScreenshotManager
import kotlinx.coroutines.flow.first
import java.text.SimpleDateFormat
import java.util.*

class RikaAgentService : Service() {

    companion object {
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "RikaAgentService"
        private const val HEARTBEAT_INTERVAL = 5000L // 5 seconds
        private const val THUMBNAIL_INTERVAL = 5000L // 5 seconds for view mode
    }

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private lateinit var repository: RikaRepository
    private lateinit var deviceInfoProvider: DeviceInfoProvider
    private lateinit var screenshotManager: ScreenshotManager
    
    private var heartbeatJob: Job? = null
    private var thumbnailJob: Job? = null
    
    // Phase 2: Linking state
    private var isLinked = false
    private var linkMode: String? = null
    private var gesturesEnabled = false
    private var handsOnMode = false

    override fun onCreate() {
        super.onCreate()
        repository = RikaRepository(this)
        deviceInfoProvider = DeviceInfoProvider(this)
        screenshotManager = ScreenshotManager(this)
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, createNotification())
        startAgentOperations()
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        stopAgentOperations()
        serviceScope.cancel()
    }

    private fun startAgentOperations() {
        serviceScope.launch {
            try {
                // Check if device is enrolled, if not enroll it
                var credentials = repository.getStoredCredentials().first()
                if (credentials == null) {
                    val enrolled = enrollDevice()
                    if (!enrolled) {
                        stopSelf()
                        return@launch
                    }
                    credentials = repository.getStoredCredentials().first()
                }

                credentials?.let { creds ->
                    // Start heartbeat
                    startHeartbeat(creds.deviceId, creds.sessionToken)
                    
                    // Listen for link events via polling (simplified for Phase 2)
                    startLinkStatusMonitoring(creds.deviceId)
                }

            } catch (e: Exception) {
                e.printStackTrace()
                stopSelf()
            }
        }
    }

    private fun stopAgentOperations() {
        heartbeatJob?.cancel()
        thumbnailJob?.cancel()
        isLinked = false
        linkMode = null
    }

    private suspend fun enrollDevice(): Boolean {
        return try {
            val deviceName = "${android.os.Build.MODEL}-${android.os.Build.USER}"
            val fingerprint = deviceInfoProvider.generateFingerprint()
            
            val result = repository.enrollDevice(deviceName, fingerprint)
            result.isSuccess
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    private fun startHeartbeat(deviceId: String, sessionToken: String) {
        heartbeatJob = serviceScope.launch {
            while (isActive) {
                try {
                    val currentApp = deviceInfoProvider.getCurrentApp()
                    val batteryLevel = deviceInfoProvider.getBatteryLevel()
                    val networkInfo = deviceInfoProvider.getNetworkInfo()
                    
                    val heartbeatData = HeartbeatData(
                        deviceId = deviceId,
                        currentApp = currentApp,
                        windowTitle = "", // Android doesn't have window titles
                        metadata = mapOf(
                            "battery_level" to batteryLevel,
                            "network_type" to networkInfo.type,
                            "network_connected" to networkInfo.isConnected,
                            "linked" to isLinked,
                            "link_mode" to (linkMode ?: ""),
                            "hands_on_mode" to handsOnMode,
                            "timestamp" to SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
                                .format(Date())
                        )
                    )

                    val result = repository.sendHeartbeat(heartbeatData, sessionToken)
                    if (result.isSuccess) {
                        val statusIcon = if (isLinked) "🔗" else "💓"
                        val modeText = if (isLinked) " ($linkMode)" else ""
                        updateNotification("$statusIcon Heartbeat sent$modeText - App: ${currentApp.take(20)}")
                    } else {
                        updateNotification("Heartbeat failed")
                    }

                } catch (e: Exception) {
                    e.printStackTrace()
                    updateNotification("Error: ${e.message}")
                }

                delay(HEARTBEAT_INTERVAL)
            }
        }
    }

    private fun startLinkStatusMonitoring(deviceId: String) {
        serviceScope.launch {
            while (isActive) {
                try {
                    // Check link status via API
                    val linkStatus = repository.getLinkStatus(deviceId)
                    linkStatus.onSuccess { status ->
                        handleLinkStatusChange(status)
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
                
                delay(10000) // Check every 10 seconds
            }
        }
    }

    private suspend fun handleLinkStatusChange(status: LinkStatus) {
        val wasLinked = isLinked
        val oldMode = linkMode
        
        isLinked = status.linked
        linkMode = status.mode
        gesturesEnabled = status.gesturesEnabled
        
        // Handle link mode changes
        if (!wasLinked && isLinked) {
            // Just got linked
            onDeviceLinked()
        } else if (wasLinked && !isLinked) {
            // Just got unlinked
            onDeviceUnlinked()
        } else if (isLinked && oldMode != linkMode) {
            // Mode changed
            onLinkModeChanged(oldMode, linkMode)
        }
    }

    private suspend fun onDeviceLinked() {
        updateNotification("🔗 Device linked in $linkMode mode")
        
        when (linkMode) {
            "view" -> startThumbnailCapture()
            "extend" -> {
                // Would start LiveKit streaming here
                updateNotification("🔗 Extended display mode active")
            }
            "control" -> {
                // Would enable remote control here
                updateNotification("🔗 Remote control mode active")
            }
        }
    }

    private suspend fun onDeviceUnlinked() {
        updateNotification("🔓 Device unlinked")
        stopThumbnailCapture()
        handsOnMode = false
    }

    private suspend fun onLinkModeChanged(oldMode: String?, newMode: String?) {
        updateNotification("🔄 Link mode changed: $oldMode → $newMode")
        
        // Stop old mode activities
        when (oldMode) {
            "view" -> stopThumbnailCapture()
        }
        
        // Start new mode activities
        when (newMode) {
            "view" -> startThumbnailCapture()
            "extend" -> updateNotification("🔗 Extended display mode active")
            "control" -> updateNotification("🔗 Remote control mode active")
        }
    }

    private suspend fun startThumbnailCapture() {
        if (!screenshotManager.hasPermission()) {
            updateNotification("📸 Screenshot permission required for view mode")
            return
        }
        
        thumbnailJob = serviceScope.launch {
            updateNotification("📸 Starting thumbnail capture")
            
            while (isActive && isLinked && linkMode == "view") {
                try {
                    val thumbnail = screenshotManager.captureScreenshot()
                    if (thumbnail != null) {
                        val uploaded = repository.uploadThumbnail(thumbnail)
                        if (uploaded.isSuccess) {
                            updateNotification("📸 Thumbnail uploaded")
                        }
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                    updateNotification("📸 Thumbnail capture failed")
                }
                
                delay(THUMBNAIL_INTERVAL)
            }
        }
    }

    private fun stopThumbnailCapture() {
        thumbnailJob?.cancel()
        thumbnailJob = null
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Rika Agent Service",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Keeps Rika Agent running in background"
            setShowBadge(false)
        }

        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.createNotificationChannel(channel)
    }

    private fun createNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🤖 Rika Agent v2")
            .setContentText("Agent is running...")
            .setSmallIcon(R.drawable.ic_notification)
            .setOngoing(true)
            .setCategory(Notification.CATEGORY_SERVICE)
            .build()
    }

    private fun updateNotification(text: String) {
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🤖 Rika Agent v2")
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_notification)
            .setOngoing(true)
            .setCategory(Notification.CATEGORY_SERVICE)
            .build()

        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
}

data class LinkStatus(
    val linked: Boolean,
    val mode: String?,
    val gesturesEnabled: Boolean,
    val expiresAt: String?
)