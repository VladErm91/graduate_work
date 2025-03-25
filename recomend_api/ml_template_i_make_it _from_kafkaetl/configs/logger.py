import logging
import sys

from configs.settings import settings


def setup_logger(logger_name="etl"):
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    try:
        log_level = getattr(logging, settings.log_level.upper())
        logger.setLevel(log_level)
    except AttributeError:
        logger.error(
            f"Неправильный уровень логирования: {settings.log_level}. Используем DEBUG."
        )
        logger.setLevel(logging.DEBUG)
    backoff_logger = logging.getLogger("backoff")
    backoff_logger.setLevel(logging.INFO)
    backoff_logger.addHandler(logging.StreamHandler())

    return logger
