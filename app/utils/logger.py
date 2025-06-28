import logging
import sys
import os

def setup_logger():
    logger = logging.getLogger("ai-mail-agent")

    # Hole das Loglevel aus der Umgebung, z. B. INFO, DEBUG, WARNING
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

logger = setup_logger()
