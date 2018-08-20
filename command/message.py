import os
import logging

import aprslib

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandMessage(Command):
    """
    AA5RObot command to send an APRS message.
    """
    def __init__(self):
        self.command = "message"
        self.syntax = "message <callsign> <message>"
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

    def shutdown(self):
        logger.info('Shutting down APRS-IS connection.')
        self.ais.close()

    def do_command(self, data):
        """
            Sends an APRS message to the given callsign.
        """
        split_data = data.split()
        try:
            split_data = data.split()
            ssid = split_data[1].upper()
        except IndexError:
            return (MessageTypes.RTM_MESSAGE, "Sorry, I need an SSID to send a message.\nType this command as '{}'.".format(self.syntax))
        
        try:
            message = ' '.join(split_data[2:])
        except IndexError:
            return (MessageTypes.RTM_MESSAGE, "Sorry, I need a message to send to {}.\nType this command as '{}'.".format(ssid, self.syntax))
        
        if message == '':
            return (MessageTypes.RTM_MESSAGE, "Sorry, I need a message to send to {}.\nType this command as '{}'.".format(ssid, self.syntax))

        # check that message length is less than 67 characters (APRS max message length)
        if len(message) > 67:
            return (MessageTypes.RTM_MESSAGE, "Sorry that message is too long to send via APRS.")

        # create APRS-IS packet
        aprs_packet = "{}>{},TCPIP::{:<9}:{}{{{}".format(self.APRS_CALLSIGN, self.APRS_CALLSIGN, ssid, message, self.message_id)
        
        # send packet to APRS-IS
        logger.info("Sending APRS packet: {}".format(aprs_packet))
        self.ais.sendall(aprs_packet)
        self.message_id += 1

        return (MessageTypes.RTM_MESSAGE, "Sent!")
