import subprocess as sp

from libqtile.confreader import ConfigError

from .progress_widget import ProgressCoreWidget
from .utils import create_logger


_logger = create_logger("BRIGHTNESS_ICON")


class _Commands():
    def __init__(self, program="brightnessctl", step=5):
        if step < 1 or step > 100:
            raise ConfigError("Invalid step provided to BrightnessIcon: '%s'" % step)

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
            raise ConfigError("Invalid program provided to BrightnessIcon: '%s'" % program)

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


class BrightnessIcon(ProgressCoreWidget):
    defaults = [
        ("program", "brightnessctl", "Program to control brightness."),
        ("step", 5, "Increment/decrement percentage of brightness."),
        ("update_interval", 0, "How often in seconds the widget refreshes."),
        ("icons", [
            ((0, 30), "\uf5dd"),
            ((30, 80), "\uf5de"),
            ((80, 100), "\uf5df"),
        ], "Icons to present inside progress bar, based on progress limits.")
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(BrightnessIcon.defaults)
        self._cmds = _Commands(self.program, self.step)
        self.add_callbacks({
            "Button1": self.cmd_set,
            "Button4": self.cmd_inc,
            "Button5": self.cmd_dec,
        })
        _logger.info("initialized")

    def update_data(self):
        progress = self.progress
        self.progress = float(self._cmds.get())
        self.pending_update = progress != self.progress

    def is_draw_update_required(self):
        return self.pending_update

    def cmd_inc(self):
        self._cmds.inc()
        self.update()

    def cmd_dec(self):
        self._cmds.dec()
        self.update()

    def cmd_set(self, level=50):
        if 0 > level > 100:
            return _logger.warning("Tried to set invalid level: %s", level)
        self._cmds.set(level)
        self.update()
