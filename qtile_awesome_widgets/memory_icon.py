from libqtile.widget import base
import psutil

from .round_progress_bar import RoundProgressBar


class MemoryIcon(RoundProgressBar):
    defaults = [
        ("timeout", 1, "How often in seconds the widget refreshes."),
        ("icons", [
            ((0, 100), "\uf85a"),
        ], "Icons to present inside progress bar, based on progress thresholds."),
        ("thresholds", [
            ((0, 50), ("00ff00", "")),
            ((50, 75), ("ffff00", "")),
            ((75, 100), ("ff0000", "")),
        ], "Defines different colors for each specified threshold.")
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(MemoryIcon.defaults)
        self.add_defaults(base._TextBox.defaults)
        self.update_level()

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        if self.timeout:
            self.timeout_add(self.timeout, self.loop)

    def get_icon(self):
        for threshs, icon in self.icons:
            if self._level >= threshs[0] and self._level <= threshs[1]:
                return icon
        return ""

    def update_level(self):
        memory = psutil.virtual_memory()
        self._level = round((memory.used / memory.total) * 100, 1)

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
        self.draw_inner_text(self.get_icon(), self.foreground, self.font, self.fontsize)
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.length)
