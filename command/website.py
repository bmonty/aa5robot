import logging

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandWebsite(Command):
    """
    AA5RObot command to create a link to the AARO website.
    """
    def __init__(self):
        self.command = "website"
        self.syntax = "website"
        self.help = "Get a link to the club's website."

    def do_command(self, data, *args):
        return (MessageTypes.RTM_MESSAGE, "The club website is at https://www.aa5ro.org/")
