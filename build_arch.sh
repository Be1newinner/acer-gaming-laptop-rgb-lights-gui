#!/bin/bash
# Builder script to generate Arch Linux package (.pkg.tar.zst) or release tarball
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
ARCH_DIR="${SCRIPT_DIR}/ArchLinux-bin-pkg"

mkdir -p "${DIST_DIR}"

echo "[*] Starting Arch Linux package build process..."

if command -v makepkg >/dev/null 2>&1; then
    echo "[*] Found makepkg on host. Building native Arch Linux package..."
    cd "${ARCH_DIR}"
    bash ./makepkg.sh
    mv "${SCRIPT_DIR}"/*.pkg.tar.zst "${DIST_DIR}/" 2>/dev/null || mv "${ARCH_DIR}"/*.pkg.tar.zst "${DIST_DIR}/" 2>/dev/null || true
    echo "[✔] Arch Linux binary package built in ${DIST_DIR}/"
else
    echo "[!] Note: 'makepkg' command not found (host is not Arch Linux)."
    echo "[*] Creating Arch Linux PKGBUILD release package tarball for Arch/AUR deployment..."
    
    ARCH_TARBALL="${DIST_DIR}/acer-predator-turbo-rgb-arch-source.tar.gz"
    tar -czf "${ARCH_TARBALL}" -C "${SCRIPT_DIR}" \
        ArchLinux-bin-pkg \
        src \
        Makefile \
        dkms.conf \
        facer_gui.py \
        facer_rgb.py \
        keyboard.py \
        keyboard.webp \
        service.sh \
        uninstall.sh \
        acer-predator-gui.desktop
        
    echo "[✔] Arch Linux package release archive created: ${ARCH_TARBALL}"
fi
