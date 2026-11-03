import sounddevice as sd, numpy as np

# Test Stereo Mix via MME - Microsoft Sound Mapper captures system output
# Microsoft Sound Mapper (device 0) routes through Windows default device

# Try MME Microsoft Sound Mapper Input while audio plays
print("Play some audio now! Testing MME capture...")

# First try WASAPI loopback workaround - open output device and capture it
# Use sounddevice's WASAPI loopback mode on speakers
try:
    print("\nTrying sounddevice WASAPI loopback...")
    # In sounddevice, WASAPI loopback = open an OUTPUT device as input
    with sd.InputStream(device=8, channels=2, samplerate=48000, dtype='float32',
                        extra_settings=sd.WasapiSettings(exclusive=False)) as stream:
        for i in range(5):
            data, _ = stream.read(2048)
            print(f"Block {i}: RMS={np.sqrt(np.mean(data**2)):.6f}")
except Exception as e:
    print(f"WASAPI loopback failed: {e}")

# Try soundcard with different blocksize
try:
    print("\nTrying soundcard loopback with smaller blocksize...")
    import soundcard as sc
    spk = sc.default_speaker()
    mic = sc.get_microphone(id=str(spk.id), include_loopback=True)
    with mic.recorder(samplerate=48000, channels=2, blocksize=4096) as rec:
        for i in range(5):
            data = rec.record(numframes=4096)
            print(f"Block {i}: RMS={np.sqrt(np.mean(data**2)):.6f} shape={data.shape}")
except Exception as e:
    print(f"soundcard loopback failed: {e}")
