import sounddevice as sd, numpy as np

for i in range(40):
    try:
        info = sd.query_devices(i)
        if info['max_input_channels'] > 0:
            hostapi = sd.query_hostapis(info['hostapi'])
            print(f"  Device {i}: '{info['name']}' | API: {hostapi['name']} | SR: {info['default_samplerate']}")
    except Exception:
        pass
