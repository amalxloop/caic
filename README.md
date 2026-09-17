# CAIC - Custom Arch ISO Creator

Latest tag: [v0.1.0](https://github.com/amalxloop/caic/tree/v0.1.0)

**CAIC** (**C**ustom **A**rch **I**SO **C**reator) is a GUI wizard to create a
customized Live ISO image for **Arch Linux and Arch-based distributions**.

CAIC is a direct fork of
**[Cubic](https://github.com/PJ-Singh-001/Cubic) (Custom Ubuntu ISO Creator)**
by PJ Singh, whose upstream codebase works with Ubuntu and Debian based
distributions but is not compatible with the Arch world. CAIC keeps the Cubic
wizard UX and code architecture while porting every distribution-specific
behaviour to the Arch stack (`pacman`, `arch-chroot`, `mkinitcpio`,
`archiso`/`xorriso`, etc.).

## Project status

The Arch port is **functionally complete**. All distribution-specific
behaviour has been ported and guarded (extract, packages, options, console,
generate/finish), the Debian packaging has been removed in favour of an Arch
`PKGBUILD`, and a headless `build-iso.py` CLI rebuilds the ISO or delegates to
`mkarchiso`. The automated test suites (generate page, packages page, boot
tab, and the `build-iso` harness) pass, and the GTK wizard has been
smoke-tested to launch against the Arch runtime dependencies. See
[PORTING.md](PORTING.md) for the component-by-component plan.

The one thing that cannot be verified in an unprivileged/headless environment
is a **physical end-to-end build** (mounting the source ISO, writing the
root-owned custom disk through `pkexec`, and producing the final image with
`xorriso`/`mksquashfs`). See [VERIFY-E2E.md](VERIFY-E2E.md) or run
`./verify-e2e.sh` on a real Arch system for the checklist.

## Licensing

- The upstream Cubic codebase is distributed under the **GNU General Public
  License v3**. Because CAIC is a derivative of Cubic, CAIC is licensed under
  **GPL v3** as well (see [LICENSE](LICENSE)). It is not possible to relicense
  GPL v3 code under GPL v2; GPL v3 and GPL v2 are incompatible.
- All original copyright notices and GPL headers in the source files are
  preserved. Some auxiliary assets retain their upstream licenses (see
  `COPYRIGHT` for the full upstream per-file list).

## Architecture overview

```
usr/share/caic/
├── caic/                # python package, `import caic.*`
├── commands/            # privileged helper shell scripts (polkit/pkexec)
├── assets/              # icons, mime types, empty.squashfs
├── caic_wizard.py       # main GUI entry point
├── caic_wizard.ui       # main GTK window definition
└── build-iso.py         # headless CLI (stdlib only) for ISO generation
usr/share/applications/caic.desktop
usr/share/bash-completion/completions/caic
usr/share/icons/hicolor/.../apps/caic.*
usr/share/man/man1/caic.1
usr/share/polkit-1/actions/caic.policy
```

## Installation

Build and install the package on Arch (this also pulls in every runtime
dependency listed in the `PKGBUILD`):

```
git clone https://github.com/amalxloop/caic.git
cd caic
makepkg -si
```

To run straight from a checkout instead, install the dependencies first:

```
sudo pacman -S --needed gtk3 python-gobject gtksourceview4 vte3 \
    python-argcomplete python-pyicu python-magic python-packaging \
    python-pexpect python-psutil python-pydbus python-pyinotify python-yaml \
    libisoburn squashfs-tools syslinux mkinitcpio pacman polkit rsync \
    systemd util-linux findutils sed
```

## Usage

### GUI wizard

```
caic [directory] [iso]
```

`directory` is a project directory (new or existing) and `iso` is the original
ISO to base a new project on (ignored when `directory` already exists). The
wizard walks through: **Prepare → Extract → Packages → Options → Console →
Generate**. Run it from a checkout without installing with:

```
python3 usr/share/caic/caic_wizard.py
```

### Headless build

`build-iso.py` rebuilds a project's ISO without the GUI. It is pure Python
standard library, so it works over SSH or in CI.

```
build-iso.py <project-directory> [options]
```

It reads the project's `caic.conf`, copies the kernel/initramfs from the
custom root into the disk layout, builds the squashfs (through
`commands/compress-root`, using `pkexec` when not root), refreshes the
checksums, recreates the attribute alias links, and rebuilds the image with
the project's stored `xorriso` template.

```
build-iso.py ~/caic/MyProject                 # default: xorriso rebuild
build-iso.py ~/caic/MyProject --mkarchiso     # delegate to archiso/mkarchiso
```

Useful flags:

| Flag | Effect |
| --- | --- |
| `--mkarchiso` | Generate an archiso profile and run `mkarchiso` instead of the stored `xorriso` template |
| `--work-directory DIR` | Scratch directory for `--mkarchiso` |
| `--output-directory DIR` | Where the resulting ISO is written |
| `--skip-kernels` | Do not copy kernel/initramfs files |
| `--skip-squashfs` | Reuse the existing squashfs |
| `--skip-checksums` | Do not regenerate checksum files |
| `--dry-run` | Print the commands without executing them |

The default (`xorriso`) mode needs `libisoburn` and `squashfs-tools`.
`--mkarchiso` additionally needs `archiso`. Writing to the root-owned custom
disk needs `polkit`/`pkexec` (or running as root).

## Development

From a checkout:

```
# GUI
python3 usr/share/caic/caic_wizard.py

# headless CLI help / dry run
python3 usr/share/caic/build-iso.py --help
python3 usr/share/caic/build-iso.py <project> --dry-run

# sanity check + test suites
python3 -m compileall -q usr/share/caic
python3 test_generate_page.py
python3 test_packages_page.py
python3 test_boot_tab.py
python3 test_build_iso.py
```

## Packaging for Arch

A `PKGBUILD` is provided (see [PKGBUILD](PKGBUILD)). It builds from the
tagged source repo and can be used directly for an AUR submission. Run
`makepkg -f` to build the `caic` package, or `makepkg -si` to build and
install.

## Acknowledgements

- **PJ Singh** — author of Cubic (Custom Ubuntu ISO Creator).
- [Cubic on GitHub](https://github.com/PJ-Singh-001/Cubic) (
  [on Launchpad](https://launchpad.net/cubic))
