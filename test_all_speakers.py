import soundcard as sc, sounddevice as sd, numpy as np

print("=== ALL SOUNDCARD SPEAKERS ===")
for s in sc.all_speakers():
    try:
        mic = sc.get_microphone(id=str(s.id), include_loopback=True)
        with mic.recorder(samplerate=44100, channels=None, blocksize=4096) as rec:
            data = rec.record(numframes=8192)
            rms = float(np.sqrt(np.mean(data**2)))
        marker = " <-- HAS AUDIO" if rms > 0.0001 else ""
        print(f"  Speaker: {s.name}, Channels: {data.shape[1]}, RMS: {rms:.6f}{marker}")
    except Exception as e:
        print(f"  Speaker: {s.name} -> Error: {e}")
