import logging

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandQrz(Command):
    """
    AA5RObot command to create a link to a callsign's QRZ.com page.
    """
    def __init__(self):
        self.command = "qrz"
        self.syntax = "qrz <callsign>"
        self.help = "Get a link to the callsign's QRZ.com page."

    def do_command(self, callsign):
        if callsign == '':
            return (MessageTypes.RTM_MESSAGE, "You need to give me a callsign!\nCommand looks like: {}".format(self.syntax))

        return (MessageTypes.RTM_MESSAGE, "https://www.qrz.com/lookup/{}".format(callsign.upper()))
