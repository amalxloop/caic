# Maintainer: CAIC contributors <caic@example.org>
# CAIC (Custom Arch ISO Creator) -- fork of Cubic (Custom Ubuntu ISO Creator).
# Upstream: https://github.com/PJ-Singh-001/Cubic   (GPL-3)
#
# This is the AUR-ready PKGBUILD. It builds from a tagged source tarball of
# the fork's git repository:
#
#   source=("$pkgname::git+https://github.com/amalxloop/caic.git#tag=v$pkgver")
#
# AUR submission checklist (run from a checkout of the AUR package repo):
#   1. makepkg --printsrcinfo > .SRCINFO   (the .SRCINFO is committed here)
#   2. makepkg -f                          (verify a clean build)
#   3. git add PKGBUILD .SRCINFO && git commit && git push
#
# To develop against the working tree instead of the remote tag, copy this
# PKGBUILD to a scratch directory, set source=() and point package() at
# $startdir (see `git log` for the previous local-build form), or simply run
# the wizard from the checkout with `python3 usr/share/caic/caic_wizard.py`.

pkgname=caic
pkgver=0.1.0
pkgrel=1
pkgdesc="GUI wizard to create a customized Live ISO image for Arch Linux and Arch-based distributions (fork of Cubic)"
arch=('any')
url="https://github.com/amalxloop/caic"
license=('GPL3')
depends=(
    # GUI + GI bindings
    'gtk3'
    'python-gobject'
    'gtksourceview4'
    'vte3'
    # Python utilities used by the wizard
    'python-argcomplete'
    'python-pyicu'
    'python-magic'
    'python-packaging'
    'python-pexpect'
    'python-psutil'
    'python-pydbus'
    'python-pyinotify'
    'python-yaml'
    # System tooling
    'coreutils'       # dd, du, rm, wc, sha256sum
    'findutils'       # find (move-path, merge-directory)
    'libisoburn'      # xorriso (generate page, ISO report, build-iso.py)
    'mkinitcpio'      # lsinitcpio (initrd inspection)
    'pacman'          # package management inside the chroot
    'polkit'          # pkexec
    'rsync'
    'sed'             # replace-text command
    'squashfs-tools'  # mksquashfs / unsquashfs (compress-root, extract-root)
    'syslinux'        # BIOS boot bits (isolinux.*, isohdpfx.bin)
    'systemd'         # systemd-nspawn, machinectl (console, pacman-in-root, mount helpers)
    'util-linux'      # mount, umount (mount-iso, unmount-iso)
)
optdepends=(
    'archiso: build the ISO with `build-iso.py --mkarchiso`'
    'qemu-full: test the generated ISO in the built-in emulator'
    'edk2-ovmf: UEFI boot testing in the emulator'
    'binwalk: improved compressed-filesystem detection'
)
makedepends=('git')

source=("$pkgname::git+https://github.com/amalxloop/caic.git#tag=v$pkgver")
sha256sums=('SKIP')

package() {
    local srcdir_tree="$srcdir/$pkgname"

    # The repository ships the final on-disk layout under usr/, so the
    # "build" is a straight copy of the working tree.
    cp -a "$srcdir_tree/usr" "$pkgdir"

    # Drop bytecode caches so __pycache__/ never ships in the package.
    find "$pkgdir/usr" -type d -name '__pycache__' -exec rm -rf {} +

    # Ship the per-file copyright / license notes where pacman exposes them.
    install -Dm0644 "$srcdir_tree/COPYRIGHT" "$pkgdir/usr/share/licenses/$pkgname/COPYRIGHT"

    # The launcher is a symlink to the actual python wizard. Its target,
    # /usr/share/caic/caic_wizard.py, makes sys.path[0] the caic package
    # parent, so `import caic` works without any PYTHONPATH hack.
    ln -sf /usr/share/caic/caic_wizard.py "$pkgdir/usr/bin/caic"
    chmod 0755 "$pkgdir/usr/share/caic/caic_wizard.py"

    # Headless CLI (stdlib only) for rebuilding the ISO or driving mkarchiso.
    ln -sf /usr/share/caic/build-iso.py "$pkgdir/usr/bin/build-iso"

    # Privileged helper scripts invoked through polkit/pkexec.
    chmod 0755 "$pkgdir"/usr/share/caic/commands/*
}
