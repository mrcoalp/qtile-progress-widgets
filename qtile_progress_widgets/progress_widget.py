import math

from libqtile import bar
from libqtile.confreader import ConfigError
from libqtile.pangocffi import markup_escape_text
from libqtile.widget import base

from .progress_bar import ProgressBar
from .utils import create_logger


_logger = create_logger("CORE")


class _LayoutHandler:
    def __init__(self, widget):
        self.widget = widget
        self.configured = False

    @property
    def width(self):
        if not self.configured:
            return 0
        return self.layout.width

    @property
    def height(self):
        if not self.configured:
            return 0
        return self.layout.height

    @property
    def text(self):
        if not self.configured:
            return ""
        return self.layout.text

    def configure(self, fontsize=None):
        # create text layout
        self.layout = self.widget.drawer.textlayout(
            "", "ffffff", self.widget.font, fontsize or self.widget.fontsize,
            self.widget.fontshadow, markup=self.widget.markup, wrap=self.widget.wrap
        )

        self.configured = True
        return self

    def update(self, params):
        if not self.configured:
            return

        for key, value in params.items():
            setattr(self.layout, key, value)

    def draw(self, x, y):
        if not self.configured:
            return

        self.layout.draw(x, y)

    def finalize(self):
        if not self.configured:
            return

        self.layout.finalize()


class _TextHandler(_LayoutHandler):
    def update(self):
        params = dict(
            text=self.widget.get_text(),
            colour=self.widget.get_text_color(),
        )
        super().update(params)


class _IconHandler(_LayoutHandler):
    def configure(self):
        return super().configure(self.widget.icon_size)

    def update(self):
        params = dict(
            text=self.widget.get_icon(),
            colour=self.widget.get_icon_color(),
        )
        super().update(params)


class ProgressCoreWidget(base._Widget, base.PaddingMixin):
    defaults = [
        ("font", "sans", "Default font"),
        ("fontsize", None, "Font size. Calculated if None."),
        ("fontshadow", None, "font shadow color, default is None(no shadow)"),
        ("markup", True, "Whether or not to use pango markup"),
        ("wrap", False, "Whether to wrap text."),
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
        if not "name" in config:
            config["name"] = "progress_" + self.__class__.__name__.lower()

        super().__init__(config.pop("width", bar.CALCULATED), **config)
        self.add_defaults(ProgressCoreWidget.defaults)

        self._icon_handler = None
        self.icon_active = False

        self._text_handler = None
        self.text_active = False

        self._progress_bar = None
        self._total_length = 0
        self.pending_update = True
        self.progress = 0

    @staticmethod
    def _is_in_limits(value, limits):
        lower, upper = limits
        if lower <= value <= upper:
            return True
        return False

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)

        if self.text_mode and self.text_mode not in ("with_icon", "without_icon"):
            raise ConfigError("Invalid text mode. Must either be None, '', 'with_icon' or 'without_icon'")

        self.icon_active = not self.text_mode or self.text_mode == "with_icon"
        self.text_active = self.text_mode in ("with_icon", "without_icon")

        size = self.oriented_size

        if self.fontsize is None:
            self.fontsize = size - size / 5

        if self.progress_bar_active:
            # forward global and user configs to progress bar, to ensure proper padding
            config = self.global_defaults.copy()
            config.update(self._user_config)
            self._progress_bar = ProgressBar(self.drawer, self.bar, size, size, self.progress_bar_thickness, **config)

        if self.icon_active:
            self._icon_handler = _IconHandler(self).configure()

        if self.text_active:
            self._text_handler = _TextHandler(self).configure()

        # update draw elements, still keeping pending update data
        # required for reconfigured widgets, upon a bar reconfigure
        # this call ensures newly created elements to update their states
        # to current widget state, since all content is dynamic
        self.update_draw_elements(reschedule=self.pending_update)

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

    def _draw_element_inside_bar(self, element, offset=0):
        """
        Draws provided element inside progress bar, when available. If bar is not active
        draws it at the start, accounting for padding.
        :return: Total drawn length.
        """

        if not element:
            return 0

        if self._progress_bar:
            # account for progress bar
            x = (self._progress_bar.total_width - element.width) / 2
            y = (self._progress_bar.height - element.height) / 2
            element.draw(x + offset, y)
            return self._progress_bar.total_width

        x, y = self._get_oriented_coords(element)
        element.draw(x + offset, y)
        return element.width + self.padding_x * 2

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

    def get_progress_bar_inner_color(self, progress=None):
        default = self.background or "000000"
        for limits, color in self.progress_bar_inner_colors:
            if self._is_in_limits(progress or self.progress, limits):
                return color or default
        return default

    def update(self):
        self.update_data()
        self.update_draw()

    def update_data(self):
        """
        To be overridden by derived widgets. Any required data should be updated
        in this method.
        """
        pass

    def update_draw(self):
        if not self.is_draw_update_required():
            return _logger.debug("skipping update on '%s'", self.name)
        self.update_draw_elements()
        self.draw_call()

    def is_draw_update_required(self):
        return True

    def update_draw_elements(self, reschedule=False):
        if self.progress_bar_active:
            completed, remaining = self.get_progress_bar_color()
            inner = self.get_progress_bar_inner_color()
            self._progress_bar.update(self.progress, completed, remaining, inner)

        if self.icon_active:
            self._icon_handler.update()

        if self.text_active:
            self._text_handler.update()

        self.pending_update = reschedule

    def update_draw_length(self):
        self._total_length = 0

        if self.progress_bar_active:
            self._total_length += self._progress_bar.total_width
            # we can return when text is to be drawn inside progress bar or
            # no text at all needs to be drawn
            # total length, in this case will be the widget of the progress bar
            if not self.text_mode or self.text_mode == "without_icon":
                return
        elif self.icon_active:
            # add icon width and its padding to total length
            self._total_length += self._icon_handler.width + self.padding_x * 2

        if self.text_active and self._text_handler.text:
            # add text width and offsets to total length
            self._total_length += self._text_handler.width + self.text_offset + self.padding_x * 2

    def draw_call(self):
        old_length = self._total_length

        self.update_draw_length()

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
        provide said elements. Those methods should return the length drawn,
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
            offset += self._draw_element_inside_bar(self._icon_handler, offset)
            return self.draw_after_elements(offset)

        if self.text_mode == "without_icon":
            # replace icon with text
            offset += self._draw_element_inside_bar(self._text_handler, offset)
            return self.draw_after_elements(offset)

        if self.text_mode != "with_icon":
            # invalid text mode
            return

        if self.progress_bar_active:
            # draw inside progress bar
            offset += self._draw_element_inside_bar(self._icon_handler, offset)
        elif self.icon_active:
            # draw icon by itself, without progress bar
            x, y = self._get_oriented_coords(self._icon_handler)
            self._icon_handler.draw(x + offset, y)
            offset += self._icon_handler.width + self.padding_x * 2

        offset += self.draw_between_elements(offset)

        if not self.text_active or not self._text_handler.text:
            return self.draw_after_elements(offset)

        x, y = self._get_oriented_coords(self._text_handler)
        self._text_handler.draw(x + self.text_offset + offset, y)
        self.draw_after_elements(offset + self._text_handler.width + self.padding_x * 2)

    def draw_oriented(self):
        self.drawer.ctx.save()
        if not self.bar.horizontal:
            # left bar reads bottom to top
            if self.bar.screen.left is self.bar:
                self.drawer.ctx.rotate(-90 * math.pi / 180.0)
                self.drawer.ctx.translate(-self.length, 0)
            # right bar is top to bottom
            else:
                self.drawer.ctx.translate(self.bar.width, 0)
                self.drawer.ctx.rotate(90 * math.pi / 180.0)
        self.draw_widget_elements()
        self.drawer.ctx.restore()

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        self.draw_oriented()
        self.drawer.draw(offsetx=self.offsetx, offsety=self.offsety, width=self.width, height=self.height)

    def finalize(self):
        if self.icon_active:
            self._icon_handler.finalize()
        if self.text_active:
            self._text_handler.finalize()
        return super().finalize()


class ProgressInFutureWidget(ProgressCoreWidget):
    def timer_setup(self):
        def on_done(update_data):
            try:
                update_data.result()
            except Exception:
                _logger.exception("update_data() raised exceptions, not rescheduling")

            try:
                self.update_draw()

                if self.update_interval is not None:
                    self.timeout_add(self.update_interval, self.timer_setup)
                else:
                    self.timer_setup()
            except Exception:
                _logger.exception("failed to reschedule.")

        self.future = self.qtile.run_in_executor(self.update_data)
        self.future.add_done_callback(on_done)
