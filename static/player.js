// Real-time Anti-Jitter Web Audio Engine for Bluetooth & Local Network
let audioCtx = null;
let gainNode = null;
let analyserNode = null;
let ws = null;
let isPlaying = false;
let nextStartTime = 0;
let wakeLock = null;
let animFrameId = null;

// Channel Mode (1 = Mono/Clear, 2 = Stereo)
let selectedChannels = 1;

// Buffer & Jitter Presets
const presets = {
  low: { preBuffer: 1, delay: 0.045, maxDrift: 0.12, label: "Low Latency (~45ms)" },
  smooth: { preBuffer: 3, delay: 0.100, maxDrift: 0.22, label: "Smooth Bluetooth (~100ms)" },
  stable: { preBuffer: 5, delay: 0.180, maxDrift: 0.35, label: "Rock Solid (~180ms)" }
};
let currentPreset = presets.smooth;
let packetQueue = [];
let isPrebuffering = true;

// UI Elements
const btnPlay = document.getElementById("btnPlay");
const playBtnText = document.getElementById("playBtnText");
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const pulseRing = document.getElementById("pulseRing");
const volumeSlider = document.getElementById("volumeSlider");
const volumeVal = document.getElementById("volumeVal");
const wakeLockToggle = document.getElementById("wakeLockToggle");
const canvas = document.getElementById("visualizerCanvas");
const canvasCtx = canvas.getContext("2d");
const presetButtons = document.querySelectorAll("[data-preset]");
const presetLabel = document.getElementById("presetLabel");
const latencyStat = document.getElementById("latencyStat");
const keepAliveAudio = document.getElementById("keepAliveAudio");
const btnMono = document.getElementById("btnMono");
const btnStereo = document.getElementById("btnStereo");
const channelLabel = document.getElementById("channelLabel");

// Canvas size
function resizeCanvas() {
  canvas.width = canvas.clientWidth * window.devicePixelRatio;
  canvas.height = canvas.clientHeight * window.devicePixelRatio;
}
window.addEventListener("resize", resizeCanvas);
resizeCanvas();

// Jitter Buffer Preset Selection
presetButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    presetButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const mode = btn.dataset.preset;
    currentPreset = presets[mode];
    presetLabel.textContent = currentPreset.label;
    latencyStat.textContent = `Buffer: ~${Math.round(currentPreset.delay * 1000)}ms`;
    // Resync buffer smoothly
    nextStartTime = 0;
    isPrebuffering = true;
    packetQueue = [];
  });
});

// Channel Mode Selection (Mono vs Stereo)
function setChannelMode(channels) {
  selectedChannels = channels;
  if (channels === 1) {
    btnMono.classList.add("active");
    btnStereo.classList.remove("active");
    channelLabel.textContent = "Bluetooth Clear (Mono)";
    latencyStat.textContent = `Format: 44.1kHz Clear Mono`;
  } else {
    btnStereo.classList.add("active");
    btnMono.classList.remove("active");
    channelLabel.textContent = "Full Stereo (High Bandwidth)";
    latencyStat.textContent = `Format: 44.1kHz Stereo`;
  }

  // Reconnect if currently playing to change server stream immediately
  if (isPlaying && ws) {
    ws.close();
  }
}

btnMono.addEventListener("click", () => setChannelMode(1));
btnStereo.addEventListener("click", () => setChannelMode(2));

// Wake Lock
async function requestWakeLock() {
  if ("wakeLock" in navigator && wakeLockToggle.checked) {
    try {
      wakeLock = await navigator.wakeLock.request("screen");
    } catch (err) {}
  }
}

function releaseWakeLock() {
  if (wakeLock) {
    wakeLock.release().catch(() => {});
    wakeLock = null;
  }
}

wakeLockToggle.addEventListener("change", () => {
  if (wakeLockToggle.checked && isPlaying) {
    requestWakeLock();
  } else {
    releaseWakeLock();
  }
});

// Master Volume Slider
volumeSlider.addEventListener("input", (e) => {
  const val = e.target.value;
  volumeVal.textContent = `${val}%`;
  if (gainNode && audioCtx) {
    gainNode.gain.setValueAtTime(val / 100, audioCtx.currentTime);
  }
});

// AudioContext Initialization
function initAudio() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContext({ sampleRate: 44100, latencyHint: "playback" });
    gainNode = audioCtx.createGain();
    analyserNode = audioCtx.createAnalyser();
    analyserNode.fftSize = 64;
    analyserNode.smoothingTimeConstant = 0.8;

    gainNode.gain.value = volumeSlider.value / 100;
    gainNode.connect(analyserNode);
    analyserNode.connect(audioCtx.destination);
  }
  if (audioCtx.state === "suspended") {
    audioCtx.resume();
  }
}

// Convert PCM to Web AudioBuffer
function decodePcmBuffer(arrayBuffer) {
  const int16Array = new Int16Array(arrayBuffer);

  if (selectedChannels === 1) {
    // Mono: half bandwidth, zero Bluetooth packet drop
    const numFrames = int16Array.length;
    const audioBuffer = audioCtx.createBuffer(1, numFrames, 44100);
    const channelData = audioBuffer.getChannelData(0);
    for (let i = 0; i < numFrames; i++) {
      channelData[i] = int16Array[i] / 32768.0;
    }
    return audioBuffer;
  } else {
    // Stereo
    const numFrames = int16Array.length / 2;
    const audioBuffer = audioCtx.createBuffer(2, numFrames, 44100);
    const leftChannel = audioBuffer.getChannelData(0);
    const rightChannel = audioBuffer.getChannelData(1);
    for (let i = 0; i < numFrames; i++) {
      leftChannel[i] = int16Array[i * 2] / 32768.0;
      rightChannel[i] = int16Array[i * 2 + 1] / 32768.0;
    }
    return audioBuffer;
  }
}

// Schedule audio buffer into the Web Audio timeline
function scheduleAudioBuffer(audioBuffer) {
  const now = audioCtx.currentTime;

  if (nextStartTime < now) {
    // Buffer underrun occurred: restart timeline with current delay
    nextStartTime = now + currentPreset.delay;
  } else if (nextStartTime > now + currentPreset.maxDrift) {
    // Lag accumulated: gently clamp to avoid latency drift
    nextStartTime = now + currentPreset.delay;
  }

  const source = audioCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(gainNode);
  source.start(nextStartTime);

  nextStartTime += audioBuffer.duration;
}

// WebSocket Connection & Stream Ingestion
function connectWebSocket() {
  updateStatus("connecting", "Connecting via Bluetooth...");

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/audio?channels=${selectedChannels}`;

  ws = new WebSocket(wsUrl);
  ws.binaryType = "arraybuffer";

  isPrebuffering = true;
  packetQueue = [];
  nextStartTime = 0;

  ws.onopen = () => {
    updateStatus("connected", "Streaming PC Audio Cleanly");
  };

  ws.onmessage = (event) => {
    if (!isPlaying || !audioCtx) return;

    const audioBuffer = decodePcmBuffer(event.data);
    if (!audioBuffer) return;

    // Pre-buffering phase to absorb initial Bluetooth radio delay
    if (isPrebuffering) {
      packetQueue.push(audioBuffer);
      if (packetQueue.length >= currentPreset.preBuffer) {
        isPrebuffering = false;
        nextStartTime = audioCtx.currentTime + currentPreset.delay;
        while (packetQueue.length > 0) {
          scheduleAudioBuffer(packetQueue.shift());
        }
      }
      return;
    }

    scheduleAudioBuffer(audioBuffer);
  };

  ws.onerror = () => {};

  ws.onclose = () => {
    if (isPlaying) {
      updateStatus("connecting", "Reconnecting...");
      setTimeout(() => {
        if (isPlaying) connectWebSocket();
      }, 1000);
    } else {
      updateStatus("disconnected", "Stopped");
    }
  };
}

// Start / Stop Handlers
async function startPlayback() {
  try {
    initAudio();
    isPlaying = true;
    btnPlay.classList.add("playing");
    playBtnText.textContent = "STOP AUDIO";
    pulseRing.classList.add("active");

    keepAliveAudio.play().catch(() => {});
    requestWakeLock();

    connectWebSocket();
    startVisualizer();
  } catch (err) {
    console.error("Playback start error:", err);
    alert("Audio initialization error: " + err.message);
    stopPlayback();
  }
}

function stopPlayback() {
  isPlaying = false;
  btnPlay.classList.remove("playing");
  playBtnText.textContent = "START AUDIO";
  pulseRing.classList.remove("active");

  if (ws) {
    ws.close();
    ws = null;
  }

  keepAliveAudio.pause();
  releaseWakeLock();
  updateStatus("disconnected", "Tap Start to Listen");
  packetQueue = [];
  nextStartTime = 0;
  isPrebuffering = true;
}

btnPlay.addEventListener("click", () => {
  if (isPlaying) {
    stopPlayback();
  } else {
    startPlayback();
  }
});

function updateStatus(state, message) {
  statusBadge.className = `status-badge ${state}`;
  statusText.textContent = message;
}

// Live Visualizer
function startVisualizer() {
  const dataArray = new Uint8Array(analyserNode.frequencyBinCount);

  function draw() {
    if (!isPlaying) {
      canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    animFrameId = requestAnimationFrame(draw);
    analyserNode.getByteFrequencyData(dataArray);

    canvasCtx.fillStyle = "#090d16";
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

    const barCount = 32;
    const barWidth = (canvas.width / barCount) * 0.75;
    const gap = (canvas.width / barCount) * 0.25;

    for (let i = 0; i < barCount; i++) {
      const value = dataArray[i * 2] || 0;
      const percent = value / 255;
      const barHeight = Math.max(4, percent * (canvas.height - 10));

      const x = i * (barWidth + gap) + gap / 2;
      const y = canvas.height - barHeight;

      const gradient = canvasCtx.createLinearGradient(0, y, 0, canvas.height);
      gradient.addColorStop(0, "#06b6d4");
      gradient.addColorStop(1, "#3b82f6");

      canvasCtx.fillStyle = gradient;
      canvasCtx.beginPath();
      canvasCtx.roundRect(x, y, barWidth, barHeight, [4, 4, 0, 0]);
      canvasCtx.fill();
    }
  }

  draw();
}
