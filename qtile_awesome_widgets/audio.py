import re
import subprocess as sp

from libqtile.confreader import ConfigError

from .progress_widget import ProgressCoreWidget
from .utils import create_logger


_logger = create_logger("AMIXER")
_log_vol = create_logger("VOLUME_ICON")
_log_mic = create_logger("MIC_ICON")


class AudioControls:
    def __init__(self, device, step, channel):
        if 1 > step > 100:
            raise ConfigError("Invalid step provided to AudioCommands: '%s'" % step)

        self.device = device
        self.step = step
        self.channel = channel

    def get(self):
        raise NotImplemented

    def is_muted(self):
        raise NotImplemented

    def inc(self):
        raise NotImplemented

    def dec(self):
        raise NotImplemented

    def toggle(self):
        raise NotImplemented


class _AmixerControls(AudioControls):
    def __init__(self, device="pulse", step=5, channel="Master"):
        super().__init__(device, step, channel)

        self._get = ["amixer", "-D", device, "sget", channel]
        self._inc = ["amixer", "-D", device, "sset", channel, "{}%+".format(step)]
        self._dec = ["amixer", "-D", device, "sset", channel, "{}%-".format(step)]
        self._tog = ["amixer", "-D", device, "sset", channel, "toggle"]

    @staticmethod
    def _safe_call(func, fallback=None):
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


class AudioWidget(ProgressCoreWidget):
    defaults = [
        ("device", "pulse", "Device name to control"),
        ("step", 5, "Increment/decrement percentage of volume."),
        ("channel", "Master", "Audio channel."),
        (
            "controls",
            None,
            "AudioControls instance to use. Leaving None will fallack to _AmixerControls. \
            Make sure to have it installed in your system, in this case."
        ),
        ("text_colors", [
            ((-1, -1), "ff0000"),
        ], "Text color, based on progress limits."),
        ("progress_bar_colors", [
            ((-1, -1), ("ff0000", "ff0000")),
        ], "Defines different colors for each specified limits."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(AudioWidget.defaults)
        self.is_muted = False
        self.add_callbacks({
            "Button1": self.cmd_toggle,
            "Button4": self.cmd_inc,
            "Button5": self.cmd_dec,
        })

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        self.controls = self.controls or _AmixerControls(self.device, self.step, self.channel)

    def _get_data(self):
        return self.cmd_get(), self.cmd_is_muted()

    def get_icon(self, _=None):
        if self.is_muted:
            return super().get_icon(-1)
        return super().get_icon()

    def get_icon_color(self, _=None):
        if self.is_muted:
            return super().get_icon_color(-1)
        return super().get_icon_color()

    def get_text_color(self, _=None):
        if self.is_muted:
            return super().get_text_color(-1)
        return super().get_text_color()

    def get_progress_bar_color(self, _=None):
        if self.is_muted:
            return super().get_progress_bar_color(-1)
        return super().get_progress_bar_color()

    def update_data(self):
        self.progress, self.is_muted = self._get_data()

    def cmd_get(self):
        return float(self.controls.get())

    def cmd_inc(self):
        self.controls.inc()
        self.update()

    def cmd_dec(self):
        self.controls.dec()
        self.update()

    def cmd_toggle(self):
        self.controls.toggle()
        self.update()

    def cmd_is_muted(self):
        return self.controls.is_muted()


class VolumeIcon(AudioWidget):
    defaults = [
        ("icons", [
            ((-1, -1), "\ufc5d"),
            ((0, 0), "\uf026"),
            ((0, 50), "\uf027"),
            ((50, 100), "\uf028"),
        ], "Icons to present inside progress bar, based on progress limits."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(VolumeIcon.defaults)
        _log_vol.info("initialized with '%s'", self.device)


class MicrophoneIcon(AudioWidget):
    defaults = [
        ("icons", [
            ((-1, -1), "\uf131"),
            ((0, 100), "\uf130"),
        ], "Icons to present inside progress bar, based on progress limits."),
        ("channel", "Capture", "Audio channel."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(MicrophoneIcon.defaults)
        _log_mic.info("initialized with '%s'", self.device)
