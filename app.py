"""Phone As PC Speaker - Main Server Application.

Captures PC audio in real-time and streams it with ultra-low latency to connected
phones over Bluetooth (Bluetooth Tethering/PAN) or Wi-Fi.
"""

import sys
import os
import io
import argparse
import asyncio
import threading
import webbrowser
from aiohttp import web, WSMsgType
import qrcode
from PIL import Image

# Ensure standard UTF-8 console output for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import DEFAULT_PORT, HOST, get_network_ips, get_network_details
from audio_streamer import AudioStreamer

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Global streamer instance
streamer = AudioStreamer()


async def handle_index(request):
    """Serve the mobile player HTML."""
    return web.FileResponse(os.path.join(STATIC_DIR, "index.html"))


async def handle_qr_png(request):
    """Dynamically generate a QR code PNG for the phone to scan."""
    host_header = request.host
    url = f"http://{host_header}/"
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return web.Response(body=buf.getvalue(), content_type="image/png")


async def handle_status(request):
    """Return JSON status of server and connected listeners."""
    return web.json_response({
        "status": "running",
        "connected_listeners": len(streamer.clients),
        "volume_rms": round(streamer.current_volume_rms, 4),
        "sample_rate": streamer.sample_rate,
        "channels": streamer.channels,
        "speaker": streamer.speaker.name if streamer.speaker else "Default",
    })


async def websocket_handler(request):
    """Handle low-latency WebSocket audio streaming."""
    ws = web.WebSocketResponse(heartbeat=15.0)
    await ws.prepare(request)

    # Read channel preference: 1 = Mono (Half bandwidth, best for Bluetooth), 2 = Stereo
    try:
        channels = int(request.query.get("channels", "1"))
    except ValueError:
        channels = 1

    client_ip = request.remote
    channel_label = "Mono (Bandwidth-Optimized)" if channels == 1 else "Stereo"
    print(f"[+] Phone connected from: {client_ip} [{channel_label}]")

    # Register client audio queue
    session = streamer.register_client(channels=channels)

    try:
        while not ws.closed:
            # Wait for audio chunk from loopback capture
            chunk = await session.queue.get()
            # Send binary 16-bit PCM chunk to phone
            await ws.send_bytes(chunk)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[-] Client connection error: {e}")
    finally:
        streamer.unregister_client(session)
        print(f"[-] Phone disconnected: {client_ip}")

    return ws


def create_app():
    """Create and configure the aiohttp web application."""
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/qr.png", handle_qr_png)
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/ws/audio", websocket_handler)
    app.router.add_static("/", STATIC_DIR, show_index=True)
    return app


def start_server_in_thread(loop, app, host, port):
    """Run aiohttp application in the given event loop with port fallback."""
    asyncio.set_event_loop(loop)
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    
    current_port = port
    site = None
    for attempt in range(5):
        try:
            site = web.TCPSite(runner, host, current_port)
            loop.run_until_complete(site.start())
            break
        except OSError:
            current_port += 1

    # Start audio capture
    streamer.start(loop)
    print(f"[*] Audio streaming server active on http://{host}:{current_port}")
    loop.run_forever()


def print_cli_banner(port, ips, net_details):
    """Print clean terminal banner with Bluetooth connection URL and QR Code."""
    bt_ips = net_details.get("bluetooth", [])
    primary_url = f"http://{ips[0]}:{port}"

    print("=" * 64)
    print("      PHONE AS PC SPEAKER - BLUETOOTH AUDIO STREAMER")
    print("=" * 64)
    
    if bt_ips:
        print("\n [✓] BLUETOOTH CONNECTION DETECTED & ACTIVE!")
        print(f"     Direct Bluetooth link: http://{bt_ips[0]}:{port}")
        print("     (Wi-Fi is NOT required - streaming purely over Bluetooth)\n")
    else:
        print("\n [!] No active Bluetooth PAN found yet.")
        print("     To use Pure Bluetooth: Pair phone -> Turn ON Bluetooth Tethering.")

    print("Scan this QR code with your phone camera or open the link:")
    for ip in ips:
        if ip in bt_ips:
            label = "PURE BLUETOOTH (NO WI-FI)"
        else:
            label = "Other Network"
        print(f"  👉 http://{ip}:{port}  [{label}]")
    print("\n" + "-" * 32)
    try:
        qr = qrcode.QRCode(border=1)
        qr.add_data(primary_url)
        qr.print_ascii(invert=True)
    except Exception:
        pass
    print("-" * 32)
    print("[*] Press Ctrl+C in this terminal to stop the server.\n")


def main():
    parser = argparse.ArgumentParser(description="Phone As PC Speaker Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode without GUI window")
    args = parser.parse_args()

    net_details = get_network_details()
    ips = get_network_ips(prefer_bluetooth=True)
    app = create_app()

    loop = asyncio.new_event_loop()
    server_thread = threading.Thread(
        target=start_server_in_thread,
        args=(loop, app, HOST, args.port),
        daemon=True,
    )
    server_thread.start()

    print_cli_banner(args.port, ips, net_details)

    if not args.cli:
        try:
            from gui import launch_gui
            launch_gui(args.port, ips, streamer, net_details)
            return
        except Exception as e:
            print(f"[*] Note: GUI skipped ({e}). Running in terminal mode.")

    # Keep CLI running until Ctrl+C
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down Phone As Speaker...")
        streamer.stop()


if __name__ == "__main__":
    main()
