from libqtile.widget import battery as bt

from .logger import create_logger
from .progress_widget import ProgressWidget


_logger = create_logger("BATTERY_ICON")


class BatteryIcon(ProgressWidget):
    defaults = [
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
            ((-1, -1), "000000"),
            ((0, 10), "ff0000"),
        ], "Icon color, based on progress limits."),
        ("text_colors", [
            ((-1, -1), "000000"),
            ((0, 10), "ff0000"),
        ], "Text color, based on progress limits."),
        ("progress_bar_colors", [
            ((0, 10), ("ff0000", "")),
            ((10, 50), ("ffff00", "")),
            ((50, 100), ("00ff00", "")),
        ], "Defines different colors for each specified limits."),
        ("progress_inner_colors", [
            ((-1, -1), "00ff00"),
        ], "Progress inner colors for each specified limit."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self._battery = bt.load_battery(**config)
        self.add_defaults(BatteryIcon.defaults)
        self._state, self.progress = self._get_status()

        _logger.debug("Initialized with current battery status: '%s' - %s%%", self._state, self.progress)

    def _get_status(self):
        status = self._battery.update_status()
        return status.state, int(status.percent * 100)

    def get_icon(self, _=None):
        if self._state == bt.BatteryState.CHARGING:
            return super().get_icon(-1)
        return super().get_icon()

    def get_text_color(self, _=None):
        if self._state == bt.BatteryState.CHARGING:
            return super().get_text_color(-1)
        return super().get_text_color()

    def get_progress_inner_color(self, _=None):
        if self._state == bt.BatteryState.CHARGING:
            return super().get_progress_inner_color(-1)
        return super().get_progress_inner_color()

    def is_update_required(self):
        state, level = self._get_status()
        if state != self._state or level != self.progress:
            self._state = state
            self.progress = level
            return True
        return False
