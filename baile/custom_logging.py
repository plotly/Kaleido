import sys
import logging
import inspect

# new constants
DEBUG2 = 5

# Create the logging
basicConfig = logging.basicConfig
logging.addLevelName(DEBUG2, "DEBUG2")

# Set logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stderr)
logger.addHandler(handler)

# Overwrite functions
def debug2(message):
    function = inspect.stack()[0].function
    logger._log(DEBUG2, f"{function.capitalize()}: {message}", ()) # The () is for the empty args

def debug1(message):
    function = inspect.stack()[0].function
    logger.debug(f"{function.capitalize()}: {message}")

def info(message):
    function = inspect.stack()[0].function
    logger.info(f"{function.capitalize()}: {message}")

def error(message):
    function = inspect.stack()[0].function
    logger.error(f"{function.capitalize()}: {message}")

def warning(message):
    function = inspect.stack()[0].function
    logger.warning(f"{function.capitalize()}: {message}")

def critical(message):
    function = inspect.stack()[0].function
    logger.critical(f"{function.capitalize()}: {message}")
