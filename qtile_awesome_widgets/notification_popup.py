from libqtile.pangocffi import markup_escape_text
from libqtile.popup import Popup


class NotificationPopup:
    def __init__(self, manager, notification, on_timeout, on_click, icon=None, lifetime=None, **config):
        self.id = notification.id
        self.manager = manager

        self.popup = Popup(manager.qtile, **config)
        self.popup.layout.width = self.popup.width - self.popup.horizontal_padding * 2
        self.popup.layout.markup = config.get("markup", False)
        self.popup.text = self._get_text(notification.summary, notification.body, notification.app_name, config)

        if icon:
            img_w = config.get("image_width", 0)
            if icon.width > img_w:
                icon.resize(width=img_w)
            self.popup.layout.width -= icon.width + self.popup.horizontal_padding

        self.icon = icon

        self.popup.height = max(
            self.popup.height,
            self.popup.layout.height,
            icon and icon.height or 0
        )
        self.popup.height += self.popup.vertical_padding * 2

        self.popup.win.process_button_click = lambda *_: on_click(self)
        self.on_timeout = lambda: on_timeout(self)

        self.lifetime = lifetime
        self.born = False
        self.alive = False
        self.killed = False
        self.future = None
        self.x = self.y = None

    def __getattr__(self, __name):
        return getattr(self.popup, __name)

    def _escape_text(self, text):
        if self.popup.layout.markup:
            return markup_escape_text(text)
        return text

    def _get_text(self, summary, body, app_name, config):
        text = ""

        def mod(t):
            return t

        app_mod = config.get("app_name_modifier", None) or mod
        summary_mod = config.get("summary_modifier", None) or mod
        body_mod = config.get("body_modifier", None) or mod

        if app_name:
            text += config.get("app_name_fmt", "{}").format(self._escape_text(app_mod(app_name)))
        text += config.get("summary_fmt", "{}").format(self._escape_text(summary_mod(summary)))
        if body:
            text += config.get("body_fmt", "{}").format(self._escape_text(body_mod(body)))

        return text

    def show(self, x, y):
        if self.killed:
            return

        if self.x == x and self.y == y:
            return

        self.x, self.y = x, y
        self.born = True
        self.alive = True

        self.popup.x = x
        self.popup.y = y
        self.place()
        self.clear()

        offset = 0

        if self.icon:
            # draw image, if any
            pos_x = self.popup.horizontal_padding
            pos_y = (self.popup.height - self.icon.height) / 2
            offset = self.icon.width + self.popup.horizontal_padding
            self.popup.drawer.ctx.save()
            self.popup.drawer.ctx.translate(pos_x, pos_y)
            self.popup.drawer.ctx.set_source(self.icon.pattern)
            self.popup.drawer.ctx.paint()
            self.popup.drawer.ctx.restore()

        # draw text
        pos_x = offset + self.popup.horizontal_padding
        pos_y = (self.popup.height - self.popup.layout.height) / 2
        self.popup.draw_text(x=pos_x, y=pos_y)
        self.popup.draw()
        self.popup.unhide()

        if self.lifetime is None:
            return

        if not self.future or self.future.cancelled():
            self.future = self.manager.timeout_add(self.lifetime, self.on_timeout)

    def is_replaced_by(self, notif):
        return notif.replaces_id == self.id

    def mark_for_kill(self):
        # when not alive but still not killed, manager will take care of killing
        # self, keeping show/kill logic in the update loop
        self.alive = False

    def kill(self):
        if self.killed:
            return
        if self.future:
            self.future.cancel()
        self.popup.kill()
        self.killed = True
        self.alive = not self.killed
