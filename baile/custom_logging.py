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
    if logger.isEnabledFor(DEBUG2):
        logger._log(DEBUG2, message, ()) # The () is for the empty args

def debug1(message):
    function = inspect.stack()[0].function
    logger.debug(f"{function}: {message}")

def info(message):
    function = inspect.stack()[0].function
    logger.info(f"{function}: {message}")

def error(message):
    function = inspect.stack()[0].function
    logger.error(f"{function}: {message}")

def warning(message):
    function = inspect.stack()[0].function
    logger.warning(f"{function}: {message}")

def critical(message):
    function = inspect.stack()[0].function
    logger.critical(f"{function}: {message}")

logger.setLevel(DEBUG2) #Just to test it