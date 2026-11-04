import logging
import sys

from src.core.correlation import get_correlation_id

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(correlation_id)s | %(message)s"

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


def setup_logging(level: str = "INFO") -> None:
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Attach correlation ID filter
    handler.addFilter(CorrelationIdFilter())

    # Configure log formatting
    handler.setFormatter(
        logging.Formatter(
            fmt=LOG_FORMAT,
            datefmt=DATE_FORMAT,
        )
    )

    # Configure root logger
    logging.basicConfig(
        level=level.upper(),
        handlers=[handler],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


logger = get_logger(__name__)
