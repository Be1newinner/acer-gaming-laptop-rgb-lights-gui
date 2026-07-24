---
name: Shipsar Bug & Compatibility Report
about: Report a bug or hardware compatibility result for Shipsar Acer Predator RGB & Turbo Control
title: '[BUG / COMPATIBILITY]: '
labels: 'bug, hardware-test'
assignees: ''
---

# ⚡ Shipsar Acer Predator RGB & Turbo Control - Issue / Test Report

Thank you for reporting an issue or hardware test result to **Shipsar Developers** 🇮🇳!

---

### 💻 Hardware & Environment Information

| Property | Value / Command output |
| :--- | :--- |
| **Acer Model** | `sudo dmidecode \| grep "Product Name" -A 2 -B 2` |
| **Linux Distribution** | `lsb_release -a` or `cat /etc/os-release` |
| **Kernel Version** | `uname -r` |
| **Installation Method** | `.deb` Package / Arch Package / `.run` Bundle / Source Build (`make`) |
| **CPU / GPU Fan Count** | CPU: ? \| GPU: ? |
| **RGB Keyboard Type** | 4-Zone RGB / Per-Key RGB / Single Color / Other |

---

### 🔍 Functionality Check

- [ ] **RGB Keyboard Backlight Works?**: (Yes / No / Partial)
- [ ] **Hardware Turbo Fan Button Works?**: (Yes / No)
- [ ] **Turbo Mode LED Lights Up?**: (Yes / No)
- [ ] **Systemd Service Running (`shipsar-acer-rgb`)?**: (Yes / No)

---

### 📋 Logs & Diagnostic Output

**1. Output of kernel driver status (`dmesg`):**
```bash
sudo dmesg | grep -iE "facer|acer_wmi|gkbbl"
```

**2. Systemd Service Logs (`journalctl`):**
```bash
sudo journalctl -u shipsar-acer-rgb --no-pager -n 30
```

---

### 📝 Detailed Description of Issue / Steps to Reproduce
*(Provide a brief explanation of what happened, expected behavior, and steps to reproduce)*
