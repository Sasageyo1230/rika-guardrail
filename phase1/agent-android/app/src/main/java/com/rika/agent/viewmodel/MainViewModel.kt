// agent-android/app/src/main/java/com/rika/agent/viewmodel/MainViewModel.kt
package com.rika.agent.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.rika.agent.data.RikaRepository
import com.rika.agent.data.model.MainUiState
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = RikaRepository(application)
    
    private val _uiState = MutableStateFlow(MainUiState())
    val uiState: StateFlow<MainUiState> = _uiState.asStateFlow()

    init {
        observeCredentials()
    }

    private fun observeCredentials() {
        viewModelScope.launch {
            repository.getStoredCredentials().collect { credentials ->
                _uiState.update { currentState ->
                    currentState.copy(
                        isEnrolled = credentials != null,
                        deviceId = credentials?.deviceId ?: ""
                    )
                }
            }
        }
    }

    fun updateServiceStatus(isRunning: Boolean) {
        _uiState.update { it.copy(isServiceRunning = isRunning) }
    }

    fun updateConnectionStatus(isConnected: Boolean) {
        _uiState.update { it.copy(isConnected = isConnected) }
    }

    fun updateLastHeartbeat() {
        val timestamp = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
        _uiState.update { it.copy(lastHeartbeat = timestamp) }
    }

    fun triggerBlackout() {
        viewModelScope.launch {
            try {
                val currentState = _uiState.value
                if (currentState.deviceId.isNotEmpty()) {
                    repository.triggerBlackout(currentState.deviceId)
                }
            } catch (e: Exception) {
                e.printStackTrace()
                // In a real app, you'd handle this error properly
            }
        }
    }
}