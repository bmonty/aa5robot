import os
import sys
import time
import re
import logging
import json

from slackclient import SlackClient

import command

RTM_READ_DELAY = 1           # number of seconds to wait between reads of Slack RTM
MAX_RECONNECT_ATTEMPTS = 5   # number of attempts to reconnect to Slack before exiting
RECONNECT_WAIT_TIME = 5      # time to wait between reconnect attempts (seconds)

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

class AA5ROBot:
    """
    A Slack bot for the AARO Slack site.
    """
    def __init__(self):
        # Get the Bot token from the environment.  Raises RunTimeError if the
        # value isn't set because the bot can't run without a token configured.
        slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
        if slack_bot_token == '':
            raise RuntimeError('SLACK_BOT_TOKEN must be set in the environment.')

        # Create the main SlackClient instance for the bot
        self.slack_client = SlackClient(slack_bot_token)

        # start initial connection to Slack RTM
        if self.slack_client.rtm_connect(with_team_state=False):
            logger.info("AA5ROBot connected to Slack.")
            self.aa5robot_id = self.slack_client.api_call("auth.test")["user_id"]
        else:
            logger.warning("Connection to Slack RTM failed.")
            self.shutdown(1)

        # Load the bot's commands
        self.commands = command.get_commands()

        print('AA5RObot initialized.')

    def start(self):
        reconnects = 0

        # Process events from Slack RTM until ctrl-c
        logger.info('Processing events from Slack...')
        while self.slack_client.server.connected is True:
            try:
                data, channel, user, ts = self.parse_bot_commands(self.slack_client.rtm_read())
                if data:
                    self.handle_command(data, channel, user, ts)
                time.sleep(RTM_READ_DELAY)
            except KeyboardInterrupt:
                self.shutdown()

        # If execution gets here, the connection to the server was interrupted.
        # Attempt up to MAX_RECONNECT_ATTEMPTS tries to reconnect to Slack.
        while reconnects < MAX_RECONNECT_ATTEMPTS:
            print('AA5RObot lost connection to Slack.  Attempting reconnect, try {}'.format(reconnects + 1))
            if self.slack_client.rtm_connect(with_team_state=False):
                print("AA5ROBot reconnected to Slack.")
                self.aa5robot_id = slack_client.api_call("auth.test")["user_id"]
                self.start()
            else:
                reconnects += 1
                time.sleep(RECONNECT_WAIT_TIME)
        
        # Bot was unable to reconnect, so end the process.
        print('Unable to reconnect to Slack.  Exiting.')
        self.shutdown(1)

    def shutdown(self, exit_code = 0):
        """
        Execute cleanup tasks before exiting the process.
        """
        # call shutdown method on all command instances
        for instance in self.commands:
            instance[1].shutdown()
        
        # end the process
        print("AA5ROBot exiting.")
        sys.exit(exit_code)

    def parse_bot_commands(self, slack_events):
        """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If a command is not found, then this function returns None, None.
        """
        for event in slack_events:
            try:
                if event["type"] == "message" and not "subtype" in event:
                    user_id, message = self.parse_direct_mention(event["text"])
                    if user_id == self.aa5robot_id:
                        return message, event["channel"], event["user"], event["ts"]
            except KeyError:
                return None, None, None, None

        return None, None, None, None

    def parse_direct_mention(self, message_text):
        """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None.
        """
        matches = re.search("^<@(|[WU].+?)>(.*)", message_text)
        # the first group contains the username, the second group contains the remaining message
        return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

    def handle_command(self, data, channel, user, ts):
        """
            Executes a bot command.
        """
        logger.debug('channel: {}, data: {}, user: {}, ts: {}'.format(channel, data, user, ts))

        # get command string
        try:
            command_str = data.split()[0].lower()
        except IndexError:
            self.send_message(channel, "Not sure what you mean.  Tell me 'help' for more info.")
            return

        if command_str == '':
            self.send_message(channel, "Not sure what you mean.  Tell me 'help' for more info.")
            return

        if command_str == 'help' or command_str == '?':
            self.handle_help(channel, ts)
            return

        command_strings = [i[0] for i in self.commands]
        if command_str in command_strings:
            logger.info("Executing command '{}'.".format(command_str))
            method, response = self.commands[command_strings.index(command_str)][1].do_command(data)

            if method == command.MessageTypes.RTM_MESSAGE:
                self.send_message(channel, response)
            
            if method == command.MessageTypes.API_CALL:
                self.chat_post_message(channel, response)

        else:
            self.send_message(channel, "Not sure what you mean.  Tell me 'help' for more info.")
            return

    def handle_help(self, channel, ts):
        """
        Sends the bot's help message to Slack.
        """
        logger.info('Processing help command...')

        help_text = "I support the following commands:\n"
        for (command_str, command_obj) in self.commands:
            help_text += "`{}` - {}\n".format(command_obj.syntax, command_obj.help)
        
        self.slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            as_user=True,
            #thread_ts=ts,
            text=help_text
        )

    def send_message(self, channel, response):
        """
        Send a text-only response via the RTM API.
        """
        self.slack_client.rtm_send_message(channel, response)

    def chat_post_message(self, channel, response):
        """
        Send a chat.postMessage API call.
        """
        self.slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            as_user=True,
            attachments=json.dumps(response)
        )

def main():
    # create the AA5RObot instance
    aa5robot = AA5ROBot()
    # start processing commands
    aa5robot.start()

if __name__ == '__main__':
    main()