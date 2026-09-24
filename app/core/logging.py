import logging
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "format": (
                "%(asctime)s | %(levelname)s | "
                "%(name)s | %(message)s"
            )
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        }
    },

    "loggers": {
        "app": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        }
    },

    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
}


def setup_logging() -> None:
    dictConfig(LOGGING_CONFIG)
