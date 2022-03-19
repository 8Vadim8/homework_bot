import logging
import logging.config

ERROR_LOG_FILENAME = "errors.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": ("%(asctime)s: %(name)s: %(lineno)d "
                       " %(levelname)s %(message)s"),
        },
        "simple": {
            "format": "%(asctime)s [%(levelname)s]  %(message)s",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "filename": ERROR_LOG_FILENAME,
            "formatter": "default",
            "maxBytes": 5000000,
            "backupCount": 2,
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": [
                "console",
                "file"
            ],
        },
    },
}


def main():
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info('информационное сообщение')
    logger.debug('отладочное сообщение!!!')
    logger.error('сообщение об ошибке')


if __name__ == '__main__':
    main()
