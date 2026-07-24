#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "[*] This script must be run as root"
   exit 1
fi

rmmod facer 2>/dev/null || true
modprobe acer_wmi 2>/dev/null || true
rm -f /usr/local/bin/facer_gui.py
rm -f /usr/share/applications/acer-predator-gui.desktop
rm -f /etc/udev/rules.d/99-acer-gkbbl.rules
udevadm control --reload-rules 2>/dev/null || true
echo "[*] Uninstalled Acer Predator RGB keyboard module and GUI."