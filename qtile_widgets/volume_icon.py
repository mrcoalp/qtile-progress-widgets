import re
import subprocess as sp

from libqtile import confreader
from libqtile.widget import base

from .logger import create_logger
from .round_progress_bar import RoundProgressBar


_logger = create_logger("VOLUME_ICON")


class _Commands():
    _get = []
    _inc = []
    _dec = []
    _tog = []

    def __init__(self, device="pulse", step=5):
        if step < 1 or step > 100:
            raise confreader.ConfigError("Invalid step provided to VolumeIcon: '%s'" % step)

        self._get = ["amixer", "-D", device, "sget", "Master"]
        self._inc = ["amixer", "-D", device, "sset", "Master", "{}%+".format(step)]
        self._dec = ["amixer", "-D", device, "sset", "Master", "{}%-".format(step)]
        self._tog = ["amixer", "-D", device, "sset", "Master", "toggle"]

    def _safe_call(self, func, fallback=None):
        try:
            return func()
        except Exception as e:
            _logger.error(str(e))
        return fallback

    def get(self):
        info = self._safe_call(lambda: sp.check_output(self._get).decode().strip(), "")
        return re.search("(\\d?\\d?\\d)%", info).group(1)

    def is_muted(self):
        info = self._safe_call(lambda: sp.check_output(self._get).decode().strip(), "")
        return re.search("\\[(o\\D\\D?)\\]", info).group(1) == "off"

    def inc(self):
        return self._safe_call(lambda: sp.call(self._inc))

    def dec(self):
        return self._safe_call(lambda: sp.call(self._dec))

    def toggle(self):
        return self._safe_call(lambda: sp.call(self._tog))


class VolumeIcon(RoundProgressBar):
    defaults = [
        ("device", "pulse", "Device name to control"),
        ("step", 5, "Increment/decrement percentage of volume."),
        ("timeout", 1, "How often in seconds the widget refreshes."),
        ("icons", [
            ((-1, -1), "\ufc5d"),
            ((0, 0), "\uf026"),
            ((0, 50), "\uf027"),
            ((50, 100), "\uf028"),
        ], "Icons to present inside progress bar, based on progress thresholds."),
        ("muted_color", None, "Color for icon and bar when muted.")
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(VolumeIcon.defaults)
        self.add_defaults(base._TextBox.defaults)
        self._cmds = _Commands(self.device, self.step)
        self.update_level()

        self.add_callbacks({
            "Button1": lambda: self.cmd_toggle(),
            "Button4": lambda: self.cmd_inc(),
            "Button5": lambda: self.cmd_dec(),
        })

        _logger.info("Initialized with '%s'", self.device)
        _logger.debug("Current volume: %s", self._cmds.get())

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        if self.timeout:
            self.timeout_add(self.timeout, self.loop)

    def get_icon(self):
        for limits, icon in self.icons:
            if self._is_muted and limits[0] == -1:
                return icon
            if self._level >= limits[0] and self._level <= limits[1]:
                return icon
        return ""

    def update_level(self):
        self._level = float(self._cmds.get())
        self._is_muted = self._cmds.is_muted()

    def update(self):
        self.update_level()
        self.draw()

    def loop(self):
        self.update()
        self.timeout_add(self.timeout, self.loop)

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        # draw progress bar
        colors = {
            "completed": self._is_muted and self.muted_color or None,
            "remaining": self._is_muted and self.muted_color or None
        }
        self.draw_progress(self._level, **colors)
        # draw icon
        icon = self.drawer.textlayout(
            self.get_icon(), self._is_muted and self.muted_color or self.foreground,
            self.font, self.fontsize, None, wrap=False
        )
        icon_x = (self.prog_width - icon.width) / 2
        icon_y = (self.prog_height - icon.height) / 2
        icon.draw(icon_x, icon_y)
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.length)

    def cmd_inc(self):
        self._cmds.inc()
        self.update()

    def cmd_dec(self):
        self._cmds.dec()
        self.update()

    def cmd_toggle(self):
        self._cmds.toggle()
        self.update()
