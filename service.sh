#!/bin/bash
# System service startup script for Shipsar Acer Predator Turbo & RGB Control

TARGET_DIR="/opt/shipsar-developers/acer-rgb-controller"
cd "$TARGET_DIR" 2>/dev/null || exit 1

rm -f /dev/acer-gkbbl-0 /dev/acer-gkbbl-static-0

rmmod acer_wmi 2>/dev/null || true
rmmod facer 2>/dev/null || true
modprobe wmi 2>/dev/null || true
modprobe sparse-keymap 2>/dev/null || true
modprobe video 2>/dev/null || true

# Load the DKMS-built module. Errors are intentionally NOT suppressed here so
# `journalctl -u shipsar-acer-rgb` shows the real reason (missing module,
# Secure Boot signature rejection, etc.) instead of failing silently.
if modprobe facer; then
	echo "[*] facer kernel module loaded via modprobe."
elif [ -f "$TARGET_DIR/src/facer.ko" ] && insmod "$TARGET_DIR/src/facer.ko"; then
	echo "[*] facer kernel module loaded via insmod fallback."
else
	echo "[!] Failed to load the facer kernel module. Check 'dkms status' and" >&2
	echo "[!] 'journalctl -u shipsar-acer-rgb' for details (missing kernel" >&2
	echo "[!] headers or an unsigned module under Secure Boot are common causes)." >&2
fi

if [ -e "/dev/acer-gkbbl-0" ]; then
	echo "[*] /dev/acer-gkbbl-0 present."
	if [ -f "$TARGET_DIR/facer_rgb.py" ]; then
		python3 "$TARGET_DIR/facer_rgb.py" -m 2 -s 3 -b 100 || echo "[!] Initial facer_rgb.py run failed." >&2
	fi
else
	echo "[!] /dev/acer-gkbbl-0 still missing after module load attempt." >&2
fi
