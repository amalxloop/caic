# Maintainer: CAIC contributors <caic@example.org>
# CAIC (Custom Arch ISO Creator) -- fork of Cubic (Custom Ubuntu ISO Creator).
# Upstream: https://github.com/PJ-Singh-001/Cubic   (GPL-3)
#
# BUILD NOTE: this PKGBUILD is a scaffold for the fork while it lives in a
# local checkout. `source` is intentionally EMPTY: makepkg is run from the
# repository root and `package()` copies the working tree (usr/, the launcher
# symlink, man pages, polkit policy, bash-completion, icons) directly from
# $startdir. This keeps the build in sync with the port as it is developed,
# without depending on a network fetch.
#
# Before publishing on AUR / a git host:
#   1. Push the fork and replace `source` with your repository, e.g.:
#        source=("$pkgname::git+https://host/$pkgname.git")
#        sha256sums=('SKIP')
#        makedepends=('git')
#   2. Or build from a release tarball of the fork with a real sha256sum.
#   The rest of this file is otherwise generic.

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
    'libisoburn'      # xorriso (generate page, ISO report)
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
    'qemu-full: test the generated ISO in the built-in emulator'
    'edk2-ovmf: UEFI boot testing in the emulator'
    'binwalk: improved compressed-filesystem detection'
)

source=()
sha256sums=()

package() {
    # Build directly from the repository root (see BUILD NOTE above).
    cp -a "$startdir/usr" "$pkgdir"

    # Drop bytecode caches so __pycache__/ never ships in the package.
    find "$pkgdir/usr" -type d -name '__pycache__' -exec rm -rf {} +

    # Ship the per-file copyright / license notes where pacman exposes them.
    install -Dm0644 "$startdir/COPYRIGHT" "$pkgdir/usr/share/licenses/$pkgname/COPYRIGHT"

    # The launcher is a symlink to the actual python wizard. Its target,
    # /usr/share/caic/caic_wizard.py, makes sys.path[0] the caic package
    # parent, so `import caic` works without any PYTHONPATH hack.
    ln -sf /usr/share/caic/caic_wizard.py "$pkgdir/usr/bin/caic"
    chmod 0755 "$pkgdir/usr/share/caic/caic_wizard.py"
    chmod 0755 "$pkgdir"/usr/share/caic/commands/*
}