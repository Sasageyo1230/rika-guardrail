// agent-android/app/src/main/java/com/rika/agent/util/DeviceInfoProvider.kt
package com.rika.agent.util

import android.app.ActivityManager
import android.content.Context
import android.content.Context.ACTIVITY_SERVICE
import android.content.IntentFilter
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.BatteryManager
import android.os.Build
import com.rika.agent.data.model.NetworkInfo
import java.security.MessageDigest
import org.json.JSONObject

class DeviceInfoProvider(private val context: Context) {

    fun generateFingerprint(): String {
        val fingerprintData = JSONObject().apply {
            put("brand", Build.BRAND)
            put("model", Build.MODEL)
            put("device", Build.DEVICE)
            put("product", Build.PRODUCT)
            put("hardware", Build.HARDWARE)
            put("manufacturer", Build.MANUFACTURER)
            put("board", Build.BOARD)
            put("sdk_int", Build.VERSION.SDK_INT)
            put("user", Build.USER)
        }

        val fingerprintString = fingerprintData.toString()
        val bytes = fingerprintString.toByteArray()
        val md = MessageDigest.getInstance("SHA-256")
        val digest = md.digest(bytes)
        
        return digest.fold("") { str, it -> str + "%02x".format(it) }
    }

    fun getCurrentApp(): String {
        return try {
            val activityManager = context.getSystemService(ACTIVITY_SERVICE) as ActivityManager
            val tasks = activityManager.getRunningTasks(1)
            
            if (tasks.isNotEmpty()) {
                val topActivity = tasks[0].topActivity
                topActivity?.packageName ?: "Unknown"
            } else {
                "Unknown"
            }
        } catch (e: Exception) {
            "Unknown"
        }
    }

    fun getBatteryLevel(): Int {
        return try {
            val batteryIntent = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            val level = batteryIntent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
            val scale = batteryIntent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
            
            if (level == -1 || scale == -1) {
                -1
            } else {
                (level * 100 / scale.toFloat()).toInt()
            }
        } catch (e: Exception) {
            -1
        }
    }

    fun getNetworkInfo(): NetworkInfo {
        return try {
            val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = connectivityManager.activeNetwork
            val capabilities = connectivityManager.getNetworkCapabilities(network)
            
            val isConnected = capabilities != null
            val type = when {
                capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true -> "WiFi"
                capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) == true -> "Cellular"
                capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) == true -> "Ethernet"
                else -> "Unknown"
            }
            
            NetworkInfo(type, isConnected)
        } catch (e: Exception) {
            NetworkInfo("Unknown", false)
        }
    }
}