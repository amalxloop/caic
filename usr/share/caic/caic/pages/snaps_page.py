#!/usr/bin/python3

########################################################################
#                                                                      #
# snaps_page.py                                                        #
#                                                                      #
# Copyright (C) 2026 PJ Singh <psingh.cubic@gmail.com>                 #
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

# https://pypi.org/project/packaging/

########################################################################
# Imports
########################################################################

import getpass
import json
import os
import re
import sys
import time

from caic.constants import BOLD_RED, NORMAL
from caic.constants import FINAL_PERCENT
from caic.constants import OK, ERROR, PROCESSING, INFORMATION
from caic.constants import STAR
from caic.constants import SLEEP_2000_MS
from caic.constants import TIME_STAMP_FORMAT_Y_M_DTH_M_S_FZ
from caic.navigator import InterruptException
from caic.utilities import displayer
from caic.utilities import constructor
from caic.utilities import file_utilities
from caic.utilities import iso_utilities
from caic.utilities import logger
from caic.utilities import model
from caic.utilities.processor import execute_synchronous
from caic.utilities.progressor import track_progress
from caic.utilities.structures import PathPair
from caic.utilities.structures import ConfigInfo

########################################################################
# Global Variables & Constants
########################################################################

name = 'snaps_page'

# ----------------------------------------------------------------------
# Global values used to find and backup snap packages
# ----------------------------------------------------------------------

# List of operating system file paths for snap packages.
# • /snap
# • /var/lib/snapd
# • /etc/systemd
# Add known operating system snap package directories to this list.
# TODO: Consider adding /usr/lib/systemd/system
os_snap_directories = [os.path.join('snap'),                \
                       os.path.join('var', 'lib', 'snapd'), \
                       os.path.join('etc', 'systemd')]

# Pairs of source and backup directories for the root and the live
# environments.
# ┌─────────────┬─────────────────────────────────┐
# │     List    │            PathPair             │
# ├─────────────┼────────────────┬────────────────┤
# │ Environment │   Source Path  │   Backup Path  │
# ├─────────────┼────────────────┼────────────────┤
# │     Root    │ ../custom_root │ ../backup_root │
# │     Live    │ ../custom_live │ ../backup_live │
# └─────────────┴────────────────┴────────────────┘
environment_path_pairs = None

# ----------------------------------------------------------------------
# Global values used to identify, remove, and configure snap packages
# ----------------------------------------------------------------------

# State object for each environment.
snap_state_config_list = None

# Seed object for each environment.
snap_seed_config_list = None

# Snap name to paths mappings for each snap package.
snap_file_path_dict = None

# ----------------------------------------------------------------------
# Global values used to display status messages
# ----------------------------------------------------------------------

# The total number of selected snap packages.
total_picks = 0

# The total number of installed snap packages.
total_snaps = 0

# ----------------------------------------------------------------------
# Global values used to display file progress
# ----------------------------------------------------------------------

# The following values, used to display file progress, must be set prior
# to invoking the move_file_progress() function.

# The index of a snap package in the snap detail list.
snap_number = 0

# The index of a file in the snap path list for a  snap package.
file_number = 0

# The total number of files for a  snap package.
total_files = 0

########################################################################
# Navigation Functions
########################################################################


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

    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    # TODO: Remove in a future release [2026-07-25]
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    # Show page help alert.
    widget = model.builder.get_object('page_help_menu_button')
    label = widget.props.text
    new_text = constructor.add_prefix(STAR, label)
    if new_text: displayer.set_button_label('page_help_menu_button', new_text)
    # Show the menu alert.
    widget = model.builder.get_object('alert_label')
    widget.set_visible(True)

    if action == 'back':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)
        displayer.set_sensitive('snaps_page__tree_view', False)
        displayer.clear_list_store('snaps_page__snap_details__list_store')
        displayer.update_status('snaps_page__overview', PROCESSING)
        message = 'Analyzing...'
        displayer.update_label('snaps_page__overview_message', message, False)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Customize❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        return

    elif action == 'next':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)
        displayer.set_sensitive('snaps_page__tree_view', False)
        displayer.clear_list_store('snaps_page__snap_details__list_store')
        displayer.update_status('snaps_page__overview', PROCESSING)
        message = 'Analyzing...'
        displayer.update_label('snaps_page__overview_message', message, False)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Customize❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        return

    elif action == 'next-snaps':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)
        displayer.set_sensitive('snaps_page__tree_view', False)
        displayer.clear_list_store('snaps_page__snap_details__list_store')
        displayer.update_status('snaps_page__overview', PROCESSING)
        message = 'Analyzing...'
        displayer.update_label('snaps_page__overview_message', message, False)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Customize❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        return

    elif action == 'error':

        # Handle the error from the leave() function.

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
    """

    # The total number of selected snap packages.
    global total_picks
    total_picks = 0

    # The total number of installed snap packages.
    global total_snaps
    total_snaps = 0

    if action == 'back':

        # --------------------------------------------------------------
        # Identify installed snap packages
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • N/A

        # Sets the following global variables:
        # • environment_path_pairs
        # • total_snaps

        identify_installed_snaps()

        # --------------------------------------------------------------
        # Display the installed snap packages
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • total_snaps
        # • total_picks

        text_a_plural = constructor.get_plural('is', 'are', total_snaps)
        text_b_number = constructor.number_as_text(total_snaps)
        text_c_plural = constructor.get_plural('package', 'packages', total_snaps)
        text_d_number = constructor.number_as_text(total_picks).title()
        text_e_plural = constructor.get_plural('package', 'packages', total_picks)
        message = f'There {text_a_plural} {text_b_number} snap {text_c_plural} installed. {text_d_number} snap {text_e_plural} will be removed.'
        displayer.update_label('snaps_page__overview_message', message, False)
        displayer.update_status('snaps_page__overview', INFORMATION)
        displayer.set_sensitive('snaps_page__tree_view', True)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Customize❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        return

    elif action == 'next':

        # --------------------------------------------------------------
        # Identify installed snap packages
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • N/A

        # Sets the following global variables:
        # • environment_path_pairs
        # • total_snaps

        identify_installed_snaps()

        # --------------------------------------------------------------
        # Display the installed snap packages
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • total_snaps
        # • total_picks

        text_a_plural = constructor.get_plural('is', 'are', total_snaps)
        text_b_number = constructor.number_as_text(total_snaps)
        text_c_plural = constructor.get_plural('package', 'packages', total_snaps)
        text_d_number = constructor.number_as_text(total_picks).title()
        text_e_plural = constructor.get_plural('package', 'packages', total_picks)
        message = f'There {text_a_plural} {text_b_number} snap {text_c_plural} installed. {text_d_number} snap {text_e_plural} will be removed.'
        displayer.update_label('snaps_page__overview_message', message, False)
        displayer.update_status('snaps_page__overview', INFORMATION)
        displayer.set_sensitive('snaps_page__tree_view', True)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Customize❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        return

    elif action == 'next-snaps':

        # --------------------------------------------------------------
        # Identify installed snap packages
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • N/A

        # Sets the following global variables:
        # • environment_path_pairs
        # • total_snaps

        identify_installed_snaps()

        # --------------------------------------------------------------
        # Display the installed snap packages
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • total_snaps
        # • total_picks

        text_a_plural = constructor.get_plural('is', 'are', total_snaps)
        text_b_number = constructor.number_as_text(total_snaps)
        text_c_plural = constructor.get_plural('package', 'packages', total_snaps)
        text_d_number = constructor.number_as_text(total_picks).title()
        text_e_plural = constructor.get_plural('package', 'packages', total_picks)
        message = f'There {text_a_plural} {text_b_number} snap {text_c_plural} installed. {text_d_number} snap {text_e_plural} will be removed.'
        displayer.update_label('snaps_page__overview_message', message, False)
        displayer.update_status('snaps_page__overview', INFORMATION)
        displayer.set_sensitive('snaps_page__tree_view', True)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Customize❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        return

    elif action == 'error':

        # Handle the error from the leave() function.

        return

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

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # TODO: Remove in a future release [2026-07-25]
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # Hide the page help alert.
        widget = model.builder.get_object('page_help_menu_button')
        label = widget.props.text
        new_text = constructor.remove_prefix(STAR, label)
        if new_text: displayer.set_button_label('page_help_menu_button', new_text)
        # Hide the menu alert.
        widget = model.builder.get_object('alert_label')
        widget.set_visible(False)

        return

    elif action == 'next':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)
        displayer.set_sensitive('snaps_page__tree_view', False)

        displayer.update_status('snaps_page__overview', PROCESSING)
        message = 'Analyzing...'
        displayer.update_label('snaps_page__overview_message', message, False)

        # --------------------------------------------------------------
        # Backup and read original snap package configurations
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • environment_path_pairs

        # Sets the following global variables:
        # • snap_state_config_list
        # • snap_seed_config_list
        # • snap_file_path_dict

        is_error = load_snap_configurations()
        if is_error:
            displayer.reset_buttons(is_back_sensitive=True, is_next_sensitive=False)
            return 'error'  # Stay on this page.

        # Pause to allow the user to see the result.
        time.sleep(SLEEP_2000_MS)

        # --------------------------------------------------------------
        # Remove selected snap files and update the snap configurations
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • snap_state_config_list
        # • snap_seed_config_list
        # • snap_file_path_dict

        # Sets the following global variables:
        # • N/A

        is_error = remove_snaps()
        if is_error:
            displayer.reset_buttons(is_back_sensitive=True, is_next_sensitive=False)
            return 'error'  # Stay on this page.

        # --------------------------------------------------------------
        # Save the updated snap configurations
        # --------------------------------------------------------------

        displayer.update_status('snaps_page__overview', PROCESSING)
        message = 'Updating the snap package configurations.'
        displayer.update_label('snaps_page__overview_message', message, False)

        # Uses the following global variables:
        # • snap_state_config_list
        # • snap_seed_config_list

        # Sets the following global variables:
        # • N/A

        is_error = update_snap_configurations()
        if is_error:
            displayer.reset_buttons(is_back_sensitive=True, is_next_sensitive=False)
            return 'error'  # Stay on this page.

        # --------------------------------------------------------------
        # Display the results
        # --------------------------------------------------------------

        # Uses the following global variables:
        # • total_picks

        displayer.update_status('snaps_page__overview', OK)
        text_a_number = constructor.number_as_text(total_picks)
        text_b_plural = constructor.get_plural('package', 'packages', total_picks)
        # text_b_number = constructor.number_as_text(total_snaps)
        # message = f'Removed {text_a_number} of {text_b_number} snap packages.'
        message = f'Removed {text_a_number} snap {text_b_plural}.'
        displayer.update_label('snaps_page__overview_message', message, False)

        # Pause to allow the user to see the result.
        time.sleep(SLEEP_2000_MS)

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # TODO: Remove in a future release [2026-07-25]
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # Hide the page help alert.
        widget = model.builder.get_object('page_help_menu_button')
        label = widget.props.text
        new_text = constructor.remove_prefix(STAR, label)
        if new_text: displayer.set_button_label('page_help_menu_button', new_text)
        # Hide the menu alert.
        widget = model.builder.get_object('alert_label')
        widget.set_visible(False)

        return

    elif action == 'error':

        # Handle the error from the leave() function.

        displayer.reset_buttons(is_back_sensitive=True, is_next_sensitive=False)

        # If the following is used, use button_style='text-button' in
        # the leave/cancel section.
        #
        # displayer.reset_buttons(
        #     back_button_label='❬Back',
        #     back_action='cancel',
        #     back_button_style='suggested-action',
        #     is_back_sensitive=True,
        #     is_back_visible=True,
        #     next_button_label='Delete',
        #     next_action='delete',
        #     next_button_style='destructive-action',
        #     is_next_sensitive=False,
        #     is_next_visible=True)

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

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return 'unknown'


########################################################################
# Handler Functions
########################################################################


def on_toggled__snaps_page__select_check_button(widget, row):

    global total_picks
    global total_snaps

    # 0: is_selected
    # 1: progress
    # 2: snap_name
    # 3: snap_title
    # 4: progress_note

    list_store = model.builder.get_object('snaps_page__snap_details__list_store')

    # Toggle the checkbox.
    list_store[row][0] = not list_store[row][0]

    # Increment or decrement the count of total selections.
    total_picks += 1 if list_store[row][0] else -1

    # Change the status icon if one or more snap packages are selected.
    status = ERROR if total_picks > 0 else INFORMATION
    displayer.update_status('snaps_page__overview', status)

    # Update the overview status message.
    text_a_plural = constructor.get_plural('is', 'are', total_snaps)
    text_b_number = constructor.number_as_text(total_snaps)
    text_c_plural = constructor.get_plural('package', 'packages', total_snaps)
    text_d_number = constructor.number_as_text(total_picks).title()
    text_e_plural = constructor.get_plural('package', 'packages', total_picks)
    message = f'There {text_a_plural} {text_b_number} snap {text_c_plural} installed. {text_d_number} snap {text_e_plural} will be removed.'
    displayer.update_label('snaps_page__overview_message', message, False)


########################################################################
# Support Functions
########################################################################

# ----------------------------------------------------------------------
# List Store Functions
# ----------------------------------------------------------------------

# N/A

# ----------------------------------------------------------------------
# Snap Package Processing Functions
# ----------------------------------------------------------------------


def insert(new_row, rows):
    """
    Insert a new row into a list of rows in alphabetical order using the
    third column for comparison.

    Arguments:
    new_row : list
        The row to insert.
    rows : Gtk.ListStore
        The list store.
    """

    # 0: is_selected
    # 1: progress
    # 2: snap_name
    # 3: snap_title
    # 4: progress_note

    for index, row in enumerate(rows):
        if new_row[2] < row[2]:
            rows.insert(index, new_row)
            break
        if new_row[2] == row[2]:
            break
    else:
        rows.append(new_row)


def identify_installed_snaps():
    """
    Identify installed snap packages from the snap state file in each
    environment.
    """

    # Uses the following global variables:
    # • N/A

    # Sets the following global variables:
    # • environment_path_pairs
    # • total_snaps

    logger.log_label('Identify installed snap packages')

    # List of operating system file paths for snap packages.
    global environment_path_pairs
    environment_path_pairs = None

    # The total number of installed snap packages.
    global total_snaps
    total_snaps = 0

    #
    # Enumerate environments that contain snap packages
    #

    # List of operating system file paths for snap packages.
    environment_path_pairs = []

    # The following values are set on the indicated pages:
    # • model.project.custom_root_directory: Start page
    # • model.project.backup_root_directory: Project page or Extract page
    # • model.project.custom_live_directory: Project page or Extract page
    # • model.project.backup_live_directory: Project page or Extract page

    # If the root environment contains snaps, assign a pair of source
    # and backup directories.
    if model.project.custom_root_directory and model.project.backup_root_directory:
        environment_path_pair = PathPair(model.project.custom_root_directory, \
                                         model.project.backup_root_directory)
        environment_path_pairs.append(environment_path_pair)

    # If the live environment contains snaps, assign a pair of source
    # and backup directories.
    if model.project.custom_live_directory and model.project.backup_live_directory:
        environment_path_pair = PathPair(model.project.custom_live_directory, \
                                         model.project.backup_live_directory)
        environment_path_pairs.append(environment_path_pair)

    #
    # Identify snap packages
    #

    list_store_name = 'snaps_page__snap_details__list_store'
    list_store = model.builder.get_object(list_store_name)

    # Read all snap packages installed in the root environment and
    # the live environment from the following files:
    # • custom-root/var/lib/snapd/state.json
    # • custom-live/var/lib/snapd/state.json
    for environment_path_pair in environment_path_pairs:

        # (1) Snap State

        # Create a working snap state file, readable (and writable)
        # by the user.
        # Note, the working *.tmp file is in the source directory.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'state.json')
        backup_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'state.json.tmp')
        # The copy-path command ensures parent directories exist.
        copy_file(source_file_path, backup_file_path, user=getpass.getuser())

        # Identify installed snap packages from the state file.
        # Insert snap package details into the list store alphabetically.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'state.json.tmp')
        logger.log_value('Identify installed snap packages from', source_file_path)
        snap_names = get_snap_names_from_state(source_file_path)
        for snap_name in snap_names:
            is_selected = False
            progress = 0
            snap_title = constructor.to_title(snap_name)
            # Add spaces to pad the text when displayed in the cell.
            progress_note = f'    {snap_name}'
            snap_details = [is_selected, progress, snap_name, snap_title, progress_note]
            insert(snap_details, list_store)

        # (2) Snap Seed

        # Create a working snap seed file, readable (and writable)
        # by the user, in the source directory.
        # Note, the working *.tmp file is in the source directory.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
        backup_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml.tmp')
        # The copy-path command ensures parent directories exist.
        copy_file(source_file_path, backup_file_path, user=getpass.getuser())

        # Identify installed snap packages from the seed file.
        # Insert snap package details into the list store alphabetically.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml.tmp')
        logger.log_value('Identify installed snap packages from', source_file_path)
        snap_names = get_snap_names_from_seed(source_file_path)
        for snap_name in snap_names:
            is_selected = False
            progress = 0
            snap_title = constructor.to_title(snap_name)
            # Add spaces to pad the text when displayed in the cell.
            progress_note = f'    {snap_name}'
            snap_details = [is_selected, progress, snap_name, snap_title, progress_note]
            insert(snap_details, list_store)

    # Set global value.
    total_snaps = len(list_store)


def load_snap_configurations():
    """
    Backup and read original snap configurations.
    """

    # Uses the following global variables:
    # • environment_path_pairs

    # Sets the following global variables:
    # • snap_state_config_list
    # • snap_seed_config_list
    # • snap_file_path_dict

    # The following are set in the identify_installed_snaps() function.

    # List of operating system file paths for snap packages.
    global environment_path_pairs

    # The following are used in the remove_snaps() function.

    # State object for each environment.
    global snap_state_config_list
    snap_state_config_list = []

    # Seed object for each environment.
    global snap_seed_config_list
    snap_seed_config_list = []

    # Snap name to paths mappings for each snap package.
    global snap_file_path_dict
    snap_file_path_dict = {}

    # Pairs of source and backup directories for the root and the live
    # environments.
    # ┌─────────────┬─────────────────────────────────┐
    # │     List    │            PathPair             │
    # ├─────────────┼────────────────┬────────────────┤
    # │ Environment │   Source Path  │   Backup Path  │
    # ├─────────────┼────────────────┼────────────────┤
    # │     Root    │ ../custom_root │ ../backup_root │
    # │     Live    │ ../custom_live │ ../backup_live │
    # └─────────────┴────────────────┴────────────────┘
    for environment_path_pair in environment_path_pairs:

        file_utilities.make_directory(environment_path_pair.backup_path)

        #
        # (1) Snap State
        #

        # The ConfigInfo class is used to store configuration
        # object and corresponding source and backup file paths for
        # the snap state configuration file in each environment.
        # ┌───────────────────────────────────────────────────────┐
        # │                    ConfigInfo                         │
        # ├───────────────┬───────────────────┬───────────────────┤
        # │ Configuration │    Source Path    │    Backup Path    │
        # ├───────────────┼───────────────────┼───────────────────┤
        # │ Dictionary    │ ../state.json     │ ../state.json.tmp │
        # └───────────────┴───────────────────┴───────────────────┘

        # Backup the original snap state file if it does not exist.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'state.json')
        backup_file_path = os.path.join(environment_path_pair.backup_path, 'var', 'lib', 'snapd', 'state.json')
        if not os.path.exists(backup_file_path):
            logger.log_label('Backup the original snap state file')
            # The copy-path command ensures parent directories exist.
            is_error = copy_file(source_file_path, backup_file_path, user='root')
            if is_error: return True  # Error

        # Commented out because this file was already created in the
        # identify_installed_snaps() function.
        '''
        # Create a working snap state file, readable (and writable)
        # by the user.
        # Note, the working *.tmp file is in the source directory.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'state.json')
        backup_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'state.json.tmp')
        # The copy-path command ensures parent directories exist.
        copy_file(source_file_path, backup_file_path, user=getpass.getuser())
        '''

        # Create a list of snap state configurations.
        # Note, the working *.tmp file is in the source directory.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'state.json')
        backup_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'state.json.tmp')
        snap_state_config = file_utilities.read_json_file(backup_file_path)
        config_info = ConfigInfo(snap_state_config, source_file_path, backup_file_path)
        snap_state_config_list.append(config_info)

        #
        # (2) Snap Seed
        #

        # The ConfigInfo class is used to store configuration
        # object and corresponding source and backup file paths for
        # the snap seed configuration file in each environment.
        # ┌───────────────────────────────────────────────────────┐
        # │                    ConfigInfo                         │
        # ├───────────────┬───────────────────┬───────────────────┤
        # │ Configuration │    Source Path    │    Backup Path    │
        # ├───────────────┼───────────────────┼───────────────────┤
        # │ Dictionary    │ ../seed.yaml      │ ../seed.yaml.tmp  │
        # └───────────────┴───────────────────┴───────────────────┘

        # Backup the original snap seed file if it does not exist.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
        backup_file_path = os.path.join(environment_path_pair.backup_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
        if not os.path.exists(backup_file_path):
            logger.log_label('Backup the original snap seed file')
            # The copy-path command ensures parent directories exist.
            is_error = copy_file(source_file_path, backup_file_path, user='root')
            if is_error: return True  # Error

        # Commented out because this file was already created in the
        # identify_installed_snaps() function.
        '''
        # Create a working snap seed file, readable (and writable)
        # by the user, in the source directory.
        # Note, the working *.tmp file is in the source directory.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
        backup_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml.tmp')
        # The copy-path command ensures parent directories exist.
        copy_file(source_file_path, backup_file_path, user=getpass.getuser())
        '''

        # Create a list of snap seed configurations.
        # Note, the working *.tmp file is in the source directory.
        source_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml')
        backup_file_path = os.path.join(environment_path_pair.source_path, 'var', 'lib', 'snapd', 'seed', 'seed.yaml.tmp')
        snap_seed_config = file_utilities.read_yaml_file(backup_file_path)
        config_info = ConfigInfo(snap_seed_config, source_file_path, backup_file_path)
        snap_seed_config_list.append(config_info)

        #
        # (3) Snap Files
        #

        # The PathPair class is used to store the source path and
        # corresponding backup path for each identified snap file
        # for each environment.
        # ┌────────────┬───────────────────────────────────────┐
        # │ Dictionary │               PathPair                │
        # ├────────────┼───────────────────┬───────────────────┤
        # │ Snap Name  │    Source Path    │    Backup Path    │
        # ├────────────┼───────────────────┼───────────────────┤
        # │ snap_name  │ ../custom_root/.. │ ../backup_root/.. │
        # │ snap_name  │ ../custom_live/.. │ ../backup_live/.. │
        # └────────────┴───────────────────┴───────────────────┘

        list_store_name = 'snaps_page__snap_details__list_store'
        list_store = model.builder.get_object(list_store_name)
        for list_store_row in list_store:

            is_selected = list_store_row[0]
            # progress = list_store_row[1]
            snap_name = list_store_row[2]
            # snap_title = list_store_row[3]
            # progress_note = list_store_row[4]

            # Skip unselected snap packages.
            if not is_selected: continue

            # Create a list of file paths for this snap.
            if snap_name not in snap_file_path_dict:
                snap_file_path_dict[snap_name] = set()
            snap_path_set = snap_file_path_dict[snap_name]
            file_name_pattern = rf'.*{snap_name}.*'
            for snap_directory in os_snap_directories:
                source_start_path = os.path.join(environment_path_pair.source_path, snap_directory)
                backup_start_path = os.path.join(environment_path_pair.backup_path, snap_directory)
                # Search for snap files based on file name.
                relative_file_paths = file_utilities.find_files_with_name(file_name_pattern, source_start_path)
                for relative_file_path in relative_file_paths:
                    source_path = os.path.join(source_start_path, relative_file_path)
                    backup_path = os.path.join(backup_start_path, relative_file_path)
                    path_pair = PathPair(source_path, backup_path)
                    snap_path_set.add(path_pair)


def remove_snaps():
    """
    Remove selected snap files and update the snap configurations.

    Returns:
    is_error : bool
        True if an error occurred, false otherwise.
    """

    # Uses the following global variables:
    # • snap_state_config_list
    # • snap_seed_config_list
    # • snap_file_path_dict

    # Sets the following global variables:
    # • N/A

    # The following are set in the load_snap_configurations() function.

    # State object for each environment.
    global snap_state_config_list

    # Seed object for each environment.
    global snap_seed_config_list

    # Snap name to paths mappings for each snap package.
    global snap_file_path_dict

    # The following values, used to display file progress, must be set
    # prior to invoking the move_file_progress() function.

    # The index of a snap package in the snap detail list.
    global snap_number

    # The index of a file in the snap path list for a snap.
    global file_number

    # The total number of files for a snap.
    global total_files

    selection_number = 0
    list_store_name = 'snaps_page__snap_details__list_store'
    list_store = model.builder.get_object(list_store_name)
    for snap_number, list_store_row in enumerate(list_store):

        is_selected = list_store_row[0]
        # progress = list_store_row[1]
        snap_name = list_store_row[2]
        # snap_title = list_store_row[3]
        # progress_note = list_store_row[4]

        # Skip unselected snap packages.
        if not is_selected: continue

        selection_number += 1

        displayer.update_status('snaps_page__overview', PROCESSING)
        text_a_number = constructor.number_as_text(selection_number)
        text_b_number = constructor.number_as_text(total_picks)
        message = f'Removing snap package {text_a_number} of {text_b_number}.'
        displayer.update_label('snaps_page__overview_message', message, False)

        # Add spaces to pad the text when displayed in the cell.
        message = f'    Removing {snap_name} ...'
        displayer.update_list_store_progress_bar_text('snaps_page__snap_details__list_store', snap_number, 4, message)

        #
        # (3) Snap Files
        #

        # Process the snap files first, since this is shown in the
        # progress bars.

        snap_path_set = snap_file_path_dict.get(snap_name, set())
        total_files = len(snap_path_set)
        for file_number, path_pair in enumerate(snap_path_set):

            # The following global values must be set prior to invoking
            # the move_file_progress() function.
            # • snap_number - Index of the snap package
            # • file_number - Current file number for this snap
            # • total_files - Total number of files for this snap
            source_path = path_pair.source_path
            backup_path = path_pair.backup_path
            # Move the selected file or directory to the backup.
            # The move-path command ensures parent directories exist.
            is_error = move_file_progress(source_path, backup_path)
            # TODO: Do we need this, since progressor already does it.
            sys.stdout.flush()  # Flush the output before proceeding.
            if is_error: return True  # Error

        #
        # (1) Snap State
        #

        for snap_state_config_info in snap_state_config_list:
            snap_state_config = snap_state_config_info.configuration
            # TODO: Consider validating state in the remove_snap_state()
            # function and returning "is_error" accordingly.
            # The snap state is validated at the end in the
            # update_snap_configurations() function, so "is_error =" is
            # not necessary here.
            remove_snap_state(snap_name, snap_state_config)

        #
        # (2) Snap Seed
        #

        for snap_seed_config_info in snap_seed_config_list:
            snap_seed_config = snap_seed_config_info.configuration
            is_error = remove_snap_seed(snap_name, snap_seed_config)
            # TODO: Do we need this, since progressor already does it.
            sys.stdout.flush()  # Flush the output before proceeding.
            if is_error: return True  # Error

        # Add spaces to pad the text when displayed in the cell.
        message = f'    Removed {snap_name}'
        displayer.update_list_store_progress_bar_text('snaps_page__snap_details__list_store', snap_number, 4, message)
        # Address situations where there were no files to move.
        displayer.update_list_store_progress_bar_percent('snaps_page__snap_details__list_store', snap_number, 1, FINAL_PERCENT)

        displayer.update_status('snaps_page__overview', OK)
        text_a_number = constructor.number_as_text(selection_number)
        text_b_number = constructor.number_as_text(total_picks)
        message = f'Removed snap package {text_a_number} of {text_b_number}.'
        displayer.update_label('snaps_page__overview_message', message, False)

        # Pause to allow the user to see the result.
        time.sleep(SLEEP_2000_MS)


def update_snap_configurations():
    """
    Save the updated snap configurations.

    Returns:
    is_error : bool
        True if an error occurred, false otherwise.
    """

    # Uses the following global variables:
    # • snap_state_config_list
    # • snap_seed_config_list

    # Sets the following global variables:
    # • N/A

    # The following are set in the load_snap_configurations() function.

    # State object for each environment.
    global snap_state_config_list

    # Seed object for each environment.
    global snap_seed_config_list

    # Save the snap state configuration file for each environment.
    for snap_state_config_info in snap_state_config_list:

        snap_state_config = snap_state_config_info.configuration
        source_file_path = snap_state_config_info.source_path
        backup_file_path = snap_state_config_info.backup_path

        # Validate the updated snap state file in memory.
        if not is_state_valid(snap_state_config): return True  # (Error)

        # Save the updated snap state file.
        # The file must be writable by the user.
        file_utilities.save_json_file(snap_state_config, backup_file_path)

        # Overwrite the snap state file with the working file.
        # The move-path command ensures parent directories exist.
        is_error = move_file(backup_file_path, source_file_path, user='root')
        if is_error: return True  # Error

    # Save the snap seed configuration file for each environment.

    for snap_seed_config_info in snap_seed_config_list:

        snap_seed_config = snap_seed_config_info.configuration
        source_file_path = snap_seed_config_info.source_path
        backup_file_path = snap_seed_config_info.backup_path

        # Save the updated snap seed file.
        # The file must be writable by the user.
        file_utilities.save_yaml_file(snap_seed_config, backup_file_path)

        # Overwrite the snap seed file with the working file.
        # The move-path command ensures parent directories exist.
        is_error = move_file(backup_file_path, source_file_path, user='root')
        if is_error: return True  # Error


# ----------------------------------------------------------------------
# Configuration Functions
# ----------------------------------------------------------------------


def get_snap_names_from_state(file_path):
    """
    Read all snap names from a /var/lib/snapd/state.json structured file
    that is readable by the user.

    Arguments:
    file_path : str
        A json file using the /var/lib/snapd/state.json structure. The
        file must be readable by the user.

    Returns:
    names : str
        List of all snap names in the file.
    """

    # Load the snap state file.
    config = file_utilities.read_json_file(file_path)
    data = config.get('data', {})  # returns dict
    snaps = data.get('snaps', {})  # returns dict
    names = list(snaps.keys())
    return names


def get_snap_names_from_seed(file_path):
    """
    Read all snap names from a /var/lib/snapd/seed/seed.yaml structured
    file that is readable by the user.

    Arguments:
    file_path : str
        A yaml file using the /var/lib/snapd/seed/seed.yaml structure.
        The file must be readable by the user.

    Returns:
    names : str
        List of all snap names in the file.
    """

    # Load the snap seed file.
    config = file_utilities.read_yaml_file(file_path)
    snaps = config.get('snaps', [])
    names = [snap.get('name') for snap in snaps if snap.get('name', None)]
    return names


def remove_snap_state(snap_name, snap_state_config):
    """
    Remove the specified snap from a the an in-memory json that
    represents the /var/lib/snapd/state.json file structure.

    Arguments:
    snap_name : str
        The name of the snap to remove.
    snap_seed_config : list or dict
        A json configuration using /var/lib/snapd/state.json
        structure.
    """

    logger.log_value('Update snap state for', snap_name)

    # Collect all task IDs from changes whose summary contains the snap
    # name (case-insensitive).
    snap_name_lower = snap_name.lower()
    task_ids = set()

    # for change in snap_state_config.get('changes', {}):
    #     summary = change.get('summary', '')
    #     if snap_name_lower in summary.lower():
    #         for task_id in change.get('task-ids', []):
    #             task_ids.add(task_id)

    changes = snap_state_config.get('changes', {})
    for change in changes.values():
        summary = change.get('summary', '')
        if snap_name_lower in summary.lower():
            for task_id in change.get('task-ids', []):
                task_ids.add(task_id)

    # Remove the snap from the registry: snap_state_config['data']['snaps'][snap_name].

    # If snap_state_config['data'] already exists, set data to its
    # existing value; otherwise create snap_state_config['data'] as an
    # empty dict {} and assign it to data.
    data = snap_state_config.setdefault('data', {})

    # If data['snaps'] already exists, set snaps to its existing value;
    # otherwise create data['snaps'] as an empty dict {} and assign it
    # to snaps.
    snaps = data.setdefault('snaps', {})

    # Delete snaps[snap_name] if it is present. If the key does not
    # exist, return None and do nothing (so a KeyError will not be
    # raised).
    snaps.pop(snap_name, None)

    # Mark related changes as Done (status 0) and the set ready-time.

    # Get the current time and convert the time zone from ±HHMM to
    # ±HH:MM. The ready-time format requires 9-digit fractional seconds
    # + time zone with colon (e.g. 2026-06-19T20:46:14.000000000-04:00).
    time_stamp = constructor.get_current_time_stamp(TIME_STAMP_FORMAT_Y_M_DTH_M_S_FZ)
    time_stamp = f'{time_stamp[:-2]}:{time_stamp[-2:]}'

    # for change in snap_state_config.get('changes', []):
    #     summary = change.get('summary', '')
    #     if snap_name_lower in summary.lower():
    #         change['status'] = 0  # Done
    #         change['ready-time'] = time_stamp

    changes = snap_state_config.get('changes', {})
    for change in changes.values():
        summary = change.get('summary', '')
        if snap_name_lower in summary.lower():
            for task_id in change.get('task-ids', []):
                change['status'] = 0  # Done
                change['ready-time'] = time_stamp

    # Mark related tasks as Completed (status 4).

    # Normalize all task IDs to strings (since JSON object keys are
    # strings).
    task_ids_str = {str(task_id) for task_id in task_ids}

    # If snap_state_config['tasks'] already exists, set tasks to its existing value;
    # otherwise create snap_state_config['tasks'] as an empty {} dict and assign it to
    # tasks.
    tasks = snap_state_config.setdefault('tasks', {})

    for task_id_str, task_object in tasks.items():
        # If the task key corresponds to one of the collected task IDs,
        # update its status.
        if task_id_str in task_ids_str:
            # Only set status when the task entry is a dict-like object.
            if isinstance(task_object, dict):
                task_object['status'] = 4  # Complete


def is_state_valid(state):
    """
    Validate the updated snap state in memory.
    """

    # logger.log_label('Validate the snap state file')
    try:
        # Serialize the Python state object into a JSON-formatted string.
        state_text = json.dumps(state, ensure_ascii=False, indent=2)
        # Verify the updated JSON is valid.
        json.loads(state_text)
    except (TypeError, ValueError) as exception:
        logger.log_value('Is the snap state file valid?', 'Error')
        return False  # (Error)
    else:
        logger.log_value('Is the snap state file valid?', True)
        return True  # (OK)


def remove_snap_seed(snap_name, snap_seed_config):
    """
    Remove the specified snap from a the an in-memory yaml that
    represents the  /var/lib/snapd/seed/seed.yaml file structure.

    Arguments:
    snap_name : str
        The name of the snap to remove.
    snap_seed_config : list or dict
        A yaml configuration using /var/lib/snapd/seed/seed.yaml
        structure.
    """

    logger.log_value('Update snap seed for', snap_name)

    snap_list = snap_seed_config.get('snaps', [])
    new_snap_list = [snap_info for snap_info in snap_list if snap_info['name'] != snap_name]
    snap_seed_config['snaps'] = new_snap_list


# ----------------------------------------------------------------------
# File Functions
# ----------------------------------------------------------------------


def copy_file(source_file_path, target_file_path, user='root'):
    """
    Copy the source file to the target file path. If the target file
    already exists, the source file will overwrite it without throwing
    an exception.

    Arguments:
    source_file_path : str
        The full path of the file to copy.
    target_file_path : str
        The full path to copy the file to.
    user : str
        The ownership of the target file. If not specified, the user
        defaults to 'root'.

    Returns:
    is_error : bool
        True if an error occurred or if interrupted, false otherwise.

    Raises:
    : Exception
        The exception that occurred.
    """

    logger.log_value('Copy file from', source_file_path)
    logger.log_value('Copy file to', target_file_path)
    try:
        # user='root'
        # user=getpass.getuser()
        program = os.path.join(model.application.directory, 'commands', 'copy-path')
        command = ['pkexec', program, source_file_path, target_file_path, user]
        result, exit_status, signal_status = execute_synchronous(command)
    except InterruptException as exception:
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = f'Error. Unable to copy {source_file_path} to {target_file_path}.'
            message = 'Error. Unable to copy file.'
        displayer.update_label('snaps_page__overview_message', message, True)
        displayer.update_status('snaps_page__overview', ERROR)
        logger.log_value('Error', f'Unable to copy {source_file_path} to {target_file_path}.')
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Error', f'Unable to copy {source_file_path} to {target_file_path}.')
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = f'Error. Unable to copy {source_file_path} to {target_file_path}.'
            message = 'Error. Unable to copy file.'
        displayer.update_label('snaps_page__overview_message', message, True)
        displayer.update_status('snaps_page__overview', ERROR)
        logger.log_value('Error', f'Unable to copy {source_file_path} to {target_file_path}.')
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    return False  # (No Error)


def move_file(source_file_path, target_file_path, user=''):
    """
    Move the source file to the target file path. If the target file
    already exists, the source file will overwrite it without throwing
    an exception.

    Arguments:
    source_file_path : str
        The full path of the file to move.
    target_file_path : str
        The full path to move the file to.
    user : str
        The ownership of the target file. If not specified, the original
        file ownership is applied.

    Returns:
    is_error : bool
        True if an error occurred or if interrupted, false otherwise.

    Raises:
    : Exception
        The exception that occurred.
    """

    logger.log_value('Move file from', source_file_path)
    logger.log_value('Move file to', target_file_path)

    try:
        # user='root'
        # user=getpass.getuser()
        program = os.path.join(model.application.directory, 'commands', 'move-path')
        command = ['pkexec', program, source_file_path, target_file_path, user]
        result, exit_status, signal_status = execute_synchronous(command)
    except InterruptException as exception:
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = f'Error. Unable to move {source_file_path} to {target_file_path}.'
            message = 'Error. Unable to remove file.'
        displayer.update_label('snaps_page__overview_message', message, True)
        displayer.update_status('snaps_page__overview', ERROR)
        logger.log_value('Error', f'Unable to move {source_file_path} to {target_file_path}.')
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Error', f'Unable to move {source_file_path} to {target_file_path}.')
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = f'Error. Unable to move {source_file_path} to {target_file_path}.'
            message = 'Error. Unable to remove file.'
        displayer.update_label('snaps_page__overview_message', message, True)
        displayer.update_status('snaps_page__overview', ERROR)
        logger.log_value('Error', f'Unable to move {source_file_path} to {target_file_path}.')
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    return False  # (No Error)


def move_file_progress(source_file_path, target_file_path, user='root'):
    """
    Move the source file to the target file path. If the target file
    already exists, the source file will overwrite it without throwing
    an exception.

    Arguments:
    source_file_path : str
        The full path of the file to move.
    target_file_path : str
        The full path to move the file to.
    user : str
        The ownership of the target file. If not specified, the original
        file ownership is applied.

    Returns:
    is_error : bool
        True if an error occurred or if interrupted, false otherwise.

    Raises:
    : Exception
        The exception that occurred.
    """

    logger.log_value('Move file from', source_file_path)
    logger.log_value('Move file to', target_file_path)

    # user='root'
    # user=getpass.getuser()
    program = os.path.join(model.application.directory, 'commands', 'move-path')
    command = ['pkexec', program, source_file_path, target_file_path, user]

    # The progress callback function.
    def progress_callback(percent):

        # The following global values must be set prior to calling
        # this function.

        # The index of this snap package.
        global snap_number
        # The current file number to process.
        global file_number
        # The total number of files to process.
        global total_files

        total_percent = (FINAL_PERCENT * file_number + percent) / total_files
        # displayer.update_progress_bar_percent('boot_copy_page__copy_files_progress_bar', total_percent)
        displayer.update_list_store_progress_bar_percent('snaps_page__snap_details__list_store', snap_number, 1, total_percent)
        if total_percent % 10 == 0:
            logger.log_value('Completed', f'{total_percent:n}%')

    try:
        track_progress(command, progress_callback, quantity=total_files)
        # Ensure progress bar displays 100%; this is necessary if the
        # file was previously moved.
        # displayer.update_list_store_progress_bar_percent('snaps_page__snap_details__list_store', snap_number, 1, FINAL_PERCENT)
    except InterruptException as exception:
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = f'Error. Unable to move {source_file_path} to {target_file_path}.'
            message = 'Error. Unable to remove file.'
        displayer.update_label('snaps_page__overview_message', message, True)
        displayer.update_status('snaps_page__overview', ERROR)
        logger.log_value('Error', f'Unable to move {source_file_path} to {target_file_path}.')
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Error', f'Unable to move {source_file_path} to {target_file_path}.')
        if any(re.findall(r'exceeds free space|No space left|out of space', str(exception), re.IGNORECASE)):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = f'Error. Unable to move {source_file_path} to {target_file_path}.'
            message = 'Error. Unable to remove file.'
        displayer.update_label('snaps_page__overview_message', message, True)
        displayer.update_status('snaps_page__overview', ERROR)
        logger.log_value('Error', f'Unable to move {source_file_path} to {target_file_path}.')
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    return False  # (No Error)
