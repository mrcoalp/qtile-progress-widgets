import psutil

from .awesome_widget import AwesomeWidget


class CPUIcon(AwesomeWidget):
    defaults = [
        ("timeout", 1, "How often in seconds the widget refreshes."),
        ("icons", [
            ((0, 100), "\ue266"),
        ], "Icons to present inside progress bar, based on progress thresholds."),
        ("icon_colors", [
            ((75, 100), "ff0000"),
        ], "Icon color, based on progress limits."),
        ("thresholds", [
            ((0, 50), ("00ff00", "")),
            ((50, 75), ("ffff00", "")),
            ((75, 100), ("ff0000", "")),
        ], "Defines different colors for each specified threshold.")
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(CPUIcon.defaults)
        self._progress = psutil.cpu_percent()

    def is_update_required(self):
        progress = psutil.cpu_percent()
        if progress != self._progress:
            self._progress = progress
            return True
        return False

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        self.draw_widget_elements()
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.length)
