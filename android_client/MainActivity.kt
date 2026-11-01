package com.example.phonespeaker

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.io.InputStream
import java.util.UUID

/**
 * Android Audio Receiver Client over Bluetooth RFCOMM / SPP.
 * Receives 16-bit PCM 44.1kHz stereo audio from Windows PC and plays via AudioTrack.
 */
class MainActivity : AppCompatActivity() {

    // Standard SPP UUID
    private val SPP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    
    private var isPlaying = false
    private var bluetoothSocket: BluetoothSocket? = null
    private var audioTrack: AudioTrack? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val btnConnect = findViewById<Button>(R.id.btnConnect)
        val tvStatus = findViewById<TextView>(R.id.tvStatus)

        btnConnect.setOnClickListener {
            if (!isPlaying) {
                connectAndPlay(tvStatus, btnConnect)
            } else {
                stopPlayback(tvStatus, btnConnect)
            }
        }
    }

    private fun connectAndPlay(tvStatus: TextView, btnConnect: Button) {
        val adapter = BluetoothAdapter.getDefaultAdapter() ?: return
        // Find paired PC
        val pairedDevices: Set<BluetoothDevice> = adapter.bondedDevices
        val pcDevice = pairedDevices.firstOrNull { it.name.contains("PC", ignoreCase = true) || it.name.contains("DESKTOP", ignoreCase = true) }
            ?: pairedDevices.firstOrNull()

        if (pcDevice == null) {
            tvStatus.text = "No paired PC found! Pair PC in Settings first."
            return
        }

        tvStatus.text = "Connecting to ${pcDevice.name}..."
        isPlaying = true
        btnConnect.text = "STOP"

        Thread {
            try {
                bluetoothSocket = pcDevice.createRfcommSocketToServiceRecord(SPP_UUID)
                bluetoothSocket?.connect()

                runOnUiThread { tvStatus.text = "Streaming live audio from ${pcDevice.name}!" }

                // Setup Low-Latency AudioTrack
                val sampleRate = 44100
                val minBufferSize = AudioTrack.getMinBufferSize(
                    sampleRate,
                    AudioFormat.CHANNEL_OUT_STEREO,
                    AudioFormat.ENCODING_PCM_16BIT
                )

                audioTrack = AudioTrack.Builder()
                    .setAudioAttributes(
                        AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_MEDIA)
                            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                            .build()
                    )
                    .setAudioFormat(
                        AudioFormat.Builder()
                            .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                            .setSampleRate(sampleRate)
                            .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                            .build()
                    )
                    .setBufferSizeInBytes(minBufferSize)
                    .setPerformanceMode(AudioTrack.PERFORMANCE_MODE_LOW_LATENCY)
                    .build()

                audioTrack?.play()

                val inputStream: InputStream = bluetoothSocket!!.inputStream
                val buffer = ByteArray(2048)

                while (isPlaying) {
                    val bytesRead = inputStream.read(buffer)
                    if (bytesRead > 0) {
                        audioTrack?.write(buffer, 0, bytesRead)
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { tvStatus.text = "Error: ${e.message}" }
            } finally {
                stopPlayback(tvStatus, btnConnect)
            }
        }.start()
    }

    private fun stopPlayback(tvStatus: TextView, btnConnect: Button) {
        isPlaying = false
        runOnUiThread {
            btnConnect.text = "CONNECT TO PC"
            tvStatus.text = "Disconnected"
        }
        try {
            audioTrack?.stop()
            audioTrack?.release()
            bluetoothSocket?.close()
        } catch (_: Exception) {}
    }
}
