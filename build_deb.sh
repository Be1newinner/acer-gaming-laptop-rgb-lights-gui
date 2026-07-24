#!/bin/bash
# Builder script to generate Debian/Ubuntu (.deb) package for Shipsar Developers
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
BUILD_ROOT="${SCRIPT_DIR}/build/deb_staging"

PACKAGE_NAME="shipsar-acer-rgb-controller"
BUILD_NUM="${BUILD_NUM:-02}"
VERSION="1.20260725-${BUILD_NUM}"
DKMS_VERSION="1.20260725"
INSTALL_TARGET="/opt/shipsar-developers/acer-rgb-controller"

echo "[*] Starting Shipsar Developers Debian (.deb) package build (Version: ${VERSION})..."

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "[!] Error: dpkg-deb tool is missing. Install dpkg-dev to build Debian packages." >&2
    exit 1
fi

# Clean & recreate staging and dist directories
rm -rf "${BUILD_ROOT}"
mkdir -p "${DIST_DIR}"
mkdir -p "${BUILD_ROOT}/DEBIAN"
mkdir -p "${BUILD_ROOT}/usr/src/facer-${DKMS_VERSION}"
mkdir -p "${BUILD_ROOT}${INSTALL_TARGET}"
mkdir -p "${BUILD_ROOT}/usr/bin"
mkdir -p "${BUILD_ROOT}/usr/share/applications"
mkdir -p "${BUILD_ROOT}/usr/share/pixmaps"
mkdir -p "${BUILD_ROOT}/lib/systemd/system"

# 1. Copy Debian control files
cp "${SCRIPT_DIR}/debian/control" "${BUILD_ROOT}/DEBIAN/control"
sed -i "s/^Version:.*/Version: ${VERSION}/" "${BUILD_ROOT}/DEBIAN/control"
cp "${SCRIPT_DIR}/debian/postinst" "${BUILD_ROOT}/DEBIAN/postinst"
cp "${SCRIPT_DIR}/debian/prerm" "${BUILD_ROOT}/DEBIAN/prerm"
chmod 755 "${BUILD_ROOT}/DEBIAN/postinst" "${BUILD_ROOT}/DEBIAN/prerm"
chmod 644 "${BUILD_ROOT}/DEBIAN/control"

# 2. Copy DKMS module sources (clean source only)
mkdir -p "${BUILD_ROOT}/usr/src/facer-${DKMS_VERSION}/src"
cp "${SCRIPT_DIR}/src/facer.c" "${BUILD_ROOT}/usr/src/facer-${DKMS_VERSION}/src/"
cp "${SCRIPT_DIR}/Makefile" "${BUILD_ROOT}/usr/src/facer-${DKMS_VERSION}/"
cp "${SCRIPT_DIR}/dkms.conf" "${BUILD_ROOT}/usr/src/facer-${DKMS_VERSION}/"

# 3. Copy application files & assets to /opt/shipsar-developers/acer-rgb-controller
cp "${SCRIPT_DIR}/facer_gui.py" "${BUILD_ROOT}${INSTALL_TARGET}/"
cp "${SCRIPT_DIR}/facer_rgb.py" "${BUILD_ROOT}${INSTALL_TARGET}/"
cp "${SCRIPT_DIR}/keyboard.py" "${BUILD_ROOT}${INSTALL_TARGET}/"
cp "${SCRIPT_DIR}/keyboard.webp" "${BUILD_ROOT}${INSTALL_TARGET}/"
cp "${SCRIPT_DIR}/service.sh" "${BUILD_ROOT}${INSTALL_TARGET}/"
cp "${SCRIPT_DIR}/uninstall.sh" "${BUILD_ROOT}${INSTALL_TARGET}/"
if [ -d "${SCRIPT_DIR}/public" ]; then
    cp -r "${SCRIPT_DIR}/public" "${BUILD_ROOT}${INSTALL_TARGET}/"
fi
chmod +x "${BUILD_ROOT}${INSTALL_TARGET}/"*.py "${BUILD_ROOT}${INSTALL_TARGET}/"*.sh

# 4. Create primary binary launcher /usr/bin/rgb-controller
cat << EOF > "${BUILD_ROOT}/usr/bin/rgb-controller"
#!/bin/sh
exec python3 ${INSTALL_TARGET}/facer_gui.py "\$@"
EOF
chmod 755 "${BUILD_ROOT}/usr/bin/rgb-controller"

# Create symlinks shipsar-acer-rgb and facer_gui -> rgb-controller
ln -sf rgb-controller "${BUILD_ROOT}/usr/bin/shipsar-acer-rgb"
ln -sf rgb-controller "${BUILD_ROOT}/usr/bin/facer_gui"

# 5. Desktop launcher & Icon Pixmaps
cp "${SCRIPT_DIR}/shipsar-acer-rgb.desktop" "${BUILD_ROOT}/usr/share/applications/"
chmod 644 "${BUILD_ROOT}/usr/share/applications/shipsar-acer-rgb.desktop"
if [ -f "${SCRIPT_DIR}/public/logo.png" ]; then
    cp "${SCRIPT_DIR}/public/logo.png" "${BUILD_ROOT}/usr/share/pixmaps/shipsar-acer-rgb.png"
    chmod 644 "${BUILD_ROOT}/usr/share/pixmaps/shipsar-acer-rgb.png"
fi

# 6. Systemd service file
cat << EOF > "${BUILD_ROOT}/lib/systemd/system/shipsar-acer-rgb.service"
[Unit]
Description=Shipsar Acer Predator RGB & Turbo Control Service
After=multi-user.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
WorkingDirectory=${INSTALL_TARGET}
ExecStart=/bin/bash ${INSTALL_TARGET}/service.sh
ExecStop=/bin/bash ${INSTALL_TARGET}/uninstall.sh

[Install]
WantedBy=multi-user.target
EOF
chmod 644 "${BUILD_ROOT}/lib/systemd/system/shipsar-acer-rgb.service"

# Build .deb package
OUTPUT_DEB="${DIST_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "${BUILD_ROOT}" "${OUTPUT_DEB}"

echo "[✔] Debian package successfully built: ${OUTPUT_DEB}"
