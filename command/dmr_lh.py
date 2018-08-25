import logging

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandDMRLh(Command):
    """
    AA5RObot command to create a link to BM's lastheard.
    """
    def __init__(self):
        self.command = "dmr_lh"
        self.syntax = "dmr_lh"
        self.help = "Get a link to the DMR BM last heard page"

    def do_command(self, data):
        return (MessageTypes.RTM_MESSAGE, "Here's a link to the BM DMR last heard page: https://brandmeister.network/?page=lh")
