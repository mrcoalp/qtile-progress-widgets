import logging
from logging.handlers import RotatingFileHandler
import os
import os
import site

from libqtile.images import Img
import requests
import validators


logging.disable(logging.DEBUG)


def create_logger(name):
    formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s]: %(message)s", "%Y/%m/%d %H:%M:%S")
    log_dir = os.path.join(site.getuserbase(), "share", "qtile-awesome-widgets")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    handler = RotatingFileHandler(os.path.join(log_dir, "widgets.log"), maxBytes=1024 * 1024 * 5, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger


def get_cairo_image(path_or_url):
    if validators.url(path_or_url):
        return Img(requests.get(path_or_url).content)
    if os.path.isfile(path_or_url):
        return Img.from_path(path_or_url)
    raise Exception("'%s' is neither a valid path nor a url." % path_or_url)
