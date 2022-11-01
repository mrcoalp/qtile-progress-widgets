import logging
from logging.handlers import RotatingFileHandler
import os
import site

from libqtile.images import Img
import requests
import validators

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    has_gtk = True
except:
    has_gtk = False


logging.disable(logging.DEBUG)


def create_logger(name):
    formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s]: %(message)s", "%Y/%m/%d %H:%M:%S")
    log_dir = os.path.join(site.getuserbase(), "share", "qtile-progress-widgets")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    handler = RotatingFileHandler(os.path.join(log_dir, "widgets.log"), maxBytes=1024 * 1024 * 5, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger


def get_cairo_image(source, bytes_img=False):
    if bytes_img:
        return Img(source)
    if validators.url(source):
        return Img(requests.get(source).content)
    source = os.path.expanduser(source)
    if os.path.isfile(source):
        return Img.from_path(source)
    raise Exception("'%s' is neither a valid path nor a url." % source)


def get_gtk_icon(icon_name):
    if not has_gtk:
        return None

    icon_theme = Gtk.IconTheme.get_default()
    icon = icon_theme.lookup_icon(icon_name, 512, 0)

    if icon:
        return icon.get_filename()

    return None
