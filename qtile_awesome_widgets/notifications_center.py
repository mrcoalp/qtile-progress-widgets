from libqtile.popup import Popup
from .utils import create_logger

_logger = create_logger("center")


class NotificationsCenter:
    def __init__(self, qtile, x, y, width, height, config):
        self.popup = Popup(qtile, x, y, width, height, **config)
        self.active = False
        self.max_height = self.popup.height
        self.stored = []

    def store_notification(self, notif_info):
        self.stored.append(notif_info)

    def show(self):
        self.popup.clear()
        for notif in self.stored:
            if notif.content:
                _logger.warning(notif.content)
        self.popup.draw()
        self.popup.unhide()
        self.active = True

    def hide(self):
        self.popup.hide()
        self.active = False

    def toggle(self):
        if self.active:
            return self.hide()
        return self.show()
