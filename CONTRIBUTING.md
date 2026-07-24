# 🇮🇳 Contributing to Shipsar Acer Predator RGB & Turbo Control

Thank you for your interest in contributing to **Shipsar Acer Predator RGB & Turbo Control**! Developed by **Shipsar Developers** in **India 🇮🇳**, this open-source project thrives on contributions from developers worldwide.

Whether you are fixing bugs, improving kernel driver compatibility, enhancing the Python GUI, or expanding Linux distribution packaging, your help is warmly welcomed!

---

## 📜 Table of Contents

1. [Code of Conduct](#-code-of-conduct)
2. [Getting Started](#-getting-started)
3. [Repository Architecture](#-repository-architecture)
4. [Development Workflow](#-development-workflow)
   - [Building Kernel Module](#1-building-the-kernel-module)
   - [Testing Python GUI](#2-testing-the-python-gui)
   - [Building Release Packages](#3-building-multi-distro-release-packages)
5. [Submitting a Pull Request](#-submitting-a-pull-request)
6. [Community & Contact](#-community--contact)

---

## 🇮🇳 Code of Conduct

We are committed to providing a welcoming, inclusive, and collaborative environment for every contributor, regardless of background, identity, or location. Please treat all maintainers and fellow community members with respect.

---

## 🚀 Getting Started

### Prerequisites

To set up your local development environment on Linux (Ubuntu, Debian, Arch, Fedora), install the required build tools:

**Ubuntu / Debian / Linux Mint:**

```bash
sudo apt update
sudo apt install build-essential linux-headers-$(uname -r) dkms python3 python3-tk rsync dpkg-dev
```

**Arch Linux / Manjaro:**

```bash
sudo pacman -S base-devel linux-headers dkms python tk rsync
```

### Fork & Clone Repository

```bash
git clone https://github.com/shipsar/acer-gaming-laptop-rgb-lights-gui.git
cd acer-gaming-laptop-rgb-lights-gui
```

---

## 📁 Repository Architecture

- **`src/facer.c`**: Linux kernel C module handling ACPI WMI calls, character devices `/dev/acer-gkbbl-0`, and turbo mode button triggers.
- **`facer_gui.py`**: Python Tkinter GUI interface (`shipsar-acer-rgb`).
- **`facer_rgb.py`**: CLI utility for low-level byte payloads sent to device nodes.
- **`service.sh`**: Systemd daemon startup script installed under `/opt/shipsar-developers/acer-rgb-controller/`.
- **`build_all.sh` / `build_deb.sh` / `build_arch.sh` / `bundle.sh`**: Automated release build pipeline scripts.
- **`debian/`**: Debian/Ubuntu package specifications and post-install hooks.
- **`ArchLinux-bin-pkg/`**: Arch Linux PKGBUILD packaging definitions.

---

## 🛠️ Development Workflow

### 1. Building the Kernel Module

Compile the `facer.ko` kernel module locally for testing:

```bash
# Compile module
make

# Test loading module
sudo insmod src/facer.ko

# View kernel logs
dmesg | tail -n 30

# Remove module after testing
sudo rmmod facer
make clean
```

> ⚠️ **Kernel Safety Warning**: Be cautious when editing ACPI WMI calls in `src/facer.c`. Always test kernel module changes on non-production kernels or test machines first.

---

### 2. Testing the Python GUI

You can launch and test GUI changes locally without installing:

```bash
python3 facer_gui.py
```

---

### 3. Building Multi-Distro Release Packages

Shipsar Developers uses an automated pipeline to generate all release packages simultaneously into `dist/`:

```bash
# Run unified release builder
./build_all.sh
# OR
make dist
```

Generated release artifacts in `dist/`:

- `dist/shipsar-acer-rgb-controller_1.20260725-1_all.deb`
- `dist/acer-predator-turbo-rgb-arch-source.tar.gz`
- `dist/AcerPredatorRGB.run`

---

## 📬 Submitting a Pull Request

1. **Create a Feature Branch**:

   ```bash
   git checkout -b feature/my-cool-feature
   ```

2. **Commit Your Changes**:
   Write clear, concise commit messages detailing what changed and why.

3. **Verify Build & Tests**:
   Ensure `make clean && ./build_all.sh` succeeds without build errors.

4. **Submit PR**:
   Push your branch to GitHub and open a Pull Request against the `main` branch of `shipsar/acer-gaming-laptop-rgb-lights-gui`.

---

## 🌐 Community & Contact

- **Maintained By**: **Shipsar Developers** 🇮🇳
- **GitHub**: [github.com/shipsar](https://github.com/shipsar)
- **Website**: [shipsar.com](https://shipsar.com)

Thank you for building high-quality open-source software with **Shipsar Developers**! 🇮🇳
