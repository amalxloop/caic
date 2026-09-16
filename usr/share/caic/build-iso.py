#!/usr/bin/python3

########################################################################
#                                                                      #
# build-iso.py                                                         #
#                                                                      #
# Build a customized Arch Linux (or Ubuntu) ISO from a CAIC project.   #
#                                                                      #
# Copyright (C) 2026 CAIC contributors                                 #
#                                                                      #
# This file is part of CAIC - Custom Arch ISO Creator.                 #
#                                                                      #
# CAIC is free software: you can redistribute it and/or modify         #
# it under the terms of the GNU General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or    #
# (at your option) any later version.                                  #
#                                                                      #
# CAIC is distributed in the hope that it will be useful,              #
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the         #
# GNU General Public License for more details.                         #
#                                                                      #
# You should have received a copy of the GNU General Public License    #
# along with CAIC. If not, see <http://www.gnu.org/licenses/>.         #
#                                                                      #
########################################################################

########################################################################
# References
########################################################################

# N/A

########################################################################
# Imports
########################################################################

import argparse
import configparser
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zlib

# The project directory names for CAIC.
CUSTOM_ROOT_DIRECTORY = 'custom-root'
CUSTOM_LIVE_DIRECTORY = 'custom-live'
CUSTOM_DISK_DIRECTORY = 'custom-disk'
CUSTOM_TEMP_DIRECTORY = 'custom-temp'

# The configuration file in the project directory.
CONFIGURATION_FILE_NAME = 'caic.conf'

# The default squashfs compression.
DEFAULT_COMPRESSION = 'gzip'

# Files excluded from the root squashfs. See commands/compress-root.
SQUASHFS_EXCLUDE_PATTERNS = (
    'proc/*', 'proc/.*',
    'run/*', 'run/.*',
    'tmp/*', 'tmp/.*',
    'var/crash/*', 'var/crash/.*',
    'swapfile',
    'root/.bash_history', 'root/.cache', 'root/.wget-hsts',
    'home/*/.bash_history', 'home/*/.cache', 'home/*/.wget-hsts',
)

# An archiso profile is required by mkarchiso. See the following
# references:
# https://wiki.archlinux.org/title/archiso
# https://gitlab.archlinux.org/archlinux/archiso/blob/master/docs/mkarchiso.1.adoc
ARCHISO_PACMAN_CONF = '''
[options]
HoldPkg= pacman glibc
Architecture = auto
SigLevel = Required DatabaseOptional
LocalFileSigLevel = Optional

[core]
Include = /etc/pacman.d/mirrorlist

[extra]
Include = /etc/pacman.d/mirrorlist

[multilib]
Include = /etc/pacman.d/mirrorlist
'''


########################################################################
# Helper Functions
########################################################################


def get_list(config, section, key, default=None):
    """Get a comma delimited value as a list of trimmed, unique values."""

    value = config.get(section, key, fallback=None)
    if not value or not value.strip():
        return default
    values = []
    for item in value.split(','):
        item = item.strip()
        if item and item not in values:
            values.append(item)
    return values


def get_attribute(config, section, key, default=''):
    """Get the last valid attribute value from the configuration."""

    values = get_list(config, section, key, default=None)
    if not values:
        return default
    return values[-1]


def decode(t):
    """Decode a hex string (zlib compressed) into text."""

    z = bytes.fromhex(t)
    b = zlib.decompress(z)
    return b.decode('utf-8')


def run(command, working_directory=None, dry_run=False):
    """Run a command, or print it when dry_run is True."""

    if dry_run:
        print(f'[dry-run] {command}')
        return 0
    result = subprocess.run(command, cwd=working_directory, shell=(isinstance(command, str)))
    return result.returncode


def create_link(directory_path, file_name, link_name, dry_run=False):
    """Create a symbolic link from link_name to file_name."""

    if not file_name or not link_name:
        return
    file_name = file_name.strip()
    link_name = link_name.strip()
    if not file_name or not link_name:
        return
    link_path = os.path.join(directory_path, link_name)
    if file_name != link_name and os.path.isfile(link_path) and not os.path.islink(link_path):
        os.remove(link_path)
    try:
        if dry_run:
            print(f'[dry-run] ln -sfn "{file_name}" "{link_path}"')
        else:
            if os.path.islink(link_path) or (file_name != link_name and os.path.exists(link_path)):
                os.remove(link_path)
            os.symlink(file_name, link_path)
    except OSError as exception:
        print(f'Error. Unable to create link {link_path}. The exception is {exception}', file=sys.stderr)


def calculate_hash(file_path, algorithm='sha256', buffer_size=2**20):
    """Calculate the hash of a file."""

    if os.path.islink(file_path):
        return None
    if algorithm == 'md5':
        hash_algorithm = hashlib.md5()
    else:
        hash_algorithm = hashlib.sha256()
    with open(file_path, 'rb') as file:
        data = file.read(buffer_size)
        while data:
            hash_algorithm.update(data)
            data = file.read(buffer_size)
    return hash_algorithm.hexdigest()


########################################################################
# Project Functions
########################################################################


class Project:
    """A CAIC project: loads <project>/caic.conf and resolves paths."""

    def __init__(self, project_directory, dry_run=False):
        self.directory = os.path.abspath(project_directory)
        self.dry_run = dry_run
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.optionxform = str
        self.config.read(self._configuration_file_path())
        self.custom_root_directory = None
        self.custom_live_directory = None
        self.custom_disk_directory = None
        self.custom_temp_directory = None
        self.is_arch = False
        self.casper_directory = None
        self.squashfs_directory = None
        self.squashfs_file_name = None
        self.minimal_squashfs_file_name = None
        self.live_squashfs_file_name = None
        self.live_generic_squashfs_file_name = None
        self.standard_squashfs_file_name = None
        self.minimal_remove_file_name = None
        self.standard_remove_file_name = None
        self.install_sources_file_name = None
        self.iso_template = None
        self.iso_file_name = None
        self.iso_directory = None
        self.iso_volume_id = None
        self.iso_release_name = None
        self.has_minimal_install = False
        self.compression = DEFAULT_COMPRESSION
        self._load()

    def _configuration_file_path(self):
        """Get the project configuration file path."""

        return os.path.join(self.directory, CONFIGURATION_FILE_NAME)

    @staticmethod
    def _is_arch_squashfs_directory(squashfs_directory):
        """Return True if the squashfs directory indicates an Arch layout."""

        return bool(squashfs_directory) and squashfs_directory.startswith('arch')

    def _load(self):
        """Load the layout from the project configuration file."""

        if not os.path.isfile(self._configuration_file_path()):
            raise FileNotFoundError(
                f'Error. The project configuration file does not exist: {self._configuration_file_path()}')

        # Phase 1: project directories.
        self.custom_root_directory = os.path.join(self.directory, CUSTOM_ROOT_DIRECTORY)
        self.custom_live_directory = os.path.join(self.directory, CUSTOM_LIVE_DIRECTORY)
        self.custom_disk_directory = os.path.join(self.directory, CUSTOM_DISK_DIRECTORY)
        self.custom_temp_directory = os.path.join(self.directory, CUSTOM_TEMP_DIRECTORY)

        # Phase 2: layout attributes.
        self.casper_directory = get_attribute(self.config, 'Layout', 'casper_directory')
        self.squashfs_directory = get_attribute(self.config, 'Layout', 'squashfs_directory')
        self.squashfs_file_name = get_attribute(self.config, 'Layout', 'squashfs_file_name')
        self.minimal_squashfs_file_name = get_attribute(self.config, 'Layout', 'minimal_squashfs_file_name')
        self.standard_squashfs_file_name = get_attribute(self.config, 'Layout', 'standard_squashfs_file_name')
        self.live_squashfs_file_name = get_attribute(self.config, 'Layout', 'live_squashfs_file_name')
        self.live_generic_squashfs_file_name = get_attribute(self.config, 'Layout', 'live_generic_squashfs_file_name')
        self.minimal_remove_file_name = get_attribute(self.config, 'Layout', 'minimal_remove_file_name')
        self.standard_remove_file_name = get_attribute(self.config, 'Layout', 'standard_remove_file_name')
        self.install_sources_file_name = get_attribute(self.config, 'Layout', 'install_sources_file_name')

        # Phase 3: status attributes.
        self.iso_template = self.config.get('Status', 'iso_template', fallback=None)

        # Phase 4: custom ISO attributes.
        self.iso_file_name = self.config.get('Custom', 'iso_file_name', fallback=None)
        self.iso_directory = self.config.get('Custom', 'iso_directory', fallback=None)
        self.iso_volume_id = self.config.get('Custom', 'iso_volume_id', fallback=None)
        self.iso_release_name = self.config.get('Custom', 'iso_release_name', fallback=None)

        # Phase 5: options.
        self.has_minimal_install = self.config.getboolean('Options', 'has_minimal_install', fallback=False)
        compression = self.config.get('Options', 'compression', fallback=None)
        if compression and compression.strip():
            self.compression = compression.strip()

        # Phase 6: determine the layout type.
        self.is_arch = self._is_arch_squashfs_directory(self.squashfs_directory)


########################################################################
# Build Functions
########################################################################


def copy_kernel_files(project):
    """Best-effort copy of the Arch kernel boot files into the custom disk."""

    if not project.is_arch:
        print('Skipping kernel copy. This step is only supported for Arch layouts.')
        return 0

    casper_directory = os.path.join(project.custom_disk_directory, project.casper_directory)
    boot_directory = os.path.join(project.custom_root_directory, 'boot')
    if not os.path.isdir(casper_directory):
        print(f'Error. The casper (boot) directory does not exist: {casper_directory}', file=sys.stderr)
        return 1
    if not os.path.isdir(boot_directory):
        print(f'Skipping kernel copy. The custom root boot directory does not exist: {boot_directory}')
        return 0

    # Identify the kernel and initramfs files in the custom root boot
    # directory. The first match is used, mirroring the GUI behavior.
    kernel_files = sorted(glob.glob(os.path.join(boot_directory, 'vmlinuz-*')))
    initramfs_files = sorted(
        glob.glob(os.path.join(boot_directory, 'initramfs-*.img')) +
        glob.glob(os.path.join(boot_directory, 'initrd-*')) +
        glob.glob(os.path.join(boot_directory, 'initramfs.img')))
    if not kernel_files:
        print(f'Skipping kernel copy. No kernel files found in {boot_directory}')
        return 0
    if not initramfs_files:
        print(f'Skipping kernel copy. No initramfs files found in {boot_directory}')
        return 0

    # Delete existing boot files in the target directory.
    for pattern in ('vmlinuz*', 'initrd*', 'initramfs*'):
        for file_path in glob.glob(os.path.join(casper_directory, pattern)):
            if os.path.isfile(file_path) or os.path.islink(file_path):
                if project.dry_run:
                    print(f'[dry-run] rm -f "{file_path}"')
                else:
                    os.remove(file_path)

    for file_path in kernel_files[:1] + initramfs_files[:1]:
        target = os.path.join(casper_directory, os.path.basename(file_path))
        print(f'Copying {file_path} to {target}')
        if not project.dry_run:
            shutil.copy2(file_path, target)

    return 0


def create_squashfs(project, source_file_path, target_file_path, file_number=0, total_files=1):
    """Compress a directory into a squashfs file, mirroring commands/compress-root."""

    target_directory = os.path.dirname(target_file_path)
    if target_directory and not os.path.isdir(target_directory):
        os.makedirs(target_directory)

    labels = ['first', 'second', 'third', 'fourth', 'fifth']
    if total_files > 1:
        text = labels[min(file_number, len(labels) - 1)]
        print(f'Compressing Linux file system ({text} of {total_files})...')
    else:
        print('Compressing the Linux file system...')

    # Prefer the CAIC compress-root wrapper, which runs mksquashfs with
    # the standard exclude patterns, exactly as the GUI does. Because the
    # custom disk is usually owned by root, run the wrapper through
    # pkexec unless the user is already root.
    command_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commands')
    compress_root = os.path.join(command_directory, 'compress-root')
    if os.path.isfile(compress_root):
        if os.geteuid() == 0:
            command = [compress_root, source_file_path, target_file_path, project.compression]
        else:
            command = ['pkexec', compress_root, source_file_path, target_file_path, project.compression]
    else:
        command = ['mksquashfs', source_file_path, target_file_path,
                   '-noappend', '-comp', project.compression, '-wildcards', '-e']
        command.extend(SQUASHFS_EXCLUDE_PATTERNS)
    print(f'Using {project.compression} compression.')
    if project.dry_run:
        print(f'[dry-run] {" ".join(command)}')
        return 0
    return run(command)


def update_checksums(project):
    """Update the checksums file on the custom disk (sha256sums.txt for Arch)."""

    if project.is_arch:
        checksums_file_name = 'sha256sums.txt'
        hash_algorithm = 'sha256'
    else:
        checksums_file_name = 'md5sum.txt'
        hash_algorithm = 'md5'

    checksums_file_path = os.path.join(project.custom_disk_directory, checksums_file_name)
    start_directory = project.custom_disk_directory

    # Identify the file paths to exclude from the checksums.
    exclude_paths = [checksums_file_path]
    template = decode(project.iso_template)
    for option in ('-b', '-c'):
        result = re.search(rf"{option} '(.*?)'", template)
        if result:
            file_path = result.group(1).strip(os.path.sep)
            file_path = os.path.join(project.custom_disk_directory, file_path)
            exclude_paths.append(file_path)
    if project.minimal_remove_file_name and not project.has_minimal_install:
        file_path = os.path.join(project.custom_disk_directory, project.squashfs_directory,
                                 project.minimal_remove_file_name)
        exclude_paths.append(file_path)
    if project.install_sources_file_name:
        file_path = os.path.join(project.custom_disk_directory, project.squashfs_directory,
                                 f'{project.install_sources_file_name}.original')
        exclude_paths.append(file_path)

    # Get relative file paths to include in the checksums.
    file_paths = []
    for directory_path, directory_names, file_names in os.walk(start_directory):
        if directory_path in exclude_paths:
            continue
        for file_name in file_names:
            file_path = os.path.join(directory_path, file_name)
            if file_path in exclude_paths:
                continue
            file_paths.append(os.path.relpath(file_path, start_directory))
    file_paths.sort(key=lambda file_path: file_path.lower())

    total_files = len(file_paths)
    if total_files == 0:
        print(f'Error. Unable to update checksums. No files found in {checksums_file_path}', file=sys.stderr)
        return 1

    print(f'Calculating checksums for {total_files} files ({checksums_file_name})...')
    if project.dry_run:
        print(f'[dry-run] write {checksums_files_name(project.is_arch)} with {total_files} entries')
        return 0

    line_separator = ''
    with open(checksums_file_path, 'w') as file:
        for file_path in file_paths:
            full_file_path = os.path.join(start_directory, file_path)
            try:
                checksum = calculate_hash(full_file_path, algorithm=hash_algorithm)
            except OSError as exception:
                print(f'Skipping file {file_path}. The exception is {exception}')
                continue
            if checksum:
                file.write(f'{line_separator}{checksum}  ./{file_path}')
                line_separator = os.linesep

    print(f'Calculated checksums for {total_files} files.')
    return 0


def checksums_files_name(is_arch):
    """Get the checksums file name for the layout."""

    return 'sha256sums.txt' if is_arch else 'md5sum.txt'


def create_links_for_attributes(project):
    """If an attribute has more than one valid value, create links."""

    def create_links(attribute, directory_path):
        values = get_list(project.config, 'Layout', attribute, default=[])
        if len(values) > 1:
            file_name = values[-1]
            for link_name in values[:-1]:
                create_link(directory_path, file_name, link_name, project.dry_run)

    create_links('casper_directory', project.custom_disk_directory)
    squashfs_directory_path = os.path.join(project.custom_disk_directory, project.squashfs_directory)
    create_links('squashfs_directory', project.custom_disk_directory)
    for attribute in (
        'squashfs_file_name', 'manifest_file_name', 'minimal_remove_file_name',
        'standard_remove_file_name', 'size_file_name', 'minimal_squashfs_file_name',
        'minimal_manifest_file_name', 'minimal_size_file_name', 'standard_squashfs_file_name',
        'standard_manifest_file_name', 'standard_size_file_name', 'install_sources_file_name',
        'live_squashfs_file_name', 'live_manifest_file_name', 'live_size_file_name',
        'live_generic_squashfs_file_name', 'live_generic_manifest_file_name',
        'live_generic_size_file_name'):
        create_links(attribute, squashfs_directory_path)


def get_xorriso_command(project):
    """Build the xorriso command from the saved ISO template."""

    template = decode(project.iso_template)
    volume_id = project.iso_volume_id.replace("'", """'"'"'""")
    boot_image_directory = project.directory.replace("'", """'"'"'""")
    complete_template = template.format(volume_id=volume_id, boot_image_directory=boot_image_directory)
    iso_file_path = os.path.join(project.iso_directory, project.iso_file_name)

    exclude_1 = ''
    if project.minimal_remove_file_name and not project.has_minimal_install:
        file_path = os.path.join(project.squashfs_directory, project.minimal_remove_file_name)
        exclude_1 = f'-m "{file_path}"'
    exclude_2 = ''
    if project.install_sources_file_name:
        file_path = os.path.join(project.custom_disk_directory, project.squashfs_directory,
                                 f'{project.install_sources_file_name}.original')
        exclude_2 = f'-m "{file_path}"'

    return ('xorriso -as mkisofs -r -J -joliet-long -l -iso-level 3'
            f' {exclude_1} {exclude_2} {complete_template} -o "{iso_file_path}" .')


def create_iso_image(project):
    """Create the ISO using xorriso."""

    print('Creating ISO image...')
    iso_file_path = os.path.join(project.iso_directory, project.iso_file_name)
    iso_directory = os.path.dirname(iso_file_path)
    if iso_directory and not os.path.isdir(iso_directory):
        os.makedirs(iso_directory)
    command = get_xorriso_command(project)
    if project.dry_run:
        print(f'[dry-run] cd {project.custom_disk_directory}')
        print(f'[dry-run] {command}')
        return 0
    return run(command, working_directory=project.custom_disk_directory)


def calculate_iso_checksum(project):
    """Calculate the checksum of the ISO and save it to a file."""

    iso_file_path = os.path.join(project.iso_directory, project.iso_file_name)
    checksum_file_name = f'{project.iso_file_name[:-4]}.md5'
    checksum_file_path = os.path.join(project.iso_directory, checksum_file_name)

    print(f'Calculating checksum for {project.iso_file_name}...')
    if project.dry_run:
        print(f'[dry-run] write {checksum_file_path}')
        return 0

    checksum = calculate_hash(iso_file_path, algorithm='md5')
    with open(checksum_file_path, 'w') as file:
        file.write(f'{checksum}  {project.iso_file_name}{os.linesep}')
    print(f'The checksum is {checksum}.')
    print(f'The checksum file is {checksum_file_path}.')
    return 0


def build_with_xorriso(project, options):
    """Rebuild the ISO using the xorriso template (default build)."""

    print(f'Building ISO for project {project.directory}')
    print(f'Layout: {"Arch" if project.is_arch else "Ubuntu"} '
          f'(squashfs directory: {project.squashfs_directory})')
    print(f'Custom disk: {project.custom_disk_directory}')
    print(f'Custom root: {project.custom_root_directory}')

    if not options.skip_kernels:
        result = copy_kernel_files(project)
        if result: return result

    # Determine the squashfs file(s) to compress. Arch layouts use a
    # single squashfs file; Ubuntu layouts may use minimal/live files.
    targets = []
    if not options.skip_squashfs:
        directory = project.squashfs_directory
        if project.live_squashfs_file_name and os.path.isdir(project.custom_live_directory):
            targets.append((project.custom_live_directory,
                            os.path.join(project.custom_disk_directory, directory, project.live_squashfs_file_name)))
        if project.minimal_squashfs_file_name and project.live_squashfs_file_name:
            targets.append((project.custom_root_directory,
                            os.path.join(project.custom_disk_directory, directory, project.minimal_squashfs_file_name)))
        else:
            file_name = project.minimal_squashfs_file_name or project.squashfs_file_name
            targets.append((project.custom_root_directory,
                            os.path.join(project.custom_disk_directory, directory, file_name)))

    for index, (source, target) in enumerate(targets):
        result = create_squashfs(project, source, target, file_number=index, total_files=len(targets))
        if result: return result

    # Ubuntu-specific metadata updates are not applicable to Arch.
    if project.is_arch:
        print('Skipping file system size and installer information (Arch layout).')
    else:
        print('Note. File system size and installer information updates are not implemented.')

    if not options.skip_checksums:
        result = update_checksums(project)
        if result: return result

    create_links_for_attributes(project)

    result = create_iso_image(project)
    if result: return result

    return calculate_iso_checksum(project)


def generate_archiso_profile(project, work_directory):
    """Generate an archiso profile from the customized project tree."""

    profile_directory = os.path.join(work_directory, 'profile')
    airootfs_directory = os.path.join(profile_directory, 'airootfs')
    packages_file_path = os.path.join(profile_directory, 'packages.x86_64')
    profiledef_file_path = os.path.join(profile_directory, 'profiledef.sh')
    pacman_conf_path = os.path.join(profile_directory, 'pacman.conf')

    os.makedirs(airootfs_directory, exist_ok=True)

    iso_name = (project.iso_file_name or 'custom').removesuffix('.iso')
    iso_label = project.iso_volume_id or iso_name[:11].upper()
    iso_version = project.iso_release_name or '1.0'

    profiledef = f'''#!/usr/bin/env bash

iso_name="{iso_name}"
iso_label="{iso_label}"
iso_publisher="CAIC"
iso_application="CAIC Live/Rescue CD"
iso_version="{iso_version}"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito' 'uefi-x64.systemd-boot.esp' 'uefi-x64.systemd-boot.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-b' '256K' '-Xbcj' 'x86')
file_permissions=(
  "/etc/shadow" "0" "0" "0400"
  "/etc/gshadow" "0" "0" "0400"
  "/etc/passwd" "0" "0" "0644"
  "/etc/group" "0" "0" "0644"
)
'''
    with open(profiledef_file_path, 'w') as file:
        file.write(profiledef)
    with open(pacman_conf_path, 'w') as file:
        file.write(ARCHISO_PACMAN_CONF)

    # Best-effort package list derived from the custom root's pacman
    # local database. mkarchiso will not fail if the list is invalid.
    packages = []
    local_db = os.path.join(project.custom_root_directory, 'var/lib/pacman/local')
    if os.path.isdir(local_db):
        for directory in sorted(os.listdir(local_db)):
            desc_path = os.path.join(local_db, directory, 'desc')
            if not os.path.isfile(desc_path):
                continue
            try:
                with open(desc_path, 'r') as file:
                    lines = file.read().splitlines()
                if '%NAME%' in lines:
                    packages.append(lines[lines.index('%NAME%') + 1])
            except OSError:
                pass
    if not packages:
        packages = ['base']
    with open(packages_file_path, 'w') as file:
        file.write('\n'.join(packages) + '\n')

    # Overlay the customized root onto the profile's airootfs so that
    # mkarchiso packages the customized environment.
    if not project.dry_run:
        for name in os.listdir(project.custom_root_directory):
            source = os.path.join(project.custom_root_directory, name)
            target = os.path.join(airootfs_directory, name)
            if os.path.isdir(source):
                shutil.copytree(source, target, symlinks=True, ignore_dangling_symlinks=True)
            else:
                shutil.copy2(source, target)
    else:
        print(f'[dry-run] copy {project.custom_root_directory} to {airootfs_directory}')

    return profile_directory


def build_with_mkarchiso(project, options):
    """Delegate the ISO build to mkarchiso (the archiso tool)."""

    mkarchiso = shutil.which('mkarchiso')
    if mkarchiso is None and not project.dry_run:
        print('Error. The mkarchiso command is not installed.'
              '\nInstall the archiso package from the Arch Linux extra repository and try again.', file=sys.stderr)
        return 1

    work_directory = os.path.abspath(options.work_directory or os.path.join(project.custom_temp_directory, 'mkarchiso'))
    output_directory = os.path.abspath(options.output_directory or project.iso_directory or project.directory)
    os.makedirs(work_directory, exist_ok=True)
    os.makedirs(output_directory, exist_ok=True)

    print(f'Generating archiso profile in {work_directory}...')
    profile_directory = generate_archiso_profile(project, work_directory)

    command = (f'{mkarchiso or "mkarchiso"} -v -w "{work_directory}" -o "{output_directory}" "{profile_directory}"')
    print(f'Running {command}')
    if project.dry_run:
        print(f'[dry-run] {command}')
        return 0
    return run(command)


########################################################################
# Command Line Interface
########################################################################


def get_arg_parser():
    """Create the argument parser for the command line interface."""

    parser = argparse.ArgumentParser(
        description='Build a customized Arch Linux (or Ubuntu) ISO from a CAIC project.')
    parser.add_argument('project_directory', type=str,
                        help='the path of the CAIC project directory containing caic.conf')
    parser.add_argument('--mkarchiso', action='store_true',
                        help='delegate the ISO build to the mkarchiso tool from the archiso package')
    parser.add_argument('--work-directory', type=str, default=None,
                        help='the work directory for the mkarchiso build (default: <project>/custom-temp/mkarchiso)')
    parser.add_argument('--output-directory', type=str, default=None,
                        help='the output directory for the ISO (default: the project ISO directory)')
    parser.add_argument('--skip-kernels', action='store_true',
                        help='do not copy the kernel boot files into the custom disk')
    parser.add_argument('--skip-squashfs', action='store_true',
                        help='do not compress the custom root file system')
    parser.add_argument('--skip-checksums', action='store_true',
                        help='do not update the checksum files')
    parser.add_argument('--dry-run', action='store_true',
                        help='print the commands without running them')
    return parser


def main():
    """The entry point for the command line interface."""

    parser = get_arg_parser()
    args = parser.parse_args()

    try:
        project = Project(args.project_directory, dry_run=args.dry_run)
    except Exception as exception:
        print(exception, file=sys.stderr)
        return 1

    if not project.is_arch and not args.mkarchiso:
        print('Warning. The xorriso build is intended for Arch Linux layouts. '
              'Ubuntu layouts are not fully supported.')

    if args.mkarchiso:
        return build_with_mkarchiso(project, args)
    return build_with_xorriso(project, args)


if __name__ == '__main__':
    sys.exit(main())