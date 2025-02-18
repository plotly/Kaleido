import logging

import logistro
import pytest

_logger = logistro.getLogger(__name__)


# pytest shuts down its capture before logging/threads finish
@pytest.fixture(scope="session", autouse=True)
def cleanup_logging_handlers(request):
    capture = request.config.getoption("--capture") != "no"
    try:
        yield
    finally:
        if capture:
            _logger.info("Conftest cleaning up handlers.")
            for handler in logging.root.handlers[:]:
                handler.flush()
                if isinstance(handler, logging.StreamHandler):
                    logging.root.removeHandler(handler)
