"""Configuration settings for Phone As Speaker server."""

import socket
import subprocess
import json

# Audio Capture Settings
SAMPLE_RATE = 44100  # 44.1 kHz CD-quality (optimal for Bluetooth bandwidth & low latency)
CHANNELS = 2         # Default capture 2 channels
BLOCK_SIZE = 2048    # 2048 frames (~46.4ms per packet): reduces packet overhead by 50% for Bluetooth

# Network & Server Settings
DEFAULT_PORT = 5000
HOST = "0.0.0.0"     # Listen on all network interfaces including Bluetooth PAN

# Queue settings
CLIENT_QUEUE_MAXSIZE = 32  # High elasticity queue to prevent packet dropping during Bluetooth hops


def get_network_details():
    """Detect Bluetooth Network and other adapters on Windows."""
    bt_ips = []
    other_ips = []

    # Query PowerShell for accurate Windows adapter aliases (Bluetooth PAN vs Wi-Fi)
    try:
        cmd = 'Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress, InterfaceAlias, InterfaceDescription | ConvertTo-Json'
        out = subprocess.check_output(['powershell', '-NoProfile', '-Command', cmd], text=True)
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        for d in data:
            alias = d.get('InterfaceAlias') or ''
            desc = d.get('InterfaceDescription') or ''
            ip = d.get('IPAddress') or ''
            if not ip or ip.startswith('127.'):
                continue
            if 'Bluetooth' in alias or 'Bluetooth' in desc:
                if not ip.startswith('169.254.'):
                    bt_ips.append(ip)
            elif not ip.startswith('169.254.'):
                other_ips.append(ip)
    except Exception:
        pass

    # Fallback standard socket enumeration if needed
    if not bt_ips and not other_ips:
        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if not ip.startswith('127.'):
                    other_ips.append(ip)
        except Exception:
            pass

    return {
        "bluetooth": bt_ips,
        "other": other_ips,
    }


def get_network_ips(prefer_bluetooth=True):
    """Retrieve IPv4 addresses, prioritizing pure Bluetooth if present."""
    details = get_network_details()
    bt = details["bluetooth"]
    other = details["other"]

    ordered = []
    if prefer_bluetooth and bt:
        ordered.extend(bt)
        ordered.extend(other)
    else:
        ordered.extend(other)
        ordered.extend(bt)

    if not ordered:
        ordered.append("127.0.0.1")

    return ordered
