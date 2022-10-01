import math

from libqtile import bar
from libqtile.confreader import ConfigError
from libqtile.pangocffi import markup_escape_text
from libqtile.widget import base

from .progress_bar import ProgressBar
from .utils import create_logger


_logger = create_logger("CORE")


class ProgressCoreWidget(base._Widget, base.PaddingMixin):
    defaults = [
        ("font", "sans", "Default font"),
        ("fontsize", None, "Font size. Calculated if None."),
        ("fontshadow", None, "font shadow color, default is None(no shadow)"),
        ("markup", True, "Whether or not to use pango markup"),
        ("foreground", "ffffff", "Foreground colour"),
        ("update_interval", 1, "How often in seconds the widget refreshes."),
        ("progress_bar_active", True, "Whether to draw round progress bar."),
        ("progress_bar_colors", [], "Progress bar colors for each specified limit."),
        ("progress_bar_inner_colors", [], "Progress inner color for each specified limit."),
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
        self.add_defaults(ProgressCoreWidget.defaults)
        self.progress = 0
        self._icon_layout = None
        self._text_layout = None
        self._progress_bar = None
        self._total_length = 0

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

        if self.text_mode and self.text_mode not in ("with_icon", "without_icon"):
            raise ConfigError("Invalid text mode. Must either be None, 'with_icon' or 'without_icon'")

        size = self.oriented_size

        if self.fontsize is None:
            self.fontsize = size - size / 5

        def create_layout(icon=False):
            fontsize = icon and self.icon_size or self.fontsize
            return self.drawer.textlayout("", "ffffff", self.font, fontsize, self.fontshadow, markup=self.markup)

        if self.progress_bar_active:
            # forward global and user configs to progress bar, to ensure proper padding
            config = self.global_defaults.copy()
            config.update(self._user_config)
            self._progress_bar = ProgressBar(self.drawer, self.bar, size, size, self.progress_bar_thickness, **config)

        if not self.text_mode or self.text_mode == "with_icon":
            self._icon_layout = create_layout(True)

        if self.text_mode in ("with_icon", "without_icon"):
            self._text_layout = create_layout()

    def timer_setup(self):
        try:
            if self.configured:
                self.update()
        except Exception as e:
            _logger.exception("exception in timer loop: %s", str(e))

        if self.update_interval:
            self.timeout_add(self.update_interval, self.timer_setup)

    def calculate_length(self):
        return self._total_length

    @property
    def oriented_size(self):
        return self.bar.horizontal and self.bar.height or self.bar.width

    def _get_oriented_coords(self, layout):
        return self.padding_x, (self.oriented_size - layout.height) / 2

    def _draw_text_inside_bar(self, layout, offset=0):
        """
        Draws provided layout inside progress bar, when available. If bar is not active
        draws it at the start, accounting for padding.
        :return: Total drawn length.
        """

        if not layout:
            return 0

        if self._progress_bar:
            # account for progress bar
            x = (self._progress_bar.total_width - layout.width) / 2
            y = (self._progress_bar.height - layout.height) / 2
            layout.draw(x + offset, y)
            return self._progress_bar.total_width

        x, y = self._get_oriented_coords(layout)
        layout.draw(x + offset, y)
        return layout.width + self.padding_x * 2

    def escape_text(self, text):
        if not self.markup:
            return text
        return markup_escape_text(text)

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
        for limits, color in self.progress_bar_inner_colors:
            if self._is_in_limits(progress or self.progress, limits):
                return color or default
        return default

    def update_data(self):
        """
        To be overridden by derived widgets. Any required data should be updated
        in this method. Make sure to defer heavy tasks, in order to prevent
        blocking.
        """
        pass

    def update_draw_elements(self):
        if self.progress_bar_active:
            completed, remaining = self.get_progress_bar_color()
            inner = self.get_progress_inner_color()
            self._progress_bar.update(self.progress, completed, remaining, inner)

        if self._icon_layout:
            self._update_layout(self._icon_layout, text=self.get_icon(), colour=self.get_icon_color())

        if self._text_layout:
            self._update_layout(self._text_layout, text=self.get_text(), colour=self.get_text_color())

    def is_update_required(self):
        return True

    def update(self):
        if not self.is_update_required():
            return _logger.debug("skipping update on '%s'", self.__class__.__name__)
        self.update_data()
        self.update_draw_elements()
        self.check_draw_call()

    def update_length(self):
        self._total_length = 0

        if self.progress_bar_active:
            self._total_length += self._progress_bar.total_width
            # we can return when text is to be drawn inside progress bar or
            # no text at all needs to be drawn
            # total length, in this case will be the widgt of the progress bar
            if not self.text_mode or self.text_mode == "without_icon":
                return
        elif self._icon_layout:
            # add icon width and its padding to total length
            self._total_length += self._icon_layout.width + self.padding_x * 2

        if self._text_layout and self._text_layout.text:
            # add text width and offsets to total length
            self._total_length += self._text_layout.width + self.text_offset + self.padding_x * 2

    def check_draw_call(self):
        old_length = self._total_length

        self.update_length()

        if old_length != self._total_length:
            # draw entire bar when length changes
            return self.bar.draw()

        return self.draw()

    def draw_before_elements(self):
        return 0

    def draw_between_elements(self, offset=0):
        return 0

    def draw_after_elements(self, offset=0):
        return 0

    def draw_widget_elements(self):
        """
        Derived widgets can add custom elements, besides the ones defined
        here. The draw_(before|between|after)_elements methods can be overridden to
        provide said elemets. Those methods should return the length drawn,
        to provide an offset for the rest of the elements.
        Widgets can end up with something like:

            | before | icon_and_or_progress | between | text | after |

        Note that all of these elements are optional.
        """

        offset = self.draw_before_elements()

        if self.progress_bar_active:
            self._progress_bar.draw_with_current_data(offset)

        if not self.text_mode:
            # draw only the icon
            offset += self._draw_text_inside_bar(self._icon_layout, offset)
            return self.draw_after_elements(offset)

        if self.text_mode == "without_icon":
            # replace icon with text
            offset += self._draw_text_inside_bar(self._text_layout, offset)
            return self.draw_after_elements(offset)

        if self.text_mode != "with_icon":
            # invalid text mode
            return

        if self.progress_bar_active:
            # draw inside progress bar
            offset += self._draw_text_inside_bar(self._icon_layout, offset)
        elif self._icon_layout:
            # draw icon by itself, without progress bar
            x, y = self._get_oriented_coords(self._icon_layout)
            self._icon_layout.draw(x + offset, y)
            offset += self._icon_layout.width + self.padding_x * 2

        offset += self.draw_between_elements(offset)

        if not self._text_layout or not self._text_layout.text:
            return self.draw_after_elements(offset)

        x, y = self._get_oriented_coords(self._text_layout)
        x += self.text_offset + offset
        self._text_layout.draw(x, y)
        self.draw_after_elements(offset + self._text_layout.width + self.padding_x * 2)

    def draw_oriented(self):
        self.drawer.ctx.save()
        if not self.bar.horizontal:
            # Left bar reads bottom to top
            if self.bar.screen.left is self.bar:
                self.drawer.ctx.rotate(-90 * math.pi / 180.0)
                self.drawer.ctx.translate(-self.length, 0)
            # Right bar is top to bottom
            else:
                self.drawer.ctx.translate(self.bar.width, 0)
                self.drawer.ctx.rotate(90 * math.pi / 180.0)
        self.draw_widget_elements()
        self.drawer.ctx.restore()

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        self.draw_oriented()
        self.drawer.draw(offsetx=self.offsetx, offsety=self.offsety, width=self.width, height=self.height)
