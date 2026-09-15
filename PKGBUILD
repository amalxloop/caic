# Maintainer: CAIC contributors <caic@example.org>
# CAIC (Custom Arch ISO Creator) — fork of Cubic (Custom Ubuntu ISO Creator).
# Upstream: https://github.com/PJ-Singh-001/Cubic   (GPL-3)

pkgname=caic
pkgver=0.1.0
pkgrel=1
pkgdesc="GUI wizard to create a customized Live ISO image for Arch Linux and Arch-based distributions (fork of Cubic)"
arch=('any')
url="https://github.com/PJ-Singh-001/Cubic"
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
    'python-python-magic'
    'python-packaging'
    'python-pexpect'
    'python-psutil'
    'python-pydbus'
    'python-pyinotify'
    'python-yaml'
    # System tooling
    'squashfs-tools'     # mksquashfs / unsquashfs (compress-root, extract-root)
    'libisoburn'         # xorriso (generate page, ISO report)
    'syslinux'           # BIOS boot bits (isolinux.*, memdisk)
    'mkinitcpio'         # initramfs regeneration (lsinitcpio)
    'pacman'             # package management inside the chroot
    'arch-install-scripts'  # arch-chroot
    'polkit'             # pkexec
    'rsync'
    'util-linux'
    'coreutils'
)
optdepends=(
    'qemu-full: test the generated ISO in the built-in emulator'
    'edk2-ovmf: UEFI boot testing in the emulator'
    'binwalk: improved compressed-filesystem detection'
)
makedepends=('git')

source=("$pkgname::https://github.com/PJ-Singh-001/Cubic/archive/refs/heads/release.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/$pkgname"

    # Copy the whole usr/ tree (data, python package, icons, man, polkit).
    cp -a usr "$pkgdir"

    # The launcher is a symlink to the actual python wizard.
    ln -sf /usr/share/caic/caic_wizard.py "$pkgdir/usr/bin/caic"
    chmod 0755 "$pkgdir/usr/share/caic/caic_wizard.py"
    chmod 0755 "$pkgdir"/usr/share/caic/commands/*
}