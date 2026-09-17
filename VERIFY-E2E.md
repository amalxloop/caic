# End-to-end verification

The port ships with automated tests
(`test_generate_page.py`, `test_packages_page.py`, `test_boot_tab.py`,
`test_build_iso.py`), but they cannot cover the parts that need a desktop
session and root: mounting the source ISO, writing the root-owned custom disk
through `pkexec`, running `mksquashfs`/`xorriso`, and booting the resulting
image. This file is the runbook for verifying those on a real Arch system.

Run `./verify-e2e.sh [PROJECT_DIR]` first: it performs all the automatable
checks, then prints the manual checklist.

## 1. Install the toolchain

```
sudo pacman -S --needed \
    gtk3 python-gobject gtksourceview4 vte3 \
    python-argcomplete python-pyicu python-magic python-packaging \
    python-pexpect python-psutil python-pydbus python-pyinotify python-yaml \
    libisoburn squashfs-tools syslinux mkinitcpio pacman polkit rsync \
    systemd util-linux findutils sed archiso
```

(`archiso` is only needed for `build-iso.py --mkarchiso`.)

## 2. Build and install CAIC

```
makepkg -si
```

Or, to run from the checkout without installing:

```
python3 usr/share/caic/caic_wizard.py
```

## 3. Automated checks

```
./verify-e2e.sh
```

Expect: all tools/modules found (or clearly warned), `compileall` clean, and
all four test suites passing.

## 4. GUI round trip

1. Start `caic`.
2. **Prepare** -- create a project from a real Arch ISO
   (`archlinux-*.iso`).
3. **Extract** -- confirm the squashfs is unsquashed and the interactive
   console opens (`systemd-nspawn`).
4. **Packages** -- install and remove a package with `pacman-in-root`;
   confirm the change is reflected.
5. **Options** -- confirm hostname, language, timezone, kernel parameters and
   `mkinitcpio` settings populate with sensible Arch defaults; change one to
   confirm persistence.
6. **Generate** -- run compress → checksum → xorriso. Watch for the
   squashfs exclusions (`proc`, `run`, `tmp`, `var/crash`, swapfile, shell
   histories, `root/.cache`) and a clean `xorriso -as mkisofs` invocation.

## 5. Headless rebuild

Once a project exists (from step 4):

```
sudo ./verify-e2e.sh ~/caic/MyProject      # runs the real build-iso.py
```

or directly:

```
sudo usr/share/caic/build-iso.py ~/caic/MyProject
sudo usr/share/caic/build-iso.py ~/caic/MyProject --mkarchiso
```

`--dry-run` (no root needed) prints every command it would run.

## 6. Inspect the image

```
isoinfo -d -i MyProject.iso
xorriso -indev MyProject.iso -report
```

Check the volume id, the BIOS/UEFI boot catalog, and that the squashfs,
`vmlinuz-*` and `initramfs-*.img` are present under `arch/`.

## 7. Boot-test

Boot the image in a VM (the wizard's built-in QEMU launcher, or manually) and,
if possible, on real hardware -- both BIOS and UEFI. Confirm it reaches the
live environment and that your customizations (installed packages, hostname,
etc.) are present.

## Reporting issues

Include: the failing step, the full console output, the project's `caic.conf`
and `caic.log` (if present), the OS/archiso versions, and whether the failure
reproduces with `build-iso.py` outside the GUI.
