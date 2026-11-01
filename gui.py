"""Tkinter Desktop Control Panel for Phone As Speaker."""

import io
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import qrcode
from PIL import Image, ImageTk


class DesktopApp:
    def __init__(self, root, port, ips, streamer, net_details=None):
        self.root = root
        self.port = port
        self.ips = ips
        self.streamer = streamer
        self.net_details = net_details or {}
        self.bt_ips = self.net_details.get("bluetooth", [])
        self.current_ip = ips[0]

        self.root.title("Phone As PC Speaker - Bluetooth Mode")
        self.root.geometry("460x670")
        self.root.minsize(440, 620)
        self.root.configure(bg="#0f172a")

        self._apply_styles()
        self._build_ui()
        self._update_qr()
        self._start_meters_loop()

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#0f172a", foreground="#f8fafc", font=("Segoe UI", 10))
        style.configure("TLabel", background="#0f172a", foreground="#f8fafc")
        style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"), foreground="#38bdf8")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 9), foreground="#94a3b8")
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"), foreground="#10b981")
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6)
        style.configure("Accent.TButton", background="#0284c7", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#0369a1")])

    def _build_ui(self):
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Label(container, text="🔊 Phone as PC Speaker", style="Header.TLabel")
        header.pack(anchor="center", pady=(0, 2))

        sub = ttk.Label(container, text="Pure Bluetooth Audio Receiver (No Wi-Fi Needed)", style="Subtitle.TLabel")
        sub.pack(anchor="center", pady=(0, 10))

        # Status badge & Bluetooth indicator
        if self.bt_ips and self.current_ip in self.bt_ips:
            status_text = "● Connected via Pure Bluetooth (No Wi-Fi)"
        else:
            status_text = "● Server Active & Capturing Audio"

        self.status_lbl = ttk.Label(container, text=status_text, style="Status.TLabel")
        self.status_lbl.pack(anchor="center", pady=(0, 12))

        # QR Code frame
        qr_card = tk.Frame(container, bg="#1e293b", bd=1, relief=tk.SOLID)
        qr_card.pack(fill=tk.X, pady=(0, 12))

        self.qr_label = tk.Label(qr_card, bg="#1e293b")
        self.qr_label.pack(pady=10)

        scan_tip = ttk.Label(qr_card, text="Scan with Phone Camera or Open Link Below", style="Subtitle.TLabel")
        scan_tip.pack(pady=(0, 10))

        # Network IP selector
        ip_frame = ttk.Frame(container)
        ip_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(ip_frame, text="Network Adapter / IP:").pack(side=tk.LEFT)
        self.ip_combo = ttk.Combobox(ip_frame, values=self.ips, state="readonly", width=18)
        self.ip_combo.set(self.current_ip)
        self.ip_combo.pack(side=tk.RIGHT, padx=4)
        self.ip_combo.bind("<<ComboboxSelected>>", self._on_ip_change)

        # Current URL display
        self.url_var = tk.StringVar(value=f"http://{self.current_ip}:{self.port}")
        url_entry = ttk.Entry(container, textvariable=self.url_var, state="readonly", font=("Consolas", 10))
        url_entry.pack(fill=tk.X, pady=(0, 8))

        # Button row: Copy URL & Open Browser
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        copy_btn = ttk.Button(btn_frame, text="📋 Copy Link", command=self._copy_link)
        copy_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        open_btn = ttk.Button(btn_frame, text="🌐 Open Browser", command=self._open_browser)
        open_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))

        # Audio VU Level Meter
        meter_card = tk.Frame(container, bg="#1e293b", bd=1, relief=tk.SOLID, padx=10, pady=8)
        meter_card.pack(fill=tk.X, pady=(0, 12))

        meter_header = tk.Frame(meter_card, bg="#1e293b")
        meter_header.pack(fill=tk.X)

        tk.Label(meter_header, text="PC Audio Input Level", bg="#1e293b", fg="#f8fafc", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.listeners_lbl = tk.Label(meter_header, text="0 phone(s) connected", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 9))
        self.listeners_lbl.pack(side=tk.RIGHT)

        self.meter_canvas = tk.Canvas(meter_card, height=14, bg="#090d16", highlightthickness=0)
        self.meter_canvas.pack(fill=tk.X, pady=(6, 0))

        # Bluetooth Guide Help Button
        help_btn = ttk.Button(container, text="📡 Bluetooth Pairing Guide", command=self._show_bt_guide)
        help_btn.pack(fill=tk.X, pady=(0, 6))

    def _update_qr(self):
        url = f"http://{self.current_ip}:{self.port}"
        qr = qrcode.QRCode(box_size=5, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        
        # Resize to crisp 180x180
        img = img.resize((180, 180), Image.Resampling.NEAREST)
        self.qr_photo = ImageTk.PhotoImage(img)
        self.qr_label.configure(image=self.qr_photo)

    def _on_ip_change(self, event=None):
        self.current_ip = self.ip_combo.get()
        self.url_var.set(f"http://{self.current_ip}:{self.port}")
        self._update_qr()

    def _copy_link(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.url_var.get())
        messagebox.showinfo("Copied", f"Link copied to clipboard:\n{self.url_var.get()}")

    def _open_browser(self):
        webbrowser.open(self.url_var.get())

    def _show_bt_guide(self):
        guide = (
            "HOW TO USE OVER BLUETOOTH:\n\n"
            "1. Pair Phone: Go to Windows Settings > Bluetooth & Devices > Add Device, "
            "and pair your smartphone.\n\n"
            "2. Turn on Bluetooth Tethering:\n"
            "   - On Android: Settings > Network/Connections > Mobile Hotspot and Tethering > "
            "turn ON 'Bluetooth tethering'.\n"
            "   - On iPhone: Settings > Personal Hotspot > Allow Others to Join.\n\n"
            "3. Connect on Windows:\n"
            "   - Right-click Bluetooth icon in taskbar tray > 'Join a Personal Area Network'.\n"
            "   - Right-click your paired phone > 'Connect using' > 'Access point'.\n\n"
            "4. Start Listening:\n"
            "   - Open the web link or scan the QR code on your phone!\n\n"
            "* Note: If your phone is connected to the same Wi-Fi, it works instantly without needing Bluetooth tethering."
        )
        messagebox.showinfo("Bluetooth Setup Guide", guide)

    def _start_meters_loop(self):
        def update():
            # Update VU meter
            rms = self.streamer.current_volume_rms
            # Scale non-linearly for natural visual audio response
            level = min(1.0, rms * 4.0)
            
            c_width = self.meter_canvas.winfo_width()
            c_height = self.meter_canvas.winfo_height()
            self.meter_canvas.delete("all")
            
            if c_width > 1:
                fill_w = int(c_width * level)
                if fill_w > 0:
                    # Color shifts from cyan to green to amber if loud
                    color = "#06b6d4" if level < 0.7 else "#f59e0b"
                    self.meter_canvas.create_rectangle(0, 0, fill_w, c_height, fill=color, outline="")

            # Update connected listeners count
            num_clients = len(self.streamer.clients)
            self.listeners_lbl.config(text=f"{num_clients} phone(s) connected")

            self.root.after(50, update)

        self.root.after(50, update)


def launch_gui(port, ips, streamer, net_details=None):
    root = tk.Tk()
    app = DesktopApp(root, port, ips, streamer, net_details)
    root.mainloop()
