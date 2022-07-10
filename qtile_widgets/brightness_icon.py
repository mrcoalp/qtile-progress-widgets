import subprocess as sp

from libqtile import confreader
from libqtile.widget import base

from .logger import create_logger
from .round_progress_bar import RoundProgressBar


_logger = create_logger("BRIGHTNESS_ICON_WIDGET")


class _Commands():
    _get = []
    _set = []
    _inc = []
    _dec = []

    def __init__(self, program="brightnessctl", step=5):
        if step < 1 or step > 100:
            raise confreader.ConfigError("Invalid step provided to BrightnessIcon: '%s'" % step)

        step = str(step)

        if program == "brightnessctl":
            self._get = ["bash", "-c", "brightnessctl -m | cut -d, -f4 | tr -d %"]
            self._set = ["brightnessctl", "set", "{}%"]
            self._inc = ["brightnessctl", "set", "+{}%".format(step)]
            self._dec = ["brightnessctl", "set", "{}-%".format(step)]
        elif program == "light":
            self._get = ["light", "-G"]
            self._set = ["light", "-S", "{}"]
            self._inc = ["light", "-A", step]
            self._dec = ["light", "-U", step]
        elif program == "xbacklight":
            self._get = ["xbacklight", "-get"]
            self._set = ["xbacklight", "-set", "{}"]
            self._inc = ["xbacklight", "-inc", step]
            self._dec = ["xbacklight", "-dec", step]
        else:
            raise confreader.ConfigError("Invalid program provided to BrightnessIcon: '%s'" % program)

    def _safe_call(self, func, fallback=None):
        try:
            return func()
        except Exception as e:
            _logger.error(str(e))
        return fallback

    def get(self):
        level = self._safe_call(lambda: sp.check_output(self._get).decode().strip(), "0")
        return "{:.0f}".format(float(level))

    def set(self, percentage):
        self._set[-1] = self._set[-1].format(percentage)
        return self._safe_call(lambda: sp.call(self._set))

    def inc(self):
        return self._safe_call(lambda: sp.call(self._inc))

    def dec(self):
        return self._safe_call(lambda: sp.call(self._dec))


class BrightnessIcon(RoundProgressBar):
    defaults = [
        ("program", "brightnessctl", "Program to control brightness."),
        ("step", 5, "Increment/decrement percentage of brightness."),
        ("timeout", 0, "How often in seconds the widget refreshes."),
        ("icons", [
            ((0, 30), "\uf5dd"),
            ((30, 80), "\uf5de"),
            ((80, 100), "\uf5df"),
        ], "Icons to present inside progress bar, based on progress thresholds.")
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(BrightnessIcon.defaults)
        self.add_defaults(base._TextBox.defaults)
        self._cmds = _Commands(self.program, self.step)
        self.update_level()

        _logger.info("Initialized with '%s'", self.program)
        _logger.debug("Current brightness: %s", self._cmds.get())

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        if self.timeout:
            self.timeout_add(self.timeout, self.loop)

    def get_icon(self):
        for threshs, icon in self.icons:
            if self._level >= threshs[0] and self._level <= threshs[1]:
                return icon

    def update_level(self):
        self._level = float(self._cmds.get())

    def update(self):
        self.update_level()
        self.draw()

    def loop(self):
        self.update()
        self.timeout_add(self.timeout, self.loop)

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        # draw progress bar
        self.draw_progress(self._level)
        # draw icon
        icon = self.drawer.textlayout(self.get_icon(), self.foreground, self.font, self.fontsize, None, wrap=False)
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
