#!/bin/bash
# Builder script to package Acer Predator RGB Control into a single self-contained executable file.
# Output file: AcerPredatorRGB.run
# Compatible with Ubuntu 22.04, 24.04, 25.04, 25.10, Debian, Arch, Fedora, etc.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
mkdir -p "${DIST_DIR}"
OUTPUT_FILE="${DIST_DIR}/AcerPredatorRGB.run"
TEMP_PAYLOAD_TAR="$(mktemp /tmp/predator_payload.XXXXXX.tar.gz)"

cleanup() {
    rm -f "${TEMP_PAYLOAD_TAR}"
}
trap cleanup EXIT

echo "[*] Creating payload archive..."

# Package required files into temporary tarball
tar -czf "${TEMP_PAYLOAD_TAR}" \
    -C "${SCRIPT_DIR}" \
    src \
    Makefile \
    dkms.conf \
    facer_gui.py \
    facer_rgb.py \
    keyboard.py \
    install.sh \
    install_service.sh \
    uninstall.sh \
    acer-predator-gui.desktop

echo "[*] Generating single-file executable: ${OUTPUT_FILE}..."

# Write header script to output file
cat << 'HEADER_EOF' > "${OUTPUT_FILE}"
#!/bin/bash
# ==============================================================================
# Shipsar Acer Predator RGB & Turbo Control - Universal Single-File Application
# Developed by Shipsar Developers
# Compatible with Ubuntu 22.04 LTS, 24.04 LTS, 25.04, 25.10 & all Linux Distros
# ==============================================================================

set -e

SHOW_HELP=0
MODE="gui"

for arg in "$@"; do
    case "$arg" in
        --install|-i)
            MODE="install"
            ;;
        --cli|-c)
            MODE="cli"
            ;;
        --uninstall|-u)
            MODE="uninstall"
            ;;
        --gui|-g)
            MODE="gui"
            ;;
        --help|-h)
            SHOW_HELP=1
            ;;
    esac
done

if [ "$SHOW_HELP" -eq 1 ]; then
    echo "Acer Predator RGB Control - Universal Single-File App"
    echo ""
    echo "Usage:"
    echo "  ./AcerPredatorRGB.run [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (no flags) / --gui  Launch Graphical User Interface (Default)"
    echo "  --install           Install kernel module, udev rules, service & desktop shortcut (Requires root)"
    echo "  --cli               Launch interactive CLI prompt"
    echo "  --uninstall         Uninstall system service, module, and desktop shortcuts (Requires root)"
    echo "  --help, -h          Show this help message"
    echo ""
    exit 0
fi

# Create secure temporary extraction directory
TMP_DIR="$(mktemp -d /tmp/acer_predator_app.XXXXXX)"
cleanup_tmp() {
    rm -rf "${TMP_DIR}"
}
trap cleanup_tmp EXIT INT TERM

# Find line number where archive starts
PAYLOAD_LINE=$(awk '/^__ARCHIVE_FOLLOWS__/ {print NR + 1; exit 0;}' "$0")

# Extract archive
tail -n +${PAYLOAD_LINE} "$0" | tar -xzf - -C "${TMP_DIR}"

cd "${TMP_DIR}"

case "$MODE" in
    gui)
        # Check if Python 3 and Tkinter are available
        if ! command -v python3 >/dev/null 2>&1; then
            echo "[!] Error: python3 is required to run the GUI." >&2
            exit 1
        fi
        exec python3 facer_gui.py "$@"
        ;;
    cli)
        if ! command -v python3 >/dev/null 2>&1; then
            echo "[!] Error: python3 is required." >&2
            exit 1
        fi
        exec python3 keyboard.py "$@"
        ;;
    install)
        if [ "$EUID" -ne 0 ]; then
            echo "[!] System installation requires root privileges."
            echo "[*] Re-running with sudo..."
            exec sudo bash "$0" --install
        fi
        bash ./install_service.sh install
        ;;
    uninstall)
        if [ "$EUID" -ne 0 ]; then
            echo "[!] Uninstallation requires root privileges."
            echo "[*] Re-running with sudo..."
            exec sudo bash "$0" --uninstall
        fi
        bash ./install_service.sh remove
        ;;
esac

exit 0

__ARCHIVE_FOLLOWS__
HEADER_EOF

# Append payload binary tarball to script
cat "${TEMP_PAYLOAD_TAR}" >> "${OUTPUT_FILE}"
chmod +x "${OUTPUT_FILE}"

echo "[*] Single-file executable built successfully!"
echo "[*] Output file: ${OUTPUT_FILE}"
echo "[*] Run './AcerPredatorRGB.run' to launch GUI or './AcerPredatorRGB.run --install' to install system-wide."
