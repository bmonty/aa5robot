import sys
import os
import os.path
import importlib
import logging
from enum import Enum, auto

class MessageTypes(Enum):
    """
    Enum used to indicate the type of bot response.
    """
    RTM_MESSAGE = auto()
    API_CALL = auto()

# list of command modules to load
commands = [
    ('command.call', 'CommandCall'),
    ('command.location', 'CommandLocation'),
    ('command.message', 'CommandMessage'),
    ('command.qrz', 'CommandQrz'),
    ('command.website', 'CommandWebsite'),
]

# import command modules and create instances of command classes
command_instances = []
for module, klass in commands:
    try:
        m = importlib.import_module(module)
    except ImportError:
        logging.warning('Failed to import module {}'.format(module))
        continue

    try:
        command_instances.append(getattr(m, klass)())
    except RuntimeError:
        logging.warning('Failed to create instance of {}'.format(klass))
        continue

def get_commands():
    """
    Returns a list of the loaded commands.
    """
    commands = []
    for instance in command_instances:
        commands.append((instance.command, instance))
    return commands

def get_help_strings():
    """
    Returns a list of help strings for all loaded commands.
    """
    help_strings = []
    for instance in command_instances:
        help_strings.append((instance.command, instance.help, instance.syntax))
    return help_strings
