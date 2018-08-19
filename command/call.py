import os
import logging
import time
import json

import requests

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandCall(Command):
    """
    AA5RObot command to lookup information on a callsign and display the info
    in a Slack channel.
    """
    def __init__(self):
        self.command = "call"
        self.syntax = "call <callsign>"
        self.help = "Display information about a callsign."

        self.USER_AGENT = os.environ.get('USER_AGENT')

    def do_command(self, input):
        """
            Looks up info for the requested callsign.
        """
        if input == '':
            return (MessageTypes.RTM_MESSAGE, "You need to give me a callsign!\nCommand looks like: {}".format(self.syntax))
        
        callsign = input.upper()
        logger.info('Running lookup for callsign {}...'.format(callsign))

        call_info = self._lookup_call(callsign)
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

                # return response as a JSON string to send to Slack using API call
                return (MessageTypes.API_CALL, call_data)
            except IndexError:
                return (MessageTypes.RTM_MESSAGE, 'Error processing info for call {}'.format(callsign))
        else:
            return (MessageTypes.RTM_MESSAGE, "Couldn't find info on call {}.".format(callsign))

    def _lookup_call(self, callsign):
        """
        Request callsign info from callook.info.
        """
        # make request to callook.info
        if self.USER_AGENT:
            request = requests.get('https://callook.info/{}/json'.format(callsign), headers={'user-agent': USER_AGENT})
        else:
            request = requests.get('https://callook.info/{}/json'.format(callsign))
    
        # check returned data, return result if ok
        if request.ok:
            result = request.json()
            if result["status"] == "VALID":
                return result

        # return None if request was not successful
        return None
