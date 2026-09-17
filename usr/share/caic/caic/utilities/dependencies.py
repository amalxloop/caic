#!/usr/bin/python3

########################################################################
#                                                                      #
# dependencies.py                                                      #
#                                                                      #
# Copyright (C) 2026 CAIC contributors                                 #
#                                                                      #
########################################################################

########################################################################
#                                                                      #
# This file is part of CAIC - Custom Arch ISO Creator.                 #
# CAIC is a fork of Cubic (Custom Ubuntu ISO Creator).                 #
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

# https://docs.python.org/3/library/shutil.html#shutil.which

########################################################################
# Imports
########################################################################

import shutil

########################################################################
# Required External Commands
########################################################################

# CAIC shells out to these command line tools. Each entry maps an
# executable name to the Arch package that provides it, so a missing
# tool can be reported with the package the user needs to install.
#
# Tools provided by the base packages (coreutils, sed, findutils,
# util-linux, systemd, polkit) are listed as well so that an unusual or
# minimal installation is reported rather than failing silently later.
REQUIRED_COMMANDS = (
    ('xorriso', 'libisoburn'),        # ISO report and image generation
    ('isoinfo', 'cdrtools'),          # ISO volume id
    ('mksquashfs', 'squashfs-tools'), # compress the custom root
    ('unsquashfs', 'squashfs-tools'), # extract the original root
    ('lsinitcpio', 'mkinitcpio'),     # inspect the initramfs
    ('machinectl', 'systemd'),        # manage the virtual environment
    ('rsync', 'rsync'),               # merge-directory
    ('find', 'findutils'),            # move-path, merge-directory
    ('sed', 'sed'),                   # replace-text
    ('mount', 'util-linux'),          # mount-iso
    ('pkexec', 'polkit'),             # run privileged helper scripts
    ('xdg-open', 'xdg-utils'),        # open help / website links
)


def get_missing_commands():
    """
    Find the required external commands that are not available.

    Returns:
    : list
        A list of (command, package) tuples for each required command
        that can not be found on the PATH. The list is empty when every
        required command is available.
    """

    missing_commands = []
    for command, package in REQUIRED_COMMANDS:
        if shutil.which(command) is None:
            missing_commands.append((command, package))

    return missing_commands


def get_missing_packages(missing_commands):
    """
    Get the sorted, unique package names for a list of missing commands.

    Arguments:
    missing_commands : list
        A list of (command, package) tuples, as returned by
        get_missing_commands().
    """

    return sorted({package for _command, package in missing_commands})
