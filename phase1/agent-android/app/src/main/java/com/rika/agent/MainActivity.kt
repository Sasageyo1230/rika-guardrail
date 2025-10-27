// agent-android/app/src/main/java/com/rika/agent/MainActivity.kt
package com.rika.agent

import android.Manifest
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.rika.agent.service.RikaAgentService
import com.rika.agent.ui.theme.RikaAgentTheme
import com.rika.agent.viewmodel.MainViewModel

class MainActivity : ComponentActivity() {
    
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        // Handle permission results
        val allGranted = permissions.values.all { it }
        if (allGranted) {
            startAgentService()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            RikaAgentTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainScreen(
                        onStartService = { requestPermissionsAndStart() },
                        onStopService = { stopAgentService() }
                    )
                }
            }
        }
    }

    private fun requestPermissionsAndStart() {
        val permissions = arrayOf(
            Manifest.permission.INTERNET,
            Manifest.permission.ACCESS_NETWORK_STATE,
            Manifest.permission.WAKE_LOCK,
            Manifest.permission.RECEIVE_BOOT_COMPLETED,
            Manifest.permission.FOREGROUND_SERVICE,
            Manifest.permission.POST_NOTIFICATIONS
        )
        
        requestPermissionLauncher.launch(permissions)
    }

    private fun startAgentService() {
        val intent = Intent(this, RikaAgentService::class.java)
        startForegroundService(intent)
    }

    private fun stopAgentService() {
        val intent = Intent(this, RikaAgentService::class.java)
        stopService(intent)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onStartService: () -> Unit,
    onStopService: () -> Unit,
    viewModel: MainViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        
        // Header
        Text(
            text = "🤖 Rika Agent",
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(top = 32.dp)
        )
        
        Text(
            text = "Android v0.1.0",
            fontSize = 16.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(32.dp))

        // Status Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = if (uiState.isServiceRunning) 
                    MaterialTheme.colorScheme.primaryContainer
                else 
                    MaterialTheme.colorScheme.errorContainer
            )
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = if (uiState.isServiceRunning) "🟢 Active" else "🔴 Inactive",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Medium
                )
                
                if (uiState.isEnrolled) {
                    Text(
                        text = "Device ID: ${uiState.deviceId}",
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 8.dp)
                    )
                }
                
                if (uiState.lastHeartbeat.isNotEmpty()) {
                    Text(
                        text = "Last heartbeat: ${uiState.lastHeartbeat}",
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }
        }

        // Controls
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Button(
                onClick = onStartService,
                modifier = Modifier.weight(1f),
                enabled = !uiState.isServiceRunning
            ) {
                Text("Start Agent")
            }
            
            Button(
                onClick = onStopService,
                modifier = Modifier.weight(1f),
                enabled = uiState.isServiceRunning,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.error
                )
            ) {
                Text("Stop Agent")
            }
        }

        // Configuration Card
        Card(
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(
                    text = "Configuration",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                
                Text(
                    text = "Core API: ${uiState.coreApiUrl}",
                    fontSize = 14.sp
                )
                
                Text(
                    text = "Status: ${if (uiState.isConnected) "Connected" else "Disconnected"}",
                    fontSize = 14.sp,
                    modifier = Modifier.padding(top = 4.dp)
                )
            }
        }

        // Emergency Blackout Button
        Spacer(modifier = Modifier.height(16.dp))
        
        Button(
            onClick = { viewModel.triggerBlackout() },
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.error
            ),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = "🚨 EMERGENCY BLACKOUT",
                fontWeight = FontWeight.Bold
            )
        }
        
        Text(
            text = "This will shut down all Rika agents immediately",
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}