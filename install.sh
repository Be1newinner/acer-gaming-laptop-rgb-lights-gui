#!/bin/bash

if [[ $EUID -ne 0 ]]; then
   echo "[*] This script must be run as root"
   exit 1
fi

if [[ -f "/sys/bus/wmi/devices/7A4DDFE7-5B5D-40B4-8595-4408E0CC7F56/" ]]; then
    echo "[*] Sorry but your device doesn't have the required WMI module"
    exit 1
fi

if [ ! "$(uname -r | grep lts)" == "" ]; then
    echo LTS kernel detected
    MAKEFLAGS="LTS=1"
fi

# Remove previous chr devices if any exists
rm /dev/acer-gkbbl-0 /dev/acer-gkbbl-static-0 -f

# compile the kernel module
if [ "$(cat /proc/version | grep clang)" != "" ]; then
    #For kernels compiled with clang
    make CC=clang LD=ld.lld $MAKEFLAGS
else
    #For normal kernels
    make $MAKEFLAGS
fi
# remove previous acer_wmi and facer modules
rmmod acer_wmi 2>/dev/null || true
rmmod facer 2>/dev/null || true

# install required modules
modprobe wmi
modprobe sparse-keymap
modprobe video

# create udev rules for Acer RGB keyboard so GUI runs without root
echo 'KERNEL=="acer-gkbbl*", MODE="0666"' > /etc/udev/rules.d/99-acer-gkbbl.rules 2>/dev/null || true
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true

# install facer module
insmod src/facer.ko

# install GUI application and desktop launcher
cp -f facer_gui.py /usr/local/bin/facer_gui.py
chmod +x /usr/local/bin/facer_gui.py
if [ -d "/usr/share/applications" ]; then
    cp -f acer-predator-gui.desktop /usr/share/applications/acer-predator-gui.desktop
    chmod 644 /usr/share/applications/acer-predator-gui.desktop
fi

echo "[*] Done! Keyboard module and GUI installed."
echo "[*] Launch GUI anytime with command 'facer_gui.py' or from Application Menu."
