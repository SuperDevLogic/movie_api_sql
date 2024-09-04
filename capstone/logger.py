import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import logging
from logging.handlers import SysLogHandler
# Enable sending logs from the standard Python logging module to Sentry
logging_integration = LoggingIntegration(
    level=logging.INFO,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR  # Send errors as events
)

PAPERTRAIL_HOST = "logs6.papertrailapp.com"
PAPERTRAIL_PORT =  13596

handler = SysLogHandler(address=(PAPERTRAIL_HOST, PAPERTRAIL_PORT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[handler]
)

def get_logger(name):
    return logging.getLogger(name)

