import os
import logging
from datetime import datetime
from threading import Thread, Lock

import aprslib

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

# AX.25 destination - APZ = Experimental, MNT = Monty
DEST="APZMNT"
MESSAGE_TX_TIMEOUT="5"  # minutes
MESSAGE_RETRY_TIME="1"  # minute

class APRSReceiver(Thread):
    
    def __init__(self, ais, messages, locks):
        super().__init__()
        self.ais = ais
        self.messages = messages
        self.locks = locks
        self.quit = False

    def run(self):
        # consumer runs until StopIteration in self.process_message, thread
        # exits when this returns
        self.ais.consumer(self.process_message)
    
    def end(self):
        self.quit = True

    def process_message(self, sentence):
        with self.locks['QUIT']:
            if self.quit:
                raise StopIteration

        print(sentence)
        # check if this is a message ack
        # {'raw': 'KG5YOV>APY100,WIDE1-1,WIDE2-1,qAR,WA5LNL::KG5YOV-15:ack1', 'from': 'KG5YOV', 'to': 'APY100', 
        #  'path': ['WIDE1-1', 'WIDE2-1', 'qAR', 'WA5LNL'], 'via': 'WA5LNL', 'addresse': 'KG5YOV-15', 
        #  'format': 'message', 'response': 'ack', 'msgNo': '1'}
        if 'addresse' in sentence and sentence['addresse'] == self.ais.callsign:
            with self.locks['MESSAGE']:
                # check if this is an ack to a message we sent
                for packet in self.messages:
                    if packet['to'] == sentence['from'] and sentence['response'] == 'ack' and packet['id'] == int(sentence['msgNo']):
                        # send the ack message to the slack channel
                        packet['slack_client'].rtm_send_message(packet['channel'], "Message ID {} to {} was acknowledged!".format(packet['id'], packet['to']))
                        # remove the ack'd packet from the list
                        self.messages.remove(packet)
                        return

            # did somone sent us a message?
            # {'raw': 'KG5YOV>APY100,WIDE1-1,WIDE2-1,qAR,WA5LNL::KG5YOV-15:ack1', 'from': 'KG5YOV', 'to': 'APY100',
            #  'path': ['WIDE1-1', 'WIDE2-1', 'qAR', 'WA5LNL'], 'via': 'WA5LNL', 'addresse': 'KG5YOV-15', 
            #  'format': 'message', 'response': 'ack', 'msgNo': '1'}
            if 'message_text' in sentence:
                # we got a message, send an ack
                print("Acknowledging message ID {} from {}.".format(sentence['msgNo'], sentence['from']))
                packet = "{}>{},TCPIP::{:<9}:ack{}".format(self.ais.callsign, DEST, sentence['from'], sentence['msgNo'])
                print(packet)
                self.ais.sendall(packet)

class CommandMessage(Command):
    """
    AA5RObot command to send an APRS message.
    """
    def __init__(self):
        self.command = "message"
        self.syntax = "message <callsign> <message>"
        self.help = "Send an APRS message to the callsign."

        # Get APRS config, don't load module if data isn't available
        APRS_CALLSIGN = os.environ.get('APRS_CALLSIGN')
        APRS_PASSWORD = os.environ.get('APRS_PASSWORD')
        if not APRS_CALLSIGN:
            logger.warning('APRS message sending not enabled.  APRS_CALLSIGN must be set in environment.')
            raise RuntimeError('APRS_CALLSIGN must be set in environment.')
        if not APRS_PASSWORD:
            logger.warning('APRS message sending not enabled.  APRS_PASSWORD must be set in environment.')
            raise RuntimeError('APRS_PASSWORD must be set in environment.')
        self.APRS_CALLSIGN = APRS_CALLSIGN

        # connect to APRS-IS, log in, and set a filter for 50-mile radius from San Antonio
        self.ais = aprslib.IS(self.APRS_CALLSIGN, passwd=APRS_PASSWORD, port=14580)
        self.ais.connect(blocking=True)
        self.ais.set_filter("r/29.42/-98.50/50")

        # set up locks
        self.locks = {
            'QUIT': Lock(),
            'MESSAGE': Lock(),
            'APRS_SEND': Lock()
        }

        # list to store messages
        self.messages = []

        # create thread to receive APRS messages
        self.aprs_receiver = APRSReceiver(self.ais, self.messages, self.locks)
        self.aprs_receiver.start()

        # instance variable to track message IDs
        self.message_id = 1

    def shutdown(self):
        # end message receiver thread, thread has to receive a message from
        # APRS-IS for the thread to end and join() to return
        logger.info('Waiting for APRS-IS receiver thread to end.')
        with self.locks['QUIT']:
            self.aprs_receiver.end()
        self.aprs_receiver.join()
        
        logger.info('Shutting down APRS-IS connection.')
        self.ais.close()

    def do_command(self, data, slack_client, channel, *args):
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

        # create APRS-IS message
        packet = {}
        packet['created'] = datetime.utcnow()
        packet['raw'] = "{}>{},TCPIP::{:<9}:{}{{{}".format(self.APRS_CALLSIGN, DEST, ssid, message, self.message_id)
        packet['id'] = self.message_id
        packet['to'] = ssid
        packet['slack_client'] = slack_client
        packet['channel'] = channel
        with self.locks['MESSAGE']:
            self.messages.append(packet)
        
        # send packet to APRS-IS
        with self.locks['APRS_SEND']:
            logger.info("Sending APRS packet: {}".format(packet['raw']))
            self.ais.sendall(packet['raw'])
        self.message_id += 1

        return (MessageTypes.RTM_MESSAGE, "Message ID {} sent to {}".format(packet['id'], ssid))
