#!/bin/bash
# Master build script to generate all release packages (.deb, Arch, and .run)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"

BUILD_NUM="${BUILD_NUM:-02}"
export BUILD_NUM

echo "================================================================="
echo " Shipsar Developers - Acer RGB & Turbo Multi-Distro Package Builder"
echo " Build Revision: 1.20260725-${BUILD_NUM}"
echo "================================================================="
echo ""

# 1. Clean previous build objects and dist directory
make clean >/dev/null 2>&1 || true
mkdir -p "${DIST_DIR}"

# 2. Build Debian package
echo "--- [1/3] Building Debian/Ubuntu (.deb) Package ---"
if bash "${SCRIPT_DIR}/build_deb.sh"; then
    echo "[✔] Debian package build successful!"
else
    echo "[✘] Debian package build failed!"
fi
echo ""

# 3. Build Arch package
echo "--- [2/3] Building Arch Linux Package ---"
if bash "${SCRIPT_DIR}/build_arch.sh"; then
    echo "[✔] Arch Linux build process successful!"
else
    echo "[✘] Arch Linux build process failed!"
fi
echo ""

# 4. Build Universal .run executable
echo "--- [3/3] Building Universal Single-File (.run) Bundle ---"
if bash "${SCRIPT_DIR}/bundle.sh"; then
    echo "[✔] Universal .run build successful!"
else
    echo "[✘] Universal .run build failed!"
fi
echo ""

# Summary of output artifacts
echo "================================================================="
echo " BUILD COMPLETE! Release packages generated in: ${DIST_DIR}"
echo "================================================================="
ls -lh "${DIST_DIR}"
echo "================================================================="
