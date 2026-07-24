#!/bin/bash
# =============================================================
#  Shipsar Developers - GitHub Release Publisher
#  Builds all packages and creates a GitHub Release with assets
#  Usage:
#    ./release_github.sh              → Builds + Releases revision 02
#    BUILD_NUM=03 ./release_github.sh → Builds + Releases revision 03
#    ./release_github.sh --skip-build → Only publish existing dist/ files
# =============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"

# ---- Version Config ----
BUILD_NUM="${BUILD_NUM:-02}"
export BUILD_NUM
DATE_VER="1.20260725"
FULL_VERSION="${DATE_VER}-${BUILD_NUM}"
TAG="v${FULL_VERSION}"
REPO="shipsar/acer-gaming-laptop-rgb-lights-gui"

# ---- Colors ----
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
RESET='\033[0m'

echo ""
echo -e "${CYAN}============================================================${RESET}"
echo -e "${CYAN}  Shipsar Developers - GitHub Release Publisher             ${RESET}"
echo -e "${CYAN}  Version: ${YELLOW}${FULL_VERSION}${CYAN}  Tag: ${YELLOW}${TAG}${RESET}"
echo -e "${CYAN}============================================================${RESET}"
echo ""

# ---- Prerequisite Checks ----
if ! command -v gh >/dev/null 2>&1; then
    echo -e "${RED}[!] GitHub CLI (gh) is not installed.${RESET}"
    echo -e "${YELLOW}    Install it with: sudo apt install gh${RESET}"
    echo -e "${YELLOW}    Then authenticate: gh auth login${RESET}"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo -e "${RED}[!] GitHub CLI is not authenticated.${RESET}"
    echo -e "${YELLOW}    Run: gh auth login${RESET}"
    exit 1
fi

# ---- Optional: Skip Build ----
SKIP_BUILD=false
for arg in "$@"; do
    if [[ "$arg" == "--skip-build" ]]; then
        SKIP_BUILD=true
    fi
done

if [[ "$SKIP_BUILD" == "false" ]]; then
    echo -e "${CYAN}[1/4] Building all release packages...${RESET}"
    bash "${SCRIPT_DIR}/build_all.sh"
    echo ""
else
    echo -e "${YELLOW}[!] Skipping build step (--skip-build specified). Using existing dist/ files.${RESET}"
fi

# ---- Verify dist files exist ----
echo -e "${CYAN}[2/4] Verifying build artifacts...${RESET}"

DEB_FILE="${DIST_DIR}/shipsar-acer-rgb-controller_${FULL_VERSION}_all.deb"
ARCH_FILE="${DIST_DIR}/acer-predator-turbo-rgb-arch-source.tar.gz"
RUN_FILE="${DIST_DIR}/AcerPredatorRGB.run"

MISSING=0
for f in "$DEB_FILE" "$ARCH_FILE" "$RUN_FILE"; do
    if [ -f "$f" ]; then
        echo -e "  ${GREEN}[✔]${RESET} Found: $(basename "$f")"
    else
        echo -e "  ${RED}[✘]${RESET} Missing: $(basename "$f")"
        MISSING=$((MISSING + 1))
    fi
done

if [[ $MISSING -gt 0 ]]; then
    echo -e "${RED}[!] $MISSING artifact(s) missing. Run ./build_all.sh first or remove --skip-build.${RESET}"
    exit 1
fi

# ---- Commit & Push code changes ----
echo ""
echo -e "${CYAN}[3/4] Committing and pushing code changes to GitHub...${RESET}"

cd "${SCRIPT_DIR}"

# Stage all changes (excluding dist binaries via .gitignore)
git add --all .
git status --short

if git diff --cached --quiet; then
    echo -e "${YELLOW}  [i] No staged changes to commit. Skipping commit step.${RESET}"
else
    git commit -m "Release v${FULL_VERSION}: Build revision ${BUILD_NUM}

- Updated GUI with Light/Dark Mode, About Developer section
- Lead Developer: Vijay Kumar | Shipsar Developers
- Website: https://shipsar.in
- Build: ${FULL_VERSION}"
fi

# Push to current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "  Pushing to branch: ${YELLOW}${CURRENT_BRANCH}${RESET}"
git push -u origin "${CURRENT_BRANCH}"

# ---- Create GitHub Release & Upload Assets ----
echo ""
echo -e "${CYAN}[4/4] Creating GitHub Release ${YELLOW}${TAG}${CYAN}...${RESET}"

# Delete existing release/tag if it already exists (allows re-release on same version)
if gh release view "${TAG}" --repo "${REPO}" >/dev/null 2>&1; then
    echo -e "${YELLOW}  [!] Release ${TAG} already exists. Deleting and re-creating...${RESET}"
    gh release delete "${TAG}" --repo "${REPO}" --yes || true
    git tag -d "${TAG}" 2>/dev/null || true
    git push origin ":refs/tags/${TAG}" 2>/dev/null || true
fi

RELEASE_NOTES="## Shipsar Acer RGB Controller — v${FULL_VERSION}

> **Developed by Shipsar Developers 🇮🇳 | Lead Developer: Vijay Kumar**
> Official Website: [shipsar.in](https://shipsar.in)
> GitHub: [github.com/shipsar](https://github.com/shipsar)

---

### What's New in v${FULL_VERSION}
- ⚡ Light Mode / Dark Mode theme switcher
- 🇮🇳 Tiranga RGB keyboard preset (Saffron, White, Green)
- 🎮 Cyberpunk, Gaming & Stealth presets
- ℹ️ About Developer section with shipsar.in link
- 🛡️ Hardware status indicator & Turbo Fan quick toggle
- 🚀 Terminal command: \`rgb-controller\`
- 📦 Build Revision: ${BUILD_NUM}

---

### Installation

#### Ubuntu / Debian
\`\`\`bash
sudo apt install ./shipsar-acer-rgb-controller_${FULL_VERSION}_all.deb
\`\`\`

#### Universal (All Distros)
\`\`\`bash
chmod +x AcerPredatorRGB.run
./AcerPredatorRGB.run --install
\`\`\`

#### Arch Linux
Extract \`acer-predator-turbo-rgb-arch-source.tar.gz\` and run \`makepkg -si\`

---

### Launch the GUI
\`\`\`bash
rgb-controller
\`\`\`
Or find **Shipsar Acer RGB Controller** in your Application Menu.

---

> This project is inspired from https://github.com/JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module"

gh release create "${TAG}" \
    --repo "${REPO}" \
    --title "Shipsar Acer RGB Controller v${FULL_VERSION}" \
    --notes "${RELEASE_NOTES}" \
    "${DEB_FILE}" \
    "${ARCH_FILE}" \
    "${RUN_FILE}"

echo ""
echo -e "${GREEN}============================================================${RESET}"
echo -e "${GREEN}  [✔] GitHub Release Published Successfully!               ${RESET}"
echo -e "${GREEN}  Tag:     ${YELLOW}${TAG}${RESET}"
echo -e "${GREEN}  Repo:    ${YELLOW}https://github.com/${REPO}/releases/tag/${TAG}${RESET}"
echo -e "${GREEN}============================================================${RESET}"
echo ""
