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
import kotlinx.coroutines.flow.first
import java.text.SimpleDateFormat
import java.util.*

class RikaAgentService : Service() {

    companion object {
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "RikaAgentService"
        private const val HEARTBEAT_INTERVAL = 5000L // 5 seconds
    }

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private lateinit var repository: RikaRepository
    private lateinit var deviceInfoProvider: DeviceInfoProvider
    private var heartbeatJob: Job? = null

    override fun onCreate() {
        super.onCreate()
        repository = RikaRepository(this)
        deviceInfoProvider = DeviceInfoProvider(this)
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
                    
                    // TODO: Connect to NATS for messaging
                    // connectToNats(creds.deviceId)
                }

            } catch (e: Exception) {
                e.printStackTrace()
                stopSelf()
            }
        }
    }

    private fun stopAgentOperations() {
        heartbeatJob?.cancel()
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
                        windowTitle = "", // Android doesn't have window titles like desktop
                        metadata = mapOf(
                            "battery_level" to batteryLevel,
                            "network_type" to networkInfo.type,
                            "network_connected" to networkInfo.isConnected,
                            "timestamp" to SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
                                .format(Date())
                        )
                    )

                    val result = repository.sendHeartbeat(heartbeatData, sessionToken)
                    if (result.isSuccess) {
                        updateNotification("Heartbeat sent - App: ${currentApp.take(20)}")
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
            .setContentTitle("🤖 Rika Agent")
            .setContentText("Agent is running...")
            .setSmallIcon(R.drawable.ic_notification)
            .setOngoing(true)
            .setCategory(Notification.CATEGORY_SERVICE)
            .build()
    }

    private fun updateNotification(text: String) {
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🤖 Rika Agent")
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_notification)
            .setOngoing(true)
            .setCategory(Notification.CATEGORY_SERVICE)
            .build()

        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
}