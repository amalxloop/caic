#!/usr/bin/python3

########################################################################
#                                                                      #
# extract_page.py                                                      #
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
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
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

# https://askubuntu.com/questions/1289400/remaster-installation-image-for-ubuntu-20-10
# http://manpages.ubuntu.com/manpages/groovy/man1/xorriso.1.html
# https://linux.die.net/man/8/mkisofs
# http://manpages.ubuntu.com/manpages/groovy/man1/dd.1.html
# https://stackoverflow.com/questions/65189149/best-regex-in-python-to-not-have-double-space-in-result-when-substring-is-remo/65189757#65189757
# https://manpages.ubuntu.com/manpages/noble/man1/unsquashfs.1.html

########################################################################
# Imports
########################################################################

from packaging import version

import glob
import locale
import os
import re
import time

from caic.constants import BOLD_RED, NORMAL
from caic.constants import CONFIG_VERSION_2024
# from caic.constants import FIFTY_PERCENT
from caic.constants import FINAL_PERCENT
from caic.constants import GAP
from caic.constants import IMAGE_FILE_NAME
from caic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from caic.constants import SLEEP_1000_MS
from caic.navigator import InterruptException
from caic.utilities import constructor
from caic.utilities import displayer
from caic.utilities import file_utilities, iso_utilities
from caic.utilities import logger
from caic.utilities import model
from caic.utilities.progressor import track_progress

########################################################################
# Global Variables & Constants
########################################################################

name = 'extract_page'

is_page_valid = False

########################################################################
# Navigation Functions
########################################################################


def is_arch_layout():
    """
    Determine if the current layout is an Arch layout, based on whether
    an Arch squashfs directory was identified (e.g. "arch" or
    "arch/x86_64"). Arch layouts do not use the Ubuntu installer
    metadata files (filesystem.size, filesystem.manifest).

    Returns:
    : bool
        True if the current layout is an Arch layout, else False.
    """

    return bool(model.layout.squashfs_directory.startswith('arch'))


def setup(action, old_page=None):
    """
    Prepare this page for display. This function is executed while the
    previous page is still shown.

    Args:
    action : str
        The action from the previous page.
    old_page : str
        The previous page; optional.

    Returns:
    : None
        To continue to this page.
    error : str
        To automatically transition to an error page.
    """

    if action == 'next':

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # TODO:
        # Remove the "if" statement in a future release but keep the
        # code inside the "if" clause. [2024-08-10]
        #
        # The code inside the "if" clause will not work for projects
        # created using Cubic version 2024.02.86, so it should only be
        # enabled for all projects after most users are no longer
        # customizing legacy projects.
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        cubic_version = constructor.get_display_version(model.project.first_version)
        if version.parse(cubic_version) >= version.parse(CONFIG_VERSION_2024):

            # Update the status in case the user modified the cubic.conf
            # project configuration file or deleted some project files.

            # Checks for legacy layouts (using ubiquity).
            is_success_analyze_1 = bool(                     \
                model.status.is_success_analyze and          \
                model.layout.casper_directory and            \
                model.layout.squashfs_directory and          \
                model.layout.squashfs_file_name)
            is_success_copy_1 = bool(                        \
                model.status.is_success_copy and             \
                model.layout.casper_directory and            \
                model.layout.squashfs_directory)
            is_success_extract_1 = bool(                     \
                model.status.is_success_extract and          \
                model.layout.squashfs_directory and          \
                model.layout.squashfs_file_name)

            # Checks for newer layouts (using subiquity).
            is_success_analyze_2 = bool(                     \
                model.status.is_success_analyze and          \
                model.layout.casper_directory and            \
                model.layout.squashfs_directory and          \
                model.layout.minimal_squashfs_file_name and  \
                model.layout.standard_squashfs_file_name and \
                model.layout.live_squashfs_file_name)

            is_success_copy_2 = bool(                        \
                model.status.is_success_copy and             \
                model.layout.casper_directory and            \
                model.layout.squashfs_directory)
            is_success_extract_2 = bool(                     \
                model.status.is_success_extract and          \
                model.layout.squashfs_directory and          \
                model.layout.minimal_squashfs_file_name and  \
                model.layout.standard_squashfs_file_name and \
                model.layout.live_squashfs_file_name)

            model.status.is_success_analyze = is_success_analyze_1 or is_success_analyze_2
            model.status.is_success_copy = is_success_copy_1 or is_success_copy_2
            model.status.is_success_extract = is_success_extract_1 or is_success_extract_2

        # --------------------------------------------------------------
        # Analyze
        # --------------------------------------------------------------

        displayer.set_visible('extract_page__analyze_original_iso_section',
                              not model.status.is_success_analyze or \
                              not model.status.iso_template)
        displayer.update_status('extract_page__analyze_original_iso', BULLET)
        displayer.update_label('extract_page__analyze_original_iso_message', '...', False)

        # --------------------------------------------------------------
        # Copy
        # --------------------------------------------------------------

        displayer.set_visible('extract_page__copy_original_iso_files_section', not model.status.is_success_copy)
        displayer.update_status('extract_page__copy_original_iso_files', BULLET)
        displayer.update_progress_bar_percent('extract_page__copy_original_iso_files_progress_bar', 0)
        # displayer.update_progress_bar_text('extract_page__copy_original_iso_files_progress_bar', None)
        displayer.update_label('extract_page__copy_original_iso_files_message', '', False)

        # --------------------------------------------------------------
        # Extract
        # --------------------------------------------------------------

        displayer.set_visible('extract_page__unsquashfs_section', not model.status.is_success_extract)
        displayer.update_status('extract_page__unsquashfs', BULLET)
        displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', 0)
        # displayer.update_progress_bar_text('extract_page__unsquashfs_progress_bar', None)
        displayer.update_label('extract_page__unsquashfs_message', '', False)

        # --------------------------------------------------------------
        # Setup the next button.
        # --------------------------------------------------------------

        # The next action is automatic. The value of the next action is
        # returned by the enter() function, so there is no need to set
        # it here. The enter function can return:
        # • 'next' - to go to the Snaps page
        # • 'next-terminal' - to go to the Terminal page
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action=None,
            next_button_style='suggested-action',
            is_next_sensitive=False,
            is_next_visible=True)

        return

    elif action == 'extract-live':

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # TODO: Remove this elif clause in the future. [2026-07-25]
        #       Extract the live squashfs for existing projects from
        #       Cubic version 2026.07.106 and earlier.
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

        # --------------------------------------------------------------
        # Analyze
        # --------------------------------------------------------------

        # Assume analysis completed successfully.
        displayer.set_visible('extract_page__analyze_original_iso_section', False)

        # --------------------------------------------------------------
        # Copy
        # --------------------------------------------------------------

        # Assume copy completed successfully.
        displayer.set_visible('extract_page__copy_original_iso_files_section', False)

        # --------------------------------------------------------------
        # Extract
        # --------------------------------------------------------------

        # The live squashfs needs to be extracted.
        displayer.set_visible('extract_page__unsquashfs_section', True)
        displayer.update_status('extract_page__unsquashfs', BULLET)
        displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', 0)
        # displayer.update_progress_bar_text('extract_page__unsquashfs_progress_bar', None)
        displayer.update_label('extract_page__unsquashfs_message', '', False)

        # --------------------------------------------------------------
        # Setup the next button.
        # --------------------------------------------------------------

        # The next action is automatic. The value of the next action is
        # returned by the enter() function, so there is no need to set
        # it here. The enter function can return:
        # • 'next' - to go to the Snaps page
        # • 'next-terminal' - to go to the Terminal page
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action=None,
            next_button_style='suggested-action',
            is_next_sensitive=False,
            is_next_visible=True)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for setup{NORMAL}')

        return 'unknown'


def enter(action, old_page=None):
    """
    Preform functions on this page after it is shown. This function is
    executed after the previous page is hidden.

    Args:
    action : str
        The action from the previous page.
    old_page : str
        The previous page; optional.

    Returns:
    : None
        To stay on this page.
    action : str
        To automatically transition to another page.
    error : str
        To automatically transition to an error page.

    Specific success or error messages should be displayed in the called
    functions, but the display status should be set here because they
    depend on the outcome of multiple functions.
    """

    if action == 'next':

        # --------------------------------------------------------------
        # Analyze
        # --------------------------------------------------------------

        if not (model.status.iso_template and model.status.is_success_analyze):

            displayer.update_status('extract_page__analyze_original_iso', PROCESSING)

            time.sleep(SLEEP_1000_MS)

            if not model.status.iso_template:

                # Delete the old image files. Ignore errors.
                file_path_pattern = os.path.join(model.project.directory, IMAGE_FILE_NAME % '[1-9]')
                file_utilities.delete_files_with_pattern(file_path_pattern)

                # Identify the template for the original disk image.
                # • Set model.status.iso_template
                is_error = analyze_iso_template()

                if is_error: return  # Stay on this page.

            if not model.status.is_success_analyze:

                source_directory_path = model.project.iso_mount_point

                # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
                # TODO: Remove this section in the future. [2024-08-10]
                # Migrate a project created using Cubic version
                # 2024.02.86 to a newer version.
                # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
                # If the original iso is not available, use the
                # previously copied disk.
                if not iso_utilities.is_mounted(model.project.iso_mount_point):
                    source_directory_path = model.project.custom_disk_directory

                # Analyze the ISO layout.
                # • Set model.status.is_success_analyze
                # • Set model.layout.squashfs_directory
                # • Set model.layout.standard_squashfs_file_name
                # • Set model.layout.casper_directory
                # • Set model.layout.*
                # • Set model.status.has_minimal_install

                is_error = analyze_iso_layout(source_directory_path)

                if is_error: return  # Stay on this page.

            # Pause to allow the user to see the result.
            message = 'Success.'
            displayer.update_label('extract_page__analyze_original_iso_message', message, False)
            displayer.update_status('extract_page__analyze_original_iso', OK)
            time.sleep(SLEEP_1000_MS)

        # --------------------------------------------------------------
        # Copy
        # --------------------------------------------------------------

        if not model.status.is_success_copy:

            displayer.update_status('extract_page__copy_original_iso_files', PROCESSING)

            # Copy important files from the original disk image.
            # Set the following:
            # • Set model.status.is_success_copy
            is_error = copy_original_iso_files()

            if is_error: return  # Stay on this page.

            # Pause to allow the user to see the result.
            message = 'Success.'
            displayer.update_label('extract_page__copy_original_iso_files_message', message, False)
            displayer.update_status('extract_page__copy_original_iso_files', OK)
            time.sleep(SLEEP_1000_MS)

        # --------------------------------------------------------------
        # Extract & Merge
        # --------------------------------------------------------------

        if not model.status.is_success_extract:

            if model.layout.squashfs_file_name:

                # There is only one squashfs file.
                total_files = 1

                displayer.update_status('extract_page__unsquashfs', PROCESSING)

                # Clear the terminal because the history will no longer be
                # valid when the new squashfs files are extracted.
                terminal = model.builder.get_object('terminal_page__terminal')
                terminal.reset(True, True)

                # Delete the custom root directory if it exists.
                file_utilities.delete_path_as_root(model.project.custom_root_directory)
                # Delete the backup root directory if it exists.
                backup_root_directory = constructor.construct_backup_root_directory(model.project.directory)
                file_utilities.delete_path_as_root(backup_root_directory)

                # ----------------------------------------------------------
                # 2. General Section
                # ----------------------------------------------------------

                file_number = 0  # 1
                file_name = model.layout.squashfs_file_name

                # Extract to custom root directory.
                source_file_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory, file_name)
                target_file_path = model.project.custom_root_directory

                message = 'Extracting the Linux file system.'
                displayer.update_label('extract_page__unsquashfs_message', message, False)

                # Set the following:
                # • model.status.is_success_copy
                is_error = extract_linux_file_system(source_file_path, target_file_path, file_number, total_files)

                if is_error: return  # Stay on this page.

                # If the root directory has snaps, set the backup directory.
                file_path_1 = os.path.join(model.project.custom_root_directory, 'var', 'lib', 'snapd', 'state.json')
                file_path_2 = os.path.join(model.project.custom_root_directory, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
                has_snaps_1 = os.path.isfile(file_path_1) or os.path.isfile(file_path_2)
                if has_snaps_1:
                    model.project.backup_root_directory = constructor.construct_backup_root_directory(model.project.directory)

                logger.log_value('Done extracting', f'{file_number + 1} of {total_files}: {file_name}')

            else:

                # There are multiple squashfs files.
                total_files = 3
                total_steps = 4

                displayer.update_status('extract_page__unsquashfs', PROCESSING)

                # Set additional required directories.
                # The custom root directory was set on the Start page.
                # model.project.custom_root_directory = constructor.construct_custom_root_directory(model.project.directory)
                model.project.custom_live_directory = constructor.construct_custom_live_directory(model.project.directory)
                model.project.custom_temp_directory = constructor.construct_custom_temp_directory(model.project.directory)

                # Clear the terminal because the history will no longer be
                # valid when the new squashfs files are extracted.
                terminal = model.builder.get_object('terminal_page__terminal')
                terminal.reset(True, True)

                # Delete the custom root directory if it exists.
                file_utilities.delete_path_as_root(model.project.custom_root_directory)
                # Delete the backup root directory if it exists.
                backup_root_directory = constructor.construct_backup_root_directory(model.project.directory)
                file_utilities.delete_path_as_root(backup_root_directory)

                # Delete the custom live directory if it exists.
                file_utilities.delete_path_as_root(model.project.custom_live_directory)
                # Delete the backup live directory if it exists.
                backup_live_directory = constructor.construct_backup_live_directory(model.project.directory)
                file_utilities.delete_path_as_root(backup_live_directory)

                # Delete the custom temp directory if it exists.
                file_utilities.delete_path_as_root(model.project.custom_temp_directory)

                # ------------------------------------------------------
                # 3. Minimal Section
                # ------------------------------------------------------

                file_number = 0  # 1st file
                file_name = model.layout.minimal_squashfs_file_name

                # 3 Extract to custom root directory.
                step_number = 0  # 1st step
                source_file_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory, file_name)
                target_file_path = model.project.custom_root_directory

                file_number_text = constructor.number_as_text(file_number + 1)
                total_files_text = constructor.number_as_text(total_files)
                message = f'Extracting Linux file system {file_number_text} of {total_files_text}.'
                displayer.update_label('extract_page__unsquashfs_message', message, False)

                # Set the following:
                # • model.status.is_success_copy
                is_error = extract_linux_file_system(source_file_path, target_file_path, step_number, total_steps)

                if is_error: return  # Stay on this page.

                logger.log_value('Done extracting', f'{file_number + 1} of {total_files}: {file_name}')

                # ------------------------------------------------------
                # 4. Standard Section
                # ------------------------------------------------------

                file_number = 1  # 2nd file
                file_name = model.layout.standard_squashfs_file_name

                # Extract to custom temp directory.
                step_number = 1  # 2nd step
                source_file_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory, file_name)
                target_file_path = model.project.custom_temp_directory

                file_number_text = constructor.number_as_text(file_number + 1)
                total_files_text = constructor.number_as_text(total_files)
                message = f'Extracting Linux file system {file_number_text} of {total_files_text}.'
                displayer.update_label('extract_page__unsquashfs_message', message, False)

                # Set the following:
                # • model.status.is_success_copy
                is_error = extract_linux_file_system(source_file_path, target_file_path, step_number, total_steps)

                if is_error: return  # Stay on this page.

                logger.log_value('Done extracting', f'{file_number + 1} of {total_files}: {file_name}')

                # Merge.
                step_number = 2  # 3rd step
                source_file_path = model.project.custom_temp_directory
                target_file_path = model.project.custom_root_directory

                file_number_text = constructor.number_as_text(file_number + 1)
                total_files_text = constructor.number_as_text(total_files)
                # message = f'Merging Linux file system {file_number_text} of {total_files_text}.'
                # message = f'Merging Linux file system one and {file_number_text}.'
                message = 'Merging Linux file systems.'
                displayer.update_label('extract_page__unsquashfs_message', message, False)

                is_error = merge_linux_file_system(source_file_path, target_file_path, step_number, total_steps)

                if is_error: return  # Stay on this page.

                # Delete the custom temp directory, since it is no
                # longer needed.
                file_utilities.delete_path_as_root(model.project.custom_temp_directory)

                # If the root directory has snaps, set the backup directory.
                file_path_1 = os.path.join(model.project.custom_root_directory, 'var', 'lib', 'snapd', 'state.json')
                file_path_2 = os.path.join(model.project.custom_root_directory, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
                has_snaps_1 = os.path.isfile(file_path_1) or os.path.isfile(file_path_2)
                if has_snaps_1:
                    model.project.backup_root_directory = constructor.construct_backup_root_directory(model.project.directory)

                # logger.log_value('Done Merging', f'{file_number + 1} of {total_files}: {file_name}')
                logger.log_value('Done Merging', f'{file_number + 1}: {file_name}')

                # ------------------------------------------------------
                # 5. Live / Installer Section
                # ------------------------------------------------------

                file_number = 2  # 3rd file
                file_name = model.layout.live_squashfs_file_name
                # file_name = model.layout.live_generic_squashfs_file_name

                # Extract to custom live directory.
                step_number = 3  # 4th step
                source_file_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory, file_name)
                target_file_path = model.project.custom_live_directory

                file_number_text = constructor.number_as_text(file_number + 1)
                total_files_text = constructor.number_as_text(total_files)
                message = f'Extracting Linux file system {file_number_text} of {total_files_text}.'
                displayer.update_label('extract_page__unsquashfs_message', message, False)

                # Set the following:
                # • model.status.is_success_copy
                is_error = extract_linux_file_system(source_file_path, target_file_path, step_number, total_steps)

                if is_error: return  # Stay on this page.

                # If the live directory has snaps, set the backup directory.
                file_path_1 = os.path.join(model.project.custom_live_directory, 'var', 'lib', 'snapd', 'state.json')
                file_path_2 = os.path.join(model.project.custom_live_directory, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
                has_snaps_2 = os.path.isfile(file_path_1) or os.path.isfile(file_path_2)
                if has_snaps_2:
                    model.project.backup_live_directory = constructor.construct_backup_live_directory(model.project.directory)

                logger.log_value('Done extracting', f'{file_number + 1} of {total_files}: {file_name}')

        # Determine if the Snaps page or the Terminal page should be
        # shown.
        has_snaps_1 = False
        if model.project.custom_root_directory:
            file_path_1 = os.path.join(model.project.custom_root_directory, 'var', 'lib', 'snapd', 'state.json')
            file_path_2 = os.path.join(model.project.custom_root_directory, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
            has_snaps_1 = os.path.isfile(file_path_1) or os.path.isfile(file_path_2)
        has_snaps_2 = False
        if model.project.custom_live_directory:
            file_path_1 = os.path.join(model.project.custom_live_directory, 'var', 'lib', 'snapd', 'state.json')
            file_path_2 = os.path.join(model.project.custom_live_directory, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
            has_snaps_2 = os.path.isfile(file_path_1) or os.path.isfile(file_path_2)

        # Pause to allow the user to see the result.
        message = 'Success.'
        displayer.update_label('extract_page__unsquashfs_message', message, False)
        displayer.update_status('extract_page__unsquashfs', OK)
        time.sleep(SLEEP_1000_MS)

        if has_snaps_1 or has_snaps_2:
            # Automatically transition to the Snaps page.
            return 'next'
        else:
            # Automatically transition to the Terminal page.
            return 'next-terminal'

    elif action == 'extract-live':

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # TODO: Remove this elif clause in the future. [2026-08-19]
        #       Extract the live squashfs for existing projects from
        #       Cubic version 2026.07.106 and earlier.
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

        # Set additional required directories.
        # The custom root directory was set on the Start page.
        # model.project.custom_root_directory = constructor.construct_custom_root_directory(model.project.directory)
        # The following were set on the Project page.
        # model.project.backup_root_directory = constructor.construct_backup_root_directory(model.project.directory)
        # model.project.custom_live_directory = constructor.construct_custom_live_directory(model.project.directory)
        # model.project.backup_live_directory = constructor.construct_backup_live_directory(model.project.directory)
        # model.project.custom_temp_directory = constructor.construct_custom_temp_directory(model.project.directory)

        # There are multiple squashfs files. Only extract the live
        # squashfs file because the root squashfs files were already
        # extracted.
        total_files = 1

        displayer.update_status('extract_page__unsquashfs', PROCESSING)

        # ------------------------------------------------------
        # 5. Live / Installer Section
        # ------------------------------------------------------

        file_number = 0  # 1st file
        file_name = model.layout.live_squashfs_file_name
        # file_name = model.layout.live_generic_squashfs_file_name

        # If the original iso is not available, use the previously
        # copied live squashfs file.
        source_directory_path = model.project.iso_mount_point
        if not iso_utilities.is_mounted(model.project.iso_mount_point):
            source_directory_path = model.project.custom_disk_directory

        # Extract to custom live directory.
        source_file_path = os.path.join(source_directory_path, model.layout.squashfs_directory, file_name)
        target_file_path = model.project.custom_live_directory

        file_number_text = constructor.number_as_text(file_number + 1)
        total_files_text = constructor.number_as_text(total_files)
        message = f'Extracting Linux file system {file_number_text} of {total_files_text}.'
        displayer.update_label('extract_page__unsquashfs_message', message, False)

        # Set the following:
        # • model.status.is_success_copy
        is_error = extract_linux_file_system(source_file_path, target_file_path, file_number, total_files)

        # Reset is_success_extract to True, because the minimal and
        # standard file systems were successfully extracted. If there
        # was an error extracting the live squashfs, and
        # is_success_extract got set to False, then the minimal and
        # standard files would be extracted again the next time the user
        # visits the extract page, overwriting the user's customizations.
        model.status.is_success_extract = True

        if is_error: return  # Stay on this page.

        # Determine if the Snaps page or the Terminal page should be
        # shown.
        has_snaps_1 = False
        if model.project.custom_root_directory:
            file_path_1 = os.path.join(model.project.custom_root_directory, 'var', 'lib', 'snapd', 'state.json')
            file_path_2 = os.path.join(model.project.custom_root_directory, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
            has_snaps_1 = os.path.isfile(file_path_1) or os.path.isfile(file_path_2)
        has_snaps_2 = False
        if model.project.custom_live_directory:
            file_path_1 = os.path.join(model.project.custom_live_directory, 'var', 'lib', 'snapd', 'state.json')
            file_path_2 = os.path.join(model.project.custom_live_directory, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
            has_snaps_2 = os.path.isfile(file_path_1) or os.path.isfile(file_path_2)

        logger.log_value('Done extracting', f'{file_number + 1} of {total_files}: {file_name}')

        # Pause to allow the user to see the result.
        message = 'Success.'
        displayer.update_label('extract_page__unsquashfs_message', message, False)
        displayer.update_status('extract_page__unsquashfs', OK)
        time.sleep(SLEEP_1000_MS)

        if has_snaps_1 or has_snaps_2:
            # Automatically transition to the Snaps page.
            return 'next'
        else:
            # Automatically transition to the Terminal page.
            return 'next-terminal'

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for enter{NORMAL}')

        return 'unknown'


def leave(action, new_page=None):
    """
    Preform functions on this page before leaving it. This function is
    executed while this page is visible.

    Args:
    action : str
        The action on this page.
    old_page : str
        The next page to show; optional.

    Returns:
    : None
        To continue to the next page.
    error : str
        To automatically transition to an error page.
    """

    if action == 'back':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'next':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'next-terminal':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return 'unknown'


########################################################################
# Handler Functions
########################################################################

# N/A

########################################################################
# Support Functions
########################################################################

# ----------------------------------------------------------------------
# Analyze Original Disk Functions
# ----------------------------------------------------------------------


def analyze_iso_template():

    logger.log_label('Generate the ISO template')

    iso_report = iso_utilities.get_iso_report()
    template = iso_utilities.generate_iso_template(iso_report)
    if template:
        model.status.iso_template = constructor.encode(template)
    else:
        model.status.iso_template = None

    if not model.status.iso_template:
        logger.log_value('Error', 'Unable to identify information about this disk')
        # message = '<span foreground="red">Error. Unable to identify information about this disk.</span>'
        message = 'Error. Unable to identify information about this disk'
        displayer.update_label('extract_page__analyze_original_iso_message', message, True)
        displayer.update_status('extract_page__analyze_original_iso', ERROR)
        return True
    else:
        return False


def identify_directories_and_files(source_directory_path, directory_attribute, file_attribute):
    """
    Identify a directory by searching for files within the directory.
    """

    directory_patterns = model.layout.values(directory_attribute)
    for directory_pattern in directory_patterns:
        directory_path_pattern = os.path.join(source_directory_path, directory_pattern)
        directory_paths = glob.glob(directory_path_pattern)
        for directory_path in directory_paths:
            if os.path.exists(directory_path):
                file_name_patterns = model.layout.values(file_attribute)
                for file_name_pattern in file_name_patterns:
                    file_path_pattern = os.path.join(directory_path, file_name_pattern)
                    file_paths = glob.glob(file_path_pattern)
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            # Set the directory.
                            directory = os.path.relpath(directory_path, source_directory_path)
                            model.layout.set(directory_attribute, directory, True)
                            # Set the file name.
                            file_name = os.path.relpath(file_path, directory_path)
                            model.layout.set(file_attribute, file_name, True)


def identify_directories(source_directory_path, directory_attribute, file_attribute):
    """
    Identify a directory by searching for files within the directory.

    Args:
        source_directory_path (str): The source directory path
        directory_attribute (str): ???
        file_attribute (str): ???

    Returns:
        ???
    """

    directory_patterns = model.layout.values(directory_attribute)
    for directory_pattern in directory_patterns:
        directory_path_pattern = os.path.join(source_directory_path, directory_pattern)
        directory_paths = glob.glob(directory_path_pattern)
        for directory_path in directory_paths:
            if os.path.exists(directory_path):
                file_name_patterns = model.layout.values(file_attribute)
                for file_name_pattern in file_name_patterns:
                    file_path_pattern = os.path.join(directory_path, file_name_pattern)
                    file_paths = glob.glob(file_path_pattern)
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            # Set the directory.
                            directory = os.path.relpath(directory_path, source_directory_path)
                            model.layout.set(directory_attribute, directory, True)
                            # Set the file name.
                            # file_name = os.path.relpath(file_path, directory_path)
                            # model.layout.set(file_attribute, file_name, True)


def identify_files(source_directory_path, directory_attribute, file_attribute):
    """
    Identify files within the directory.

    Args:
        source_directory_path (str): The source directory path
        directory_attribute (str): ???
        file_attribute (str): ???

    Returns:
        ???
    """

    directory_patterns = model.layout.values(directory_attribute)
    for directory_pattern in directory_patterns:
        directory_path_pattern = os.path.join(source_directory_path, directory_pattern)
        directory_paths = glob.glob(directory_path_pattern)
        for directory_path in directory_paths:
            if os.path.exists(directory_path):
                file_name_patterns = model.layout.values(file_attribute)
                for file_name_pattern in file_name_patterns:
                    file_path_pattern = os.path.join(directory_path, file_name_pattern)
                    file_paths = glob.glob(file_path_pattern)
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            # Set the directory.
                            # directory = os.path.relpath(directory_path, source_directory_path)
                            # model.layout.set(directory_attribute, directory, True)
                            # Set the file name.
                            file_name = os.path.relpath(file_path, directory_path)
                            model.layout.set(file_attribute, file_name, True)


def identify_paths(source_directory_path, path_attribute):
    """
    Identify files or directories within the source directory.

    Args:
        source_directory_path (str): The source directory path
        path_attribute (str):

    Returns:
        ???
    """

    path_patterns = model.layout.values(path_attribute)
    for path_pattern in path_patterns:
        full_path_pattern = os.path.join(source_directory_path, path_pattern)
        full_paths = glob.glob(full_path_pattern)
        for full_path in full_paths:
            if os.path.exists(full_path):
                # Set the file name or directory.
                path = os.path.relpath(full_path, source_directory_path)
                model.layout.set(path_attribute, path, True)


def analyze_iso_layout(source_directory_path):
    """
    Set valid possible values for each attribute as True.
    Set invalid possible values for each attribute as False.
    (See the Structures class).

    Args:
        source_directory_path (str): The source directory path

    Returns:
        None: N/A
    """

    logger.log_label('Analyze the ISO layout')

    logger.log_value('Analyze', source_directory_path)

    # Sections:
    # 1. Casper Section - vmlinuz and initrd files
    # 2. General Section - squashfs directory
    # 3. Minimal Section - minimal install squashfs files
    # 4. Standard Section - standard install squashfs files
    # 5. Live / Installer Section - install sources and live squashfs files
    # 6. Additional Section - additional directory or file paths

    # 1. Casper Section
    #    • model.layout.casper_directory
    #    • model.layout.initrd_file_name
    #    • model.layout.vmlinuz_file_name
    # 2. General Section
    #    • model.layout.squashfs_directory
    #    • model.layout.squashfs_file_name
    #    • model.layout.manifest_file_name
    #    • model.layout.minimal_remove_file_name
    #    • model.layout.standard_remove_file_name
    #    • model.layout.size_file_name
    # 3. Minimal Section
    #    • model.layout.minimal_squashfs_file_name
    #    • model.layout.minimal_manifest_file_name
    #    • model.layout.minimal_size_file_name
    # 4. Standard Section
    #    • model.layout.standard_squashfs_file_name
    #    • model.layout.standard_manifest_file_name
    #    • model.layout.standard_size_file_name
    # 5. Live / Installer Section
    #    • model.layout.install_sources_file_name
    #    • model.layout.live_squashfs_file_name
    #    • model.layout.live_manifest_file_name
    #    • model.layout.live_size_file_name
    #    • model.layout.live_generic_squashfs_file_name
    #    • model.layout.live_generic_manifest_file_name
    #    • model.layout.live_generic_size_file_name
    # 6. Additional Section
    #    • model.layout.additional_include_path
    #    • model.layout.additional_exclude_path (not set in model)

    # Initialize the layout.
    # Although layout is reset on the Start page and the Delete page,
    # if the user clicks cancel, returns to the project page, and
    # selects a different original ISO, the layout values should be
    # reset, so the values from the previous ISO are not preserved.
    model.layout.reset()

    # 1. Casper Section

    # Identify Directories
    # Identify the casper_directory using:
    # • initrd_file_name
    # • vmlinuz_file_name
    identify_directories(source_directory_path, 'casper_directory', 'initrd_file_name')
    identify_directories(source_directory_path, 'casper_directory', 'vmlinuz_file_name')

    # Identify Files
    identify_files(source_directory_path, 'casper_directory', 'initrd_file_name')
    identify_files(source_directory_path, 'casper_directory', 'vmlinuz_file_name')

    # 2. General Section

    # Identify Directories
    # Identify the squashfs_directory using:
    # • squashfs_file_name
    # • minimal_squashfs_file_name
    # • standard_squashfs_file_name
    identify_directories(source_directory_path, 'squashfs_directory', 'squashfs_file_name')
    identify_directories(source_directory_path, 'squashfs_directory', 'minimal_squashfs_file_name')
    identify_directories(source_directory_path, 'squashfs_directory', 'standard_squashfs_file_name')

    # Identify Files
    identify_files(source_directory_path, 'squashfs_directory', 'squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'minimal_remove_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'standard_remove_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'size_file_name')

    # 3. Minimal Section

    # Identify Files
    identify_files(source_directory_path, 'squashfs_directory', 'minimal_squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'minimal_manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'minimal_size_file_name')

    # 4. Standard Section

    # Identify Files
    identify_files(source_directory_path, 'squashfs_directory', 'standard_squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'standard_manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'standard_size_file_name')

    # 5. Live / Installer Section

    # Identify Files
    identify_files(source_directory_path, 'squashfs_directory', 'install_sources_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'live_squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'live_manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'live_size_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'live_generic_squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'live_generic_manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'live_generic_size_file_name')

    # 6. Additional Section

    # Identify Files or Directories
    identify_paths(source_directory_path, 'additional_include_path')

    # The files md5sum.txt, MD5SUMS, and .disk/release_notes_url are
    # required by Cubic. But they may not exist on the source disk, so
    # they cannot be automatically validated using the functions
    # identify_directories_and_files(), identify_directories(),
    # identify_files(), or identify_paths(). Therefore, these values
    # are explicitly set to valid (i.e. True). Excluding these files
    # prevents them from being overwritten or removed by the rsync
    # command in the copy_original_iso_files() function.

    # identify_paths(source_directory_path, 'additional_exclude_path')
    model.layout.additional_exclude_path = 'md5sum.txt', True
    model.layout.additional_exclude_path = 'MD5SUMS', True
    model.layout.additional_exclude_path = '.disk/release_notes_url', True
    # Arch ISO disks use sha256sums.txt instead of md5sum.txt.
    model.layout.additional_exclude_path = 'sha256sums.txt', True

    # Exclude all *.gpg files in the squashfs directory.
    model.layout.additional_exclude_path = f'{model.layout.squashfs_directory}/*.gpg', True

    # Set important files that may not exist on the original ISO.
    # Arch layouts do not use filesystem.size or filesystem.manifest.
    if not is_arch_layout():
        if not model.layout.size_file_name:
            model.layout.size_file_name = 'filesystem.size', True
        if not model.layout.manifest_file_name:
            model.layout.manifest_file_name = 'filesystem.manifest', True

    # print('-' * 80)
    # model.layout.print()
    # print('-' * 80)

    # Identify if the ISO has a legacy minimal install option.
    model.options.has_minimal_install = bool(model.layout.minimal_remove_file_name)

    # Check if the analysis succeeded

    logger.log_value('The casper directory is', model.layout.casper_directory)
    logger.log_value('The squashfs directory is', model.layout.squashfs_directory)
    logger.log_value('The squashfs file name is', model.layout.squashfs_file_name)
    is_success_analyze_1 = bool(                    \
        model.layout.casper_directory and           \
        model.layout.squashfs_directory and         \
        model.layout.squashfs_file_name)
    logger.log_value('Is success analyze 1?', is_success_analyze_1)

    logger.log_value('The casper directory is', model.layout.casper_directory)
    logger.log_value('The squashfs directory is', model.layout.squashfs_directory)
    logger.log_value('The minimal squashfs file name is', model.layout.minimal_squashfs_file_name)
    logger.log_value('The standard squashfs file name is', model.layout.standard_squashfs_file_name)
    is_success_analyze_2 = bool(                    \
        model.layout.casper_directory and           \
        model.layout.squashfs_directory and         \
        model.layout.minimal_squashfs_file_name and \
        model.layout.standard_squashfs_file_name)
    logger.log_value('Is success analyze 2', is_success_analyze_2)

    model.status.is_success_analyze = is_success_analyze_1 or is_success_analyze_2

    is_error = not model.status.is_success_analyze

    ### TODO:
    ### Display error and stop spinner.
    logger.log_value('Is error?', is_error)

    return is_error


# ----------------------------------------------------------------------
# Copy Original Disk Files Functions
# ----------------------------------------------------------------------
"""
Here is an example of the files that are copied (and not copied) for
ubuntu-24.04-desktop. Note that "??" represents languages, including
"no-languages".

~ ~ ~  copy: filesystem.manifest
~ ~ ~  copy: filesystem.size
~ ~ ~  copy: install-sources.yaml
do not copy: minimal.manifest
do not copy: minimal.size
do not copy: minimal.squashfs
do not copy: minimal.squashfs.gpg

do not copy: minimal.??.manifest
do not copy: minimal.??.size
do not copy: minimal.??.squashfs
do not copy: minimal.??.squashfs.gpg

do not copy: minimal.standard.manifest
do not copy: minimal.standard.size
do not copy: minimal.standard.squashfs
do not copy: minimal.standard.squashfs.gpg

~ ~ ~  copy: minimal.standard.live.manifest
do not copy: minimal.standard.live.size
do not copy: minimal.standard.live.squashfs
do not copy: minimal.standard.live.squashfs.gpg

do not copy: minimal.standard.??.manifest
do not copy: minimal.standard.??.size
do not copy: minimal.standard.??.squashfs
do not copy: minimal.standard.??.squashfs.gpg

do not copy: minimal.enhanced-secureboot.manifest
do not copy: minimal.enhanced-secureboot.size
do not copy: minimal.enhanced-secureboot.squashfs
do not copy: minimal.enhanced-secureboot.squashfs.gpg

do not copy: minimal.enhanced-secureboot.??.manifest
do not copy: minimal.enhanced-secureboot.??.size
do not copy: minimal.enhanced-secureboot.??.squashfs
do not copy: minimal.enhanced-secureboot.??.squashfs.gpg

do not copy: minimal.standard.enhanced-secureboot.manifest
do not copy: minimal.standard.enhanced-secureboot.size
do not copy: minimal.standard.enhanced-secureboot.squashfs
do not copy: minimal.standard.enhanced-secureboot.squashfs.gpg

do not copy: minimal.standard.enhanced-secureboot.??.manifest
do not copy: minimal.standard.enhanced-secureboot.??.size
do not copy: minimal.standard.enhanced-secureboot.??.squashfs
do not copy: minimal.standard.enhanced-secureboot.??.squashfs.gpg

~ ~ ~  copy: initrd
~ ~ ~  copy: vmlinuz
"""


def copy_original_iso_files():
    """
    Excludes all files in the casper and squashfs directories, but
    copies specified files.

    Exclude or copy the following files:

    do not copy: md5sum.txt
    do not copy: MD5SUMS
    do not copy: .disk/release notes url

    # 1. Casper Section
    ~ ~ ~  copy: initrd file name
    ~ ~ ~  copy: vmlinuz file name

    # 2. General Section
    do not copy: squashfs file name
    do not copy: manifest file name
    ~ ~ ~  copy: minimal remove file name
    ~ ~ ~  copy: standard remove file name
    do not copy: size file name

    # 3. Minimal Section
    do not copy: minimal squashfs file name
    do not copy: minimal manifest file name
    do not copy: minimal size file name

    # 4. Standard Section
    do not copy: standard squashfs file name
    do not copy: standard manifest file name
    do not copy: standard size file name

    # 5. Live / Installer Section
    ~ ~ ~  copy: install sources file name
    do not copy: live squashfs file name
    ~ ~ ~  copy: live manifest file name
    do not copy: live size file name
    ~ ~ ~  copy: live generic squashfs file name
    ~ ~ ~  copy: live generic manifest file name
    ~ ~ ~  copy: live generic size file name

    # 6. Additional Section
    ~ ~ ~  copy: casper/extras
    ~ ~ ~  copy: casper/maas
    """

    logger.log_label('Copy important files from the original disk image')

    # Add a "/" at the end of the path so rsync copies the contents
    # of the source directory to the target directory.
    source_file_path = os.path.join(model.project.iso_mount_point, '')
    logger.log_value('The source file path is', source_file_path)

    # Add a "/" at the end of the path so rsync copies files into
    # the target directory. This is not required, but is consistent
    # with the source directory path above.
    target_file_path = os.path.join(model.project.custom_disk_directory, '')
    logger.log_value('The target file path is', target_file_path)

    # Sections:
    # 1. Casper Section - vmlinuz and initrd files
    # 2. General Section - squashfs directory
    # 3. Minimal Section - minimal install squashfs files
    # 4. Standard Section - standard install squashfs files
    # 5. Live / Installer Section - install sources and live squashfs files
    # 6. Additional Section - additional directory or file paths

    # ------------------------------------------------------------------
    # Includes
    # ------------------------------------------------------------------

    # 1. Casper Section
    include_11 = constructor.construct_rsync_includes(model.layout.casper_directory_as_list, model.layout.initrd_file_name_as_list)
    include_12 = constructor.construct_rsync_includes(model.layout.casper_directory_as_list, model.layout.vmlinuz_file_name_as_list)

    # 2. General Section
    include_21 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.minimal_remove_file_name_as_list)
    include_22 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.standard_remove_file_name_as_list)

    # 3. Minimal Section
    # N/A

    # 4. Standard Section
    # N/A

    # 5. Live / Installer Section
    include_51 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.install_sources_file_name_as_list)
    # include_52 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.live_squashfs_file_name_as_list)
    include_53 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.live_manifest_file_name_as_list)
    # include_54 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.live_size_file_name_as_list)
    include_55 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.live_generic_squashfs_file_name_as_list)
    include_56 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.live_generic_manifest_file_name_as_list)
    include_57 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.live_generic_size_file_name_as_list)

    # 6. Additional Section
    include_61 = constructor.construct_rsync_includes(model.layout.additional_include_path_as_list)

    # ------------------------------------------------------------------
    # Excludes
    # ------------------------------------------------------------------

    # 1. Casper Section
    # The * is used to exclude all files in the casper directory.
    # However, the preceding includes supersede all excludes, so
    # specified files in the casper directory will still be copied.
    exclude_11 = constructor.construct_rsync_excludes(model.layout.casper_directory_as_list, ['*'])

    # 2. General Section
    # The * is used to exclude all files in the squashfs directory.
    # However, the preceding includes supersede all excludes, so
    # specified files in the squashfs directory will still be copied.
    exclude_21 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, ['*'])

    # 3. Minimal Section
    # N/A

    # 4. Standard Section
    # N/A

    # 5. Live / Installer Section
    exclude_52 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.live_squashfs_file_name_as_list)
    exclude_54 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.live_size_file_name_as_list)

    # 6. Additional Section
    exclude_61 = constructor.construct_rsync_excludes(model.layout.additional_exclude_path_as_list)

    # ------------------------------------------------------------------
    # Copy files from the original iso
    # ------------------------------------------------------------------

    # Use the following rsync options:
    # ┌───────┬──────────────────┬─────────────────────────────────────┐
    # │ Short │ Long             │ Description                         │
    # ├───────┼──────────────────┼─────────────────────────────────────┤
    # │       │ --info=progress2 │ Output the total progress, instead  │
    # │       │                  │   of progress for individual files  │
    # │       │ --delete         │ Delete extraneous files from        │
    # │       │                  │   destination directories           │
    # │ -r    │ --recursive      │ Recurse into directories            │
    # │ -l    │ --links          │ Copy symlinks as symlinks           │
    # │       │ --chmod=CHMOD    │ Apply comma-separated permissions   │
    # │       │                  │   --chmod=u+rwX,g=rX,o=rX           │
    # │       │                  │   Set Read/write permissions for    │
    # │       │                  │   the user, group, and other        │
    # └───────┴──────────────────┴─────────────────────────────────────┘

    # Do not include a leading "/" in front of the relative file paths,
    # in the include and exclude arguments. Includes must precede
    # excludes.
    command = (
        'rsync'
        f' --info=progress2 "{source_file_path}" "{target_file_path}"'
        ' --delete'
        # ' --archive'
        ' --recursive'
        ' --links'
        ' --chmod=u+rwX,g=rX,o=rX'
        #
        # Includes
        #
        # 1. Casper Section
        f' {include_11}'  # initrd_file_name
        f' {include_12}'  # vmlinuz_file_name
        # 2. General Section
        f' {include_21}'  # minimal_remove_file_name
        f' {include_22}'  # standard_remove_file_name
        # 3. Minimal Section
        #   N/A
        # 4. Standard Section
        #   N/A
        # 5. Live / Installer Section
        f' {include_51}'  # install_sources_file_name
        # f' {include_52}'  # live_squashfs_file_name
        f' {include_53}'  # live_manifest_file_name
        # f' {include_54}'  # live_size_file_name
        f' {include_55}'  # live_generic_squashfs_file_name
        f' {include_56}'  # live_generic_manifest_file_name
        f' {include_57}'  # live_generic_size_file_name
        # 6. Additional Section
        f' {include_61}'  # additional_include_path
        #
        # Excludes
        #
        # 1. Casper Section
        f' {exclude_11}'  # casper_directory
        # 2. General Section
        f' {exclude_21}'  # squashfs_directory
        # 3. Minimal Section
        #   N/A
        # 4. Standard Section
        #   N/A
        # 5. Live / Installer Section
        f' {exclude_52}'  # live_squashfs_file_name
        f' {exclude_54}'  # live_size_file_name
        # 6. Additional Section
        f' {exclude_61}'  # additional_exclude_path
    )

    # The progress callback function.
    def progress_callback(percent):
        displayer.update_progress_bar_percent('extract_page__copy_original_iso_files_progress_bar', percent)
        if percent % 10 == 0:
            logger.log_value('Completed', f'{percent:n}%')

    try:
        track_progress(command, progress_callback)
    except InterruptException as exception:
        model.status.is_success_copy = False
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to copy files from the original disk image.</span>'
            message = 'Error. Unable to copy files from the original disk image.'
        displayer.update_label('extract_page__copy_original_iso_files_message', message, True)
        displayer.update_status('extract_page__copy_original_iso_files', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        model.status.is_success_copy = False
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to copy files from the original disk image.</span>'
            message = 'Error. Unable to copy files from the original disk image.'
        displayer.update_label('extract_page__copy_original_iso_files_message', message, True)
        displayer.update_status('extract_page__copy_original_iso_files', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    model.status.is_success_copy = True

    return False  # (No Error)


# ----------------------------------------------------------------------
# Extract Linux File System Functions
# ----------------------------------------------------------------------


def extract_linux_file_system(source_file_path, target_file_path, file_number, total_files):

    logger.log_label('Extract the compressed Linux file system')
    logger.log_value('The source file path is', source_file_path)
    logger.log_value('The target file path is', target_file_path)

    program = os.path.join(model.application.directory, 'commands', 'extract-root')
    command = ['pkexec', program, source_file_path, target_file_path]

    # The progress callback function.
    def progress_callback(percent):
        # total_percent = Start % + Δ %
        total_percent = (FINAL_PERCENT * file_number + percent) / total_files
        # displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', total_percent)
        displayer.update_progress_bar_text('extract_page__unsquashfs_progress_bar', f'{locale.format_string("%.1f", total_percent, True)}{GAP}%')
        displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', total_percent)
        if total_percent % 5 == 0:
            logger.log_value('Completed', f'{total_percent:n}%')

    try:
        track_progress(command, progress_callback)
    except InterruptException as exception:
        model.status.is_success_extract = False
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to extract the compressed Linux file system.</span>'
            message = 'Error. Unable to extract the compressed Linux file system.'
        displayer.update_label('extract_page__unsquashfs_message', message, True)
        displayer.update_status('extract_page__unsquashfs', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        model.status.is_success_extract = False
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to extract the compressed Linux file system.</span>'
            message = 'Error. Unable to extract the compressed Linux file system.'
        displayer.update_label('extract_page__unsquashfs_message', message, True)
        displayer.update_status('extract_page__unsquashfs', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    model.status.is_success_extract = True
    return False  # (No error)


def merge_linux_file_system(source_file_path, target_file_path, file_number, total_files):

    logger.log_label('Merge the compressed Linux file system')
    logger.log_value('The source file path is', source_file_path)
    logger.log_value('The target file path is', target_file_path)

    program = os.path.join(model.application.directory, 'commands', 'merge-directory')
    command = ['pkexec', program, source_file_path, target_file_path]

    # The progress callback function.
    def progress_callback(percent):
        # total_percent = Start % + Δ %
        total_percent = (FINAL_PERCENT * file_number + percent) / total_files
        # displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', total_percent)
        displayer.update_progress_bar_text('extract_page__unsquashfs_progress_bar', f'{locale.format_string("%.1f", total_percent, True)}{GAP}%')
        displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', total_percent)
        if total_percent % 5 == 0:
            logger.log_value('Completed', f'{total_percent:n}%')

    try:
        track_progress(command, progress_callback)
    except InterruptException as exception:
        model.status.is_success_extract = False
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to extract the compressed Linux file system.</span>'
            message = 'Error. Unable to extract the compressed Linux file system.'
        displayer.update_label('extract_page__unsquashfs_message', message, True)
        displayer.update_status('extract_page__unsquashfs', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        model.status.is_success_extract = False
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to extract the compressed Linux file system.</span>'
            message = 'Error. Unable to extract the compressed Linux file system.'
        displayer.update_label('extract_page__unsquashfs_message', message, True)
        displayer.update_status('extract_page__unsquashfs', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    model.status.is_success_extract = True
    return False  # (No error)
