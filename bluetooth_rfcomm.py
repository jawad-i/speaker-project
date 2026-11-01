"""Optional Direct Bluetooth RFCOMM (Serial Port Profile) Audio Server.

This script demonstrates transmitting raw PCM audio directly over a Bluetooth RFCOMM
socket to a paired Android device running a Bluetooth SPP client.
"""

import socket
import threading
import time
import numpy as np
import soundcard as sc
from config import SAMPLE_RATE, CHANNELS, BLOCK_SIZE


def run_bluetooth_rfcomm_server(channel=1):
    """Start Bluetooth RFCOMM listener for paired mobile devices."""
    if not hasattr(socket, "AF_BLUETOOTH"):
        print("[!] AF_BLUETOOTH not supported on this Python build.")
        return

    server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    
    # Bind to local Bluetooth adapter (BDADDR_ANY is "00:00:00:00:00:00" or empty string)
    try:
        server_sock.bind(("", channel))
        server_sock.listen(1)
        print(f"[*] Bluetooth RFCOMM Server listening on channel {channel}...")
        print("[*] Waiting for paired phone to connect via Bluetooth SPP...")
    except Exception as e:
        print(f"[!] Bluetooth bind error: {e}")
        return

    spk = sc.default_speaker()
    mic = sc.get_microphone(id=str(spk.id), include_loopback=True)

    while True:
        try:
            client_sock, client_info = server_sock.accept()
            print(f"[+] Phone connected via Bluetooth RFCOMM: {client_info}")

            # Capture and stream audio directly
            with mic.recorder(samplerate=SAMPLE_RATE, channels=CHANNELS, blocksize=BLOCK_SIZE) as rec:
                while True:
                    data = rec.record(numframes=BLOCK_SIZE)
                    pcm_bytes = np.clip(data * 32767.0, -32768, 32767).astype(np.int16).tobytes()
                    client_sock.sendall(pcm_bytes)

        except (ConnectionResetError, BrokenPipeError):
            print("[-] Phone disconnected from Bluetooth RFCOMM.")
        except KeyboardInterrupt:
            print("[*] Stopping RFCOMM server.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")
            time.sleep(1)
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    server_sock.close()


if __name__ == "__main__":
    run_bluetooth_rfcomm_server()
