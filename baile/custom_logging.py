import logging
import inspect

# new constants
DEBUG1 = 10
DEBUG2 = 5

basicConfig = logging.basicConfig

logger = logging.getLogger(__name__)

def debug2(message):
    logger.name = __name__+":"+inspect.stack()[0].function
    logger.debug(msg=message, stacklevel=DEBUG2)

def debug1(message):
    logger.name = __name__+":"+inspect.stack()[0].function
    logger.debug(msg=message, stacklevel=DEBUG1)

def info(message):
    logger.name = __name__+":"+inspect.stack()[0].function
    logger.info(msg=message)

def error(message):
    logger.name = __name__+":"+inspect.stack()[0].function
    logger.error(msg=message)

def warning(message):
    logger.name = __name__+":"+inspect.stack()[0].function
    logger.warning(msg=message)

def critical(message):
    logger.name = __name__+":"+inspect.stack()[0].function
    logger.critical(msg=message)
