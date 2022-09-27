import psutil

from .awesome_widget import AwesomeWidget


class MemoryIcon(AwesomeWidget):
    defaults = [
        ("icons", [
            ((0, 100), "\uf85a"),
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
        ], "Defines different colors for each specified limits."),
        ("text_format", "{MemPercent:.0f}", "Format string to present text."),
        ("measure_mem", "M", "Measurement for Memory (G, M, K, B)"),
        ("measure_swap", "M", "Measurement for Swap (G, M, K, B)"),
    ]
    measures = {"G": 1024 * 1024 * 1024, "M": 1024 * 1024, "K": 1024, "B": 1}

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(MemoryIcon.defaults)
        self.calc_mem = self.measures[self.measure_mem]
        self.calc_swap = self.measures[self.measure_swap]
        self._values = self._get_values()

    def _get_values(self):
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        values = {
            "MemUsed": mem.used / self.calc_mem, "MemTotal": mem.total / self.calc_mem,
            "MemFree": mem.free / self.calc_mem, "MemPercent": mem.percent,
            "Buffers": mem.buffers / self.calc_mem, "Active": mem.active / self.calc_mem,
            "Inactive": mem.inactive / self.calc_mem, "Shmem": mem.shared / self.calc_mem,
            "SwapTotal": swap.total / self.calc_swap, "SwapFree": swap.free / self.calc_swap,
            "SwapUsed": swap.used / self.calc_swap, "SwapPercent": swap.percent, "mm": self.measure_mem,
            "ms": self.measure_swap,
        }
        return values

    def get_text(self):
        return self.text_format.format(**self._values)

    def is_update_required(self):
        values = self._get_values()
        if values != self._values:
            self._values = values
            return True
        return False

    def update(self):
        self.progress = float(self._values["MemPercent"])
        super().update()
