import re
import subprocess as sp

from libqtile.widget import base

from .logger import create_logger
from .round_progress_bar import RoundProgressBar


_logger = create_logger("BATTERY_ICON")


class BatteryIcon(RoundProgressBar):
    defaults = [
        ("charging_color", "00ff00", "Inner color, when charging."),
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
        ], "Icons to present inside progress bar, based on progress thresholds."),
        ("thresholds", [
            ((0, 10), ("ff0000", "")),
            ((10, 50), ("ffff00", "")),
            ((50, 100), ("00ff00", "")),
        ], "Defines different colors for each specified threshold.")
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(BatteryIcon.defaults)
        self.add_defaults(base._TextBox.defaults)
        self.update_level()

        _logger.debug("Initialized with current battery status: '%s' - %s%%", self._status, self._level)

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        if self.timeout:
            self.timeout_add(self.timeout, self.loop)

    def get_icon(self):
        for threshs, icon in self.icons:
            if self._status == "Charging" and threshs[0] == -1 and threshs[1] == -1:
                return icon
            if self._level >= threshs[0] and self._level <= threshs[1]:
                return icon
        return ""

    def update_level(self):
        info = sp.check_output(["acpi"]).decode().strip()
        filtered = re.search(".+: (.+), (\\d?\\d?\\d)%,?(.*)", info)
        self._status = filtered.group(1)
        self._level = float(filtered.group(2))

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
        # fill circle when a charging color is provided
        if self._status == "Charging" and self.charging_color:
            self.fill_inner(self.charging_color)
        # draw icon
        icon = self.drawer.textlayout(self.get_icon(), self.foreground, self.font, self.fontsize, None, wrap=False)
        icon_x = (self.prog_width - icon.width) / 2
        icon_y = (self.prog_height - icon.height) / 2
        icon.draw(icon_x, icon_y)
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.length)
