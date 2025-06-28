# app/logger.py
import logging
import sys

def setup_logger():
    logger = logging.getLogger("ai-mail-agent")
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

logger = setup_logger()
