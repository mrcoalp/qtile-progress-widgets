import psutil

from .awesome_widget import AwesomeWidget


class MemoryIcon(AwesomeWidget):
    defaults = [
        ("timeout", 1, "How often in seconds the widget refreshes."),
        ("icons", [
            ((0, 100), "\uf85a"),
        ], "Icons to present inside progress bar, based on progress thresholds."),
        ("icon_colors", [
            ((75, 100), "ff0000"),
        ], "Icon color, based on progress limits."),
        ("thresholds", [
            ((0, 50), ("00ff00", "")),
            ((50, 75), ("ffff00", "")),
            ((75, 100), ("ff0000", "")),
        ], "Defines different colors for each specified threshold."),
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
        values = {}
        values["MemUsed"] = mem.used / self.calc_mem
        values["MemTotal"] = mem.total / self.calc_mem
        values["MemFree"] = mem.free / self.calc_mem
        values["MemPercent"] = mem.percent
        values["Buffers"] = mem.buffers / self.calc_mem
        values["Active"] = mem.active / self.calc_mem
        values["Inactive"] = mem.inactive / self.calc_mem
        values["Shmem"] = mem.shared / self.calc_mem
        values["SwapTotal"] = swap.total / self.calc_swap
        values["SwapFree"] = swap.free / self.calc_swap
        values["SwapUsed"] = swap.used / self.calc_swap
        values["SwapPercent"] = swap.percent
        values["mm"] = self.measure_mem
        values["ms"] = self.measure_swap
        return values

    def get_text(self):
        return self.text_format.format(**self._values)

    def is_update_required(self):
        values = self._get_values()
        if values != self._values:
            self._values = values
            return True
        return False

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        self._progress = float(self._values["MemPercent"])
        self.draw_widget_elements()
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.length)
