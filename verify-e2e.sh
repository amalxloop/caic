#!/usr/bin/env bash
#
# CAIC end-to-end verification helper.
#
# This script cannot perform the privileged, GUI-driven parts of a real ISO
# build by itself. It does everything that is automatable -- dependency and
# toolchain checks, the Python import check, and the unit test suites -- then
# prints the manual checklist for the parts that need a desktop session and
# root (see VERIFY-E2E.md).
#
# Usage:
#   ./verify-e2e.sh [PROJECT_DIR]
#
# If PROJECT_DIR is supplied it must already contain a caic.conf (i.e. a
# project created by the GUI). The script then runs `build-iso.py --dry-run`
# against it and, when running as root, the real build.

set -uo pipefail

PASS=0
FAIL=0
WARN=0
PROJECT_DIR="${1:-}"

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUILD_ISO="$REPO_DIR/usr/share/caic/build-iso.py"

say()  { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
ok()   { printf '  \033[32mOK\033[0m   %s\n' "$*"; PASS=$((PASS + 1)); }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$*"; FAIL=$((FAIL + 1)); }
warn() { printf '  \033[33mWARN\033[0m %s\n' "$*"; WARN=$((WARN + 1)); }
info() { printf '       %s\n' "$*"; }

say "Environment"
info "repository : $REPO_DIR"
info "user       : $(id -un) (uid $(id -u))"
if [ "$(id -u)" -eq 0 ]; then
    info "privilege  : root (real builds can run)"
else
    info "privilege  : unprivileged (real builds need sudo or pkexec)"
fi

say "Required command-line tools"
check_tool() {
    local cmd="$1" pkg="$2"
    if command -v "$cmd" >/dev/null 2>&1; then
        ok "$cmd ($pkg)"
    else
        warn "$cmd not found -- install '$pkg'"
    fi
}
check_tool python3   python
check_tool xorriso   libisoburn
check_tool mksquashfs squashfs-tools
check_tool unsquashfs squashfs-tools
check_tool pkexec    polkit
check_tool mkinitcpio mkinitcpio
check_tool rsync     rsync
check_tool mkarchiso archiso

say "Python modules used by the wizard"
check_pymod() {
    local mod="$1" pkg="$2"
    if python3 -c "import $mod" >/dev/null 2>&1; then
        ok "$mod ($pkg)"
    else
        warn "cannot import $mod -- install '$pkg'"
    fi
}
check_pymod gi          python-gobject
check_pymod pexpect     python-pexpect
check_pymod psutil      python-psutil
check_pymod magic       python-magic
check_pymod yaml        python-yaml
check_pymod pydbus      python-pydbus
check_pymod pyinotify   python-pyinotify
check_pymod packaging   python-packaging
check_pymod icu         python-pyicu

say "Byte-compilation"
if python3 -m compileall -q "$REPO_DIR/usr/share/caic" >/dev/null 2>&1; then
    ok "compileall usr/share/caic"
else
    bad "compileall usr/share/caic"
fi

say "Test suites"
for test_file in test_generate_page.py test_packages_page.py test_boot_tab.py test_build_iso.py; do
    if [ ! -f "$REPO_DIR/$test_file" ]; then
        warn "$test_file missing"
        continue
    fi
    if output="$(cd "$REPO_DIR" && python3 "$test_file" 2>&1)"; then
        ok "$test_file -- $(printf '%s' "$output" | tail -n 1)"
    else
        bad "$test_file"
        printf '%s\n' "$output" | sed 's/^/       /'
    fi
done

if [ -n "$PROJECT_DIR" ]; then
    say "build-iso.py against $PROJECT_DIR"
    if [ ! -f "$PROJECT_DIR/caic.conf" ]; then
        bad "no caic.conf in $PROJECT_DIR (not a CAIC project?)"
    else
        if output="$(python3 "$BUILD_ISO" "$PROJECT_DIR" --dry-run 2>&1)"; then
            ok "dry run (xorriso template mode)"
        else
            bad "dry run (xorriso template mode)"
            printf '%s\n' "$output" | sed 's/^/       /'
        fi
        if output="$(python3 "$BUILD_ISO" "$PROJECT_DIR" --mkarchiso --dry-run 2>&1)"; then
            ok "dry run (--mkarchiso mode)"
        else
            bad "dry run (--mkarchiso mode)"
            printf '%s\n' "$output" | sed 's/^/       /'
        fi
        if [ "$(id -u)" -eq 0 ]; then
            info "running REAL build-iso.py as root..."
            if python3 "$BUILD_ISO" "$PROJECT_DIR"; then
                ok "real build (xorriso template mode)"
            else
                bad "real build (xorriso template mode)"
            fi
        else
            warn "skipping real build (re-run with sudo: sudo $0 $PROJECT_DIR)"
        fi
    fi
fi

printf '\n\033[1m== Summary ==\033[0m\n'
printf '  passed: %d   failed: %d   warnings: %d\n' "$PASS" "$FAIL" "$WARN"

say "Manual checklist (not automatable here)"
cat <<'EOF'
  1. Launch the GUI:            caic   (or python3 usr/share/caic/caic_wizard.py)
  2. New project from a real Arch ISO (e.g. an archlinux-*.iso).
  3. Extract -- confirm unsquashfs succeeds and the console opens.
  4. Packages -- confirm pacman-in-root install/remove works.
  5. Options  -- confirm defaults populate; change one to test persistence.
  6. Generate -- let it compress, checksum and xorriso the image.
  7. Verify the output image:
        isoinfo -d -i <image>.iso          # volume id / boot catalog
        xorriso -indev <image>.iso -report
  8. Boot-test it in a VM (qemu) or on real hardware (BIOS and UEFI).
  9. Repeat the generate step with build-iso.py --mkarchiso for the
     archiso profile path.

  Report any failure with the full console output and the project's
  caic.conf. See VERIFY-E2E.md for details.
EOF

[ "$FAIL" -eq 0 ]
