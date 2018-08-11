import os
import time
import re
import json

import requests
from slackclient import SlackClient

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

RTM_READ_DELAY = 1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def handle_help():
    return """I know how to do the following:
call <callsign>\t\tGet info on a callsign.
qrz <callsign>\t\tGet a link to a callsign on QRZ.com.
help, ?\t\tShow this help information.
"""

def lookup_call(callsign):
    request = requests.get('https://callook.info/{}/json'.format(callsign))
    
    data = None
    if request.ok:
        result = json.loads(request.content)
        if result["status"] == "VALID":
            data = result
    
    return data

def parse_bot_commands(slack_events, aa5robot_id):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If a command is not found, then this function returns None, None.
    """
    for event in slack_events:
        try:
            if event["type"] == "message" and not "subtype" in event:
                user_id, message = parse_direct_mention(event["text"])
                if user_id == aa5robot_id:
                    return message, event["channel"]
        except KeyError:
            return None, None

    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None.
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes a bot command.
    """
    default_response = "Not sure what you mean."

    response = None
    if command.startswith('call'):
        callsign = command.split()[1]
        print('Running lookup for callsign {}...'.format(callsign.upper()))
        call_info = lookup_call(callsign)
        if call_info:
            try:
                response = """Here's what I found for callsign {}:
    Name: {}
    Address: {}, {}
    License Class: {}
    License Granted: {}
                """.format(
                        callsign.upper(), 
                        call_info["name"].title(),
                        call_info["address"]["line1"].title(),
                        call_info["address"]["line2"].title(),
                        call_info["current"]["operClass"].capitalize(),
                        call_info["otherInfo"]["grantDate"]
                    )
            except:
                reponse = 'Error processing info for call {}'.format(callsign)
        else:
            response = "Couldn't find info on call {}.".format(callsign)

    if command.startswith('qrz'):
        callsign = command.split()[1].upper()
        response = "https://www.qrz.com/lookup/{}".format(callsign)

    if command.startswith('help') or command.startswith('?'):
        response = handle_help()

    # send the response back to the channel
    slack_client.rtm_send_message(channel, response or default_response)
    print('Command processed.')

def aa5robot():
    if slack_client.rtm_connect(with_team_state=False):
        print("AA5ROBot connected and running.")
        aa5robot_id = slack_client.api_call("auth.test")["user_id"]

        while slack_client.server.connected is True:
            command, channel = parse_bot_commands(slack_client.rtm_read(), aa5robot_id)
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)

    else:
        print("Connection failed.")

if __name__ == '__main__':
    aa5robot()