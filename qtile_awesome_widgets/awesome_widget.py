import html

from libqtile import bar
from libqtile.widget import base

from .round_progress_bar import RoundProgressBar


class AwesomeWidget(base._Widget, base.PaddingMixin):
    defaults = [
        ("font", "sans", "Default font"),
        ("fontsize", None, "Font size. Calculated if None."),
        ("fontshadow", None, "font shadow color, default is None(no shadow)"),
        ("markup", True, "Whether or not to use pango markup"),
        ("foreground", "ffffff", "Foreground colour"),
        ("timeout", 1, "How often in seconds the widget refreshes."),
        ("show_progress_bar", True, "Whether to draw round progress bar."),
        ("progress_bar_colors", [], "Progress bar colors for each specified limit."),
        ("progress_inner_colors", [], "Progress inner color for each specified limit."),
        ("progress_bar_thickness", 2, "Progress bar stroke thickness."),
        ("icons", [], "Icons to present inside progress bar, based on progress limits."),
        ("icon_colors", [], "Icon color, based on progress limits."),
        ("icon_size", None, "Icon size. Fontsize used if None."),
        ("text_mode", None, "Show text mode. Use 'with_icon' or 'without_icon'. None to not show."),
        ("text_format", "{:.0f}", "Format string to present text."),
        ("text_offset", 0, "Text offset. Negative values can be used to bring it closer to icon."),
        ("text_colors", [], "Text color, based on progress limits."),
    ]

    def __init__(self, **config):
        super().__init__(bar.CALCULATED, **config)
        self.add_defaults(AwesomeWidget.defaults)
        self.progress = 0
        self._icon_layout = None
        self._text_layout = None
        self._total_length = None

    @staticmethod
    def _is_in_limits(value, limits):
        lower, upper = limits
        if lower <= value <= upper:
            return True
        return False

    @staticmethod
    def _update_layout(layout, **kwargs):
        for key, value in kwargs.items():
            setattr(layout, key, value)

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)

        if self.fontsize is None:
            self.fontsize = self.bar.height - self.bar.height / 5

        def create_layout(icon=False):
            return self.drawer.textlayout(
                "",
                "ffffff",
                self.font,
                icon and self.icon_size or self.fontsize,
                self.fontshadow,
                markup=self.markup,
            )

        if self.show_progress_bar:
            self._progress_bar = RoundProgressBar(self.drawer, self.bar.height, self.bar.height, **self._user_config)

        if not self.text_mode or self.text_mode == "with_icon":
            self._icon_layout = create_layout(True)

        if self.text_mode in ["with_icon", "without_icon"]:
            self._text_layout = create_layout()

        self.update()

        if self.timeout <= 0:
            return

        self.timeout_add(self.timeout, self.loop)

    def _has_something_to_draw(self):
        if self.show_progress_bar:
            return True
        if self._icon_layout and self._icon_layout.text:
            return True
        if self._text_layout and self._text_layout.text:
            return True
        return False

    def _draw_text_in_inner_circle(self, layout):
        # relative to round progress bar attributes
        x = (self._progress_bar.width - layout.width) / 2
        y = (self._progress_bar.height - layout.height) / 2
        layout.draw(x, y)

    def calculate_length(self):
        return self._total_length

    def escape_text(self, text):
        if not self.markup:
            return text
        return html.escape(text)

    def get_icon(self, progress=None):
        for limits, icon in self.icons:
            if self._is_in_limits(progress or self.progress, limits):
                return icon or ""
        return ""

    def get_icon_color(self, progress=None):
        default = self.foreground or "ffffff"
        for limits, color in self.icon_colors:
            if self._is_in_limits(progress or self.progress, limits):
                return color or default
        return default

    def get_text(self):
        return self.text_format.format(self.progress)

    def get_text_color(self, progress=None):
        default = self.foreground or "ffffff"
        for limits, color in self.text_colors:
            if self._is_in_limits(progress or self.progress, limits):
                return color or default
        return default

    def get_progress_bar_color(self, progress=None):
        completed = self.foreground or "ffffff"
        remaining = self.background or "000000"
        for limits, colors in self.progress_bar_colors:
            if self._is_in_limits(progress or self.progress, limits):
                comp, rem = colors
                return (comp or completed, rem or remaining)
        return (completed, remaining)

    def get_progress_inner_color(self, progress=None):
        default = self.background or "000000"
        for limits, color in self.progress_inner_colors:
            if self._is_in_limits(progress or self.progress, limits):
                return color or default
        return default

    def is_update_required(self):
        return False

    def update(self):
        icon_config = dict(layout=self._icon_layout, text=self.get_icon(), colour=self.get_icon_color())
        text_config = dict(layout=self._text_layout, text=self.get_text(), colour=self.get_text_color())

        if self._icon_layout:
            self._update_layout(**icon_config)
        if self._text_layout:
            self._update_layout(**text_config)

        self._total_length = 0

        if self.show_progress_bar:
            self._total_length += self._progress_bar.width
            if not self.text_mode or self.text_mode == "without_icon":
                return
        else:
            self._total_length += self._icon_layout.width

        if self._text_layout.text and self.text_mode == "with_icon":
            self._total_length += (self._text_layout.width + self.text_offset + (self.padding_x * 2))

    def check_draw_call(self):
        if not self.is_update_required():
            # avoid unnecessary draw calls
            return

        old_length = self._total_length

        self.update()

        if not self._has_something_to_draw():
            # avoid unnecessary draw calls
            return

        if old_length != self._total_length:
            # draw entire bar when length changes
            return self.bar.draw()

        return self.draw()

    def loop(self):
        self.check_draw_call()
        self.timeout_add(self.timeout, self.loop)

    def draw_widget_elements(self):
        if self.show_progress_bar:
            completed, remaining = self.get_progress_bar_color()
            inner = self.get_progress_inner_color()
            self._progress_bar.draw(
                self.progress,
                thickness=float(self.progress_bar_thickness),
                completed=completed,
                remaining=remaining,
                inner=inner,
            )

        if not self.text_mode:
            # draw only the icon
            return self._draw_text_in_inner_circle(self._icon_layout)

        if self.text_mode == "without_icon":
            # replace icon with text
            return self._draw_text_in_inner_circle(self._text_layout)

        if self.text_mode != "with_icon":
            # invalid text mode
            return

        if self.show_progress_bar:
            # draw inside progress bar
            self._draw_text_in_inner_circle(self._icon_layout)
            text_start = self._progress_bar.width
        else:
            # draw icon by itself, without progress bar
            x, y = self.padding_x, (self.bar.height - self._icon_layout.height) / 2
            self._icon_layout.draw(x, y)
            text_start = self._icon_layout.width

        if not self._text_layout.text:
            return

        x, y = self.padding_x + text_start + self.text_offset, (self.bar.height - self._text_layout.height) / 2
        self._text_layout.draw(x, y)

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        self.draw_widget_elements()
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.width, height=self.height)
