from libqtile.widget import base
import psutil

from .round_progress_bar import RoundProgressBar


class CPUIcon(RoundProgressBar):
    defaults = [
        ("timeout", 1, "How often in seconds the widget refreshes."),
        ("icons", [
            ((0, 100), "\ue266"),
        ], "Icons to present inside progress bar, based on progress thresholds."),
        ("thresholds", [
            ((0, 50), ("00ff00", "")),
            ((50, 75), ("ffff00", "")),
            ((75, 100), ("ff0000", "")),
        ], "Defines different colors for each specified threshold.")
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(CPUIcon.defaults)
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
        self._level = round(psutil.cpu_percent(), 1)

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
