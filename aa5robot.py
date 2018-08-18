import os
import sys
import time
import re
import json
import time
import urllib.parse

import requests
from slackclient import SlackClient
import aprslib
import logging

APRS_CALLSIGN = os.environ.get('APRS_CALLSIGN')
APRS_PASSWORD = os.environ.get('APRS_PASSWORD')
APRS_FI_TOKEN = os.environ.get('APRS_FI_TOKEN')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
if os.environ.get('DEBUG'):
    DEBUG = True
    logging.basicConfig(level=logging.DEBUG)
else:
    DEBUG = False

USER_AGENT = "aa5robot/1.0 (+https://github.com/bmonty/aa5robot)"
RTM_READ_DELAY = 1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

slack_client = SlackClient(SLACK_BOT_TOKEN)
ais = aprslib.IS(APRS_CALLSIGN, passwd=APRS_PASSWORD, port=14580)
message_id = 1

def handle_help():
    return (True, """I know how to do the following:
call <callsign>\t\tGet info on a callsign.
qrz <callsign>\t\tGet a link to a callsign on QRZ.com.
location <callsign>\t\tGet the last APRS location report for a callsign.  Callsign should be a SSID (i.e. KG5YOV-9)
website\t\t\t\tGet a link to the club's website.
help, ?\t\t\t\tShow this help information.
""")

def lookup_call(callsign):
    request = requests.get('https://callook.info/{}/json'.format(callsign), headers={'user-agent': USER_AGENT})
    
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

def command_message(input):
    """
        Sends an APRS message to the given callsign.
    """
    if not APRS_CALLSIGN or not APRS_PASSWORD:
        return (True, "Sorry, I can't send messages because APRS is not configured.")

    inputs = input.split()
    try:
        callsign = inputs[1].upper()
    except IndexError:
        return (True, "You need to give me a callsign.")
    
    try:
        message = inputs[2]
    except IndexError:
        return (True, "You need to give me a message to send.")

    callsign = inputs[1].upper()
    message = ' '.join(inputs[2:])
    if len(message) > 67:
        return (True, "Sorry that message is too long to send via APRS.")

    aprs_packet = "{}>{},TCPIP::{:<9}:{}{{1".format(APRS_CALLSIGN, APRS_CALLSIGN, callsign, message)
    print("Sending APRS packet: {}".format(aprs_packet))
    ais.sendall(aprs_packet)

    return (True, "sent!")

def command_location(input):
    """
        Looks up the latest reported location in aprs.fi for a callsign.
    """
    response = None

    try:
        callsign = input.split()[1].upper()
    except IndexError:
        return (True, "You need to give me a callsign!")

    request = requests.get('https://api.aprs.fi/api/get?name={}&what=loc&apikey={}&format=json'.format(callsign, APRS_FI_TOKEN), headers={'user-agent': USER_AGENT})

    if request.ok:
        try:
            result = request.json()
        except ValueError:
            return (True, "Error getting data from aprs.fi.")

        try:
            if result["result"] != "ok":
                return (True, "Error getting data from aprs.fi.")
        except KeyError:
            return (True, "Error parsing data from aprs.fi.")

        try:
            data = result["entries"][0]
            location = "{},{}".format(data["lat"], data["lng"])
            response = [
                {
                    "text": "*{} APRS Location Info*".format(callsign)
                },
                {
                    "fallback": "Map of {}'s location.".format(callsign),
                    "title": "Last Reported Location",
                    "image_url": "https://maps.googleapis.com/maps/api/staticmap?center={}&zoom=9&scale=1&size=600x300&maptype=roadmap&format=png&visual_refresh=true&markers=size:mid%7Ccolor:0xff0000%7Clabel:%7C{}".format(location, location)
                },
                {
                    "fields": [
                                    {
                                        "title": "Time of Report",
                                        "value": "<!date^{}^{{date_pretty}}|error> <!date^{}^{{time_secs}}|error>".format(data["lasttime"], data["lasttime"]),
                                        "short": True
                                    },
                                    {
                                        "title": "Comment",
                                        "value": "{}".format(data["comment"]),
                                        "short": False
                                    }
                            ]
                }
            ]
        except KeyError:
            return (True, "Error parsing data from aprs.fi.")
        
        return (False, json.dumps(response))

def command_call(input):
    """
        Looks up info for the requested callsign.
    """
    response = None
    
    try:
        callsign = input.split()[1].upper()
    except IndexError:
        return (True, "You need to give me a callsign!\nCommand looks like: call <callsign>")
    else:
        print('Running lookup for callsign {}...'.format(callsign))

        call_info = lookup_call(callsign)
        if call_info:
            try:
                # create location string
                location = "{},{}".format(call_info["location"]["latitude"], call_info["location"]["longitude"])
                
                # convert license grant date to seconds since unix epoch
                grant_struct_time = time.strptime(call_info["otherInfo"]["grantDate"], '%m/%d/%Y')
                epoch_grant_date = int(time.mktime(grant_struct_time))

                # Create the object with response data. This is a Slack "attachments" object.
                call_data = [
                    {
                        "text": "*{}*".format(callsign)
                    },
                    {
                        "fields": [
                                {
                                    "title": "Name",
                                    "value": call_info["name"].title(),
                                    "short": False
                                },
                                {
                                    "title": "License Class",
                                    "value": call_info["current"]["operClass"].capitalize(),
                                    "short": True
                                },
                                {
                                    "title": "License Granted",
                                    "value": "<!date^{}^{{date_pretty}}|{}>".format(epoch_grant_date, call_info["otherInfo"]["grantDate"]),
                                    "short": True
                                }
                        ]
                    },
                    {
                        "fallback": "Map of {}'s location.".format(callsign),
                        "title": "{}'s Location".format(callsign),
                        "image_url": "https://maps.googleapis.com/maps/api/staticmap?center={}&zoom=9&scale=1&size=600x300&maptype=roadmap&format=png&visual_refresh=true&markers=size:mid%7Ccolor:0xff0000%7Clabel:%7C{}".format(location, location)
                    }
                ]

                # turn response into a JSON string
                response = (False, json.dumps(call_data))
            except:
                reponse = (True, 'Error processing info for call {}'.format(callsign))
        else:
            response = (True, "Couldn't find info on call {}.".format(callsign))
        
        return response

def command_qrz(input):
    """
        Creates a QRZ.com link for the requested callsign.
    """
    try:
        callsign = input.split()[1].upper()
    except IndexError:
        return (True, "You need to give me a callsign!\nCommand looks like: qrz <callsign>")
    else:
        return (True, "https://www.qrz.com/lookup/{}".format(callsign))

def command_website():
    return True, "The club website is at https://www.aa5ro.org/"

def handle_command(input, channel, user):
    """
        Executes a bot command.
    """
    method = True
    response = None
    command = input.split()[0].lower()

    if command.startswith('call'):
        method, response = command_call(input)

    elif command.startswith('qrz'):
        method, response = command_qrz(input)

    elif command.startswith('website'):
        method, response = command_website()

    elif command.startswith('location'):
        method, response = command_location(input)

    elif command.startswith('message'):
        method, response = command_message(input)

    elif command.startswith('help') or command.startswith('?'):
        method, response = handle_help()

    else:
        response = "Not sure what you mean."

    # send the response back to the channel
    if method:
        # send a text-only response via the RTM API
        slack_client.rtm_send_message(channel, response)
    else:
        # send a JSON response via the Web API
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            as_user=True,
            attachments=response
        )

def aa5robot():
    if slack_client.rtm_connect(with_team_state=False):
        print("AA5ROBot connected and running.")
        aa5robot_id = slack_client.api_call("auth.test")["user_id"]

        # connect to APRS-IS
        ais.connect()

        while slack_client.server.connected is True:
            try:
                command, channel = parse_bot_commands(slack_client.rtm_read(), aa5robot_id)
                if command:
                    handle_command(command, channel, aa5robot_id)
                time.sleep(RTM_READ_DELAY)
            except KeyboardInterrupt:
                ais.close()
                print("AA5ROBot exiting.")
                sys.exit()

    else:
        print("Connection failed.")

if __name__ == '__main__':
    aa5robot()