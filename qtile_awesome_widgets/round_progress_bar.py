import math

from libqtile.widget.base import PaddingMixin


class RoundProgressBar(PaddingMixin):
    def __init__(self, drawer, width, height, **config):
        super().__init__(**config)
        self.add_defaults(PaddingMixin.defaults)
        self.drawer = drawer
        self.width = width
        self.height = height

    def draw(self, percentage, thickness=2, completed=None, remaining=None, inner=None):
        center = self.width / 2
        radius = (self.width - (self.padding * 2)) / 2
        end_angle = percentage * 2 * math.pi / 100

        # draw completed
        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, 0, end_angle)
        self.drawer.set_source_rgb(completed or "ffffff")
        self.drawer.ctx.set_line_width(thickness)
        self.drawer.ctx.stroke()
        # draw remaining
        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, end_angle, 2 * math.pi)
        self.drawer.set_source_rgb(remaining or "000000")
        self.drawer.ctx.set_line_width(thickness)
        self.drawer.ctx.stroke()

        if not inner:
            return

        center = self.width / 2
        radius = (self.width - (self.padding * 2) - thickness) / 2

        self.drawer.ctx.new_sub_path()
        self.drawer.ctx.arc(center, center, radius, 0, 2 * math.pi)
        self.drawer.set_source_rgb(inner)
        self.drawer.ctx.fill()
