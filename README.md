This is a simple Slack robot designed to provide info to AARO club members.

The script expects the following environment variables to be set:

**SLACK_BOT_TOKEN** - Bot User OAuth Access Token from Slack's API page.  This token is required.
**APRS_CALLSIGN** - The callsign to use when sending to APRS-IS
**APRS_PASSWORD** - APRS-IS password for the value in ```APRS_CALLSIGN```
**APRS_FI_TOKEN** - API token for accessing aprs.fi

The robot can be run in two ways:
1. Run the python script on the host.  You will need to install the package
dependencies before running the script.
2. Use the included Dockerfile to create an image and run the bot as a container.

To run the bot on the command line, it's recommended to create a virtualenv.
Once the virtualenv is setup and active, clone the repo.  Run the following to
start the bot:
```
> pip install -r ./requirements.txt
> python aa5robot.py
```

To run the bot as a docker container:
```
> docker build -t aa5robot:latest .
> docker run -d --name aa5robot -e SLACK_BOT_TOKEN='<token>' aa5robot:latest
```
