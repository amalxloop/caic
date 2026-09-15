#!/usr/bin/python3

########################################################################
#                                                                      #
# caic_wizard.py                                                      #
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

# N/A

########################################################################
# Imports
########################################################################

import argcomplete
import argparse
import gi
import glob
import importlib
import mimetypes
import os
import traceback

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from caic.constants import CUBIC_COPYRIGHT
from caic.constants import CUBIC_WEBSITE, CUBIC_URLS
from caic import navigator
from caic.utilities import constructor
from caic.utilities import logger
from caic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

# N/A

########################################################################
# Arguments
########################################################################

parser = argparse.ArgumentParser(
    prog='caic',
    description='CAIC (Custom Arch ISO Creator) is a GUI wizard to create a customized Live ISO image for Arch Linux and Arch-based distributions.')
parser.add_argument('directory', nargs='?', help='directory for a new or existing project')
parser.add_argument('iso', nargs='?', help='original ISO file for a new project (ignored for existing projects)')
parser.add_argument("-l", "--log", action="store_true", help="output a formatted log to a file in the project directory")
parser.add_argument("-v", "--verbose", action="store_true", help="output a formatted log to the console")
parser.add_argument("-V", "--version", action="store_true", help="print version information and exit")

if os.getuid() == 0:
    print('Error: CAIC may not be run using sudo or as root because it is a graphical user interface application.')
    print()
    parser.print_help()
    print()
    exit()

argcomplete.autocomplete(parser)
arguments = parser.parse_args()

if arguments.version:
    version = constructor.get_package_version('caic')
    display_version = constructor.get_display_version(version)
    urls = constructor.decode_object(CUBIC_URLS)
    website = urls[CUBIC_WEBSITE]
    print(f'CAIC version... {display_version}')
    print(f'Copyright....... {CUBIC_COPYRIGHT}')
    print(f'Website......... {website}')
    exit()

########################################################################
# Main Application
########################################################################

try:

    version = constructor.get_package_version('caic')
    display_version = constructor.get_display_version(version)
    urls = constructor.decode_object(CUBIC_URLS)
    website = urls[CUBIC_WEBSITE]

    # Set logger values from the command line arguments, if supplied.
    logger.verbose = arguments.verbose
    logger.log = arguments.log

    logger.log_title('CAIC - Custom Arch ISO Creator')

    logger.log_value('CAIC version', display_version)
    logger.log_value('Copyright', CUBIC_COPYRIGHT)
    logger.log_value('Website', website)

    # ------------------------------------------------------------------
    # Initialize.
    # ------------------------------------------------------------------

    logger.log_title('Initialize')

    # Real path is necessary here.
    model.application.directory = os.path.dirname(os.path.realpath(__file__))

    # Get the user's home directory.
    model.application.user_home = os.path.expanduser('~')

    # Get the running Cubic version.
    model.application.cubic_version = constructor.get_package_version('caic')
    ### TODO: FOR TESTING ONLY
    # model.application.cubic_version = '2026.08.108-release~202608201745~ubuntu26.04'

    # Get the running kernel version.
    model.application.kernel_version = constructor.get_kernel_version()

    # Set model values from the command line arguments, if supplied.
    if arguments.directory:
        model.arguments.directory = os.path.realpath(arguments.directory)
    if arguments.iso:
        model.arguments.file_path = os.path.realpath(arguments.iso)

    # Add additional mime types.
    mimetypes.init()
    file_path = os.path.join(model.application.directory, 'assets', 'mime.types')
    mimetypes.types_map.update(mimetypes.read_mime_types(file_path))

    # ------------------------------------------------------------------
    # Create the user interface.
    # ------------------------------------------------------------------

    # Load the user interface.
    file_path = os.path.join(model.application.directory, 'caic_wizard.ui')
    model.builder = Gtk.Builder.new_from_file(file_path)

    # Connect the signals to handlers in the associated module.
    model.builder.connect_signals(navigator)

    #
    # Pages
    #

    logger.log_label('Setup pages')

    # Get the stack.
    pages = model.builder.get_object('pages')

    # Setup each page.
    pattern = os.path.join(model.application.directory, 'caic', 'pages', '*_page.ui')
    file_paths = sorted(glob.glob(pattern))
    for file_path in file_paths:

        # Get the module name.
        module_name = os.path.basename(file_path)[:-3]
        logger.log_value('Setup', module_name.replace('_', ' '))

        # Load the user interface.
        model.builder.add_from_file(file_path)

        # Load the module.
        module = importlib.import_module(f'caic.pages.{module_name}')

        # Connect the signals to handlers in the associated module.
        model.builder.connect_signals(module)

        # Add the page to the stack.
        page = model.builder.get_object(module.name)
        pages.add_named(page, module.name)

    # Set the first page for the stack.
    page = model.builder.get_object('start_page')
    pages.set_visible_child(page)

    #
    # Header Bar
    #

    # Add previously loaded widgets to the header bar.

    # TODO: Can adding widgets to the header bar be moved to the individual pages?

    header_bar = model.builder.get_object('header_bar')

    # Project page
    widget = model.builder.get_object('project_page__test_header_bar_button')
    header_bar.add(widget)
    widget = model.builder.get_object('project_page__delete_header_bar_button')
    header_bar.add(widget)
    widget = model.builder.get_object('project_page__header_bar_box')
    header_bar.add(widget)

    # Packages page
    widget = model.builder.get_object('packages_page__header_bar_box_1')
    header_bar.add(widget)
    widget = model.builder.get_object('packages_page__header_bar_box_2')
    header_bar.add(widget)

    # Options page
    options_page__stack_switcher = model.builder.get_object('options_page__stack_switcher')
    options_page__stack = model.builder.get_object('options_page__stack')
    options_page__stack_switcher.set_stack(options_page__stack)

    # Terminal page
    widget = model.builder.get_object('terminal_page__copy_header_bar_button')
    header_bar.add(widget)

    # Finish page
    widget = model.builder.get_object('finish_page__test_header_bar_button')
    header_bar.add(widget)

    #
    # Menu
    #

    # The following may be prefixed with ★ on the Start page setup()
    # function.

    # Alert Label
    # Cubic Wiki
    # Cubic Page Help
    # Cubic Website
    # Cubic About
    # Cubic Donate

    #
    # File Choosers
    #

    logger.log_label('Setup file choosers')

    pattern = os.path.join(model.application.directory, 'caic', 'choosers', '*_chooser.ui')
    file_paths = sorted(glob.glob(pattern))
    for file_path in file_paths:

        # Get the module name.
        module_name = os.path.basename(file_path)[:-3]
        logger.log_value('Setup', module_name.replace('_', ' '))

        # Load the user interface.
        model.builder.add_from_file(file_path)

        # Load the module.
        module = importlib.import_module(f'caic.choosers.{module_name}')

        # Connect the signals to handlers in the associated module.
        model.builder.connect_signals(module)

    # ------------------------------------------------------------------
    # Start the user interface.
    # ------------------------------------------------------------------

    # Show the window.
    window = model.builder.get_object('window')
    window.show()

    # Open the application.
    navigator.handle_navigation('open')

    # Start the Gtk main loop.
    Gtk.main()

except Exception as exception:
    logger.log_value('Exception', exception)
    logger.log_value('The trace back is', traceback.format_exc())
