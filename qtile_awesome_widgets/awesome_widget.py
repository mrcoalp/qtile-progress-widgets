from libqtile.confreader import ConfigError

from .round_progress_bar import RoundProgressBar


class AwesomeWidget(RoundProgressBar):
    defaults = [
        ("font", "sans", "Default font"),
        ("fontsize", None, "Font size. Calculated if None."),
        ("timeout", 1, "How often in seconds the widget refreshes."),
        ("show_progress_bar", True, "Whether to draw round progress bar."),
        ("icons", [], "Icons to present inside progress bar, based on progress limits."),
        ("icon_colors", [], "Icon color, based on progress limits."),
        ("icon_size", "", "Icon size. When empty, fontsize will be used."),
        ("show_text", "", "Show text method. Use 'with_icon' or 'without_icon'. Empty to not show."),
        ("text_format", "{:.0f}", "Format string to present text."),
        ("text_offset", 0, "Text offset. Negative values can be used to bring it closer to icon."),
        ("text_colors", [], "Text color, based on progress limits."),
    ]
    _progress = 0

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(AwesomeWidget.defaults)

    @staticmethod
    def _is_in_limits(value, limits):
        lower, upper = limits
        if value >= lower and value <= upper:
            return True
        return False

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        self._total_length = super().calculate_length()
        if self.timeout <= 0:
            return
        self.timeout_add(self.timeout, self.loop)

    def calculate_length(self):
        return self._total_length

    def get_icon(self, progress=None):
        for limits, icon in self.icons:
            if self._is_in_limits(progress or self._progress, limits):
                return icon
        return ""

    def get_icon_color(self, progress=None):
        for limits, color in self.icon_colors:
            if self._is_in_limits(progress or self._progress, limits):
                return color
        return self.foreground or "ffffff"

    def get_text(self):
        return self.text_format.format(self._progress)

    def get_text_color(self, progress=None):
        for limits, color in self.text_colors:
            if self._is_in_limits(progress or self._progress, limits):
                return color
        return self.foreground or "ffffff"

    def is_update_required(self):
        return False

    def update(self):
        # avoid unnecessary draw calls
        if not self.is_update_required():
            return
        self.draw()

    def loop(self):
        self.update()
        self.timeout_add(self.timeout, self.loop)

    def draw_widget_elements(self, completed=None, remaining=None, inner_color=None):
        if self.show_progress_bar:
            self.draw_progress_bar(self._progress, completed, remaining)

        if inner_color:
            self.paint_inner_circle(inner_color)

        icon_config = [self.get_icon(), self.get_icon_color(), self.font, self.icon_size or self.fontsize]

        if not self.show_text:
            # draw only the icon
            return self.draw_text_in_inner_circle(*icon_config)

        if self.show_text not in ["with_icon", "without_icon"]:
            raise ConfigError("Invalid 'show_text' method. Must be either 'with_icon' or 'without_icon'")

        text_config = [self.get_text(), self.get_text_color(), self.font, self.fontsize]

        if self.show_text == "without_icon":
            # replace icon with text
            return self.draw_text_in_inner_circle(*text_config)

        text_start = super().calculate_length()

        if not self.show_progress_bar:
            # draw icon by itself, without progress bar
            icon = self.drawer.textlayout(*icon_config, None, wrap=False)
            x, y = self.padding_x, (self.bar.height - icon.height) / 2
            icon.draw(x, y)
            text_start = icon.width
        else:
            # draw inside progress bar
            self.draw_text_in_inner_circle(*icon_config)

        text = self.drawer.textlayout(*text_config, None, wrap=False)
        x, y = self.padding_x + text_start + self.text_offset, (self.bar.height - text.height) / 2
        text.draw(x, y)

        self._total_length = text_start + text.width + self.padding_x + self.text_offset

    def draw(self):
        raise ConfigError("Draw method not overridden by custom awesome widget.")
