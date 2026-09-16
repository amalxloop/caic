# CAIC - Custom Arch ISO Creator

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

The repository currently contains the Cubic source tree, renamed and rebranded
as CAIC, with structurally mechanical changes applied (package name, paths,
icons, imports, and user-facing labels). The **Arch port itself is not complete**
yet — see [PORTING.md](PORTING.md) for the detailed component-by-component plan
and the current state of each item.

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
├── caic_wizard.py       # main entry point
└── caic_wizard.ui       # main GTK window definition
usr/share/applications/caic.desktop
usr/share/bash-completion/completions/caic
usr/share/icons/hicolor/.../apps/caic.*
usr/share/man/man1/caic.1
usr/share/polkit-1/actions/caic.policy
```

## Development

Run from a checkout without installing:

```
python3 usr/share/caic/caic_wizard.py
```

Run the sanity check over the Python sources:

```
python3 -m compileall -q usr/share/caic
```

## Packaging for Arch

A `PKGBUILD` is provided (see [PKGBUILD](PKGBUILD)). Run `makepkg`
from the repository root to build the `caic` package directly from the
checkout (see the BUILD NOTE at the top of the PKGBUILD).

## Acknowledgements

- **PJ Singh** — author of Cubic (Custom Ubuntu ISO Creator).
- [Cubic on GitHub](https://github.com/PJ-Singh-001/Cubic) (
  [on Launchpad](https://launchpad.net/cubic))