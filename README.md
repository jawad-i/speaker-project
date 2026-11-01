# 🔊 Phone as PC Speaker (Pure Bluetooth Audio Streamer)

Turn your phone into a real-time, low-latency wireless speaker for your Windows PC **using only Bluetooth — zero Wi-Fi required!**

Whatever audio plays on your PC (YouTube, movies, music, games) is captured live via Windows WASAPI loopback and streamed directly to your phone.

---

## 🔵 Pure Bluetooth Mode (No Wi-Fi Needed)

Your PC and phone connect directly over Bluetooth using **Bluetooth Tethering / PAN (Personal Area Network)**:

1. **Wi-Fi is NOT required**: You can completely turn Wi-Fi OFF on both your phone and PC.
2. **Bandwidth**: Bluetooth provides 2–3 Mbps link speed, which is plenty for crystal-clear 44.1 kHz stereo audio (requires ~0.7 Mbps).
3. **Latency**: Sub-30ms with hardware Web Audio API acceleration.

---

## 🚀 How to Run in Pure Bluetooth Mode

### Step 1: Connect Phone to PC via Bluetooth
1. On your phone, go to **Settings > Bluetooth**, pair with your Windows PC.
2. On your phone, turn on **Bluetooth Tethering**:
   - **Android**: Go to `Settings` &rarr; `Connections / Network` &rarr; `Mobile Hotspot and Tethering` &rarr; turn **ON** `Bluetooth tethering`.
   - **iPhone**: Go to `Settings` &rarr; `Personal Hotspot` &rarr; turn **ON** `Allow Others to Join`.
3. On your Windows PC:
   - In the taskbar system tray (bottom-right), right-click the **Bluetooth icon** &rarr; click **Join a Personal Area Network**.
   - Right-click your paired phone name &rarr; select **Connect using** &rarr; **Access point**.

### Step 2: Start the Audio Server
In your PowerShell terminal:
```powershell
.\run.ps1
```
*(Or double-click `start.bat`)*

The server will automatically detect your active Bluetooth link and display:
```
[✓] BLUETOOTH CONNECTION DETECTED & ACTIVE!
    Direct Bluetooth link: http://10.85.34.157:5000
    (Wi-Fi is NOT required - streaming purely over Bluetooth)
```

### Step 3: Listen on Your Phone
1. Open the phone browser (Chrome, Safari, Firefox) and go to:
   ```
   http://10.85.34.157:5000
   ```
   *(Or scan the QR code displayed on your PC screen)*
2. Tap **START AUDIO**.
3. Any sound playing on your PC will immediately play out of your phone speaker!
