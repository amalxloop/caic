import os, subprocess, sys, tempfile, zlib, importlib.util

sys.path.insert(0, 'usr/share/caic')

spec = importlib.util.spec_from_file_location('build_iso', 'usr/share/caic/build-iso.py')
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)

PASS = 0

def ok(cond, label):
    global PASS
    assert cond, label
    PASS += 1
    print('OK:', label)


def encode(t):
    b = t.encode('utf-8')
    z = zlib.compress(b)
    return z.hex().upper()


def make_project(root):
    """Create a synthetic Arch CAIC project and return its directory."""
    proj = os.path.join(root, 'proj')
    os.makedirs(os.path.join(proj, 'custom-root', 'boot'), exist_ok=True)
    os.makedirs(os.path.join(proj, 'custom-root', 'var/lib/pacman/local/base-1-1'), exist_ok=True)
    os.makedirs(os.path.join(proj, 'custom-disk', 'arch/x86_64'), exist_ok=True)
    os.makedirs(os.path.join(proj, 'custom-disk', 'arch/boot/x86_64'), exist_ok=True)
    os.makedirs(os.path.join(proj, 'custom-temp'), exist_ok=True)
    os.makedirs(os.path.join(proj, 'custom-live'), exist_ok=True)

    with open(os.path.join(proj, 'custom-root', 'boot', 'vmlinuz-linux'), 'wb') as f:
        f.write(b'vmlinuz')
    with open(os.path.join(proj, 'custom-root', 'boot', 'initramfs-linux.img'), 'wb') as f:
        f.write(b'initramfs')
    with open(os.path.join(proj, 'custom-root', 'var/lib/pacman/local/base-1-1', 'desc'), 'w') as f:
        f.write('%NAME%\nbase\n')
    with open(os.path.join(proj, 'custom-disk', 'arch', 'x86_64', 'airootfs.sfs'), 'wb') as f:
        f.write(b'sfs1')
    with open(os.path.join(proj, 'custom-root', 'root.txt'), 'w') as f:
        f.write('hello\n')

    template = ("-b '/arch/boot/syslinux/isolinux.bin' -c '/arch/boot/syslinux/boot.cat' "
                "-no-emul-boot -boot-load-size 4 -boot-info-table "
                "-isohybrid-mbr '/arch/boot/syslinux/isohdpfx.bin' "
                "-eltorito-alt-boot -e '/arch/boot/EFI/archiso/efiboot.img' -no-emul-boot "
                "-V '{volume_id}' -x '{boot_image_directory}/custom-root'")

    conf = f"""[Project]
cubic_version = 0.1.0
create_date = 2026-01-01
modify_date = 2026-01-02
directory = {proj}

[Original]
iso_file_name = archlinux-2026.01.01-x86_64.iso
iso_directory = {proj}
iso_volume_id = ARCH_202601
iso_release_name = 2026.01.01
iso_disk_name = ARCH_202601

[Custom]
iso_version_number = 1
iso_file_name = custom.iso
iso_directory = {proj}
iso_volume_id = CAIC_CUSTOM
iso_release_name = 2026.01.01
iso_disk_name = CAIC_CUSTOM

[Layout]
casper_directory = arch/boot, arch/x86_64, arch/boot/x86_64
squashfs_directory = arch, arch/x86_64
squashfs_file_name = airootfs.sfs
manifest_file_name = pkglist.x86_64.txt
minimal_remove_file_name =
standard_remove_file_name =
size_file_name =
minimal_squashfs_file_name =
standard_squashfs_file_name =
live_squashfs_file_name =
live_generic_squashfs_file_name =
install_sources_file_name =

[Status]
is_success_analyze = True
is_success_copy = True
is_success_extract = True
iso_template = {encode(template)}
iso_checksum =
iso_checksum_file_name =

[Options]
update_os_release = True
has_minimal_install = False
compression = zstd
"""
    with open(os.path.join(proj, 'caic.conf'), 'w') as f:
        f.write(conf)
    return proj


def test_accessors():
    p = bi.Project(make_project(tmp := tempfile.mkdtemp()))
    ok(p.is_arch, 'Arch layout detected')
    ok(p.casper_directory == 'arch/boot/x86_64', f'casper_directory resolved: {p.casper_directory}')
    ok(p.squashfs_directory == 'arch/x86_64', f'squashfs_directory resolved: {p.squashfs_directory}')
    ok(p.squashfs_file_name == 'airootfs.sfs', f'squashfs_file_name resolved: {p.squashfs_file_name}')
    ok(p.compression == 'zstd', f'compression: {p.compression}')
    ok(p.iso_file_name == 'custom.iso', p.iso_file_name)
    ok(not p.has_minimal_install, 'has_minimal_install default False')
    return tmp


def test_decode_roundtrip():
    tpl = "-b '/arch/boot/syslinux/isolinux.bin' -V '{volume_id}'"
    ok(bi.decode(encode(tpl)) == tpl, 'encode/decode roundtrip')
    try:
        bi.decode('XYZ-not-hex')
        ok(False, 'decode should reject non-hex')
    except Exception:
        ok(True, 'decode rejects non-hex')


def test_xorriso_command(tmp):
    p = bi.Project(os.path.join(tmp, 'proj'))
    cmd = bi.get_xorriso_command(p)
    path = os.path.join(p.iso_directory, p.iso_file_name)
    ok(cmd.startswith('xorriso -as mkisofs -r -J -joliet-long -l -iso-level 3'), cmd[:60])
    ok(f'-o "{path}"' in cmd, f'Output path in command: {cmd[-60:]}')
    ok("-V 'CAIC_CUSTOM'" in cmd, 'Volume id substituted')
    ok("'arch/x86_64/airootfs.sfs'" not in cmd, 'No exclude for standard squashfs')


def test_checksums(tmp):
    p = bi.Project(os.path.join(tmp, 'proj'))
    # Real checksums only (pure python); no root required.
    rc = bi.update_checksums(p)
    ok(rc == 0, 'update_checksums returns 0')
    checksums_path = os.path.join(p.custom_disk_directory, 'sha256sums.txt')
    ok(os.path.isfile(checksums_path), 'sha256sums.txt written')
    content = open(checksums_path).read()
    ok('airootfs.sfs' in content, 'airootfs.sfs checksummed')
    ok('sha256sums.txt  ' not in content, 'Checksums file does not reference itself')
    # Re-running update_checksums must not crash (self-exclusion works).
    rc = bi.update_checksums(p)
    ok(rc == 0, 'update_checksums idempotent')


def hashlib_sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def test_copy_kernels(tmp):
    p = bi.Project(os.path.join(tmp, 'proj'))
    rc = bi.copy_kernel_files(p)
    ok(rc == 0, 'copy_kernel_files returns 0')
    target = os.path.join(p.custom_disk_directory, 'arch/boot/x86_64')
    ok(os.path.isfile(os.path.join(target, 'vmlinuz-linux')), 'vmlinuz copied')
    ok(os.path.isfile(os.path.join(target, 'initramfs-linux.img')), 'initramfs copied')


def test_create_links(tmp):
    p = bi.Project(os.path.join(tmp, 'proj'))
    bi.create_links_for_attributes(p)
    # squashfs_directory aliases: 'arch' -> 'arch/x86_64'. In the
    # synthetic project 'arch' is a real directory, so the link goes
    # into the squashfs directory: airootfs.sfs stays a file.
    sfs_path = os.path.join(p.custom_disk_directory, 'arch/x86_64', 'airootfs.sfs')
    ok(os.path.isfile(sfs_path), f'airootfs.sfs present: {sfs_path}')
    # casper_directory aliases only exist when the target is a living dir;
    # assert no exceptions and the standard squashfs alias set was processed.
    link = os.path.join(p.custom_disk_directory, 'arch/x86_64')
    ok(os.path.isdir(link), f'squashfs dir intact: {link}')


def test_mkarchiso_profile(tmp):
    p = bi.Project(os.path.join(tmp, 'proj'))
    work = os.path.join(tmp, 'mkwork')
    os.makedirs(work, exist_ok=True)
    profile = bi.generate_archiso_profile(p, work)
    ok(os.path.isfile(os.path.join(profile, 'profiledef.sh')), 'profiledef.sh generated')
    ok(os.path.isfile(os.path.join(profile, 'pacman.conf')), 'pacman.conf generated')
    packages = open(os.path.join(profile, 'packages.x86_64')).read().splitlines()
    ok('base' in packages, f'packages derived from pacman db: {packages}')
    profiledef = open(os.path.join(profile, 'profiledef.sh')).read()
    ok('iso_name="custom"' in profiledef, 'profiledef iso_name from custom.iso')
    ok('bootmodes=(' in profiledef, 'profiledef bootmodes present')
    ok('install_dir="arch"' in profiledef, 'profiledef install_dir=arch')


def test_ubuntu_layout_not_arch():
    tmp = tempfile.mkdtemp()
    proj = os.path.join(tmp, 'proj')
    os.makedirs(os.path.join(proj, 'custom-root'))
    os.makedirs(os.path.join(proj, 'custom-disk'))
    os.makedirs(os.path.join(proj, 'custom-temp'))
    os.makedirs(os.path.join(proj, 'custom-live'))
    conf = f"""[Project]
directory = {proj}
[Layout]
casper_directory = casper
squashfs_directory = casper
squashfs_file_name = filesystem.squashfs
[Status]
iso_template = {encode('-V {{volume_id}}')}
[Custom]
iso_file_name = custom.iso
iso_directory = {proj}
[Options]
compression = gzip
"""
    with open(os.path.join(proj, 'caic.conf'), 'w') as f:
        f.write(conf)
    p = bi.Project(proj)
    ok(not p.is_arch, 'Ubuntu layout not Arch')
    ok(not bi.checksums_files_name(p.is_arch) == 'sha256sums.txt', 'Ubuntu uses md5sum.txt (is_arch False)')


def test_dry_run_does_not_require_mkarchiso(tmp):
    p = bi.Project(os.path.join(tmp, 'proj'))
    # build_iso.main() is exercised via run() below with --dry-run.
    args = type('A', (), {
        'mkarchiso': True, 'dry_run': True,
        'work_directory': None, 'output_directory': None,
        'skip_kernels': False, 'skip_squashfs': False, 'skip_checksums': False})()
    rc = bi.build_with_mkarchiso(p, args)
    ok(rc == 0, 'mkarchiso dry-run returns 0 without mkarchiso installed')


def test_main_help_and_full_dry(tmp):
    r = subprocess.run([sys.executable, 'usr/share/caic/build-iso.py', '--help'],
                       capture_output=True, text=True)
    ok(r.returncode == 0 and 'project_directory' in r.stdout, '--help works')
    r = subprocess.run([sys.executable, 'usr/share/caic/build-iso.py',
                        os.path.join(tmp, 'proj'), '--dry-run'],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    ok(r.returncode == 0, 'dry-run returns 0')
    ok('Creating ISO image' in out, 'xorriso step invoked')
    ok('Compressing the Linux file system' in out, 'squashfs step invoked')
    ok('sha256sums.txt' in out, 'checksums step invoked')


def test_pkexec_fallback_present(tmp):
    p = bi.Project(os.path.join(tmp, 'proj'))
    # compress-root wrapper exists check (function returns path only); verify commands dir.
    command_directory = os.path.join('usr/share/caic', 'commands')
    ok(os.path.isfile(os.path.join(command_directory, 'compress-root')), 'compress-root command exists')


def main():
    tmp = test_accessors()
    test_decode_roundtrip()
    test_xorriso_command(tmp)
    test_checksums(tmp)
    test_copy_kernels(tmp)
    test_create_links(tmp)
    test_mkarchiso_profile(tmp)
    test_dry_run_does_not_require_mkarchiso(tmp)
    test_main_help_and_full_dry(tmp)
    test_ubuntu_layout_not_arch()
    test_pkexec_fallback_present(tmp)
    print(f'ALL BUILD-ISO TESTS PASSED ({PASS} checks)')


if __name__ == '__main__':
    main()