#!/usr/bin/python3

########################################################################
#                                                                      #
# terminal_page.py                                                     #
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

# https://lazka.github.io/pgi-docs/#Vte-2.90/classes/Terminal.html
# https://lazka.github.io/pgi-docs/#Vte-2.91/classes/Terminal.html
# https://lazka.github.io/pgi-docs/Gtk-3.0/structs/TargetEntry.html#methods
# https://lazka.github.io/pgi-docs/Gtk-3.0/flags.html#Gtk.TargetFlags

########################################################################
# Imports
########################################################################

import gi

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gdk
# from gi.repository import Gio
from gi.repository import Gtk

import os
import re
import time

from cubic.choosers import copy_file_chooser
from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import CONTROL_SHIFT_KEYS_1, CONTROL_SHIFT_KEYS_2
from cubic.constants import LOCK_FILE_NAME
from cubic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from cubic.constants import SLEEP_0250_MS
from cubic.constants import STAR
from cubic.navigator import handle_navigation
from cubic.utilities import console
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import file_utilities
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.displayer import MONOSPACE_FONT

########################################################################
# Global Variables & Constants
########################################################################

name = 'terminal_page'

# Indicates if the virtual environment is running.
is_running = False

########################################################################
# Initialize
########################################################################

terminal = model.builder.get_object('terminal_page__terminal')

# Set Terminal Font
terminal.set_font(MONOSPACE_FONT)
'''
# Set Terminal Colors
# TODO: Create and use displayer.get_terminal_colors() function.
schema_source = Gio.SettingsSchemaSource.get_default()
_, schemas = schema_source.list_schemas(True)
if 'org.gnome.Terminal.Legacy.Profile' in schemas:

    logger.log_value('Set terminal colors?', 'Yes, using GNOME Terminal')
    settings = Gio.Settings.new_with_path('org.gnome.Terminal.Legacy.Profile', '/org/gnome/terminal/legacy/')

    # Foreground color
    # Get value and unpack GLib.Variant type.
    # fg_color_hex = settings.get_value('foreground-color').unpack()
    # fg_color_rgb = Gdk.RGBA()
    # fg_color_rgb.parse(fg_color_hex)

    # Background color
    # Get value and unpack GLib.Variant type.
    # bg_color_hex = settings.get_value('background-color').unpack()
    # bg_color_rgb = Gdk.RGBA()
    # bg_color_rgb.parse(bg_color_hex)

    # Pallet
    # Get value and unpack GLib.Variant type.
    palette_hex = settings.get_value('palette').unpack()
    palette_rgb = []
    for color_hex in palette_hex:
        color_rgb = Gdk.RGBA()
        color_rgb.parse(color_hex)
        palette_rgb.append(color_rgb)

    # Set terminal colors
    # If foreground is None and palette_size is greater than 0, the new
    # foreground color is taken from palette[7].
    # If background is None and palette_size is greater than 0, the new
    # background color is taken from palette[0].
    terminal.set_colors(None, None, palette_rgb)

elif 'org.gnome.Ptyxis.Profile' in schemas:

    # Ptyxis does not have a key for foreground color.
    # Ptyxis does not have a key for background color.
    # The value for the palette key in Ptyxis is the name of a color
    # theme, and it is not a list of hex color codes.

    logger.log_value('Set terminal colors?', 'Yes, using Ptyxis Terminal')
    # settings = Gio.Settings.new_with_path('org.gnome.Ptyxis.Profile', '/org/gnome/Ptyxis/')

    # Foreground color
    # Get value and unpack GLib.Variant type.
    # fg_color_hex = settings.get_value('foreground-color').unpack()
    # fg_color_rgb = Gdk.RGBA()
    # fg_color_rgb.parse(fg_color_hex)

    # Background color
    # Get value and unpack GLib.Variant type.
    # bg_color_hex = settings.get_value('background-color').unpack()
    # bg_color_rgb = Gdk.RGBA()
    # bg_color_rgb.parse(bg_color_hex)

    # Get value and unpack GLib.Variant type.
    # palette_hex = settings.get_value('palette').unpack()
    # palette_rgb = []
    # for color_hex in palette_hex:
    #     color_rgb = Gdk.RGBA()
    #     color_rgb.parse(color_hex)
    #     palette_rgb.append(color_rgb)

    # Solarized Palette
    # Replaced '#073642' with '#102142' to address background issue in
    # Ubuntu 25.10.
    palette_hex = [
        '#102142',
        '#DC322F',
        '#859900',
        '#B58900',
        '#268BD2',
        '#D33682',
        '#2AA198',
        '#EEE8D5',
        '#002B36',
        '#CB4B16',
        '#586E75',
        '#657B83',
        '#839496',
        '#6C71C4',
        '#93A1A1',
        '#FDF6E3'
    ]
    palette_rgb = []
    for color_hex in palette_hex:
        color_rgb = Gdk.RGBA()
        color_rgb.parse(color_hex)
        palette_rgb.append(color_rgb)

    # Set terminal colors
    # If foreground is None and palette_size is greater than 0, the new
    # foreground color is taken from palette[7].
    # If background is None and palette_size is greater than 0, the new
    # background color is taken from palette[0].
    terminal.set_colors(None, None, palette_rgb)

else:

    logger.log_value('Set terminal colors?', 'Skip')
'''

# Set Terminal Colors
logger.log_value('Set terminal colors', 'Solarized')

# Explicitly use the Solarized palette.
# Replace #073642 with #102142 to address background color issue in
# Ubuntu 25.10.
palette_hex = [
    '#102142',
    '#DC322F',
    '#859900',
    '#B58900',
    '#268BD2',
    '#D33682',
    '#2AA198',
    '#EEE8D5',
    '#002B36',
    '#CB4B16',
    '#586E75',
    '#657B83',
    '#839496',
    '#6C71C4',
    '#93A1A1',
    '#FDF6E3'
]
palette_rgb = []
for color_hex in palette_hex:
    color_rgb = Gdk.RGBA()
    color_rgb.parse(color_hex)
    palette_rgb.append(color_rgb)

# Set terminal colors
# If foreground is None and palette_size is greater than 0, the new
# foreground color is taken from palette[7].
# If background is None and palette_size is greater than 0, the new
# background color is taken from palette[0].
terminal.set_colors(None, None, palette_rgb)

# Allow Drag and Drop in the Terminal

flags = Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP

# https://lazka.github.io/pgi-docs/Gtk-3.0/flags.html#Gtk.TargetFlags
# 1 = SAME_APP
# 2 = SAME_WIDGET
# 3 = OTHER_APP
# 4 = OTHER_WIDGET
targets = [Gtk.TargetEntry.new('text/uri-list', Gtk.TargetFlags.OTHER_APP, 80), Gtk.TargetEntry.new('text/plain', Gtk.TargetFlags.OTHER_APP, 80)]

actions = Gdk.DragAction.COPY

terminal.drag_dest_set(flags, targets, actions)

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

        # The virtual environment will be started in enter().

        # Determine if the Snaps page or the Project page should be
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

        if has_snaps_1 or has_snaps_2:
            # Show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'Yes')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=False,
                is_next_visible=True)

        else:
            # Do not show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'No')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back-project',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=False,
                is_next_visible=True)

        displayer.set_visible('terminal_page__copy_header_bar_button', True)
        displayer.set_sensitive('terminal_page__copy_header_bar_button', False)

        return

    if action == 'cancel':

        # Do not assume the virtual environment is running.

        # Determine if the Snaps page or the Project page should be
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

        if has_snaps_1 or has_snaps_2:
            # Show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'Yes')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=is_running,
                is_next_visible=True)

        else:
            # Do not show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'No')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back-project',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=is_running,
                is_next_visible=True)

        displayer.set_visible('terminal_page__copy_header_bar_button', True)
        displayer.set_sensitive('terminal_page__copy_header_bar_button', is_running)

        return

    if action == 'copy-terminal':

        # Do not assume the virtual environment is running.

        # Determine if the Snaps page or the Project page should be
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

        if has_snaps_1 or has_snaps_2:
            # Show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'Yes')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=is_running,
                is_next_visible=True)

        else:
            # Do not show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'No')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back-project',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=is_running,
                is_next_visible=True)

        displayer.set_visible('terminal_page__copy_header_bar_button', True)
        displayer.set_sensitive('terminal_page__copy_header_bar_button', is_running)

        return

    elif action == 'back-terminal':

        # The virtual environment will be started in enter().

        # Determine if the Snaps page or the Project page should be
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

        if has_snaps_1 or has_snaps_2:
            # Show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'Yes')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=False,
                is_next_visible=True)

        else:
            # Do not show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'No')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back-project',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=False,
                is_next_visible=True)

        displayer.set_visible('terminal_page__copy_header_bar_button', True)
        displayer.set_sensitive('terminal_page__copy_header_bar_button', False)

        return

    elif action == 'next':

        # The virtual environment will be started in enter().

        # Determine if the Snaps page or the Project page should be
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

        if has_snaps_1 or has_snaps_2:
            # Show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'Yes')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=False,
                is_next_visible=True)

        else:
            # Do not show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'No')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back-project',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=False,
                is_next_visible=True)

        displayer.set_visible('terminal_page__copy_header_bar_button', True)
        displayer.set_sensitive('terminal_page__copy_header_bar_button', False)

        return

    elif action == 'next-terminal':

        # The virtual environment will be started in enter().

        # Determine if the Snaps page or the Project page should be
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

        if has_snaps_1 or has_snaps_2:
            # Show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'Yes')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=False,
                is_next_visible=True)

        else:
            # Do not show the Snaps page.
            # logger.log_value('Show the Snaps page?', 'No')
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back-project',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style=None,
                is_next_sensitive=False,
                is_next_visible=True)

        displayer.set_visible('terminal_page__copy_header_bar_button', True)
        displayer.set_sensitive('terminal_page__copy_header_bar_button', False)

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

        # Attempt to enter the virtual environment.
        console.enter_virtual_environment(update_status)

        return

    elif action == 'cancel':

        return

    elif action == 'copy-terminal':

        return

    elif action == 'back-terminal':

        # Attempt to enter the virtual environment.
        console.enter_virtual_environment(update_status)

        return

    elif action == 'next':

        # Update the release description.
        if model.options.update_os_release:
            update_release_descriptions()

        # Attempt to enter the virtual environment.
        console.enter_virtual_environment(update_status)

        return

    elif action == 'next-terminal':

        # Update the release description.
        if model.options.update_os_release:
            update_release_descriptions()

        # Attempt to enter the virtual environment.
        console.enter_virtual_environment(update_status)

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

        displayer.set_visible('terminal_page__copy_header_bar_button', False)

        # The terminal continues running whenever the application
        # navigates away from the Terminal page, so the pseudo terminal
        # process must be explicitly killed.
        console.exit_virtual_environment()

        # Delete the virtual environment lock file.
        lock_file_path = os.path.join(model.project.directory, LOCK_FILE_NAME)
        result, exit_status, signal_status = file_utilities.delete_path_as_root(lock_file_path)

        time.sleep(SLEEP_0250_MS)

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

    if action == 'back-project':

        # Do not show the Snaps page.

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('terminal_page__copy_header_bar_button', False)

        # The terminal continues running whenever the application
        # navigates away from the Terminal page, so the pseudo terminal
        # process must be explicitly killed.
        console.exit_virtual_environment()

        # Delete the virtual environment lock file.
        lock_file_path = os.path.join(model.project.directory, LOCK_FILE_NAME)
        result, exit_status, signal_status = file_utilities.delete_path_as_root(lock_file_path)

        time.sleep(SLEEP_0250_MS)

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

    elif action == 'copy-terminal':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('terminal_page__copy_header_bar_button', False)

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

        displayer.set_visible('terminal_page__copy_header_bar_button', False)

        # Update the release description.
        if model.options.update_os_release:
            update_release_descriptions()

        # The terminal continues running whenever the application
        # navigates away from the Terminal page, so the pseudo terminal
        # process must be explicitly killed.
        console.exit_virtual_environment()

        # Delete the virtual environment lock file.
        lock_file_path = os.path.join(model.project.directory, LOCK_FILE_NAME)
        result, exit_status, signal_status = file_utilities.delete_path_as_root(lock_file_path)

        time.sleep(SLEEP_0250_MS)

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

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('terminal_page__copy_header_bar_button', False)

        # The terminal continues running whenever the application
        # navigates away from the Terminal page, so the pseudo terminal
        # process must be explicitly killed.
        console.exit_virtual_environment()

        # Delete the virtual environment lock file.
        lock_file_path = os.path.join(model.project.directory, LOCK_FILE_NAME)
        result, exit_status, signal_status = file_utilities.delete_path_as_root(lock_file_path)

        # Save the model values.
        # model.project.configuration.save()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('terminal_page__copy_header_bar_button', False)

        # The terminal continues running whenever the application
        # navigates away from the Terminal page, so the pseudo terminal
        # process must be explicitly killed.
        console.exit_virtual_environment()

        # Delete the virtual environment lock file.
        lock_file_path = os.path.join(model.project.directory, LOCK_FILE_NAME)
        result, exit_status, signal_status = file_utilities.delete_path_as_root(lock_file_path)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return 'unknown'


########################################################################
# File Chooser Functions
########################################################################


def selected_uris(uris):

    # logger.log_value('The selected uris are', uris)

    model.selected_uris = uris

    model.current_directory = console.get_current_directory()
    logger.log_value('The current directory is', model.current_directory)

    # Go to the copy page.

    # The pseudo terminal process is not registered with the
    # processor module. As a result, the terminal's process
    # is not terminated by the interrupt_navigation_thread() function
    # of the navigator module. This allows the terminal to continue
    # running while the application navigates away from the terminal
    # page. The pseudo terminal process must be explicitly killed by
    # executing the exit_virtual_environment() function of the
    # console module.
    handle_navigation('copy-terminal')


########################################################################
# Handler Functions
########################################################################


def on_terminal_page__terminal_child_exited(*args):
    """
    This function is not used.
    """

    logger.log_label('On terminal page terminal child exited')
    logger.log_value('The arcuments are', args)
    for arg in args:
        logger.log_value('The argument is', arg)


def on_clicked__terminal_page__copy_header_bar_button(widget):

    logger.log_label('Clicked terminal page copy header bar button')

    copy_file_chooser.open(selected_uris)


def on_key_press_event__terminal_page(widget, event):

    # logger.log_value('Key press event', chr(event.keyval))

    # The event.type is Gdk.EventType.KEY_PRESS.
    if event.state == CONTROL_SHIFT_KEYS_1 or event.state == CONTROL_SHIFT_KEYS_2:

        # Copy (<Ctrl><Shift><C> or <Ctrl><Shift><c>)
        if event.keyval == 99 or event.keyval == 67:
            # logger.log_value('Copy key press event', f'<Ctrl><Shift><{event.keyval:c}>')
            terminal = model.builder.get_object('terminal_page__terminal')
            terminal_has_selection = terminal.get_has_selection()
            if terminal_has_selection:
                terminal.copy_clipboard()
                # terminal.unselect_all()
            # Return True to prevent the event from being propagated to
            # the Terminal.
            return True

        # Paste (<Ctrl><Shift><V> or <Ctrl><Shift><v>)
        if event.keyval == 86 or event.keyval == 118:
            # logger.log_value('Copy key press event', f'<Ctrl><Shift><{event.keyval:c}>')
            terminal = model.builder.get_object('terminal_page__terminal')
            terminal.paste_clipboard()
            # Return True to prevent the event from being propagated to
            # the Terminal.
            return True

        # Select All (<Ctrl><Shift><A> or <Ctrl><Shift><a>)
        if event.keyval == 65 or event.keyval == 97:
            # logger.log_value('Copy key press event', f'<Ctrl><Shift><{event.keyval:c}>')
            terminal = model.builder.get_object('terminal_page__terminal')
            terminal.select_all()
            # Return True to prevent the event from being propagated to
            # the Terminal.
            return True


def on_drag_data_received__terminal_page(widget, drag_context, x, y, data, info, drag_time):

    # Skip if terminal is not running.
    if not is_running: return

    logger.log_value('Drag data received for', 'terminal page')

    # Gtk.SelectionData
    # https://lazka.github.io/pgi-docs/#Gtk-3.0/classes/SelectionData.html

    # The data type is....................... text/uri-list
    # The data type is....................... text/plain
    atom = data.get_data_type()
    data_type = str(atom)
    logger.log_value('The data type is', data_type)

    text = data.get_text()

    if text is not None:
        console.send_text_to_terminal(text)
    else:
        model.selected_uris = data.get_uris()
        logger.log_value('The selected uris are', model.selected_uris)

        model.current_directory = console.get_current_directory()
        logger.log_value('The current directory is', model.current_directory)

        # Go to the copy page.

        # The pseudo terminal process is not registered with the
        # processor module. As a result, the terminal's process
        # is not terminated by the interrupt_navigation_thread() function
        # of the navigator module. This allows the terminal to continue
        # running while the application navigates away from the terminal
        # page. The pseudo terminal process must be explicitly killed by
        # executing the exit_virtual_environment() function of the
        # console module.
        handle_navigation('copy-terminal')


def on_button_press_event__terminal_page(widget, event):

    # The event.type is Gdk.EventType.BUTTON_PRESS.
    if event.button == 3:

        logger.log_value('Mouse button 3 pressed for', 'terminal page')

        terminal = model.builder.get_object('terminal_page__terminal')
        terminal_has_selection = terminal.get_has_selection()

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        # Menu Item 1: Select Text
        displayer.set_sensitive('terminal_page__select_all_menu_item', True)

        # Menu Item 2: Copy Test
        if (terminal_has_selection):
            displayer.set_sensitive('terminal_page__copy_text_menu_item', True)
        else:
            displayer.set_sensitive('terminal_page__copy_text_menu_item', False)

        # Menu Item 3: Paste Text
        clipboard_has_text = clipboard.wait_is_text_available()
        if (is_running and clipboard_has_text and not terminal_has_selection):
            displayer.set_sensitive('terminal_page__paste_text_menu_item', True)
        else:
            displayer.set_sensitive('terminal_page__paste_text_menu_item', False)

        # Menu Item 4: Paste Files
        clipboard_has_uris = clipboard.wait_is_uris_available()
        if (is_running and clipboard_has_uris and not terminal_has_selection):
            count = len(clipboard.wait_for_uris())
            label = 'Paste File' if count == 1 else f'Paste {count} Files'
            displayer.update_menu_item('terminal_page__paste_file_menu_item', label)
            displayer.set_sensitive('terminal_page__paste_file_menu_item', True)
        else:
            label = 'Paste File(s)'
            displayer.update_menu_item('terminal_page__paste_file_menu_item', label)
            displayer.set_sensitive('terminal_page__paste_file_menu_item', False)

        menu = model.builder.get_object('terminal_page__menu')
        menu.popup(None, None, None, None, event.button, event.time)


def on_button_release_event__terminal_page__copy_text_menu_item(*args):

    terminal = model.builder.get_object('terminal_page__terminal')
    terminal.copy_clipboard()
    # terminal.unselect_all()


def on_button_release_event__terminal_page__paste_file_menu_item(*args):

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    model.selected_uris = clipboard.wait_for_uris()

    model.current_directory = console.get_current_directory()
    logger.log_value('The current directory is', model.current_directory)

    # Go to the copy page.

    # The pseudo terminal process is not registered with the
    # processor module. As a result, the terminal's process
    # is not terminated by the interrupt_navigation_thread() function
    # of the navigator module. This allows the terminal to continue
    # running while the application navigates away from the terminal
    # page. The pseudo terminal process must be explicitly killed by
    # executing the exit_virtual_environment() function of the
    # console module.
    handle_navigation('copy-terminal')


def on_button_release_event__terminal_page__paste_text_menu_item(*args):

    terminal = model.builder.get_object('terminal_page__terminal')
    terminal.paste_clipboard()


def on_button_release_event__terminal_page__select_all_menu_item(*args):

    terminal = model.builder.get_object('terminal_page__terminal')
    terminal.select_all()


########################################################################
# Support Functions
########################################################################


def update_status(status):
    """
    A callback function supplied by the client in order to be notified
    whenever the virtual environment starts or exits. This function must
    take a boolean status as the only argument. The function
    terminal.watch_child(process_id) is not used because it only sends a
    child-exited signal when the pseudo terminal exits, but it does not
    notify when the virtual environment has started successfully.
    """

    # Save the status so it can be used by the navigation actions.
    global is_running
    is_running = status

    # Reset buttons based on status.
    displayer.reset_buttons(is_back_sensitive=True, is_next_sensitive=status)
    displayer.set_sensitive('terminal_page__copy_header_bar_button', status)

    # Display the status.
    if status:
        message = 'You are in the virtual environment.'
        displayer.update_status_image('terminal_page__status', OK)
        displayer.update_label('terminal_page__status_label', message, False)
        displayer.update_label('terminal_page__kernel_version_label', f'kernel {model.application.kernel_version}')
    else:
        message = 'You are not in the virtual environment.'
        displayer.update_status_image('terminal_page__status', ERROR)
        displayer.update_label('terminal_page__status_label', message, True)
        displayer.update_label('terminal_page__kernel_version_label', '')

    logger.log_value('Virtual environment status message', message)


def update_release_description(base_file_path, relative_file_path, search_text, replacement_text):
    """
    Update the release description in a specified file.

    Args:
        base_file_path (str): The base directory where the target file is located.
        relative_file_path (str): The relative path to the target file from the base directory.
        search_text (str): The text pattern to search for in the target file.
        replacement_text (str): The text to replace the found pattern with.
    """

    full_file_path = os.path.join(base_file_path, relative_file_path)
    real_file_path = os.path.realpath(full_file_path)

    # The target file path may be the same as the source file path, if
    # source file path is not a link.
    display_source_file_path = os.path.join(os.path.sep, relative_file_path)
    display_target_file_path = os.path.join(os.path.sep, os.path.relpath(real_file_path, base_file_path))

    logger.log_value('Update release description', display_source_file_path)

    # Check if the full file path is a symbolic link.
    if os.path.islink(full_file_path):
        logger.log_value(f'File {display_source_file_path} is a link to', display_target_file_path)

    # Ensure the full file path exists and is a regular file.
    if not os.path.isfile(full_file_path):
        logger.log_value('Unable to update release description', f'The file {display_target_file_path} does not exist')
        return

    # Check if the file contains the specified search text.
    if not file_utilities.find_in_file(search_text, full_file_path):
        logger.log_value('Unable to update release description', f'The file {display_target_file_path} does not contain {search_text}')
        return

    # Check if the replacement text has already been applied.
    if file_utilities.find_in_file(re.escape(replacement_text), full_file_path):
        # Display the existing release description.
        match = file_utilities.find_in_file(search_text, full_file_path)
        if match: logger.log_value('Already updated release description', match[0])
        return

    # Replace the specified search text with the replacement text.
    result, exit_status, signal_status = file_utilities.replace_text_in_file(real_file_path, search_text, replacement_text)
    if exit_status == OK:
        # Display the updated release description.
        match = file_utilities.find_in_file(search_text, full_file_path)
        if match: logger.log_value('The new release description is', match[0])
    else:
        logger.log_value('Unable to update release description', display_source_file_path)
        logger.log_value('The result is', result)
        logger.log_value('The exit status, signal status is', f'{exit_status}, {signal_status}')


def update_release_descriptions():
    """
    Update the release descriptions in the following files:
    • /etc/lsb-release
    • /etc/os-release
    • /usr/lib/os-release
    """

    logger.log_label('Update the release descriptions')

    description = f'{model.custom.iso_volume_id} (Cubic {model.project.modify_date})'

    relative_file_path = os.path.join('etc', 'lsb-release')
    search_text = r'DISTRIB_DESCRIPTION.*'
    replacement_text = rf'DISTRIB_DESCRIPTION="{description}"'
    update_release_description(model.project.custom_root_directory, relative_file_path, search_text, replacement_text)

    relative_file_path = os.path.join('etc', 'os-release')
    search_text = r'PRETTY_NAME.*'
    replacement_text = rf'PRETTY_NAME="{description}"'
    update_release_description(model.project.custom_root_directory, relative_file_path, search_text, replacement_text)

    relative_file_path = os.path.join('usr', 'lib', 'os-release')
    search_text = r'PRETTY_NAME.*'
    replacement_text = rf'PRETTY_NAME="{description}"'
    update_release_description(model.project.custom_root_directory, relative_file_path, search_text, replacement_text)
