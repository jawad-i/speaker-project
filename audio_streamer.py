"""Windows WASAPI Audio Capture Engine and Stream Distributor."""

import asyncio
import threading
import time
import numpy as np
import soundcard as sc
from config import SAMPLE_RATE, CHANNELS, BLOCK_SIZE, CLIENT_QUEUE_MAXSIZE


class ClientSession:
    def __init__(self, queue: asyncio.Queue, channels: int = 1):
        self.queue = queue
        self.channels = channels  # 1 = Mono (Half bandwidth, crystal-clear on Bluetooth), 2 = Stereo


class AudioStreamer:
    def __init__(self, sample_rate=SAMPLE_RATE, channels=CHANNELS, block_size=BLOCK_SIZE):
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        self.running = False
        self.is_paused = False
        self.clients = set()
        self.lock = threading.Lock()
        self.current_volume_rms = 0.0
        self.capture_thread = None
        self.loop = None
        self.speaker = None

    def get_devices(self):
        """List available output speakers."""
        try:
            return sc.all_speakers()
        except Exception as e:
            print(f"Error enumerating speakers: {e}")
            return []

    def start(self, loop: asyncio.AbstractEventLoop, speaker_id=None):
        """Start WASAPI audio capture in background thread."""
        if self.running:
            return
        self.loop = loop
        self.running = True

        if speaker_id:
            self.speaker = sc.get_speaker(speaker_id)
        else:
            self.speaker = sc.default_speaker()

        self.capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.capture_thread.start()

    def stop(self):
        """Stop audio capture."""
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)

    def register_client(self, channels: int = 1):
        """Register a new websocket client with its desired channel mode."""
        q = asyncio.Queue(maxsize=CLIENT_QUEUE_MAXSIZE)
        session = ClientSession(queue=q, channels=channels)
        with self.lock:
            self.clients.add(session)
        return session

    def unregister_client(self, session: ClientSession):
        """Unregister a client session."""
        with self.lock:
            self.clients.discard(session)

    def _capture_worker(self):
        """Worker thread running WASAPI loopback with optimized Bluetooth packet sizing."""
        print(f"[*] Starting WASAPI loopback on: {self.speaker.name} (BlockSize: {self.block_size})")
        while self.running:
            try:
                mic = sc.get_microphone(id=str(self.speaker.id), include_loopback=True)
                with mic.recorder(samplerate=self.sample_rate, channels=self.channels, blocksize=self.block_size) as rec:
                    while self.running:
                        # Record one audio chunk
                        data = rec.record(numframes=self.block_size)

                        # RMS Volume calculation
                        if self.is_paused:
                            data = np.zeros_like(data)
                            rms = 0.0
                        else:
                            rms = float(np.sqrt(np.mean(data ** 2)))
                        self.current_volume_rms = rms

                        with self.lock:
                            if not self.clients:
                                continue
                            active_sessions = list(self.clients)

                        # Pre-encode stereo and mono
                        stereo_bytes = np.clip(data * 32767.0, -32768, 32767).astype(np.int16).tobytes()
                        mono_data = np.mean(data, axis=1)
                        mono_bytes = np.clip(mono_data * 32767.0, -32768, 32767).astype(np.int16).tobytes()

                        for session in active_sessions:
                            payload = mono_bytes if session.channels == 1 else stereo_bytes
                            if self.loop and self.loop.is_running():
                                self.loop.call_soon_threadsafe(self._push_to_client, session.queue, payload)

            except Exception as e:
                print(f"[!] Audio loopback error: {e}. Retrying in 1.0s...")
                time.sleep(1.0)

    def _push_to_client(self, q: asyncio.Queue, chunk: bytes):
        """Safely push chunk to queue with high elasticity."""
        if q.full():
            try:
                q.get_nowait()  # Drop oldest frame only if client is severely backed up
            except asyncio.QueueEmpty:
                pass
        try:
            q.put_nowait(chunk)
        except asyncio.QueueFull:
            pass
