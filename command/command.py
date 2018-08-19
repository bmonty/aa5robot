import logging

logger = logging.getLogger(__name__)

class Command:
    def do_command(self):
        """
        Empty method that must be overriden for the command to do
        anything useful.
        """
        logger.warning('This command doesn\'t do anything!')
