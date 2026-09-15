#!/usr/bin/python3

########################################################################
#                                                                      #
# model.py                                                             #
#                                                                      #
# Copyright (C) 2020 PJ Singh <psingh.cubic@gmail.com>                 #
#                                                                      #
########################################################################

########################################################################
#                                                                      #
# This file is part of Cubic - Custom Ubuntu ISO Creator.              #
#                                                                      #
# Cubic is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or    #
# (at your option) any later version.                                  #
#                                                                      #
# Cubic is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY, without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the         #
# GNU General Public License for more details.                         #
#                                                                      #
# You should have received a copy of the GNU General Public License    #
# along with Cubic. If not, see <http://www.gnu.org/licenses/>.        #
#                                                                      #
########################################################################

########################################################################
# References
########################################################################

# N/A

########################################################################
# Imports
########################################################################

from caic.utilities.structures import Attributes, Fields

########################################################################
# Application
########################################################################

builder = None
page = None

application = Fields('application')
application.directory = None
application.user_home = None
application.kernel_version = None
application.configuration = None
application.cubic_version = None
application.visited_sites = None
application.projects = None
application.iso_file_path = None

########################################################################
# Arguments
########################################################################

arguments = Fields('arguments')
arguments.directory = None
arguments.file_path = None

########################################################################
# Project
########################################################################

project = Fields('project')
project.cubic_version = None
project.first_version = None
project.create_date = None
project.modify_date = None
project.directory = None
project.configuration = None
project.iso_mount_point = None
project.custom_root_directory = None
project.custom_live_directory = None
project.custom_temp_directory = None
project.backup_root_directory = None
project.backup_live_directory = None
project.custom_disk_directory = None

########################################################################
# Original
########################################################################

original = Fields('original')
original.iso_file_name = None
original.iso_directory = None
original.iso_volume_id = None
original.iso_release_name = None
original.iso_disk_name = None
original.iso_release_notes_url = None

########################################################################
# Custom
########################################################################

custom = Fields('custom')
custom.iso_version_number = None
custom.iso_file_name = None
custom.iso_directory = None
custom.iso_volume_id = None
custom.iso_release_name = None
custom.iso_disk_name = None
custom.iso_release_notes_url = None

########################################################################
# Layout
########################################################################

# Sections:
# 1. Casper Section - vmlinuz and initrd files
# 2. General Section - squashfs directory
# 3. Minimal Section - minimal install squashfs files
# 4. Standard Section - standard install squashfs files
# 5. Live / Installer Section - install sources and live squashfs files
# 6. Additional Section - additional directory or file paths

layout = Attributes('layout')

# The assignment for layout.<attribute> takes up to three arguments.
# (See the structures module for more information). When two arguments
# are supplied, the second argument is a flag that indicates if the
# value (i.e. the first argument) is valid. Below, all values are
# initially set to False (invalid), and they must be validated on the
# Extract page using the identify_directories_and_files(),
# identify_directories(), identify_files(), or identify_paths()
# functions; values may also be explicitly set as valid (i.e. True).
# Note that the model.layout.reset() function sets all values as invalid
# prior to the Extract page, where they are validated in the
# analyze_iso_layout() function.

# 1. Casper Section

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# Workaround for Pop!_OS
# Pop!_OS explicitly requires an unusually named casper directory where
# initrd and vmlinuz are located. Using the link "casper" as the
# casper_directory_path does not work. Example directories are:
# - casper_pop-os_20.04_amd64_intel_debug_25
# - casper_pop-os_21.10_amd64_intel_debug_59
# - casper_pop-os_22.04_amd64_nvidia_debug_407
# The pattern "casper_pop-os*" will capture these directories.
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

layout.casper_directory = 'd-i', False
layout.casper_directory = 'd-i/gtk', False
layout.casper_directory = 'install', False
layout.casper_directory = 'install/gtk', False
layout.casper_directory = 'live', False
layout.casper_directory = 'boot/grml64full', False
layout.casper_directory = 'isolinux', False
layout.casper_directory = 'casper', False
layout.casper_directory = 'casper_pop-os*', False

# Only used to identify the casper directory.
layout.initrd_file_name = 'initrd.img', False  # grml64
layout.initrd_file_name = 'initrd.gz', False
layout.initrd_file_name = 'initrd.lz', False
layout.initrd_file_name = 'initrd', False

# Only used to identify the casper directory.
layout.vmlinuz_file_name = 'vmlinuz.efi', False
layout.vmlinuz_file_name = 'vmlinuz', False

# 2. General Section

layout.squashfs_directory = 'install', False
layout.squashfs_directory = 'live', False
layout.squashfs_directory = 'live/grml64-full', False
layout.squashfs_directory = 'LiveOS', False
layout.squashfs_directory = 'casper', False

layout.squashfs_file_name = 'grml64-full.squashfs', False
layout.squashfs_file_name = 'squashfs.img', False
layout.squashfs_file_name = 'filesystem.squashfs', False

layout.manifest_file_name = 'filesystem.manifest', False
layout.manifest_file_name = 'squashfs.manifest', False

layout.minimal_remove_file_name = 'filesystem.manifest-minimal-remove', False

layout.standard_remove_file_name = 'filesystem.manifest-remove', False

layout.size_file_name = 'filesystem.size', False

# 3. Minimal Section

layout.minimal_squashfs_file_name = 'minimal.squashfs', False
layout.minimal_squashfs_file_name = 'ubuntu-server-minimal.squashfs', False

layout.minimal_manifest_file_name = 'minimal.manifest', False
layout.minimal_manifest_file_name = 'ubuntu-server-minimal.manifest', False

layout.minimal_size_file_name = 'minimal.size', False
layout.minimal_size_file_name = 'ubuntu-server-minimal.size', False

# 4. Standard Section

layout.standard_squashfs_file_name = 'minimal.standard.squashfs', False
layout.standard_squashfs_file_name = 'ubuntu-server-minimal.ubuntu-server.squashfs', False

layout.standard_manifest_file_name = 'minimal.standard.manifest', False
layout.standard_manifest_file_name = 'ubuntu-server-minimal.ubuntu-server.manifest', False

layout.standard_size_file_name = 'minimal.standard.size', False
layout.standard_size_file_name = 'ubuntu-server-minimal.ubuntu-server.size', False

# 5. Live / Installer Section

layout.install_sources_file_name = 'install-sources.yaml', False

layout.live_squashfs_file_name = 'installer.squashfs', False
layout.live_squashfs_file_name = 'minimal.standard.live.squashfs', False
layout.live_squashfs_file_name = 'ubuntu-server-minimal.ubuntu-server.installer.squashfs', False

layout.live_manifest_file_name = 'minimal.standard.live.manifest', False
layout.live_manifest_file_name = 'ubuntu-server-minimal.ubuntu-server.installer.manifest', False

layout.live_size_file_name = 'minimal.standard.live.size', False
layout.live_size_file_name = 'ubuntu-server-minimal.ubuntu-server.installer.size', False

layout.live_generic_squashfs_file_name = 'ubuntu-server-minimal.ubuntu-server.installer.generic.squashfs', False

layout.live_generic_manifest_file_name = 'ubuntu-server-minimal.ubuntu-server.installer.generic.manifest', False

layout.live_generic_size_file_name = 'ubuntu-server-minimal.ubuntu-server.installer.generic.size', False

# 6. Additional Section

# Ubuntu Server 18.04, 18.04.3, 18.04.4
layout.additional_include_path = 'casper/extras', False

# Ubuntu Server 18.04.3, 18.04.4, 18.04.5, 18.04.6, 20.04, 20.04.3, 20.04.4, 20.04.6, 21.04
layout.additional_include_path = 'casper/maas', False

# Ubuntu Server 16.04.6, 18.04.2, 18.04.5
layout.additional_include_path = 'install/hwe-netboot', False

# Ubuntu Server 14.04.5, 16.04.6, 18.04.2, 18.04.5
layout.additional_include_path = 'install/netboot', False

# The files md5sum.txt, MD5SUMS, and .disk/release_notes_url are
# required by Cubic, but they may not exist on the source disk. These
# values are explicitly set to valid (True) on the Extract page in the
# analyze_iso_layout() function.
layout.additional_exclude_path = 'md5sum.txt', False
layout.additional_exclude_path = 'MD5SUMS', False
layout.additional_exclude_path = '.disk/release_notes_url', False

# Exclude all *.gpg files in the squashfs directory.
# The value for model.layout.additional_exclude_path requires
# model.layout.squashfs_directory to be set first, so it is can not be
# set here and must be set on the Extract page.
# model.layout.additional_exclude_path = f'{model.layout.squashfs_directory}/*.gpg', True

########################################################################
# Status
########################################################################

status = Fields('status')
status.is_success_analyze = None
status.is_success_copy = None
status.is_success_extract = None
status.iso_template = None
status.iso_checksum = None
status.iso_checksum_file_name = None

########################################################################
# Generated
########################################################################

generated = Fields('generated')
generated.iso_version_number = None
generated.iso_file_name = None
generated.iso_directory = None
generated.iso_volume_id = None
generated.iso_release_name = None
generated.iso_disk_name = None
generated.iso_release_notes_url = None

########################################################################
# Options
########################################################################

options = Fields('options')
options.update_os_release = None
options.has_minimal_install = None
options.boot_configurations = None
options.compression = None

########################################################################
# Page/Module Specific
########################################################################

# ----------------------------------------------------------------------
# Terminal page, Preseed tab, ISO Boot tab
# ----------------------------------------------------------------------

# Stores the current directory selected on the Terminal page, the
# Preseed tab, or the ISO Boot tab. This is the directory to copy files
# into.
current_directory = None

# Stores the uniform resource identifiers of files selected on the
# Terminal page, the Preseed tab, or the ISO Boot tab. These are the
# files to be copied.
selected_uris = None

# ----------------------------------------------------------------------
# Prepare page, Linux Kernels tab
# ----------------------------------------------------------------------

selected_kernel_index = None
kernel_details_list = None  # List of kernel detail dictionaries

# ----------------------------------------------------------------------
# Prepare page, Packages page
# ----------------------------------------------------------------------

package_details_list = None

# ----------------------------------------------------------------------
# Generate page, Finish page
# ----------------------------------------------------------------------

iso_file_size = None
file_system_size = 0

# ----------------------------------------------------------------------
# Emulator, Test 1 page, Test 2 page
# ----------------------------------------------------------------------

emulator_memory = None
