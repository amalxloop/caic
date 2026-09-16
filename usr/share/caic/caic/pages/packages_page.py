#!/usr/bin/python3

########################################################################
#                                                                      #
# packages_page.py                                                     #
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

# https://pypi.org/project/packaging/

########################################################################
# Imports
########################################################################

import os

from caic.constants import BOLD_RED, NORMAL, OK
from caic.utilities import displayer
from caic.utilities import file_utilities
from caic.utilities import iso_utilities
from caic.utilities import logger
from caic.utilities import model
from caic.utilities.processor import execute_synchronous

########################################################################
# Global Variables & Constants
########################################################################

name = 'packages_page'

undo_index = 0
undo_list = None

has_minimal_install = None


def is_arch_layout():
    """
    Determine if the current layout is an Arch layout, based on whether
    an Arch squashfs directory was identified (e.g. "arch" or
    "arch/x86_64"). Arch layouts install and remove packages with
    pacman instead of writing Ubuntu installer manifest files.

    Returns:
    : bool
        True if the current layout is an Arch layout, else False.
    """

    return bool(model.layout.squashfs_directory.startswith('arch'))


def create_package_details_list(root_directory):
    """
    Create a list of installed package details. This function delegates
    to the identical function in prepare_page.py.

    Arguments:
    root_directory : str
        The root directory of "var/lib/pacman" (the pacman database).

    Returns:
    package_details_list : list
        A list of package details.
    """

    logger.log_label('Create list of installed packages')

    from caic.pages.prepare_page import create_package_details_list as create_list
    return create_list(root_directory)

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

    global undo_index
    global undo_list

    if action == 'back':

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        displayer.set_visible('packages_page__header_bar_box_1', True)
        displayer.set_visible('packages_page__header_bar_box_2', True)
        displayer.set_visible('packages_page__arch_install_box', False)
        displayer.set_visible('options_page__stack_switcher', False)

        return

    elif action == 'next':

        undo_index = 0
        undo_list = []

        displayer.update_list_store('packages_page__list_store', model.package_details_list)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        # Show the revert, and undo, and redo buttons buttons.
        displayer.set_visible('packages_page__header_bar_box_1', True)
        displayer.set_sensitive('packages_page__revert_header_bar_button', False)
        displayer.set_sensitive('packages_page__undo_header_bar_button', False)
        displayer.set_sensitive('packages_page__redo_header_bar_button', False)

        # Show or hide the minimal install switch and column.
        global has_minimal_install

        if is_arch_layout():
            # Arch layouts use pacman package operations instead of the
            # Ubuntu installer manifest process. Hide the minimal install
            # switch and column (private arch has no minimal install
            # concept) and show the install packages entry.
            has_minimal_install = False
            logger.log_value('Use Arch layout package operations?', 'Yes')
            displayer.activate_switch('packages_page__minimal_install_header_bar_switch', False)
            displayer.set_column_visible('packages_page__remove_2_tree_view_column', False)
            displayer.set_visible('packages_page__header_bar_box_2', False)
            displayer.set_visible('packages_page__arch_install_box', True)
            displayer.update_label('packages_page__intro_label', 'Select packages to be removed from the custom disk, or install new packages with pacman.')
            displayer.update_label('packages_page__subtitle_label', 'Check marked packages will be <i>removed from</i> the custom disk image.')
            displayer.update_entry('packages_page__install_entry', '')
            displayer.update_label('packages_page__install_message_label', '', False)
            displayer.set_sensitive('packages_page__install_button', True)
        else:
            has_minimal_install = model.options.has_minimal_install
            displayer.set_visible('packages_page__arch_install_box', False)
            if has_minimal_install:
                # Activate the the minimal install switch.
                logger.log_value('Activate the minimal install switch?', 'Yes')
                displayer.activate_switch('packages_page__minimal_install_header_bar_switch', True)
                # Show the minimal install check box column.
                logger.log_value('Show the minimal install column?', 'Yes')
                displayer.set_column_visible('packages_page__remove_2_tree_view_column', True)
            else:
                # Deactivate the the minimal install switch.
                logger.log_value('Activate the minimal install switch?', 'No')
                displayer.activate_switch('packages_page__minimal_install_header_bar_switch', False)
                # Hide the minimal install check box column.
                logger.log_value('Show the minimal install column?', 'No')
                displayer.set_column_visible('packages_page__remove_2_tree_view_column', False)
            displayer.set_visible('packages_page__header_bar_box_2', True)

        # Hide the stack switcher.
        displayer.set_visible('options_page__stack_switcher', False)

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

    if action == 'back':

        return

    elif action == 'next':

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

        displayer.set_visible('packages_page__header_bar_box_1', False)
        displayer.set_visible('packages_page__header_bar_box_2', False)

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'next':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('packages_page__header_bar_box_1', False)
        displayer.set_visible('packages_page__header_bar_box_2', False)
        displayer.set_visible('packages_page__arch_install_box', False)

        if is_arch_layout():
            # Arch layouts do not use the Ubuntu installer manifest
            # process. Remove the checked packages with pacman instead.
            logger.log_label('Remove selected packages with pacman')
            is_error = remove_selected_packages()
            if is_error:
                displayer.update_label('packages_page__install_message_label', 'Error. Unable to remove the selected packages.', True)
                displayer.set_visible('packages_page__arch_install_box', True)
                displayer.reset_buttons(is_back_sensitive=True, is_next_sensitive=True)
                return 'error'
            # The minimal install concept does not apply to Arch.
            model.options.has_minimal_install = False
            # Save the model values.
            model.project.configuration.save()
            return

        # Create the removable packages list for a standard install.
        logger.log_label('Create the removable packages list for a standard install')
        create_standard_removable_packages_list()

        # Create the removable packages list for a minimal install.
        logger.log_label('Create the removable packages list for a minimal install')
        create_minimal_removable_packages_list()

        # Update the model to acknowledge changes.
        model.options.has_minimal_install = has_minimal_install

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'error':

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


def on_clicked__packages_page__revert_header_bar_button(widget):

    global undo_index
    global undo_list

    # 0: is standard selected?
    # 1: is minimal selected?
    # 2: is minimal selected initial?
    # 3: is minimal active?
    # 4: package name
    # 5: package version

    list_store = model.builder.get_object('packages_page__list_store')

    while undo_index > 0:

        undo_index -= 1

        row, column = undo_list[undo_index]

        displayer.select_tree_view_row('packages_page__tree_view', row)
        # displayer.scroll_to_tree_view_row('packages_page__tree_view', row)
        # time.sleep(SLEEP_0250_MS)
        """
        print(
            ' -'
            f' Row: {row},'
            f' Column: {column},'
            f' Standard: {list_store[row][0]},'
            f' Minimal: {list_store[row][1]},'
            f' Previous: {list_store[row][2]},'
            f' Active: {list_store[row][3]},'
            f' Length: {len(undo_list)},'
            f' Index: {undo_index}')
        """

        if column == 0:
            list_store[row][0] = not list_store[row][0]
            # Update the list store even though the minimal check button
            # column may not be visible.
            if list_store[row][0]:
                # Backup original minimal check button value
                list_store[row][2] = list_store[row][1]
                # Set minimal check button selected
                list_store[row][1] = True
                # Set minimal check button inactive
                list_store[row][3] = False
            else:
                # Restore original minimal check button value
                list_store[row][1] = list_store[row][2]
                # Set minimal check button active
                list_store[row][3] = True
        else:
            list_store[row][1] = not list_store[row][1]

    # if undo_index == 0:
    displayer.set_sensitive('packages_page__revert_header_bar_button', False)
    displayer.set_sensitive('packages_page__undo_header_bar_button', False)

    displayer.set_sensitive('packages_page__redo_header_bar_button', True)
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """


def on_clicked__packages_page__undo_header_bar_button(widget):

    global undo_index
    global undo_list

    undo_index -= 1

    # 0: is standard selected?
    # 1: is minimal selected?
    # 2: is minimal selected initial?
    # 3: is minimal active?
    # 4: package name
    # 5: package version

    list_store = model.builder.get_object('packages_page__list_store')

    row, column = undo_list[undo_index]

    displayer.select_tree_view_row('packages_page__tree_view', row)
    # displayer.scroll_to_tree_view_row('packages_page__tree_view', row)
    # time.sleep(SLEEP_0250_MS)
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """

    if column == 0:
        list_store[row][0] = not list_store[row][0]
        # Update the list store even though the minimal check button
        # column may not be visible.
        if list_store[row][0]:
            # Backup original minimal check button value
            list_store[row][2] = list_store[row][1]
            # Set minimal check button selected
            list_store[row][1] = True
            # Set minimal check button inactive
            list_store[row][3] = False
        else:
            # Restore original minimal check button value
            list_store[row][1] = list_store[row][2]
            # Set minimal check button active
            list_store[row][3] = True
    else:
        list_store[row][1] = not list_store[row][1]

    if undo_index == 0:
        displayer.set_sensitive('packages_page__revert_header_bar_button', False)
        displayer.set_sensitive('packages_page__undo_header_bar_button', False)

    displayer.set_sensitive('packages_page__redo_header_bar_button', True)
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """


def on_clicked__packages_page__redo_header_bar_button(widget):

    global undo_index
    global undo_list

    # 0: is standard selected?
    # 1: is minimal selected?
    # 2: is minimal selected initial?
    # 3: is minimal active?
    # 4: package name
    # 5: package version

    list_store = model.builder.get_object('packages_page__list_store')

    row, column = undo_list[undo_index]

    displayer.select_tree_view_row('packages_page__tree_view', row)
    # displayer.scroll_to_tree_view_row('packages_page__tree_view', row)
    # time.sleep(SLEEP_0250_MS)
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """

    if column == 0:
        list_store[row][0] = not list_store[row][0]
        # Update the list store even though the minimal check button
        # column may not be visible.
        if list_store[row][0]:
            # Backup original minimal check button value
            list_store[row][2] = list_store[row][1]
            # Set minimal check button selected
            list_store[row][1] = True
            # Set minimal check button inactive
            list_store[row][3] = False
        else:
            # Restore original minimal check button value
            list_store[row][1] = list_store[row][2]
            # Set minimal check button active
            list_store[row][3] = True
    else:
        list_store[row][1] = not list_store[row][1]

    undo_index += 1

    if len(undo_list) == undo_index:
        displayer.set_sensitive('packages_page__redo_header_bar_button', False)

    displayer.set_sensitive('packages_page__revert_header_bar_button', True)
    displayer.set_sensitive('packages_page__undo_header_bar_button', True)
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """


def on_state_set__packages_page__minimal_install_header_bar_switch(widget, is_active):

    global has_minimal_install
    if is_active:
        # Show the minimal install check box column.
        has_minimal_install = True
        logger.log_value('Show the minimal install column?', 'Yes')
        displayer.set_column_visible('packages_page__remove_2_tree_view_column', True)
    else:
        # Do not show the minimal install check box column.
        has_minimal_install = False
        logger.log_value('Show the minimal install column?', 'No')
        displayer.set_column_visible('packages_page__remove_2_tree_view_column', False)


def on_toggled__packages_page__remove_1_check_button(widget, row):

    global undo_index
    global undo_list

    # 0: is standard selected?
    # 1: is minimal selected?
    # 2: is minimal selected initial?
    # 3: is minimal active?
    # 4: package name
    # 5: package version

    list_store = model.builder.get_object('packages_page__list_store')
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """

    # Note: column = 0

    list_store[row][0] = not list_store[row][0]

    # Update the list store even though the minimal check button
    # column may not be visible.
    if list_store[row][0]:
        # Backup original minimal check button value
        list_store[row][2] = list_store[row][1]
        # Set minimal check button selected
        list_store[row][1] = True
        # Set minimal check button inactive
        list_store[row][3] = False
    else:
        # Restore original minimal check button value
        list_store[row][1] = list_store[row][2]
        # Set minimal check button active
        list_store[row][3] = True

    if len(undo_list) > undo_index:
        # print(f' - Insert at {undo_index}, value {[row, 0]}')
        undo_list[undo_index] = [row, 0]
    else:
        # print(f' - Append at {undo_index+1}, value {[row, 0]}')
        undo_list.append([row, 0])

    undo_index += 1

    displayer.set_sensitive('packages_page__revert_header_bar_button', True)
    displayer.set_sensitive('packages_page__undo_header_bar_button', True)
    displayer.set_sensitive('packages_page__redo_header_bar_button', False)
    del undo_list[undo_index:]
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """


def on_toggled__packages_page__remove_2_check_button(widget, row):

    global undo_index
    global undo_list

    # 0: is standard selected?
    # 1: is minimal selected?
    # 2: is minimal selected initial?
    # 3: is minimal active?
    # 4: package name
    # 5: package version

    list_store = model.builder.get_object('packages_page__list_store')
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """

    # Note: column = 1

    list_store[row][1] = not list_store[row][1]

    if len(undo_list) > undo_index:
        # print(f' - Insert at {undo_index}, value {[row, 1]}')
        undo_list[undo_index] = [row, 1]
    else:
        # print(f' - Append at {undo_index+1}, value {[row, 1]}')
        undo_list.append([row, 1])

    undo_index += 1

    displayer.set_sensitive('packages_page__revert_header_bar_button', True)
    displayer.set_sensitive('packages_page__undo_header_bar_button', True)
    displayer.set_sensitive('packages_page__redo_header_bar_button', False)
    del undo_list[undo_index:]
    """
    print(
        ' -'
        f' Row: {row},'
        f' Column: {column},'
        f' Standard: {list_store[row][0]},'
        f' Minimal: {list_store[row][1]},'
        f' Previous: {list_store[row][2]},'
        f' Active: {list_store[row][3]},'
        f' Length: {len(undo_list)},'
        f' Index: {undo_index}')
    """


def on_activate__packages_page__install_entry(widget):

    install_packages()


def on_clicked__packages_page__install_button(widget):

    install_packages()


########################################################################
# Support Functions
########################################################################


def install_packages():

    if not is_arch_layout():
        logger.log_value('Install packages?', 'No. Not an Arch layout.')
        return

    displayer.set_sensitive('packages_page__install_button', False)

    entry_name = 'packages_page__install_entry'
    widget = model.builder.get_object(entry_name)
    text = widget.get_text()
    package_names = text.split()
    if not package_names:
        logger.log_value('Install packages?', 'No packages specified.')
        displayer.update_label('packages_page__install_message_label', 'Enter the names of the packages to install.', True)
        displayer.set_sensitive('packages_page__install_button', True)
        return

    package_list = ' '.join(package_names)
    logger.log_label('Install packages with pacman')
    logger.log_value('Packages to install', package_list)

    displayer.update_label('packages_page__install_message_label', f'Installing {package_list} ... (requires authorization)')

    program = os.path.join(model.application.directory, 'commands', 'pacman-in-root')
    command = ['pkexec', program, model.project.custom_root_directory, '--sync', '--noconfirm', '--needed'] + package_names
    result, exit_status, signal_status = execute_synchronous(command, model.project.custom_root_directory)

    # Refresh the installed package list.
    model.package_details_list = create_package_details_list(model.project.custom_root_directory)
    displayer.update_list_store('packages_page__list_store', model.package_details_list)

    if exit_status == OK:
        message = f'Installed {package_list}.'
        displayer.update_label('packages_page__install_message_label', message, False)
    else:
        message = f'Error. Unable to install {package_list}.'
        displayer.update_label('packages_page__install_message_label', message, True)
        logger.log_value('Error. The result is', result)

    displayer.set_sensitive('packages_page__install_button', True)


def remove_selected_packages():

    logger.log_label('Remove selected packages with pacman')

    list_store_name = 'packages_page__list_store'
    logger.log_value('Get user selections from', list_store_name)
    list_store = model.builder.get_object(list_store_name)
    removable_packages_list = []
    item = list_store.get_iter_first()
    while item is not None:

        # 0: is standard selected?
        # 1: is minimal selected?
        # 2: is minimal selected initial?
        # 3: is minimal active?
        # 4: package name
        # 5: package version

        flag = list_store.get_value(item, 0)
        package_name = list_store.get_value(item, 4)
        if flag:
            removable_packages_list.append(package_name)
        item = list_store.iter_next(item)

    if not removable_packages_list:
        logger.log_value('Remove packages?', 'No packages selected.')
        return False  # (No Error)

    package_list = ' '.join(removable_packages_list)
    logger.log_value('Packages to remove', package_list)

    program = os.path.join(model.application.directory, 'commands', 'pacman-in-root')
    command = ['pkexec', program, model.project.custom_root_directory, '--remove', '--recursive', '--nosave', '--noconfirm'] + removable_packages_list
    result, exit_status, signal_status = execute_synchronous(command, model.project.custom_root_directory)

    if exit_status == OK:
        logger.log_value('Removed packages', package_list)
        return False  # (No Error)
    else:
        logger.log_value('Error. Unable to remove', package_list)
        logger.log_value('Error. The result is', result)
        return True  # (Error)


def create_standard_removable_packages_list():

    # logger.log_label('Create standard removable packages list')

    list_store_name = 'packages_page__list_store'
    logger.log_value('Get user selections from', list_store_name)
    list_store = model.builder.get_object(list_store_name)
    removable_packages_list = []
    item = list_store.get_iter_first()
    while item is not None:

        # 0: is standard selected?
        # 1: is minimal selected?
        # 2: is minimal selected initial?
        # 3: is minimal active?
        # 4: package name
        # 5: package version

        flag = list_store.get_value(item, 0)
        package_name = list_store.get_value(item, 4)
        if flag:
            removable_packages_list.append(package_name)
        item = list_store.iter_next(item)

    number_of_packages_total = len(model.package_details_list)
    number_of_packages_to_remove = len(removable_packages_list)
    number_of_packages_to_retain = number_of_packages_total - number_of_packages_to_remove
    logger.log_value('Total number of installed packages', number_of_packages_total)
    logger.log_value('New number of packages to be removed for a standard install', number_of_packages_to_remove)
    logger.log_value('New number of packages to be retained for a standard install', number_of_packages_to_retain)

    # Save the standard install filesystem.manifest-remove file. If there
    # are no packages to remove, an empty file will be created.
    if model.layout.standard_remove_file_name:
        file_path = os.path.join(model.project.custom_disk_directory, \
                                 model.layout.squashfs_directory, \
                                 model.layout.standard_remove_file_name)

        file_utilities.write_lines(removable_packages_list, file_path, raise_exception=False)


def create_minimal_removable_packages_list():

    # logger.log_label('Create minimal removable packages list')

    list_store_name = 'packages_page__list_store'
    logger.log_value('Get user selections from', list_store_name)
    list_store = model.builder.get_object(list_store_name)
    removable_packages_list = []
    item = list_store.get_iter_first()
    while item is not None:

        # 0: is standard selected?
        # 1: is minimal selected?
        # 2: is minimal selected initial?
        # 3: is minimal active?
        # 4: package name
        # 5: package version

        # Include packages that are selected for removal for a minimal
        # install and are not selected for removal for a standard
        # install.
        # flag = list_store.get_value(item, 1) and list_store.get_value(item, 3)

        # Include packages that are selected for removal for a minimal
        # install, even if they are selected for removal for a standard
        # install.
        flag = list_store.get_value(item, 1)
        package_name = list_store.get_value(item, 4)
        if flag:
            removable_packages_list.append(package_name)
        item = list_store.iter_next(item)

    number_of_packages_total = len(model.package_details_list)
    number_of_packages_to_remove = len(removable_packages_list)
    number_of_packages_to_retain = number_of_packages_total - number_of_packages_to_remove
    logger.log_value('Total number of installed packages', number_of_packages_total)
    logger.log_value('New number of packages to be removed for a minimal install', number_of_packages_to_remove)
    logger.log_value('New number of packages to be retained for a minimal install', number_of_packages_to_retain)

    # Save the minimal install filesystem.manifest-minimal-remove
    # file, even if there are no packages to remove. If the file
    # does not exist an empty file will be created.
    if model.layout.minimal_remove_file_name:
        file_path = os.path.join(model.project.custom_disk_directory, \
                                 model.layout.squashfs_directory, \
                                 model.layout.minimal_remove_file_name)
        file_utilities.write_lines(removable_packages_list, file_path, raise_exception=False)
