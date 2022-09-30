from libqtile.images import Img
import requests


def get_cairo_image(path, url=False):
    if url:
        return Img(requests.get(path).content)
    return Img.from_path(path)
