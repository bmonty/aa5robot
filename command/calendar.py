import logging

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandCalendar(Command):
    """
    AA5RObot command to create a link to the AARO calender.
    """
    def __init__(self):
        self.command = "calendar"
        self.syntax = "calendar"
        self.help = "Get a link to the club's calender."

    def do_command(self, data):
        return (MessageTypes.RTM_MESSAGE, "The club's calendar is at https://www.aa5ro.org/events")
