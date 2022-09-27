import psutil

from .awesome_widget import AwesomeWidget


class CPUIcon(AwesomeWidget):
    defaults = [
        ("icons", [
            ((0, 100), "\ue266"),
        ], "Icons to present inside progress bar, based on progress limits."),
        ("icon_colors", [
            ((50, 75), "ffff00"),
            ((75, 100), "ff0000"),
        ], "Icon color, based on progress limits."),
        ("text_colors", [
            ((50, 75), "ffff00"),
            ((75, 100), "ff0000"),
        ], "Text color, based on progress limits."),
        ("progress_bar_colors", [
            ((50, 75), ("ffff00", "")),
            ((75, 100), ("ff0000", "")),
        ], "Defines different colors for each specified limits.")
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(CPUIcon.defaults)
        self.progress = psutil.cpu_percent()

    def is_update_required(self):
        progress = psutil.cpu_percent()
        if progress != self.progress:
            self.progress = progress
            return True
        return False
