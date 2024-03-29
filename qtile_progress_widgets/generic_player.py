import asyncio
import json

from dbus_next.constants import MessageType
from dbus_next.signature import Variant
from libqtile.confreader import ConfigError
from libqtile.utils import _send_dbus_message, add_signal_receiver

from .progress_widget import ProgressCoreWidget
from .utils import create_logger, get_cairo_image


_logger = create_logger("GENERIC_PLAYER_ICON")


class GenericPlayer(ProgressCoreWidget):
    defaults = [
        (
            "text_format",
            "<b>{xesam_title}</b> | {xesam_artist} | <i>{xesam_album}</i>",
            "Format string to present text."
        ),
        ("states_text", {
            "Playing": "\uf04c ",
            "Paused": "\uf04b ",
            "Stopped": "\uf04d ",
        }, "Text to prefix track info (or show inside progress bar), per player state."),
        (
            "states_inside_bar",
            False,
            "Whether or not to show states text inside progress bar. When false, states text is show as a prefix to the text."
        ),
        ("show_album_art", False, "Whether or not to show album art for the current playing track."),
        ("mpris_player", None, "MPRIS 2 compatible player identifier."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(GenericPlayer.defaults)
        self.metadata = {}
        self.playback_status = "Stopped"
        self.playback_position = 0
        self._active = False
        self._album_art_image = None
        self.add_callbacks({
            "Button1": self.cmd_play_pause,
            "Button4": self.cmd_next,
            "Button5": self.cmd_previous,
        })

    async def _config_async(self):
        if self.mpris_player is None:
            raise ConfigError("a mpris player must be provided in order to use widget")

        # listen to player updates
        sub = await add_signal_receiver(
            lambda msg: asyncio.create_task(self._on_properties_changed(*msg.body)),
            session_bus=True,
            signal_name="PropertiesChanged",
            bus_name=self.mpris_player,
            path="/org/mpris/MediaPlayer2",
            dbus_interface="org.freedesktop.DBus.Properties",
        )
        if not sub:
            _logger.warning("Failed to add 'PropertiesChanged' signal to %s", self.mpris_player)

        # listen to dbus app state updates, to react when our client state changes
        sub = await add_signal_receiver(
            lambda msg: asyncio.create_task(self._on_name_owner_changed(*msg.body)),
            session_bus=True,
            signal_name="NameOwnerChanged",
            dbus_interface="org.freedesktop.DBus",
        )
        if not sub:
            _logger.warning("Failed to add 'NameOwnerChanged' signal to %s", self.mpris_player)

    def _on_properties_changed(self, _, updated, __):
        if not self.configured:
            return

        if "Metadata" in updated:
            self._update_metadata(updated["Metadata"].value)

        if "PlaybackStatus" in updated:
            self.playback_status = updated["PlaybackStatus"].value

        self._active = True

        data = json.dumps(self.metadata, indent=2)
        _logger.debug("%s updated:\nDATA: %s\nSTATUS: %s", self.mpris_player, data, self.playback_status)

        self._check_refresh_on_signal()

    def _on_name_owner_changed(self, name, _, new):
        if name != self.mpris_player:
            return

        self._active = len(new) > 0
        self.pending_update = True

        _logger.debug("%s changed state: %s", self.mpris_player, self._active)

        self._check_refresh_on_signal()

    async def _send_command(self, interface, cmd, signature="", *args):
        bus, message = await _send_dbus_message(
            True,
            MessageType.METHOD_CALL,
            self.mpris_player,
            interface,
            "/org/mpris/MediaPlayer2",
            cmd,
            signature,
            list(args),
        )
        if bus:
            bus.disconnect()

        if message.message_type != MessageType.METHOD_RETURN:
            _logger.warning("%s: failed to send cmd '%s' on interface: '%s'.", self.mpris_player, cmd, interface)
            return None
        if message.body:
            return message.body[0].value
        return None

    def _check_refresh_on_signal(self):
        # when timeout is set, no action is required. handled in next loop tick
        if self.update_interval > 0:
            return
        # else, we check for required draw call
        self.update()

    def _update_metadata(self, metadata):
        self.metadata = {}
        for key, variant in metadata.items():
            value = variant.value
            # replace colons in key, to ease out the process of text formatting
            prop = key.replace(":", "_")
            if isinstance(value, list):
                value = "/".join((v for v in value if isinstance(v, str)))
            self.metadata[prop] = value if not isinstance(value, str) else self.escape_text(value)

        if self.show_album_art and "mpris_artUrl" in self.metadata:
            self._album_art_image = None
            asyncio.create_task(self._fetch_album_art(), name="qpw_gpi_fetch_art")

    async def _fetch_album_art(self):
        art_url = self.metadata["mpris_artUrl"]
        if not art_url:
            return
        try:
            img = get_cairo_image(art_url)
            img.resize(height=self.oriented_size - self.padding * 2)
            self._album_art_image = img
        except Exception as e:
            _logger.error(str(e))

    async def _refresh_metadata(self):
        data = {
            "Metadata": Variant("a{sv}", await self.get_player_property("Metadata")),
            "PlaybackStatus": Variant("s", await self.get_player_property("PlaybackStatus")),
        }
        self._on_properties_changed(None, data, None)

    async def _refresh_playback_progress(self):
        self.playback_position = await self.get_player_property("Position") or 0
        length = self.metadata["mpris_length"]
        # ensure length is not 0, to avoid division by zero
        self.progress = length and float(self.playback_position / length * 100) or 0

    def _player_cmd(self, cmd, signature="", *args):
        if self.mpris_player is None:
            return
        asyncio.create_task(self._send_command("org.mpris.MediaPlayer2.Player", cmd, signature, *args))

    def _get_album_art_length(self):
        if not self._active:
            return 0
        if not self.show_album_art or not self._album_art_image:
            return 0
        return self._album_art_image.width + self.padding_x * 2

    async def get_player_property(self, property):
        return await self._send_command("org.freedesktop.DBus.Properties", "Get", "ss", "org.mpris.MediaPlayer2.Player", property)

    def calculate_length(self):
        return super().calculate_length() + self._get_album_art_length()

    def get_text(self):
        if not self._active or not self.metadata:
            return ""
        if self.states_inside_bar:
            return self.text_format.format(**self.metadata)
        states_text = self.states_text or {}
        return states_text.get(self.playback_status, "") + self.text_format.format(**self.metadata)

    def get_icon(self, progress=None):
        icon = super().get_icon(progress)
        if not self.states_inside_bar:
            return icon
        states_text = self.states_text or {}
        return states_text.get(self.playback_status, icon)

    def update_data(self):
        # clear data when player is not active
        if not self._active and (self.progress or self.metadata):
            self.progress = 0
            self.metadata = {}
            self.playback_status = "Stopped"
        # refresh metadata when active
        if self._active and not self.metadata:
            asyncio.create_task(self._refresh_metadata(), name="refresh_metadata")
        # refresh playback progress when active and option enabled
        if self._active and self.progress_bar_active and "mpris_length" in self.metadata:
            asyncio.create_task(self._refresh_playback_progress(), name="refresh_playback_progress")

    def is_draw_update_required(self):
        return self.pending_update or self._active

    def draw_between_elements(self, offset=0):
        if not self._active:
            return 0
        if not self.show_album_art or not self._album_art_image:
            return 0
        self.drawer.ctx.save()
        self.drawer.ctx.translate(offset + self.padding_x, self.padding)
        self.drawer.ctx.set_source(self._album_art_image.pattern)
        self.drawer.ctx.paint()
        self.drawer.ctx.restore()
        return self._get_album_art_length()

    def cmd_next(self):
        self._player_cmd("Next")

    def cmd_previous(self):
        self._player_cmd("Previous")

    def cmd_pause(self):
        self._player_cmd("Pause")

    def cmd_play_pause(self):
        self._player_cmd("PlayPause")

    def cmd_stop(self):
        self._player_cmd("Stop")

    def cmd_play(self):
        self._player_cmd("Play")

    def cmd_seek(self, offset):
        # offset in microseconds
        self._player_cmd("Seek", "x", offset)

    def cmd_set_position(self, track_id, position):
        # position in microseconds
        self._player_cmd("SetPosition", "ox", track_id, position)

    def cmd_open_url(self, url):
        self._player_cmd("OpenUrl", "s", url)
