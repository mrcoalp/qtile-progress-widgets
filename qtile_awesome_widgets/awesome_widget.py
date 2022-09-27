from .round_progress_bar import RoundProgressBar


class AwesomeWidget(RoundProgressBar):
    defaults = [
        ("font", "sans", "Default font"),
        ("fontsize", None, "Font size. Calculated if None."),
        ("fontshadow", None, "font shadow color, default is None(no shadow)"),
        ("markup", True, "Whether or not to use pango markup"),
        ("timeout", 1, "How often in seconds the widget refreshes."),
        ("show_progress_bar", True, "Whether to draw round progress bar."),
        ("icons", [], "Icons to present inside progress bar, based on progress limits."),
        ("icon_colors", [], "Icon color, based on progress limits."),
        ("icon_size", "", "Icon size. When empty, fontsize will be used."),
        ("text_mode", "", "Show text mode. Use 'with_icon' or 'without_icon'. Empty to not show."),
        ("text_format", "{:.0f}", "Format string to present text."),
        ("text_offset", 0, "Text offset. Negative values can be used to bring it closer to icon."),
        ("text_colors", [], "Text color, based on progress limits."),
    ]
    _progress = 0
    _icon_layout = None
    _text_layout = None
    _total_length = None

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(AwesomeWidget.defaults)

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

        if not self.text_mode or self.text_mode == "with_icon":
            self._icon_layout = create_layout(True)

        if self.text_mode in ["with_icon", "without_icon"]:
            self._text_layout = create_layout()

        self.update()

        if self.timeout <= 0:
            return

        self.timeout_add(self.timeout, self.loop)

    def _can_draw(self):
        if self.show_progress_bar:
            return True
        if self._icon_layout and self._icon_layout.text:
            return True
        if self._text_layout and self._text_layout.text:
            return True
        return False

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
        icon_config = dict(layout=self._icon_layout, text=self.get_icon(), colour=self.get_icon_color())
        text_config = dict(layout=self._text_layout, text=self.get_text(), colour=self.get_text_color())

        if self._icon_layout:
            self._update_layout(**icon_config)
        if self._text_layout:
            self._update_layout(**text_config)

        self._total_length = 0

        if self.show_progress_bar:
            self._total_length += super().calculate_length()
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

        if not self._can_draw():
            # avoid unnecessary draw calls
            return

        if old_length != self._total_length:
            # draw entire bar when length changes
            return self.bar.draw()

        return self.draw()

    def loop(self):
        self.check_draw_call()
        self.timeout_add(self.timeout, self.loop)

    def draw_text_in_inner_circle(self, layout):
        # relative to round progress bar attributes
        x = (self.prog_width - layout.width) / 2
        y = (self.prog_height - layout.height) / 2
        layout.draw(x, y)

    def draw_widget_elements(self):
        if self.show_progress_bar:
            self.draw_progress_bar(self._progress)

        if not self.text_mode:
            # draw only the icon
            return self.draw_text_in_inner_circle(self._icon_layout)

        if self.text_mode == "without_icon":
            # replace icon with text
            return self.draw_text_in_inner_circle(self._text_layout)

        if self.text_mode != "with_icon":
            # invalid text mode
            return

        text_start = super().calculate_length()

        if self.show_progress_bar:
            # draw inside progress bar
            self.draw_text_in_inner_circle(self._icon_layout)
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
