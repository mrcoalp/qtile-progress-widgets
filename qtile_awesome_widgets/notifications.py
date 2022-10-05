import io

from PIL import Image
from dbus_next.constants import MessageType
from libqtile.notify import ClosedReason, Notification, notifier
from libqtile.utils import _send_dbus_message

from .notification_popup import NotificationPopup
from .progress_widget import ProgressCoreWidget
from .utils import create_logger, get_cairo_image


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
        ("text_mode", "with_icon", "Show text mode. Use 'with_icon' or 'without_icon'. None to not show."),
        ("default_timeout", 10, "Default notification timeout, when notification does not have one."),
        ("max_missed", 50, "Max number of missed notifications saved. These can be revisited or cleared."),
        ("external_service", False, "Whether to use an external notification service or qtile's one."),
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
        ("popup_border", "000000", "Border colour."),
        ("popup_border_width", 0, "Line width of drawn borders."),
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
        self.missed = []
        self.current_id = 0
        self.app_name = "NotificationsWidget"
        _logger.info("initialized")

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)

        if self.update_interval is not None:
            _logger.warning("update_interval will be ignored. widget updates itself based on notifications")
            self.update_interval = None

    async def _config_async(self):
        if not self.external_service:
            def on_notification(notification):
                # should this run in an executor?
                self.qtile.run_in_executor(self._on_notification, notification)

            return await notifier.register(on_notification, ("actions", "body"))

        bus, msg = await _send_dbus_message(
            True,
            MessageType.METHOD_CALL,
            destination='org.freedesktop.DBus',
            interface='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            member='AddMatch',
            signature='s',
            body=["eavesdrop=true, interface='org.freedesktop.Notifications', member='Notify'"],
        )

        def create_notification(app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout):
            return Notification(
                app_name=app_name,
                replaces_id=replaces_id,
                app_icon=app_icon,
                summary=summary,
                body=body,
                actions=actions,
                hints=hints,
                timeout=expire_timeout,
            )

        def on_message(message):
            self.qtile.run_in_executor(self._on_notification, create_notification(*message.body))

        if bus and msg and msg.message_type == MessageType.METHOD_RETURN:
            bus.add_message_handler(on_message)
        else:
            _logger.warning("unable to eavesdrop Notifications' Notify method")

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

        # self.qtile.run_in_executor(self.queue_notification, notification)
        self.app_name = notification.app_name
        self.queue_notification(notification)

    def _get_notification_hints(self, notification):
        hints = {}
        for internal_id, hint_keys in self.server_hints.items():
            for hint in hint_keys:
                if hint in notification.hints:
                    hints[internal_id] = notification.hints[hint].value
                    continue
        return hints

    def _get_popup_config(self):
        if self._popup_config is not None:
            return self._popup_config

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

        return self._popup_config

    def queue_notification(self, notification):
        icon = None
        hints = self._get_notification_hints(notification)

        if notification.app_icon:
            icon = get_cairo_image(notification.app_icon)
        elif "icon_name" in hints:
            icon = get_cairo_image(hints["icon_name"])
        elif "icon_data" in hints:
            icon = get_cairo_image(pixbuf_to_image_bytes(hints["icon_data"]), bytes_img=True)

        lifetime = self.default_timeout
        if notification.timeout > 0:
            lifetime = notification.timeout / 1000

        self.displaying.append(NotificationPopup(
            self,
            notification.summary,
            on_timeout=self.on_popup_timeout,
            on_click=self.on_popup_clicked,
            app_name=notification.app_name,
            body=notification.body,
            image=icon,
            lifetime=lifetime,
            **self._get_popup_config(),
        ))

        self.update()

    def on_popup_timeout(self, popup):
        self.missed.append(popup)
        popup.kill()
        self.update()

    def on_popup_clicked(self, popup):
        popup.kill()
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
        return len(self.missed)

    def update_data(self):
        offset = 0

        for popup in reversed(self.displaying):
            if not popup.created or popup.alive:
                popup.show(x=self._get_popup_x(popup), y=self._get_popup_y(popup) + offset)
                offset += popup.height + self.popup_margin
            elif not popup.alive and not popup.killed:
                popup.kill()

        self.displaying = [p for p in self.displaying if p.alive]
        self.progress = len(self.missed) / self.max_missed * 100
