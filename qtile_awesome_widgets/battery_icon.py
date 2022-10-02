from libqtile.widget import battery as bt

from .progress_widget import ProgressInFutureWidget
from .utils import create_logger


_logger = create_logger("BATTERY_ICON")


class BatteryIcon(ProgressInFutureWidget):
    defaults = [
        ("update_interval", 10, "How often in seconds the widget refreshes."),
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
        ("progress_bar_inner_colors", [
            ((-1, -1), "00ff00"),
        ], "Progress inner colors for each specified limit."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(BatteryIcon.defaults)
        self._battery = bt.load_battery(**config)
        self.state = bt.BatteryState.UNKNOWN
        _logger.debug("initialized")

    def _get_status(self):
        status = self._battery.update_status()
        return status.state, int(status.percent * 100)

    def get_icon(self, _=None):
        if self.state == bt.BatteryState.CHARGING:
            return super().get_icon(-1)
        return super().get_icon()

    def get_text_color(self, _=None):
        if self.state == bt.BatteryState.CHARGING:
            return super().get_text_color(-1)
        return super().get_text_color()

    def get_progress_bar_inner_color(self, _=None):
        if self.state == bt.BatteryState.CHARGING:
            return super().get_progress_bar_inner_color(-1)
        return super().get_progress_bar_inner_color()

    def update_data(self):
        state, progress = self.state, self.progress
        self.state, self.progress = self._get_status()
        self.pending_update = state != self.state or progress != self.progress

    def is_draw_update_required(self):
        return self.pending_update
