import math

from libqtile.widget.base import PaddingMixin


class RoundProgressBar(PaddingMixin):
    def __init__(self, drawer, bar, width, height, **config):
        super().__init__(**config)
        self.add_defaults(PaddingMixin.defaults)
        self.drawer = drawer
        self.bar = bar
        self.width = width
        self.height = height

    def draw(self, percentage, thickness=2, completed=None, remaining=None, inner=None):
        x, y, padding, scale_x, scale_y = 0, 0, 0, 1, 1

        if self.bar.horizontal:
            padding = self.padding_x
            x = (self.width + (padding * 2)) / 2
            y = self.bar.height / 2
        else:
            padding = self.padding_y
            x = self.bar.width / 2
            y = (self.height + (padding * 2)) / 2

        size = max(self.width, self.height)
        radius = (size - (padding * 2)) / 2
        end_angle = percentage * 2 * math.pi / 100

        if self.width > self.height:
            scale_x, scale_y = 1, self.height / self.width
        elif self.height > self.width:
            scale_x, scale_y = self.width / self.height, 1

        self.drawer.ctx.save()

        self.drawer.ctx.scale(scale_x, scale_y)
        self.drawer.ctx.set_line_width(thickness)

        if inner:
            self.drawer.set_source_rgb(inner)
            self.drawer.ctx.arc(x, y, radius, 0, 2 * math.pi)
            self.drawer.ctx.fill()

        # draw completed
        self.drawer.set_source_rgb(completed or "ffffff")
        self.drawer.ctx.arc(x, y, radius, 0, end_angle)
        self.drawer.ctx.stroke()

        # draw remaining
        self.drawer.set_source_rgb(remaining or "000000")
        self.drawer.ctx.arc(x, y, radius, end_angle, 2 * math.pi)
        self.drawer.ctx.stroke()

        self.drawer.ctx.restore()
