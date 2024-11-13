import sys
import logging
import inspect

# new constant
DEBUG2 = 5

# Create the logging
basicConfig = logging.basicConfig
logging.addLevelName(DEBUG2, "DEBUG2")

# Set logger
logger = logging.getLogger(__name__)

# Create handler
handler = logging.StreamHandler(stream=sys.stderr)

# Create Formatter
formatter = logging.Formatter('%(asctime)s - %(message)s') #TODO

# Customize logger
handler.setFormatter(formatter)
logger.addHandler(handler)

# Improve the name
def _get_name():
    level = inspect.currentframe().f_back.f_code.co_name
    upper_frame = inspect.currentframe().f_back.f_back
    module_frame = inspect.getmodule(upper_frame)
    package = (
        module_frame.__package__
        if module_frame
        else inspect.getmodule(upper_frame.f_back).__package__
    )
    file = (
    module_frame.__name__
    if module_frame
    else inspect.getmodule(upper_frame.f_back).__name__
    )
    module_function = upper_frame.f_code.co_name
    return f"{level.upper()} - {package}:{file}:{module_function}()"


# Custom debug with custom level
def debug2(message, tag=None):
    if tag
        logger.log(DEBUG2, f"{_get_name()}: {message} ({tag})")
    else:
        logger.log(DEBUG2, f"{_get_name()}: {message}")


# Wrap function
def debug1(message, tag=None):
    if tag:
        logger.debug(f"{_get_name()}: {message} ({tag})")
    else:
        logger.debug(f"{_get_name()}: {message}")


# Wrap function
def info(message, tag=None):
    if tag:
        logger.info(f"{_get_name()}: {message} ({tag})")
    else:
        logger.info(f"{_get_name()}: {message}")


# Wrap function
def warning(message, tag=None):
    if tag:
        logger.warning(f"{_get_name()}: {message} ({tag})")
    else:
        logger.warning(f"{_get_name()}: {message}")


# Wrap function
def error(message, tag=None):
    if tag:
        logger.error(f"{_get_name()}: {message} ({tag})")
    else:
        logger.error(f"{_get_name()}: {message}")


# Wrap function
def critical(message, tag=None):
    if tag:
        logger.critical(f"{_get_name()}: {message} ({tag})")
    else:
        logger.critical(f"{_get_name()}: {message}")
