import math

from libqtile import bar
from libqtile.widget import base


class RoundProgressBar(base._Widget, base.PaddingMixin):
    defaults = [
        ("foreground", "ffffff", "Foreground colour"),
        ("thresholds", [], "Defines different colors for each specified threshold"),
        ("thickness", 2, "Stroke thickness"),
    ]
    comp_color_override = None
    rem_color_override = None
    inner_color_override = None

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

    def draw_progress_bar(self, percentage):
        comp = self.comp_color_override or self.foreground or "ffffff"
        rem = self.rem_color_override or self.background or "000000"

        for limits, colors in self.thresholds:
            lower, upper = limits
            if lower <= percentage <= upper:
                foreground, background = colors
                comp = self.comp_color_override or foreground or comp
                rem = self.rem_color_override or background or rem

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

        self.paint_inner_circle()

    def paint_inner_circle(self):
        if not self.inner_color_override:
            return

        center = self.prog_width / 2
        radius = (self.prog_width - (self.padding_y * 2) - self.thickness) / 2

        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, 0, 2 * math.pi)
        self.drawer.set_source_rgb(self.inner_color_override)
        self.drawer.ctx.fill()
