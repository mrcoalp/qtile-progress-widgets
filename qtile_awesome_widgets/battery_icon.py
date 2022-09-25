from libqtile.widget import battery as bt

from .awesome_widget import AwesomeWidget
from .logger import create_logger


_logger = create_logger("BATTERY_ICON")


class BatteryIcon(AwesomeWidget):
    defaults = [
        ("charging_color", "00ff00", "Center circle (or text and icon) color, when charging."),
        ("timeout", 10, "How often in seconds the widget refreshes."),
        ("icons", [
            ((-1, -1), "\uf583"),
            ((0, 10), "\uf579"),
            ((10, 20), "\uf57a"),
            ((20, 30), "\uf57b"),
            ((30, 40), "\uf57c"),
            ((40, 50), "\uf57d"),
            ((50, 60), "\uf57e"),
            ((60, 70), "\uf57f"),
            ((70, 80), "\uf580"),
            ((80, 90), "\uf581"),
            ((90, 100), "\uf578"),
        ], "Icons to present inside progress bar, based on progress limits."),
        ("icon_colors", [
            ((-1, -1), "00ff00"),
            ((0, 10), "ff0000"),
        ], "Icon color, based on progress limits."),
        ("text_colors", [
            ((-1, -1), "00ff00"),
            ((0, 10), "ff0000"),
        ], "Text color, based on progress limits."),
        ("thresholds", [
            ((0, 10), ("ff0000", "")),
            ((10, 50), ("ffff00", "")),
            ((50, 100), ("00ff00", "")),
        ], "Defines different colors for each specified threshold."),
    ]
    _state = None

    def __init__(self, **config):
        super().__init__(**config)
        self._battery = bt.load_battery(**config)
        self.add_defaults(BatteryIcon.defaults)
        self._state, self._text = self._get_status()

        _logger.debug("Initialized with current battery status: '%s' - %s%%", self._state, self._text)

    def _get_status(self):
        status = self._battery.update_status()
        return status.state, int(status.percent * 100)

    def get_icon(self):
        if self._state == bt.BatteryState.CHARGING:
            return super().get_icon(-1)
        return super().get_icon()

    def is_update_required(self):
        state, level = self._get_status()
        if state != self._state or level != self._text:
            self._state = state
            self._text = level
            return True
        return False

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        # fill circle when a charging color is provided
        is_charging = self._state == bt.BatteryState.CHARGING
        self._progress = float(self._text)
        self.draw_widget_elements(is_charging and self.charging_color or None)
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.length)
