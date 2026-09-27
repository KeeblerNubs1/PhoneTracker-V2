# Android Agent

Implement the agent as a standard Android application using Kotlin.

Required behavior:
1. Explain location collection before requesting permission.
2. Request Android location permission through the normal system dialog.
3. Show an ongoing foreground-service notification while tracking.
4. Provide Start/Stop controls.
5. Display the enrolled device ID and server URL.
6. Send only the location and health fields configured by the user.
7. Allow the user to revoke tracking by stopping the service or uninstalling the app.

Recommended Android components:
- Kotlin
- Jetpack Compose
- Fused Location Provider
- Foreground Service
- Android Keystore for local secrets
- HTTPS/TLS for transport

Do not implement hidden services, stealth persistence, accessibility abuse, SMS interception, call interception, credential collection, microphone/camera activation without visible consent, exploit delivery, or bypasses of Android security controls.
