import logging

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandDStarRefs(Command):
    """
    AA5RObot command to create a link to DStar DPlus reflectors.
    """
    def __init__(self):
        self.command = "dstar_refs"
        self.syntax = None
        self.help = "Get a link to DStar DPlus reflectors."

    def do_command(self, data):
        return (MessageTypes.RTM_MESSAGE, "Here's the DStar DPlus reflector page http://www.dstarinfo.com/reflectors.aspx")
