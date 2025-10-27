// agent-android/app/src/main/java/com/rika/agent/data/RikaRepository.kt
package com.rika.agent.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import com.rika.agent.data.api.RikaApiService
import com.rika.agent.data.model.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "rika_preferences")

class RikaRepository(private val context: Context) {

    companion object {
        private val DEVICE_ID_KEY = stringPreferencesKey("device_id")
        private val SESSION_TOKEN_KEY = stringPreferencesKey("session_token")
        private val ENROLLED_AT_KEY = stringPreferencesKey("enrolled_at")
        private val CORE_API_URL_KEY = stringPreferencesKey("core_api_url")
        
        private const val DEFAULT_CORE_API_URL = "http://192.168.1.100:8000" // Update to your PC's IP
    }

    private val dataStore = context.dataStore
    
    private val apiService: RikaApiService by lazy {
        val baseUrl = getCoreApiUrl()
        Retrofit.Builder()
            .baseUrl(baseUrl)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(RikaApiService::class.java)
    }

    private fun getCoreApiUrl(): String {
        // In a real app, you'd want to make this configurable
        // For now, return the default
        return DEFAULT_CORE_API_URL
    }

    suspend fun enrollDevice(deviceName: String, fingerprint: String): Result<DeviceCredentials> {
        return try {
            // Step 1: Request enrollment token
            val enrollRequest = EnrollRequest(deviceName, "mobile")
            val enrollResponse = apiService.enroll(enrollRequest)
            
            // Step 2: Complete enrollment
            val completeRequest = EnrollCompleteRequest(enrollResponse.token, fingerprint)
            val completeResponse = apiService.completeEnrollment(completeRequest)
            
            // Store credentials
            val credentials = DeviceCredentials(
                deviceId = completeResponse.deviceId,
                sessionToken = completeResponse.credentials.sessionToken,
                enrolledAt = System.currentTimeMillis().toString()
            )
            
            storeCredentials(credentials)
            Result.success(credentials)
            
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendHeartbeat(heartbeatData: HeartbeatData, sessionToken: String): Result<Unit> {
        return try {
            apiService.sendHeartbeat(heartbeatData, "Bearer $sessionToken")
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun triggerBlackout(deviceId: String): Result<Unit> {
        return try {
            val blackoutRequest = BlackoutRequest(deviceId, "Manual blackout from Android")
            apiService.triggerBlackout(blackoutRequest)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private suspend fun storeCredentials(credentials: DeviceCredentials) {
        dataStore.edit { preferences ->
            preferences[DEVICE_ID_KEY] = credentials.deviceId
            preferences[SESSION_TOKEN_KEY] = credentials.sessionToken
            preferences[ENROLLED_AT_KEY] = credentials.enrolledAt
        }
    }

    fun getStoredCredentials(): Flow<DeviceCredentials?> {
        return dataStore.data.map { preferences ->
            val deviceId = preferences[DEVICE_ID_KEY]
            val sessionToken = preferences[SESSION_TOKEN_KEY]
            val enrolledAt = preferences[ENROLLED_AT_KEY]
            
            if (deviceId != null && sessionToken != null && enrolledAt != null) {
                DeviceCredentials(deviceId, sessionToken, enrolledAt)
            } else {
                null
            }
        }
    }

    suspend fun clearCredentials() {
        dataStore.edit { preferences ->
            preferences.remove(DEVICE_ID_KEY)
            preferences.remove(SESSION_TOKEN_KEY)
            preferences.remove(ENROLLED_AT_KEY)
        }
    }
}