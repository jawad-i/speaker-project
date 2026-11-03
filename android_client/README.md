# BlueBridge Android Audio Receiver (Optional Companion)

If you prefer a native Android APK instead of opening the mobile Web Player in your phone browser, this directory provides the native implementation using Android's low-latency `AudioTrack` API.

### How it works:
1. Pairs with your Windows PC via Bluetooth.
2. Opens an RFCOMM / SPP Bluetooth Socket (`00001101-0000-1000-8000-00805F9B34FB`).
3. Streams uncompressed 16-bit 44.1kHz PCM stereo audio from `bluetooth_rfcomm.py`.
4. Writes directly to hardware-accelerated `AudioTrack(PERFORMANCE_MODE_LOW_LATENCY)`.

### Permissions required in `AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
```

> **Note**: For zero-installation on your phone, simply run the primary server (`python app.py` or double-click `start.bat`) and open the link/QR code in your mobile browser. The Web Audio API provides identical sub-30ms performance with no build steps required!
