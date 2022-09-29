import math

from libqtile.widget.base import PaddingMixin


class RoundProgressBar(PaddingMixin):
    def __init__(self, drawer, bar, width, height, **config):
        super().__init__(**config)
        self.add_defaults(PaddingMixin.defaults)

        self.drawer = drawer
        self.bar = bar

        self.width = min(width, bar.horizontal and bar.width or bar.height)
        self.height = min(height, bar.horizontal and bar.height or bar.width)

        bar_size = self.bar.horizontal and self.bar.height or self.bar.width

        self.x = (self.width + (self.padding * 2)) / 2
        self.y = bar_size / 2

        self.size = max(self.width, self.height)
        self.radius = (self.size - (self.padding * 2)) / 2

        self.scale_x, self.scale_y = 1, 1
        if self.width > self.height:
            self.scale_x, self.scale_y = 1, self.height / self.width
        elif self.height > self.width:
            self.scale_x, self.scale_y = self.width / self.height, 1

    def draw(self, percentage, thickness=2, completed=None, remaining=None, inner=None):
        end_angle = percentage / 100 * 2 * math.pi

        self.drawer.ctx.save()

        self.drawer.ctx.scale(self.scale_x, self.scale_y)
        self.drawer.ctx.set_line_width(thickness)

        if inner:
            self.drawer.set_source_rgb(inner)
            self.drawer.ctx.arc(self.x, self.y, self.radius, 0, 2 * math.pi)
            self.drawer.ctx.fill()

        # draw completed
        self.drawer.set_source_rgb(completed or "ffffff")
        self.drawer.ctx.arc(self.x, self.y, self.radius, 0, end_angle)
        self.drawer.ctx.stroke()

        # draw remaining
        self.drawer.set_source_rgb(remaining or "000000")
        self.drawer.ctx.arc(self.x, self.y, self.radius, end_angle, 2 * math.pi)
        self.drawer.ctx.stroke()

        self.drawer.ctx.restore()
