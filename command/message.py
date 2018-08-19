import os
import logging

import aprslib

from .command import Command

logger = logging.getLogger(__name__)

class CommandMessage(Command):
    """
    AA5RObot command to send an APRS message.
    """
    def __init__(self):
        self.command = "message"
        self.syntax = "message <callsign>"
        self.help = "Send an APRS message to the callsign."

        # check if APRS is configured
        APRS_CALLSIGN = os.environ.get('APRS_CALLSIGN')
        APRS_PASSWORD = os.environ.get('APRS_PASSWORD')
        if not APRS_CALLSIGN:
            logger.warning('APRS message sending not enabled.  APRS_CALLSIGN must be set in environment.')
            raise RuntimeError('APRS_CALLSIGN must be set in environment.')
        if not APRS_PASSWORD:
            logger.warning('APRS message sending not enabled.  APRS_PASSWORD must be set in environment.')
            raise RuntimeError('APRS_PASSWORD must be set in environment.')
        
        self.APRS_CALLSIGN = APRS_CALLSIGN
        self.APRS_PASSWORD = APRS_PASSWORD

        # configure aprslib
        self.ais = aprslib.IS(self.APRS_CALLSIGN, passwd=self.APRS_PASSWORD, port=14580)
        self.ais.connect()

        # instance variable to track message IDs
        self.message_id = 1


    def __del__(self):
        self.ais.close()

    def do_command(self, input):
        """
            Sends an APRS message to the given callsign.
        """
        inputs = input.split()

        # check for callsign
        try:
            callsign = inputs[0].upper()
        except IndexError:
            return (Command.RTM_MESSAGE, "You need to give me a callsign.")
        
        # check for message
        message = ' '.join(inputs[1:])
        if message == '':
            return (Command.RTM_MESSAGE, "You need to give me a message to send.")

        # check that message length is less than 67 characters (APRS max message length)
        if len(message) > 67:
            return (Command.RTM_MESSAGE, "Sorry that message is too long to send via APRS.")

        # create APRS-IS packet
        aprs_packet = "{}>{},TCPIP::{:<9}:{}{{{}".format(self.APRS_CALLSIGN, self.APRS_CALLSIGN, callsign, message, self.message_id)
        
        # send packet to APRS-IS
        logger.info("Sending APRS packet: {}".format(aprs_packet))
        self.ais.sendall(aprs_packet)
        self.message_id += 1

        return (Command.RTM_MESSAGE, "Sent!")
