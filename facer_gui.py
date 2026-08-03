#!/usr/bin/env python3
"""
Shipsar Acer Predator RGB & Turbo Control Center
Developed by Shipsar Developers 🇮🇳 | Lead Developer: Vijay Kumar | Website: https://shipsar.in
Native GUI for Acer Predator, Helios, and Nitro gaming laptops on Linux.
"""

import json
import os
import platform
import sys
import math
import subprocess
import threading
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, simpledialog

# System constants
PAYLOAD_SIZE = 16
CHARACTER_DEVICE = "/dev/acer-gkbbl-0"
PAYLOAD_SIZE_STATIC_MODE = 4
CHARACTER_DEVICE_STATIC = "/dev/acer-gkbbl-static-0"

CONFIG_DIRECTORY = str(Path.home()) + "/.config/predator/saved profiles"
DRIVER_VERSION = "1.20260725-02"
FACER_RGB_SCRIPT = str(Path(__file__).resolve().parent / "facer_rgb.py")
DEVELOPER_EMAIL = "info@shipsar.in"

# Effect Modes
MODES = [
    {"id": 0, "name": "Static Mode", "desc": "Per-zone static RGB coloring (Zones 1-4)"},
    {"id": 1, "name": "Breathing", "desc": "Pulsing backlight with single color"},
    {"id": 2, "name": "Neon", "desc": "Smooth rainbow spectrum cycle across zones"},
    {"id": 3, "name": "Wave", "desc": "Color wave animation moving across keyboard"},
    {"id": 4, "name": "Shifting", "desc": "Color shift animation with custom color"},
    {"id": 5, "name": "Zoom", "desc": "Concentric expanding color effect"}
]

PRESET_COLORS = [
    ("Red", "#FF0000", (255, 0, 0)),
    ("Green", "#00FF00", (0, 255, 0)),
    ("Blue", "#0088FF", (0, 136, 255)),
    ("Cyan", "#00FFFF", (0, 255, 255)),
    ("Magenta", "#FF00FF", (255, 0, 255)),
    ("Yellow", "#FFFF00", (255, 255, 0)),
    ("Orange", "#FF8800", (255, 136, 0)),
    ("Purple", "#8800FF", (136, 0, 255)),
    ("White", "#FFFFFF", (255, 255, 255)),
    ("Off", "#000000", (0, 0, 0))
]


class PredatorRGBApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shipsar Acer Predator RGB Control")
        self.root.geometry("1020x760")
        self.root.minsize(960, 700)

        # State Variables
        self.is_dark_mode = tk.BooleanVar(value=True)
        self.current_mode = tk.IntVar(value=3)  # Default: Wave
        self.selected_zone = tk.IntVar(value=1) # Default: Zone 1
        self.speed = tk.IntVar(value=4)
        self.brightness = tk.IntVar(value=100)
        self.direction = tk.IntVar(value=1)     # 1: Right to Left, 2: Left to Right
        self.auto_apply = tk.BooleanVar(value=True)
        self.turbo_mode = tk.BooleanVar(value=False)
        self.device_status_reason = None

        # RGB Colors for Zones (Static mode support per zone)
        self.zone_colors = {
            1: (0, 210, 255),
            2: (0, 150, 255),
            3: (0, 100, 255),
            4: (0, 210, 255)
        }

        # Dynamic mode global RGB color
        self.dynamic_red = tk.IntVar(value=0)
        self.dynamic_green = tk.IntVar(value=210)
        self.dynamic_blue = tk.IntVar(value=255)

        self.animation_phase = 0.0
        self.anim_job = None
        self._app_icon = None

        # Setup Theme & UI
        self.setup_theme()
        self.build_ui()
        self.ensure_config_dir()
        self.refresh_profiles()
        self.check_device_status()
        self.start_animation()

    def setup_theme(self):
        """Setup custom theme (Dark or Light mode)."""
        try:
            icon_paths = [
                Path(__file__).parent / "public" / "logo.png",
                Path("/opt/shipsar-developers/acer-rgb-controller/public/logo.png"),
                Path("/usr/share/pixmaps/shipsar-acer-rgb.png")
            ]
            for ipath in icon_paths:
                if ipath.exists():
                    self._app_icon = tk.PhotoImage(file=str(ipath))
                    self.root.iconphoto(True, self._app_icon)
                    break
        except Exception:
            pass

        if self.is_dark_mode.get():
            # Dark Theme Palette
            self.colors = {
                "bg_dark": "#12151e",
                "bg_card": "#1b1f2e",
                "bg_input": "#242a3e",
                "accent_cyan": "#00d2ff",
                "accent_blue": "#0072ff",
                "text_light": "#e6edf3",
                "text_muted": "#8b949e",
                "border": "#2d344b",
                "success": "#2ed573",
                "warning": "#ffa502",
                "danger": "#ff4757"
            }
        else:
            # Light Theme Palette
            self.colors = {
                "bg_dark": "#f4f6fb",
                "bg_card": "#ffffff",
                "bg_input": "#e2e8f0",
                "accent_cyan": "#0284c7",
                "accent_blue": "#2563eb",
                "text_light": "#1e293b",
                "text_muted": "#64748b",
                "border": "#cbd5e1",
                "success": "#16a34a",
                "warning": "#d97706",
                "danger": "#dc2626"
            }

        self.root.configure(bg=self.colors["bg_dark"])

        style = ttk.Style()
        style.theme_use('clam')

        # Frame styles
        style.configure("TFrame", background=self.colors["bg_dark"])
        style.configure("Card.TFrame", background=self.colors["bg_card"], relief="flat")

        # Label styles
        style.configure("TLabel", background=self.colors["bg_dark"], foreground=self.colors["text_light"], font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=self.colors["bg_card"], foreground=self.colors["text_light"], font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=self.colors["bg_dark"], foreground=self.colors["accent_cyan"], font=("Segoe UI", 16, "bold"))
        style.configure("Subtitle.TLabel", background=self.colors["bg_dark"], foreground=self.colors["text_muted"], font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=self.colors["bg_card"], foreground=self.colors["accent_cyan"], font=("Segoe UI", 11, "bold"))
        style.configure("Badge.TLabel", background=self.colors["bg_input"], foreground=self.colors["accent_cyan"], font=("Segoe UI", 9, "bold"))

        # Radiobutton styles
        style.configure("TRadiobutton", background=self.colors["bg_card"], foreground=self.colors["text_light"], font=("Segoe UI", 10))
        style.map("TRadiobutton", background=[("active", self.colors["bg_card"])])

        # Checkbutton styles
        style.configure("TCheckbutton", background=self.colors["bg_card"], foreground=self.colors["text_light"], font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", self.colors["bg_card"])])

        # Button styles
        style.configure("Primary.TButton", background=self.colors["accent_blue"], foreground="#ffffff", font=("Segoe UI", 10, "bold"), padding=(12, 6))
        style.map("Primary.TButton", background=[("active", self.colors["accent_cyan"]), ("pressed", "#0055cc")])

        style.configure("Secondary.TButton", background=self.colors["bg_input"], foreground=self.colors["text_light"], font=("Segoe UI", 9), padding=(8, 4))
        style.map("Secondary.TButton", background=[("active", self.colors["border"])])

        style.configure("Danger.TButton", background=self.colors["danger"], foreground="#ffffff", font=("Segoe UI", 9, "bold"), padding=(8, 4))
        style.map("Danger.TButton", background=[("active", "#ff6b81")])

        # Scale slider styles
        style.configure("Horizontal.TScale", background=self.colors["bg_card"], troughcolor=self.colors["bg_input"], bordercolor=self.colors["border"])

        # Combobox style
        style.configure("TCombobox", fieldbackground=self.colors["bg_input"], background=self.colors["bg_card"], foreground=self.colors["text_light"], bordercolor=self.colors["border"])

    def toggle_theme(self):
        """Switches between Dark Mode and Light Mode."""
        self.is_dark_mode.set(not self.is_dark_mode.get())
        self.setup_theme()
        # Re-build UI to update all widget backgrounds
        for child in self.root.winfo_children():
            child.destroy()
        self.build_ui()
        self.check_device_status()
        self.refresh_profiles()

    def build_ui(self):
        # Header Bar
        header_frame = ttk.Frame(self.root, style="TFrame")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ttk.Frame(header_frame, style="TFrame")
        title_box.pack(side="left")
        
        header_title_frame = ttk.Frame(title_box, style="TFrame")
        header_title_frame.pack(anchor="w")
        ttk.Label(header_title_frame, text="⚡ SHIPSAR PREDATOR SENSE", style="Title.TLabel").pack(side="left")
        ttk.Label(header_title_frame, text=" 🇮🇳", font=("Segoe UI", 14)).pack(side="left")
        ttk.Label(title_box, text="Shipsar Developers • Acer RGB & Turbo Control Center", style="Subtitle.TLabel").pack(anchor="w")

        # Top Right Controls
        right_header = ttk.Frame(header_frame, style="TFrame")
        right_header.pack(side="right")

        theme_btn_text = "🌙 Dark Mode" if self.is_dark_mode.get() else "☀️ Light Mode"
        ttk.Button(right_header, text=theme_btn_text, style="Secondary.TButton", command=self.toggle_theme).pack(side="right", padx=(10, 0))
        ttk.Button(right_header, text="ℹ️ About Developer", style="Secondary.TButton", command=self.open_about_dialog).pack(side="right", padx=5)

        # Device Status Indicator Pill
        self.status_label = tk.Label(
            right_header,
            text="Checking Device...",
            bg=self.colors["bg_input"],
            fg=self.colors["text_muted"],
            font=("Segoe UI", 9, "bold"),
            padx=12, pady=4,
            relief="flat",
            cursor="hand2"
        )
        self.status_label.pack(side="right", padx=5)
        self.status_label.bind("<Button-1>", lambda e: self.on_status_label_click())

        # Main Workspace (Split Left/Right)
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(fill="both", expand=True, padx=20, pady=5)

        # Left Column: Keyboard Visualizer + System Status + Profiles
        left_col = ttk.Frame(main_container, style="TFrame")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Keyboard Preview Card
        preview_card = ttk.Frame(left_col, style="Card.TFrame", padding=15)
        preview_card.pack(fill="x", pady=(0, 10))

        ttk.Label(preview_card, text="KEYBOARD LIVE PREVIEW", style="Header.TLabel").pack(anchor="w", pady=(0, 10))

        # Canvas for 4-Zone Keyboard
        canvas_bg = "#0d0f17" if self.is_dark_mode.get() else "#e2e8f0"
        self.canvas = tk.Canvas(
            preview_card,
            width=440,
            height=160,
            bg=canvas_bg,
            highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        self.canvas.pack(fill="x", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Zone Selector Buttons under Visualizer
        zone_btn_frame = ttk.Frame(preview_card, style="Card.TFrame")
        zone_btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(zone_btn_frame, text="Select Zone (Static Mode):", style="Card.TLabel").pack(side="left")
        self.zone_btns = []
        for z in range(1, 5):
            btn = tk.Button(
                zone_btn_frame,
                text=f"Zone {z}",
                bg=self.colors["bg_input"],
                fg=self.colors["text_light"],
                activebackground=self.colors["accent_blue"],
                activeforeground="#ffffff",
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                command=lambda zid=z: self.select_zone(zid)
            )
            btn.pack(side="left", padx=4)
            self.zone_btns.append(btn)

        # System & Hardware Info Card
        sys_card = ttk.Frame(left_col, style="Card.TFrame", padding=12)
        sys_card.pack(fill="x", pady=(0, 10))

        ttk.Label(sys_card, text="HARDWARE & SYSTEM STATUS", style="Header.TLabel").pack(anchor="w", pady=(0, 5))

        sys_grid = ttk.Frame(sys_card, style="Card.TFrame")
        sys_grid.pack(fill="x")

        ttk.Label(sys_grid, text=f"Kernel Driver: facer v{DRIVER_VERSION}", style="Card.TLabel").pack(side="left")
        ttk.Label(sys_grid, text=" | ", style="Card.TLabel").pack(side="left")
        ttk.Label(sys_grid, text="Path: /opt/shipsar-developers/", style="Card.TLabel").pack(side="left")

        # Quick Fan Turbo Toggle Button
        self.turbo_btn = tk.Button(
            sys_card,
            text="🚀 MAX TURBO FAN: OFF",
            bg=self.colors["bg_input"],
            fg=self.colors["text_light"],
            activebackground=self.colors["warning"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10, pady=4,
            command=self.toggle_turbo_fan
        )
        self.turbo_btn.pack(anchor="e", pady=(5, 0))

        # Profiles Manager Card
        profiles_card = ttk.Frame(left_col, style="Card.TFrame", padding=15)
        profiles_card.pack(fill="both", expand=True)

        ttk.Label(profiles_card, text="PROFILES MANAGER", style="Header.TLabel").pack(anchor="w", pady=(0, 5))

        p_controls = ttk.Frame(profiles_card, style="Card.TFrame")
        p_controls.pack(fill="x", pady=5)

        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(p_controls, textvariable=self.profile_var, state="readonly")
        self.profile_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Button(p_controls, text="Load", style="Secondary.TButton", command=self.load_profile).pack(side="left", padx=2)
        ttk.Button(p_controls, text="Save As...", style="Secondary.TButton", command=self.save_profile).pack(side="left", padx=2)
        ttk.Button(p_controls, text="Delete", style="Danger.TButton", command=self.delete_profile).pack(side="left", padx=2)

        # Right Column: Effects & Color Controls + About Card
        right_col = ttk.Frame(main_container, style="TFrame")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Effect Mode Selection Card
        mode_card = ttk.Frame(right_col, style="Card.TFrame", padding=15)
        mode_card.pack(fill="x", pady=(0, 10))

        ttk.Label(mode_card, text="EFFECT MODES", style="Header.TLabel").pack(anchor="w", pady=(0, 5))

        mode_grid = ttk.Frame(mode_card, style="Card.TFrame")
        mode_grid.pack(fill="x")

        for i, m in enumerate(MODES):
            r = i // 2
            c = i % 2
            rb = ttk.Radiobutton(
                mode_grid,
                text=f"{m['name']}",
                value=m["id"],
                variable=self.current_mode,
                command=self.on_mode_change,
                style="TRadiobutton"
            )
            rb.grid(row=r, column=c, sticky="w", padx=10, pady=4)

        self.mode_desc_lbl = ttk.Label(mode_card, text="", style="Subtitle.TLabel")
        self.mode_desc_lbl.pack(anchor="w", pady=(5, 0))

        # Speed, Brightness & Direction Card
        params_card = ttk.Frame(right_col, style="Card.TFrame", padding=(15, 12))
        params_card.pack(fill="x", pady=(0, 10))

        # Brightness Slider
        b_frame = ttk.Frame(params_card, style="Card.TFrame")
        b_frame.pack(fill="x", pady=3)
        ttk.Label(b_frame, text="Brightness:", style="Card.TLabel", width=12).pack(side="left")
        self.b_scale = ttk.Scale(b_frame, from_=0, to=100, variable=self.brightness, command=lambda v: self.on_param_change())
        self.b_scale.pack(side="left", fill="x", expand=True, padx=10)
        self.b_val_lbl = ttk.Label(b_frame, text="100%", style="Card.TLabel", width=5)
        self.b_val_lbl.pack(side="right")

        # Speed Slider
        s_frame = ttk.Frame(params_card, style="Card.TFrame")
        s_frame.pack(fill="x", pady=3)
        ttk.Label(s_frame, text="Speed:", style="Card.TLabel", width=12).pack(side="left")
        self.s_scale = ttk.Scale(s_frame, from_=0, to=9, variable=self.speed, command=lambda v: self.on_param_change())
        self.s_scale.pack(side="left", fill="x", expand=True, padx=10)
        self.s_val_lbl = ttk.Label(s_frame, text="4", style="Card.TLabel", width=5)
        self.s_val_lbl.pack(side="right")

        # Direction Toggle
        self.d_frame = ttk.Frame(params_card, style="Card.TFrame")
        self.d_frame.pack(fill="x", pady=3)
        ttk.Label(self.d_frame, text="Direction:", style="Card.TLabel", width=12).pack(side="left")
        ttk.Radiobutton(self.d_frame, text="Right → Left", value=1, variable=self.direction, command=self.on_param_change).pack(side="left", padx=10)
        ttk.Radiobutton(self.d_frame, text="Left → Right", value=2, variable=self.direction, command=self.on_param_change).pack(side="left", padx=10)

        # Color Selector & Presets Card
        color_card = ttk.Frame(right_col, style="Card.TFrame", padding=(15, 12))
        color_card.pack(fill="both", expand=True)

        ttk.Label(color_card, text="COLOR SELECTION & PRESETS", style="Header.TLabel").pack(anchor="w", pady=(0, 5))

        # Color Swatch & Hex Entry
        c_top = ttk.Frame(color_card, style="Card.TFrame")
        c_top.pack(fill="x", pady=5)

        self.color_swatch = tk.Label(c_top, width=6, height=2, bg="#00d2ff", relief="solid", bd=1)
        self.color_swatch.pack(side="left", padx=(0, 10))

        ttk.Label(c_top, text="Hex:", style="Card.TLabel").pack(side="left")
        self.hex_var = tk.StringVar(value="#00D2FF")
        self.hex_entry = tk.Entry(c_top, textvariable=self.hex_var, bg=self.colors["bg_input"], fg=self.colors["text_light"], insertbackground="white", width=9, font=("Consolas", 10, "bold"))
        self.hex_entry.pack(side="left", padx=5)
        self.hex_entry.bind("<Return>", self.on_hex_enter)

        ttk.Button(c_top, text="Pick Color...", style="Secondary.TButton", command=self.open_color_picker).pack(side="right")

        # RGB Sliders
        rgb_frame = ttk.Frame(color_card, style="Card.TFrame")
        rgb_frame.pack(fill="x", pady=5)

        # Red
        r_line = ttk.Frame(rgb_frame, style="Card.TFrame")
        r_line.pack(fill="x", pady=2)
        ttk.Label(r_line, text="R:", foreground="#ff4757", font=("Segoe UI", 10, "bold"), width=3, style="Card.TLabel").pack(side="left")
        self.r_scale = ttk.Scale(r_line, from_=0, to=255, variable=self.dynamic_red, command=lambda v: self.on_rgb_slider_change())
        self.r_scale.pack(side="left", fill="x", expand=True, padx=5)

        # Green
        g_line = ttk.Frame(rgb_frame, style="Card.TFrame")
        g_line.pack(fill="x", pady=2)
        ttk.Label(g_line, text="G:", foreground="#2ed573", font=("Segoe UI", 10, "bold"), width=3, style="Card.TLabel").pack(side="left")
        self.g_scale = ttk.Scale(g_line, from_=0, to=255, variable=self.dynamic_green, command=lambda v: self.on_rgb_slider_change())
        self.g_scale.pack(side="left", fill="x", expand=True, padx=5)

        # Blue
        b_line = ttk.Frame(rgb_frame, style="Card.TFrame")
        b_line.pack(fill="x", pady=2)
        ttk.Label(b_line, text="B:", foreground="#1e90ff", font=("Segoe UI", 10, "bold"), width=3, style="Card.TLabel").pack(side="left")
        self.b_rgb_scale = ttk.Scale(b_line, from_=0, to=255, variable=self.dynamic_blue, command=lambda v: self.on_rgb_slider_change())
        self.b_rgb_scale.pack(side="left", fill="x", expand=True, padx=5)

        # Quick Theme Presets (Including Tiranga 🇮🇳)
        preset_frame = ttk.Frame(color_card, style="Card.TFrame")
        preset_frame.pack(fill="x", pady=5)
        ttk.Label(preset_frame, text="Quick Theme Presets:", style="Card.TLabel").pack(anchor="w")

        p_buttons_frame = ttk.Frame(preset_frame, style="Card.TFrame")
        p_buttons_frame.pack(fill="x", pady=3)

        ttk.Button(p_buttons_frame, text="🇮🇳 Tiranga", style="Secondary.TButton", command=self.apply_tiranga_preset).pack(side="left", padx=2)
        ttk.Button(p_buttons_frame, text="⚡ Cyberpunk", style="Secondary.TButton", command=self.apply_cyberpunk_preset).pack(side="left", padx=2)
        ttk.Button(p_buttons_frame, text="🎮 Gaming", style="Secondary.TButton", command=self.apply_gaming_preset).pack(side="left", padx=2)
        ttk.Button(p_buttons_frame, text="🌙 Stealth", style="Secondary.TButton", command=self.apply_stealth_preset).pack(side="left", padx=2)

        # Color Palette Grid
        p_grid = ttk.Frame(color_card, style="Card.TFrame")
        p_grid.pack(fill="x", pady=3)

        for name, hex_code, rgb in PRESET_COLORS:
            btn = tk.Button(
                p_grid,
                bg=hex_code,
                activebackground=hex_code,
                width=3,
                height=1,
                relief="flat",
                command=lambda r=rgb[0], g=rgb[1], b=rgb[2]: self.set_rgb(r, g, b)
            )
            btn.pack(side="left", padx=2, pady=2)

        # About Developer Footer Card
        dev_card = ttk.Frame(right_col, style="Card.TFrame", padding=10)
        dev_card.pack(fill="x", pady=(10, 0))

        dev_info_frame = ttk.Frame(dev_card, style="Card.TFrame")
        dev_info_frame.pack(side="left")
        ttk.Label(dev_info_frame, text="Maintained by Shipsar Developers 🇮🇳", style="Header.TLabel").pack(anchor="w")
        ttk.Label(dev_info_frame, text="Lead Developer: Vijay Kumar", style="Subtitle.TLabel").pack(anchor="w")

        ttk.Button(dev_card, text="🌐 shipsar.in", style="Primary.TButton", command=lambda: self.open_url_async("https://shipsar.in")).pack(side="right")

        # Bottom Action Bar
        bottom_bar = ttk.Frame(self.root, style="TFrame")
        bottom_bar.pack(fill="x", padx=20, pady=(10, 15))

        ttk.Checkbutton(bottom_bar, text="Auto-Apply Changes", variable=self.auto_apply, style="TCheckbutton").pack(side="left", pady=5)

        ttk.Button(bottom_bar, text="⚡ APPLY TO KEYBOARD", style="Primary.TButton", command=self.apply_to_hardware).pack(side="right")

        # Initial UI State Updates
        self.update_mode_ui()
        self.update_color_ui_from_vars()

    def update_mode_ui(self):
        m_id = self.current_mode.get()
        mode_info = next((m for m in MODES if m["id"] == m_id), MODES[0])
        self.mode_desc_lbl.config(text=mode_info["desc"])

        # Enable/Disable sliders depending on mode requirements
        if m_id == 0:  # Static mode
            self.s_scale.configure(state="disabled")
            self.d_frame.pack_forget()
        elif m_id in [3, 4]:  # Wave / Shifting (uses direction)
            self.s_scale.configure(state="normal")
            if not self.d_frame.winfo_ismapped():
                self.d_frame.pack(fill="x", pady=3)
        else:  # Breath, Neon, Zoom
            self.s_scale.configure(state="normal")
            self.d_frame.pack_forget()

        self.update_zone_button_states()
        self.update_color_ui_from_vars()

    def update_zone_button_states(self):
        m_id = self.current_mode.get()
        active_z = self.selected_zone.get()

        for idx, btn in enumerate(self.zone_btns, start=1):
            if m_id == 0:  # Static mode
                btn.configure(state="normal")
                if idx == active_z:
                    btn.configure(bg=self.colors["accent_cyan"], fg="#000000")
                else:
                    btn.configure(bg=self.colors["bg_input"], fg=self.colors["text_light"])
            else:
                btn.configure(state="disabled", bg=self.colors["bg_input"], fg=self.colors["text_muted"])

    def select_zone(self, zone_id):
        self.selected_zone.set(zone_id)
        # Load zone's RGB into sliders
        r, g, b = self.zone_colors[zone_id]
        self.dynamic_red.set(r)
        self.dynamic_green.set(g)
        self.dynamic_blue.set(b)
        self.update_zone_button_states()
        self.update_color_ui_from_vars()

    def set_rgb(self, r, g, b):
        self.dynamic_red.set(r)
        self.dynamic_green.set(g)
        self.dynamic_blue.set(b)
        self.update_color_ui_from_vars()
        self.on_param_change()

    def on_rgb_slider_change(self):
        self.update_color_ui_from_vars()
        self.on_param_change()

    def update_color_ui_from_vars(self):
        r = int(self.dynamic_red.get())
        g = int(self.dynamic_green.get())
        b = int(self.dynamic_blue.get())

        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        self.hex_var.set(hex_code)
        self.color_swatch.configure(bg=hex_code)

        if self.current_mode.get() == 0:
            # Update zone color
            self.zone_colors[self.selected_zone.get()] = (r, g, b)

    def on_hex_enter(self, event=None):
        val = self.hex_var.get().strip().lstrip("#")
        if len(val) == 6:
            try:
                r = int(val[0:2], 16)
                g = int(val[2:4], 16)
                b = int(val[4:6], 16)
                self.set_rgb(r, g, b)
            except ValueError:
                pass

    def open_color_picker(self):
        r = int(self.dynamic_red.get())
        g = int(self.dynamic_green.get())
        b = int(self.dynamic_blue.get())
        initial_hex = f"#{r:02X}{g:02X}{b:02X}"

        color = colorchooser.askcolor(initialcolor=initial_hex, title="Choose Keyboard Backlight Color")
        if color and color[0]:
            cr, cg, cb = int(color[0][0]), int(color[0][1]), int(color[0][2])
            self.set_rgb(cr, cg, cb)

    # Preset Theme Handlers
    def apply_tiranga_preset(self):
        """Applies 🇮🇳 Indian Tiranga colors to 4 Zones."""
        self.current_mode.set(0) # Static mode
        self.zone_colors[1] = (255, 153, 51)  # Saffron
        self.zone_colors[2] = (255, 255, 255) # White
        self.zone_colors[3] = (255, 255, 255) # White
        self.zone_colors[4] = (19, 136, 8)    # Green
        self.update_mode_ui()
        self.on_param_change()
        messagebox.showinfo("Preset Applied", "🇮🇳 Indian Flag (Tiranga) RGB preset applied!")

    def apply_cyberpunk_preset(self):
        self.current_mode.set(0)
        self.zone_colors[1] = (0, 255, 255)  # Cyan
        self.zone_colors[2] = (0, 255, 255)
        self.zone_colors[3] = (255, 0, 127)  # Neon Pink
        self.zone_colors[4] = (255, 0, 127)
        self.update_mode_ui()
        self.on_param_change()

    def apply_gaming_preset(self):
        self.current_mode.set(0)
        self.zone_colors[1] = (255, 0, 0)   # Red
        self.zone_colors[2] = (255, 0, 0)
        self.zone_colors[3] = (0, 136, 255) # Blue
        self.zone_colors[4] = (0, 136, 255)
        self.update_mode_ui()
        self.on_param_change()

    def apply_stealth_preset(self):
        self.current_mode.set(0)
        for z in range(1, 5):
            self.zone_colors[z] = (100, 100, 100) # Dim White
        self.update_mode_ui()
        self.on_param_change()

    def toggle_turbo_fan(self):
        self.turbo_mode.set(not self.turbo_mode.get())
        if self.turbo_mode.get():
            self.turbo_btn.config(text="🚀 MAX TURBO FAN: ON", bg=self.colors["danger"], fg="#ffffff")
        else:
            self.turbo_btn.config(text="🚀 MAX TURBO FAN: OFF", bg=self.colors["bg_input"], fg=self.colors["text_light"])
        self.apply_to_hardware(silent=True)

    def on_mode_change(self):
        self.update_mode_ui()
        self.on_param_change()

    def on_param_change(self):
        self.b_val_lbl.config(text=f"{int(self.brightness.get())}%")
        self.s_val_lbl.config(text=f"{int(self.speed.get())}")

        if self.auto_apply.get():
            self.apply_to_hardware(silent=True)

    # Keyboard Visualizer Canvas Drawing & Animation
    def on_canvas_click(self, event):
        if self.current_mode.get() != 0:
            return
        w = self.canvas.winfo_width()
        zone_w = w / 4.0
        clicked_zone = int(event.x // zone_w) + 1
        clicked_zone = max(1, min(4, clicked_zone))
        self.select_zone(clicked_zone)

    def start_animation(self):
        self.animate_canvas()

    def animate_canvas(self):
        self.animation_phase += 0.15
        self.draw_keyboard_canvas()
        self.anim_job = self.root.after(50, self.animate_canvas)

    def draw_keyboard_canvas(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1:
            w, h = 440, 160

        m_id = self.current_mode.get()
        spd = self.speed.get()
        brt = self.brightness.get() / 100.0

        # Calculate colors for each of the 4 zones
        colors = [(0, 0, 0)] * 4

        if m_id == 0:  # Static mode
            for z in range(1, 5):
                r, g, b = self.zone_colors[z]
                colors[z - 1] = (int(r * brt), int(g * brt), int(b * brt))
        elif m_id == 1:  # Breath
            r, g, b = self.dynamic_red.get(), self.dynamic_green.get(), self.dynamic_blue.get()
            factor = (math.sin(self.animation_phase * (spd * 0.3 + 0.5)) + 1.0) / 2.0 * brt
            c = (int(r * factor), int(g * factor), int(b * factor))
            colors = [c] * 4
        elif m_id == 2:  # Neon Spectrum
            for z in range(4):
                hue = (self.animation_phase * (spd * 0.1 + 0.2) + z * 0.5) % (2 * math.pi)
                r = int((math.sin(hue) + 1) / 2 * 255 * brt)
                g = int((math.sin(hue + 2.094) + 1) / 2 * 255 * brt)
                b = int((math.sin(hue + 4.188) + 1) / 2 * 255 * brt)
                colors[z] = (r, g, b)
        elif m_id == 3:  # Wave
            dir_mult = 1 if self.direction.get() == 1 else -1
            for z in range(4):
                phase = self.animation_phase * (spd * 0.2 + 0.3) * dir_mult + z * 0.8
                r = int((math.sin(phase) + 1) / 2 * 255 * brt)
                g = int((math.sin(phase + 2) + 1) / 2 * 255 * brt)
                b = int((math.sin(phase + 4) + 1) / 2 * 255 * brt)
                colors[z] = (r, g, b)
        elif m_id == 4:  # Shifting
            r, g, b = self.dynamic_red.get(), self.dynamic_green.get(), self.dynamic_blue.get()
            dir_mult = 1 if self.direction.get() == 1 else -1
            for z in range(4):
                factor = (math.sin(self.animation_phase * (spd * 0.25 + 0.3) * dir_mult + z * 0.7) + 1.0) / 2.0 * brt
                colors[z] = (int(r * factor), int(g * factor), int(b * factor))
        elif m_id == 5:  # Zoom
            r, g, b = self.dynamic_red.get(), self.dynamic_green.get(), self.dynamic_blue.get()
            for z in range(4):
                dist = abs(z - 1.5)
                factor = (math.sin(self.animation_phase * (spd * 0.3 + 0.4) - dist * 0.8) + 1.0) / 2.0 * brt
                colors[z] = (int(r * factor), int(g * factor), int(b * factor))

        # Render 4 Zones on Canvas
        margin = 15
        zone_w = (w - (margin * 2) - 15) / 4.0
        top_y = 20
        bot_y = h - 25

        active_zone = self.selected_zone.get()

        for z in range(4):
            x1 = margin + z * (zone_w + 5)
            x2 = x1 + zone_w
            cr, cg, cb = colors[z]
            hex_col = f"#{cr:02X}{cg:02X}{cb:02X}"

            # Zone rectangle
            border_col = self.colors["accent_cyan"] if (m_id == 0 and (z + 1) == active_zone) else self.colors["border"]
            border_w = 2 if (m_id == 0 and (z + 1) == active_zone) else 1

            self.canvas.create_rectangle(
                x1, top_y, x2, bot_y,
                fill=hex_col,
                outline=border_col,
                width=border_w
            )

            # Simulated Key Caps inside Zone
            rows, cols = 3, 4
            kw = (zone_w - 10) / cols
            kh = (bot_y - top_y - 25) / rows
            for r in range(rows):
                for c in range(cols):
                    kx1 = x1 + 5 + c * kw
                    ky1 = top_y + 5 + r * kh
                    kx2 = kx1 + kw - 2
                    ky2 = ky1 + kh - 2
                    key_dark = f"#{max(0, cr-60):02X}{max(0, cg-60):02X}{max(0, cb-60):02X}"
                    self.canvas.create_rectangle(kx1, ky1, kx2, ky2, fill=key_dark, outline="#111", width=1)

            # Label for Zone
            self.canvas.create_text(
                (x1 + x2) / 2,
                bot_y + 12,
                text=f"ZONE {z+1}",
                fill=self.colors["accent_cyan"] if (m_id == 0 and (z + 1) == active_zone) else self.colors["text_muted"],
                font=("Segoe UI", 8, "bold")
            )

    # Hardware Interface
    def check_device_status(self):
        """Checks character device existence and permissions."""
        dev_dynamic = os.path.exists(CHARACTER_DEVICE)
        dev_static = os.path.exists(CHARACTER_DEVICE_STATIC)

        if not dev_dynamic and not dev_static:
            self.device_status_reason = (
                "Kernel module not loaded: neither /dev/acer-gkbbl-0 nor "
                "/dev/acer-gkbbl-static-0 exist.\n\n"
                "Run 'sudo modprobe facer' or check 'dkms status' / "
                "'journalctl -u shipsar-acer-rgb' for build errors."
            )
            self.status_label.config(
                text="❌ Module Unloaded",
                bg=self.colors["danger"],
                fg="#ffffff"
            )
        elif not os.access(CHARACTER_DEVICE, os.W_OK) and not os.access(CHARACTER_DEVICE_STATIC, os.W_OK):
            self.device_status_reason = (
                "The RGB character device exists but is not writable by this user.\n\n"
                "Run the app as root, or install the udev rule so it can run "
                "unprivileged:\n"
                "echo 'KERNEL==\"acer-gkbbl*\", MODE=\"0666\"' | sudo tee "
                "/etc/udev/rules.d/99-acer-gkbbl.rules && sudo udevadm control "
                "--reload-rules && sudo udevadm trigger"
            )
            self.status_label.config(
                text="⚠️ Requires Root / udev",
                bg=self.colors["warning"],
                fg="#000000"
            )
        else:
            self.device_status_reason = None
            self.status_label.config(
                text="✔ Kernel Driver Active",
                bg=self.colors["success"],
                fg="#000000"
            )

    def on_status_label_click(self):
        if self.device_status_reason:
            self.show_error_dialog(
                self.status_label.cget("text").lstrip("❌⚠️ ").strip() or "Hardware Status",
                self.device_status_reason,
                action_desc="Device status check"
            )
        else:
            messagebox.showinfo("Device Status", "✔ Kernel driver is active and the RGB device is writable.")

    @staticmethod
    def open_url_async(url):
        """webbrowser.open() can block for several seconds while the browser/mail
        client cold-starts - always run it off the UI thread."""
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()

    # Error Reporting
    def gather_system_info(self):
        """Collects OS/kernel/device details useful for diagnosing hardware errors."""
        os_release = {}
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if "=" in line:
                        k, _, v = line.strip().partition("=")
                        os_release[k] = v.strip('"')
        except OSError:
            pass

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "os": os_release.get("PRETTY_NAME", platform.platform()),
            "kernel": platform.release(),
            "arch": platform.machine(),
            "python_version": platform.python_version(),
            "desktop": os.environ.get("XDG_CURRENT_DESKTOP", "unknown"),
            "session_type": os.environ.get("XDG_SESSION_TYPE", "unknown"),
            "dynamic_device": "present" if os.path.exists(CHARACTER_DEVICE) else "MISSING",
            "static_device": "present" if os.path.exists(CHARACTER_DEVICE_STATIC) else "MISSING",
        }

    def build_error_report(self, title, error_detail, action_desc=""):
        info = self.gather_system_info()
        lines = [
            "Shipsar Acer RGB Controller - Error Report",
            "=" * 43,
            f"Timestamp: {info['timestamp']}",
            f"App Version: {DRIVER_VERSION}",
            "",
            "--- System Info ---",
            f"OS: {info['os']}",
            f"Kernel: {info['kernel']} ({info['arch']})",
            f"Python: {info['python_version']}",
            f"Desktop: {info['desktop']} ({info['session_type']})",
            "",
            "--- Device Status ---",
            f"/dev/acer-gkbbl-0: {info['dynamic_device']}",
            f"/dev/acer-gkbbl-static-0: {info['static_device']}",
            "",
            "--- Current Settings ---",
            f"Mode: {self.current_mode.get()}",
            f"Speed: {self.speed.get()}",
            f"Brightness: {self.brightness.get()}",
            f"Direction: {self.direction.get()}",
            f"Color: R={self.dynamic_red.get()} G={self.dynamic_green.get()} B={self.dynamic_blue.get()}",
            "",
            "--- Error ---",
            f"Context: {title}",
        ]
        if action_desc:
            lines.append(f"Action: {action_desc}")
        lines.append(f"Details: {error_detail}")
        return "\n".join(lines)

    def show_error_dialog(self, title, error_detail, action_desc=""):
        """Shows an error with a full diagnostic report the user can copy or email to the developer."""
        report = self.build_error_report(title, error_detail, action_desc)

        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("560x480")
        win.configure(bg=self.colors["bg_card"])
        win.transient(self.root)
        win.grab_set()

        content = ttk.Frame(win, style="Card.TFrame", padding=15)
        content.pack(fill="both", expand=True)

        ttk.Label(content, text=f"⚠ {title}", style="Header.TLabel", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(content, text=error_detail, style="Card.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(0, 10))
        ttk.Label(content, text="Full diagnostic report (included when emailing the developer):", style="Card.TLabel").pack(anchor="w")

        text_frame = ttk.Frame(content, style="Card.TFrame")
        text_frame.pack(fill="both", expand=True, pady=(5, 10))

        report_box = tk.Text(
            text_frame, wrap="word", height=14,
            bg=self.colors["bg_input"], fg=self.colors["text_light"],
            insertbackground=self.colors["text_light"], relief="flat"
        )
        report_box.insert("1.0", report)
        report_box.configure(state="disabled")
        report_box.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, command=report_box.yview)
        scrollbar.pack(side="right", fill="y")
        report_box.configure(yscrollcommand=scrollbar.set)

        def copy_report():
            self.root.clipboard_clear()
            self.root.clipboard_append(report)
            copy_btn.config(text="✔ Copied!")
            win.after(2000, lambda: copy_btn.config(text="📋 Copy to Clipboard"))

        def email_developer():
            subject = urllib.parse.quote(f"Shipsar Acer RGB Controller - Error Report ({title})")
            body = urllib.parse.quote(report)
            self.open_url_async(f"mailto:{DEVELOPER_EMAIL}?subject={subject}&body={body}")

        btn_frame = ttk.Frame(content, style="Card.TFrame")
        btn_frame.pack(fill="x")

        copy_btn = ttk.Button(btn_frame, text="📋 Copy to Clipboard", style="Secondary.TButton", command=copy_report)
        copy_btn.pack(side="left", padx=(0, 5))

        ttk.Button(
            btn_frame, text=f"📧 Send to Developer ({DEVELOPER_EMAIL})",
            style="Primary.TButton", command=email_developer
        ).pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Close", style="Secondary.TButton", command=win.destroy).pack(side="right")

    def apply_to_hardware(self, silent=False):
        """Sends payload to Linux kernel character device or calls facer_rgb.py."""
        m_id = self.current_mode.get()
        sp = int(self.speed.get())
        br = int(self.brightness.get())
        di = int(self.direction.get())
        r = int(self.dynamic_red.get())
        g = int(self.dynamic_green.get())
        b = int(self.dynamic_blue.get())

        success = True
        err_msg = ""

        if not os.path.exists(CHARACTER_DEVICE) and not os.path.exists(CHARACTER_DEVICE_STATIC):
            self.check_device_status()
            if not silent:
                self.show_error_dialog("Hardware Error", self.device_status_reason, action_desc="Apply to hardware")
            return

        try:
            if m_id == 0:  # Static mode per zone
                for z_id in range(1, 5):
                    zr, zg, zb = self.zone_colors[z_id]
                    payload_static = [0] * PAYLOAD_SIZE_STATIC_MODE
                    payload_static[0] = 1 << (z_id - 1)
                    payload_static[1] = zr
                    payload_static[2] = zg
                    payload_static[3] = zb

                    if os.path.exists(CHARACTER_DEVICE_STATIC):
                        with open(CHARACTER_DEVICE_STATIC, 'wb') as cd:
                            cd.write(bytes(payload_static))
                    else:
                        cmd = [sys.executable, FACER_RGB_SCRIPT, "-m", "0", "-z", str(z_id), "-cR", str(zr), "-cG", str(zg), "-cB", str(zb)]
                        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                payload_dyn = [0] * PAYLOAD_SIZE
                payload_dyn[2] = br
                payload_dyn[9] = 1
                if os.path.exists(CHARACTER_DEVICE):
                    with open(CHARACTER_DEVICE, 'wb') as cd:
                        cd.write(bytes(payload_dyn))

            else:  # Dynamic mode
                payload = [0] * PAYLOAD_SIZE
                payload[0] = m_id
                payload[1] = sp
                payload[2] = br
                payload[3] = 8 if m_id == 3 else 0
                payload[4] = di
                payload[5] = r
                payload[6] = g
                payload[7] = b
                payload[9] = 1

                if os.path.exists(CHARACTER_DEVICE):
                    with open(CHARACTER_DEVICE, 'wb') as cd:
                        cd.write(bytes(payload))
                else:
                    cmd = [
                        sys.executable, FACER_RGB_SCRIPT,
                        "-m", str(m_id),
                        "-s", str(sp),
                        "-b", str(br),
                        "-d", str(di),
                        "-cR", str(r),
                        "-cG", str(g),
                        "-cB", str(b)
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        except PermissionError:
            success = False
            err_msg = f"Permission denied writing to {CHARACTER_DEVICE}. Run app as root or configure udev rules."
        except subprocess.CalledProcessError as e:
            success = False
            stderr_text = e.stderr.decode(errors="replace").strip() if e.stderr else ""
            err_msg = str(e) + (f"\nSubprocess stderr: {stderr_text}" if stderr_text else "")
        except Exception as e:
            success = False
            err_msg = str(e)

        if not silent:
            if success:
                messagebox.showinfo("Success", "Keyboard backlight settings applied successfully!")
            else:
                self.show_error_dialog("Hardware Error", f"Failed to apply settings:\n{err_msg}", action_desc="Apply to hardware")

    # About Developer Dialog Modal
    def open_about_dialog(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("About Shipsar Developers")
        about_win.geometry("480x420")
        about_win.resizable(False, False)
        about_win.configure(bg=self.colors["bg_card"])

        # Make modal
        about_win.transient(self.root)
        about_win.grab_set()

        content = ttk.Frame(about_win, style="Card.TFrame", padding=20)
        content.pack(fill="both", expand=True)

        ttk.Label(content, text="⚡ Shipsar Acer RGB Control", style="Header.TLabel", font=("Segoe UI", 14, "bold")).pack(anchor="center", pady=(0, 5))
        ttk.Label(content, text=f"Version {DRIVER_VERSION}", style="Subtitle.TLabel").pack(anchor="center", pady=(0, 15))

        info_text = (
            "🏢 Maintained by: Shipsar Developers 🇮🇳\n\n"
            "👤 Lead Developer: Vijay Kumar\n\n"
            "🌐 Official Website: https://shipsar.in\n\n"
            "📦 GitHub Repository: https://github.com/shipsar\n\n"
            "An open-source hardware utility for Acer Predator, Helios, "
            "and Nitro laptops, crafted with pride in India."
        )

        lbl = tk.Label(
            content,
            text=info_text,
            bg=self.colors["bg_input"],
            fg=self.colors["text_light"],
            font=("Segoe UI", 10),
            justify="center",
            padx=15, pady=15,
            relief="flat"
        )
        lbl.pack(fill="x", pady=10)

        btn_frame = ttk.Frame(content, style="Card.TFrame")
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="🌐 Visit Website (shipsar.in)", style="Primary.TButton", command=lambda: self.open_url_async("https://shipsar.in")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", style="Secondary.TButton", command=about_win.destroy).pack(side="left", padx=5)

    # Profile Management
    def ensure_config_dir(self):
        Path(CONFIG_DIRECTORY).mkdir(parents=True, exist_ok=True)

    def refresh_profiles(self):
        self.ensure_config_dir()
        profiles = [p.stem for p in Path(CONFIG_DIRECTORY).glob("*.json")]
        self.profile_combo['values'] = profiles
        if profiles and not self.profile_var.get():
            self.profile_var.set(profiles[0])

    def save_profile(self):
        name = simpledialog.askstring("Save Profile", "Enter profile name:", parent=self.root)
        if not name:
            return

        name = name.strip().replace(" ", "_")
        profile_data = {
            "mode": self.current_mode.get(),
            "speed": self.speed.get(),
            "brightness": self.brightness.get(),
            "direction": self.direction.get(),
            "red": self.dynamic_red.get(),
            "green": self.dynamic_green.get(),
            "blue": self.dynamic_blue.get(),
            "zone_colors": {str(k): list(v) for k, v in self.zone_colors.items()}
        }

        filepath = Path(CONFIG_DIRECTORY) / f"{name}.json"
        try:
            with open(filepath, 'w') as f:
                json.dump(profile_data, f, indent=4)
            messagebox.showinfo("Saved", f"Profile '{name}' saved successfully!")
            self.refresh_profiles()
            self.profile_var.set(name)
        except Exception as e:
            self.show_error_dialog("Profile Save Error", f"Could not save profile:\n{e}", action_desc=f"Save profile '{name}'")

    def load_profile(self):
        name = self.profile_var.get()
        if not name:
            messagebox.showwarning("Warning", "Select a profile to load.")
            return

        filepath = Path(CONFIG_DIRECTORY) / f"{name}.json"
        if not filepath.exists():
            messagebox.showerror("Error", f"Profile '{name}' not found.")
            return

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            if "mode" in data: self.current_mode.set(data["mode"])
            if "speed" in data: self.speed.set(data["speed"])
            if "brightness" in data: self.brightness.set(data["brightness"])
            if "direction" in data: self.direction.set(data["direction"])
            if "red" in data: self.dynamic_red.set(data["red"])
            if "green" in data: self.dynamic_green.set(data["green"])
            if "blue" in data: self.dynamic_blue.set(data["blue"])

            if "zone_colors" in data:
                for k, v in data["zone_colors"].items():
                    self.zone_colors[int(k)] = tuple(v)

            self.update_mode_ui()
            self.update_color_ui_from_vars()
            self.apply_to_hardware(silent=True)
            messagebox.showinfo("Loaded", f"Profile '{name}' loaded and applied!")
        except Exception as e:
            self.show_error_dialog("Profile Load Error", f"Failed to load profile:\n{e}", action_desc=f"Load profile '{name}'")

    def delete_profile(self):
        name = self.profile_var.get()
        if not name:
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{name}'?"):
            filepath = Path(CONFIG_DIRECTORY) / f"{name}.json"
            if filepath.exists():
                filepath.unlink()
                messagebox.showinfo("Deleted", f"Profile '{name}' deleted.")
                self.profile_var.set("")
                self.refresh_profiles()


def main():
    root = tk.Tk()
    app = PredatorRGBApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
