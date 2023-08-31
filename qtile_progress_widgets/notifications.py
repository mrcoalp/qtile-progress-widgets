import io
import os

from PIL import Image
from dbus_next.constants import MessageType
from libqtile.notify import ClosedReason, Notification, notifier
from libqtile.utils import _send_dbus_message

from .notification_popup import NotificationPopup
from .progress_widget import ProgressCoreWidget
from .utils import create_logger, get_cairo_image, get_gtk_icon


_logger = create_logger("NOTIFICATIONS")


def pixbuf_to_image_bytes(icon_data):
    """
    Convert gdkpixbuf data to PIL image.
    Pixbuf notification data:
        0 - width
        1 - height
        2 - rowstride
        3 - has_alpha
        4 - bits_per_sample
        5 - n_channels
        6 - data
    """

    w = icon_data[0]
    h = icon_data[1]
    stride = icon_data[2]
    mode = "RGB" if not icon_data[3] else "RGBA"
    data = icon_data[6]

    im = Image.frombytes(mode, (w, h), data, "raw", mode, stride)
    img_byte_arr = io.BytesIO()
    im.save(img_byte_arr, format='PNG')

    return img_byte_arr.getvalue()


class Notifications(ProgressCoreWidget):
    defaults = [
        (
            "update_interval",
            None,
            "How often in seconds the widget refreshes. "
            "This setting is disabled for this widget, since it updates itself whenever there's "
            "a new notification."
        ),
        ("icons", [
            ((0, 100), "\uf00b"),
        ], "Icons to present inside progress bar, based on progress limits."),
        ("default_timeout", 10, "Default notification timeout, when notification does not have one."),
        ("max_missed", 50, "Max number of missed notifications saved. These can be revisited or cleared."),
        (
            "popup_pos_x",
            lambda qtile, bar, popup: bar.screen.width - popup.width - 5,
            "Either an hardcoded coord or a function returning a coord. The function takes "
            "three arguments (qtile, bar, popup), to adjust in relation to them."
        ),
        (
            "popup_pos_y",
            lambda qtile, bar, popup: bar.height + 5,
            "Either an hardcoded coord or a function returning a coord. The function takes "
            "three arguments (qtile, bar, popup), to adjust in relation to them."
        ),
        ("popup_width", 350, "Width of the notification popup."),
        ("popup_height", 80, "Min popup height. Gets resized when contents require it to."),
        ("popup_opacity", 1.0, "Opacity of notifications."),
        ("popup_foreground", None, "Colour of text. When None, uses the same as the widget."),
        ("popup_background", None, "Background colour. When None, uses the same as the widget."),
        ("popup_low_foreground", None, "Colour of text for low urgency notifications. When None, uses default."),
        ("popup_low_background", None, "Background colour for low urgency notifications. When None, uses default."),
        ("popup_normal_foreground", None, "Colour of text for normal urgency notifications. When None, uses default."),
        ("popup_normal_background", None, "Background colour for normal urgency notifications. When None, uses default."),
        ("popup_critical_foreground", None, "Colour of text for critical urgency notifications. When None, uses default."),
        ("popup_critical_background", None, "Background colour for critical urgency notifications. When None, uses default."),
        ("popup_border", "000000", "Border colour."),
        ("popup_border_width", 0, "Line width of drawn borders."),
        ("popup_low_border", None, "Border colour for low urgency notifications. When None, uses default."),
        ("popup_low_border_width", None, "Line width of drawn borders for low urgency notifications. When None, uses default."),
        ("popup_normal_border", None, "Border colour for normal urgency notifications. When None, uses default."),
        ("popup_normal_border_width", None, "Line width of drawn borders for normal urgency notifications. When None, uses default."),
        ("popup_critical_border", None, "Border colour for critical urgency notifications. When None, uses default."),
        ("popup_critical_border_width", None, "Line width of drawn borders for critical urgency notifications. When None, uses default."),
        ("popup_font", None, "Font used in notifications. When None, uses the same as widget."),
        ("popup_fontsize", None, "Size of font. When None, uses the same as widget."),
        ("popup_fontshadow", None, "Colour for text shadows, or None for no shadows."),
        ("popup_image_width", 70, "Max notification image width, when available."),
        (
            "popup_app_name_fmt",
            "<i>{} :: </i>",
            "App name text format. Empty string hides it. "
            "App name, summary and body strings are concatenated."
        ),
        (
            "popup_app_name_modifier",
            None,
            "Define a modifier function. Function takes in the original value and should "
            "return an updated one."
            "e.g. function in config that removes line returns:"
            "def my_func(app_name)"
            "   return app_name.replace('\n', '')"
            "then set option popup_app_name_modifier=my_func",
        ),
        (
            "popup_summary_fmt",
            "<b>{}</b>",
            "Summary text format. Empty string hides it. "
            "App name, summary and body strings are concatenated."
        ),
        (
            "popup_summary_modifier",
            None,
            "Define a modifier function. Function takes in the original value and should "
            "return an updated one."
            "e.g. function in config that removes line returns:"
            "def my_func(summary)"
            "   return summary.replace('\n', '')"
            "then set option popup_summary_modifier=my_func",
        ),
        (
            "popup_body_fmt",
            "\n{}",
            "Body text format. Empty string hides it. "
            "App name, summary and body strings are concatenated."
        ),
        (
            "popup_body_modifier",
            None,
            "Define a modifier function. Function takes in the original value and should "
            "return an updated one."
            "e.g. function in config that removes line returns:"
            "def my_func(body)"
            "   return body.replace('\n', '')"
            "then set option popup_body_modifier=my_func",
        ),
        ("popup_horizontal_padding", 5, "Padding at sides of text."),
        ("popup_vertical_padding", 5, "Padding at top and bottom of text."),
        ("popup_margin", 5, "Margin between popups."),
        ("popup_text_alignment", "left", "Text alignment: left, center or right."),
        ("popup_wrap", True, "Whether to wrap text."),
        ("popup_markup", True, "Whether or not to use pango markup."),
        (
            "notif_center_enabled",
            False,
            "Whether or not to enable notifications center. When enabled, bar widget will start "
            "monitoring the unread box left space. When clicked, the widget will toggle notifications center."
        ),
    ]
    server_hints = {
        "urgency": ("urgency",),
        "category": ("category",),
        "desktop_entry": ("desktop-entry",),
        "value": ("value",),
        "transient": ("transient",),
        "icon_name": ("image-path",),
        "icon_data": ("image-data", "image_data", "icon_data",),
        "foreground": ("fgcolor",),
        "background": ("bgcolor",),
        "frame": ("frcolor",),
        "highlight": ("hlcolor",),
    }

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(Notifications.defaults)
        self._popup_config = None
        self.displaying = []
        self.center = None
        _logger.info("initialized")

    @staticmethod
    def _get_notification_icon(notification, hints):
        app_icon = notification.app_icon

        if app_icon:
            icon_path = get_gtk_icon(app_icon)
            if icon_path:
                # icon was found in current gtk theme
                return get_cairo_image(icon_path)
            if os.path.exists(app_icon):
                # icon is an abs path to an os' file
                return get_cairo_image(app_icon)

        if "icon_name" in hints:
            return get_cairo_image(hints["icon_name"])

        if "icon_data" in hints:
            img_bytes = pixbuf_to_image_bytes(hints["icon_data"])
            return get_cairo_image(img_bytes, bytes_img=True)

        return None

    def _configure(self, qtile, bar):
        if self.update_interval is not None:
            _logger.warning("update_interval will be ignored. widget updates itself based on notifications")
            self.update_interval = None

        super()._configure(qtile, bar)
        self._prepare_popup_config()

        if self.notif_center_enabled:
            # create notifications center
            from .notifications_center import NotificationsCenter
            self.center = NotificationsCenter(qtile, 0, 0, 200, bar.screen.height, {
                "background": "000000"
            })

            # enable mouse callbacks
            self.add_callbacks({
                "Button1": lambda: self.center.toggle()
            })

    async def _config_async(self):
        await notifier.register(self._on_notification, ("actions", "body"), self._on_notification_close)

    def _prepare_popup_config(self):
        if self._popup_config is not None:
            return

        self._popup_config = {}

        for key, _, _ in Notifications.defaults.copy():
            if not key.startswith("popup_"):
                continue
            # remove popup_ prefix from config, passing the expected
            # config keys to popup
            k = key.replace("popup_", "")
            # when value is none, try to get from widget config
            value = getattr(self, key, None)
            if value is None:
                value = getattr(self, k, None)
            if k == "fontsize":
                # font size is a special case, since all widgets use
                # fontsize, and popups use font_size
                k = "font_size"
            self._popup_config[k] = value

    def _on_notification(self, notification):
        log = ""
        for key, value in notification.__dict__.items():
            if key == "hints":
                log += "%s:" % key
                for k, v in value.items():
                    if k == "icon_data":
                        continue
                    log += "\n\t%s: %s" % (k, v)
                log += "\n"
                continue
            log += "%s: %s\n" % (key, value)
        _logger.info(log)

        self.qtile.call_soon_threadsafe(self._queue_notification, notification)

    def _on_notification_close(self, nid):
        for popup in self.displaying:
            if popup.id == nid:
                self._close_notification(popup, ClosedReason.method, False)
        self.update()

    def _queue_notification(self, notification):
        hints = self._get_notification_hints(notification)

        self.displaying.append(NotificationPopup(
            self,
            notification,
            on_timeout=self._expire_notification,
            on_click=self._dismiss_notification,
            **self._get_notification_config(notification, hints),
        ))

        for n in self.displaying:
            if n.is_replaced_by(notification):
                self._close_notification(n, ClosedReason.dismissed, False)

        self.update()

    def _get_notification_hints(self, notification):
        hints = {}
        for internal_id, hint_keys in self.server_hints.items():
            for hint in hint_keys:
                if hint in notification.hints:
                    hints[internal_id] = notification.hints[hint].value
                    continue
        return hints

    def _get_notification_config(self, notification, hints):
        # copy to keep defaults
        config = self._popup_config.copy()

        # get lifetime
        lifetime = self.default_timeout
        if notification.timeout > 0:
            # notification's timeout is in milliseconds
            lifetime = notification.timeout / 1000
        config["lifetime"] = lifetime

        # get icon
        # this process takes a toll on performace... can we optimize this? @performance
        config["icon"] = self._get_notification_icon(notification, hints)

        # get urgency and update colors, when available
        if "urgency" in hints:
            urgency = hints["urgency"]
            affected_props = ["foreground", "background", "border", "border_width"]

            def update_urgency_attribute(prefix, attr):
                override = config.get("%s_%s" % (prefix, attr), None)
                if override is not None:
                    config[attr] = override

            if urgency in ["l", "L", 0]:
                for attr in affected_props:
                    update_urgency_attribute("low", attr)
            elif urgency in ["n", "N", 1]:
                for attr in affected_props:
                    update_urgency_attribute("normal", attr)
            elif urgency in ["c", "C", 2]:
                for attr in affected_props:
                    update_urgency_attribute("critical", attr)

        return config

    def _expire_notification(self, popup):
        if self.notif_center_enabled:
            self.center.store_notification(popup.get_info())

            while len(self.center.stored) > self.max_missed:
                self.center.stored.pop(0)

        self._close_notification(popup, ClosedReason.expired)

    def _dismiss_notification(self, popup):
        self._close_notification(popup, ClosedReason.dismissed)

    def _close_notification(self, popup, reason, update=True):
        popup.mark_for_kill()
        notifier._service.NotificationClosed(popup.id, reason)

        if update:
            self.update()

    def _get_popup_x(self, popup):
        if callable(self.popup_pos_x):
            return self.popup_pos_x(self.qtile, self.bar, popup)
        return self.popup_pos_x

    def _get_popup_y(self, popup):
        if callable(self.popup_pos_y):
            return self.popup_pos_y(self.qtile, self.bar, popup)
        return self.popup_pos_y

    def get_text(self):
        if not self.notif_center_enabled:
            return ""
        return len(self.center.stored)

    def update_data(self):
        offset = 0

        for popup in reversed(self.displaying):
            if not popup.born or popup.alive:
                popup.show(x=self._get_popup_x(popup), y=self._get_popup_y(popup) + offset)
                offset += popup.height + self.popup_margin
            elif not popup.alive and not popup.killed:
                # kill marked for kill popups
                popup.kill()

        self.displaying = [p for p in self.displaying if p.alive]

        if self.notif_center_enabled:
            self.progress = len(self.center.stored) / self.max_missed * 100

    def finalize(self):
        self.qtile.call_soon_threadsafe(self._finalize)

    async def _finalize(self):
        task = notifier.unregister(self._on_notification)

        if task:
            await task

        super().finalize()
