import logging

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandDStarLh(Command):
    """
    AA5RObot command to create a link to DStar DPlus reflector's last heard.
    """
    def __init__(self):
        self.command = "dstar_lh"
        self.syntax = "dstar_lh"
        self.help = "Get a link to DStar DPlus lastheard page"

    def do_command(self, data):
        return (MessageTypes.RTM_MESSAGE, "Here's a link to the DStar DPlus last heard page: http://www.dstarusers.org/lastheard.php")
