import logging
from logging.handlers import RotatingFileHandler
import os
import site

formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s]: %(message)s", "%Y/%m/%d %H:%M:%S")

log_dir = os.path.join(site.getuserbase(), "share", "qtile-awesome-widgets")

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

handler = RotatingFileHandler(os.path.join(log_dir, "widgets.log"), maxBytes=1024 * 1024 * 5, backupCount=5)
handler.setFormatter(formatter)


def create_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
