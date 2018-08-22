import logging

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandDMRTg(Command):
    """
    AA5RObot command to create a link to BM's talkgroup list.
    """
    def __init__(self):
        self.command = "dmr_tg"
        self.syntax = None
        self.help = "Get a link to the BM's DMR talkgroup list"

    def do_command(self, data):
        return (MessageTypes.RTM_MESSAGE, "Here's a link to the BM's DMR talkgroup page: https://brandmeister.network/?page=talkgroups")
