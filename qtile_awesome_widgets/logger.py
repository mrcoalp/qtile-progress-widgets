import logging
from logging.handlers import RotatingFileHandler
import os

formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s]: %(message)s", "%H:%M:%S")

log_dir = os.path.expanduser("~/.local/share/qtile-widgets")

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

handler = RotatingFileHandler(os.path.join(log_dir, "widgets.log"), maxBytes=1024, backupCount=5)
handler.setFormatter(formatter)


def create_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
