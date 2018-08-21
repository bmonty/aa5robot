import logging

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandWebsite(Command):
    """
    AA5RObot command to create a link to the AARO calender.
    """
    def __init__(self):
        self.command = "calendar"
        self.syntax = None
        self.help = "Get a link to the club's calender."

    def do_command(self, data):
        return (MessageTypes.RTM_MESSAGE, "The club website is at https://www.aa5ro.org/events")
