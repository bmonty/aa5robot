import os
import logging

import requests

from . import MessageTypes
from .command import Command

logger = logging.getLogger(__name__)

class CommandLocation(Command):
    """
    AA5RObot command to get an SSID's last reported location.
    """
    def __init__(self):
        self.command = "location"
        self.syntax = "location <SSID>"
        self.help = "Get APRS info on an SSID's last reported location."

        # get aprs.fi api token from environment variable
        aprs_fi_token = os.environ.get('APRS_FI_TOKEN')
        if aprs_fi_token == '':
            logger.warning('APRS location info not enabled.  APRS_FI_TOKEN must be set in environment.')
            raise RuntimeError('APRS_FI_TOKEN is not set.')
        else:
            self.aprs_fi_token = aprs_fi_token

        # this user agent string is used to comply with aprs.fi usage rules
        self.user_agent = "aa5robot/1.0 (+https://github.com/bmonty/aa5robot)"

    def do_command(self, ssid):
        if ssid == '':
            return (MessageTypes.RTM_MESSAGE, "You need to give me an SSID.")

        logger.info('Making request to aprs.fi for latest location of {}.'.format(ssid))
        request = requests.get('https://api.aprs.fi/api/get?name={}&what=loc&apikey={}&format=json'.format(ssid.upper(), self.aprs_fi_token), headers={'user-agent': self.user_agent})

        if request.ok:
            try:
                result = request.json()
            except ValueError:
                logger.info('Error getting data from aprs.fi.')
                return (MessageTypes.RTM_MESSAGE, "Error getting data from aprs.fi.")

            try:
                if result["result"] != "ok":
                    logger.info('Error getting data from aprs.fi.')
                    return (MessageTypes.RTM_MESSAGE, "Error getting data from aprs.fi.")
            except KeyError:
                logger.info('Error getting data from aprs.fi.')
                return (MessageTypes.RTM_MESSAGE, "Error parsing data from aprs.fi.")

            if result["found"] == 0:
                logger.info("There is no location info for {}.".format(ssid))
                return (MessageTypes.RTM_MESSAGE, "There is no location info for that SSID.")

            try:
                data = result["entries"][0]
                location = "{},{}".format(data["lat"], data["lng"])
                response = [
                    {
                        "text": "*{} APRS Location Info*".format(ssid.upper())
                    },
                    {
                        "fallback": "Map of {}'s location.".format(ssid.upper()),
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

                logger.info('Successfully retrieved latest location of {}'.format(ssid))
                return (MessageTypes.API_CALL, response)
            except KeyError:
                logger.info('Error parsing data from aprs.fi.')
                return (MessageTypes.RTM_MESSAGE, "Error parsing data from aprs.fi.")
