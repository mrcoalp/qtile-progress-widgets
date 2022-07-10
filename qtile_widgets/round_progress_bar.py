import math

from libqtile.widget import base
from libqtile import bar


class RoundProgressBar(base._Widget, base.PaddingMixin):
    defaults = [
        ("color_completed", "ffffff", "Color of the completed stroke of progress bar"),
        ("color_remaining", "666666", "Color of the remaining stroke of progress bar"),
        ("thresholds", [], "Defines different colors for each specified threshold"),
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

    def draw_progress(self, percentage):
        color = self.color_completed

        if self.thresholds:
            for lvls, clr in self.thresholds:
                if percentage >= lvls[0] and percentage <= lvls[1]:
                    color = clr

        center = self.prog_width / 2
        radius = (self.prog_width - (self.padding_y * 2)) / 2
        end_angle = percentage * 2 * math.pi / 100

        # draw completed
        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, 0, end_angle)
        self.drawer.set_source_rgb(color)
        self.drawer.ctx.stroke()
        # draw remaining
        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, end_angle, 2 * math.pi)
        self.drawer.set_source_rgb(self.color_remaining)
        self.drawer.ctx.stroke()
