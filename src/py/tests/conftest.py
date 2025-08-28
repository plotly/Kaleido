import logging
import os
import platform

import logistro
import pytest
from hypothesis import HealthCheck, settings

_logger = logistro.getLogger(__name__)

settings.register_profile(
    "ci",
    deadline=None,  # no per-example deadline
    suppress_health_check=(HealthCheck.too_slow,),  # avoid flaky "too slow" on CI
)


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


is_ci = os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI") == "true"
if is_ci and platform.system in {"Windows", "Darwin"}:
    settings.load_profile("ci")
