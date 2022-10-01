import math

from libqtile.widget.base import PaddingMixin


class ProgressBar(PaddingMixin):
    def __init__(self, drawer, bar, width, height, thickness, **config):
        super().__init__(**config)
        self.add_defaults(PaddingMixin.defaults)

        self.drawer = drawer
        self.bar = bar

        self.width = min(width, bar.horizontal and bar.width or bar.height)
        self.height = min(height, bar.horizontal and bar.height or bar.width)
        self.total_width = self.width + self.padding * 2

        bar_size = self.bar.horizontal and self.bar.height or self.bar.width

        self.x = self.total_width / 2
        self.y = bar_size / 2

        self.scale_x, self.scale_y = 1, 1

        if self.width > self.height:
            self.scale_x, self.scale_y = 1, self.height / self.width
        elif self.height > self.width:
            self.scale_x, self.scale_y = self.width / self.height, 1

        size = max(self.width, self.height)
        self.radius = (size - (self.padding * 2)) / 2

        self.thickness = thickness
        self.percentage = 0
        self.completed = "ffffff"
        self.remaining = "000000"
        self.inner = ""

    def update(self, percentage, completed, remaining, inner):
        self.percentage = percentage
        self.completed = completed
        self.remaining = remaining
        self.inner = inner

    def draw_self(self, offset=0):
        return self.draw(self.percentage, self.completed, self.remaining, self.inner, offset)

    def draw(self, percentage, completed=None, remaining=None, inner=None, offset=0):
        end_angle = percentage / 100 * 2 * math.pi

        self.drawer.ctx.save()

        self.drawer.ctx.scale(self.scale_x, self.scale_y)
        self.drawer.ctx.set_line_width(self.thickness)

        radius = self.radius - self.thickness / 2
        x = self.x + offset

        if inner:
            self.drawer.set_source_rgb(inner)
            self.drawer.ctx.arc(x, self.y, radius, 0, 2 * math.pi)
            self.drawer.ctx.fill()

        # draw completed
        self.drawer.set_source_rgb(completed or "ffffff")
        self.drawer.ctx.arc(x, self.y, radius, 0, end_angle)
        self.drawer.ctx.stroke()

        # draw remaining
        self.drawer.set_source_rgb(remaining or "000000")
        self.drawer.ctx.arc(x, self.y, radius, end_angle, 2 * math.pi)
        self.drawer.ctx.stroke()

        self.drawer.ctx.restore()
