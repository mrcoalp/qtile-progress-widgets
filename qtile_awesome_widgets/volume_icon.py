import re
import subprocess as sp

from libqtile import confreader

from .logger import create_logger
from .progress_widget import ProgressWidget


_logger = create_logger("VOLUME_ICON")


class _Commands():
    def __init__(self, device="pulse", step=5):
        if step < 1 or step > 100:
            raise confreader.ConfigError("Invalid step provided to VolumeIcon: '%s'" % step)

        self._get = ["amixer", "-D", device, "sget", "Master"]
        self._inc = ["amixer", "-D", device, "sset", "Master", "{}%+".format(step)]
        self._dec = ["amixer", "-D", device, "sset", "Master", "{}%-".format(step)]
        self._tog = ["amixer", "-D", device, "sset", "Master", "toggle"]
        self._mic_tog = ["amixer", "-D", device, "sset", "Capture", "toggle"]

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

    def mic_toggle(self):
        return self._safe_call(lambda: sp.call(self._mic_tog))


class VolumeIcon(ProgressWidget):
    defaults = [
        ("device", "pulse", "Device name to control"),
        ("step", 5, "Increment/decrement percentage of volume."),
        ("icons", [
            ((-1, -1), "\ufc5d"),
            ((0, 0), "\uf026"),
            ((0, 50), "\uf027"),
            ((50, 100), "\uf028"),
        ], "Icons to present inside progress bar, based on progress limits."),
        ("text_colors", [
            ((-1, -1), "ff0000"),
        ], "Text color, based on progress limits."),
        ("progress_bar_colors", [
            ((-1, -1), ("ff0000", "ff0000")),
        ], "Defines different colors for each specified limits."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(VolumeIcon.defaults)
        self._cmds = _Commands(self.device, self.step)
        self.progress, self._is_muted = self._get_data()

        self.add_callbacks({
            "Button1": self.cmd_toggle,
            "Button4": self.cmd_inc,
            "Button5": self.cmd_dec,
        })

        _logger.info("Initialized with '%s'", self.device)
        _logger.debug("Current volume: %s", self._cmds.get())

    def _get_data(self):
        return float(self._cmds.get()), self._cmds.is_muted()

    def get_icon(self, _=None):
        if self._is_muted:
            return super().get_icon(-1)
        return super().get_icon()

    def get_icon_color(self, _=None):
        if self._is_muted:
            return super().get_icon_color(-1)
        return super().get_icon_color()

    def get_text_color(self, _=None):
        if self._is_muted:
            return super().get_text_color(-1)
        return super().get_text_color()

    def get_progress_bar_color(self, _=None):
        if self._is_muted:
            return super().get_progress_bar_color(-1)
        return super().get_progress_bar_color()

    def is_update_required(self):
        level, is_muted = self._get_data()
        if self.progress != level or self._is_muted != is_muted:
            self.progress, self._is_muted = level, is_muted
            return True
        return False

    def cmd_inc(self):
        self._cmds.inc()
        self.check_draw_call()

    def cmd_dec(self):
        self._cmds.dec()
        self.check_draw_call()

    def cmd_toggle(self):
        self._cmds.toggle()
        self.check_draw_call()

    def cmd_mic_toggle(self):
        self._cmds.mic_toggle()
        self.check_draw_call()
