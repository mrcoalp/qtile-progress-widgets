import os

from libqtile.images import Img
import requests
import validators


def get_cairo_image(path_or_url):
    if validators.url(path_or_url):
        return Img(requests.get(path_or_url).content)
    if os.path.isfile(path_or_url):
        return Img.from_path(path_or_url)
    raise Exception("'%s' is neither a valid path nor a url." % path_or_url)
