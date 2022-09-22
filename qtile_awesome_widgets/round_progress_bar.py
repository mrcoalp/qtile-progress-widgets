import math

from libqtile import bar
from libqtile.widget import base


class RoundProgressBar(base._Widget, base.PaddingMixin):
    defaults = [
        ("thresholds", [], "Defines different colors for each specified threshold"),
        ("thickness", 2, "Stroke thickness"),
    ]

    def __init__(self, **config):
        super().__init__(bar.CALCULATED, **config)
        self.add_defaults(RoundProgressBar.defaults)
        self.add_defaults(base.PaddingMixin.defaults)

    def _configure(self, qtile, bar):
        base._Widget._configure(self, qtile, bar)
        self.prog_width = self.bar.height
        self.prog_height = self.bar.height

    def calculate_length(self):
        return self.prog_width

    def draw_progress(self, percentage, completed=None, remaining=None):
        comp = completed or self.foreground or "ffffff"
        rem = remaining or self.background or "666666"

        for limits, colors in self.thresholds:
            if percentage >= limits[0] and percentage <= limits[1]:
                comp = completed or colors[0] or comp
                rem = remaining or colors[1] or rem

        center = self.prog_width / 2
        radius = (self.prog_width - (self.padding_y * 2)) / 2
        end_angle = percentage * 2 * math.pi / 100

        # draw completed
        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, 0, end_angle)
        self.drawer.set_source_rgb(comp)
        self.drawer.ctx.set_line_width(self.thickness)
        self.drawer.ctx.stroke()
        # draw remaining
        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, end_angle, 2 * math.pi)
        self.drawer.set_source_rgb(rem)
        self.drawer.ctx.set_line_width(self.thickness)
        self.drawer.ctx.stroke()

    def fill_inner(self, color):
        center = self.prog_width / 2
        radius = (self.prog_width - (self.padding_y * 2) - self.thickness) / 2

        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, 0, 2 * math.pi)
        self.drawer.set_source_rgb(color)
        self.drawer.ctx.fill()
