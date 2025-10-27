# Rika Android Agent v0.1.0

Android agent skeleton for the Rika ecosystem. This is a basic implementation that provides core functionality for device enrollment, heartbeat monitoring, and emergency blackout features.

## Features

- **Device Enrollment**: Automatic device registration with Rika Core
- **Heartbeat Monitoring**: Regular status updates to Core API
- **Foreground Service**: Persistent background operation
- **Emergency Blackout**: Manual trigger for system shutdown
- **Boot Receiver**: Auto-start on device boot
- **Material 3 UI**: Modern Android interface

## Architecture

```
app/src/main/java/com/rika/agent/
├── MainActivity.kt              # Main UI activity
├── data/
│   ├── RikaRepository.kt       # Data layer and API communication
│   ├── api/
│   │   └── RikaApiService.kt   # Retrofit API interface
│   └── model/
│       └── Models.kt           # Data models
├── service/
│   └── RikaAgentService.kt     # Background service
├── receiver/
│   └── BootReceiver.kt         # Boot completion receiver
├── util/
│   └── DeviceInfoProvider.kt   # Device fingerprinting
├── viewmodel/
│   └── MainViewModel.kt        # UI state management
└── ui/theme/                   # Material 3 theming
```

## Configuration

Update the Core API URL in `RikaRepository.kt`:
```kotlin
private const val DEFAULT_CORE_API_URL = "http://YOUR_PC_IP:8000"
```

## Permissions

The app requires these permissions:
- `INTERNET` - API communication
- `ACCESS_NETWORK_STATE` - Network status monitoring
- `WAKE_LOCK` - Prevent device sleep
- `RECEIVE_BOOT_COMPLETED` - Auto-start on boot
- `FOREGROUND_SERVICE` - Background operation
- `POST_NOTIFICATIONS` - Service notifications

## Installation

1. Open project in Android Studio
2. Update Core API URL configuration
3. Build and install APK
4. Grant required permissions
5. Start agent service

## Integration with Rika Core

The agent automatically:
1. Enrolls with Core API on first run
2. Sends heartbeats every 5 seconds
3. Monitors device state and battery
4. Responds to blackout events

## Future Enhancements

- NATS messaging integration
- Voice command support
- Advanced device control
- Biometric authentication
- Location tracking
- Screen sharing capabilities

## Dependencies

- Retrofit 2.9.0 (HTTP client)
- Jetpack Compose (Modern UI)
- Coroutines (Async operations)
- DataStore (Local storage)
- Work Manager (Background tasks)

## Notes

This is a skeleton implementation designed for Phase 1 of the Rika Project. It provides the foundation for more advanced mobile agent capabilities.