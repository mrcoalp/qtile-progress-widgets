import asyncio

from dbus_next.constants import MessageType
from dbus_next.signature import Variant
from libqtile.utils import _send_dbus_message, add_signal_receiver

from .awesome_widget import AwesomeWidget
from .logger import create_logger


_logger = create_logger("GENERIC_PLAYER_ICON")


class GenericPlayerIcon(AwesomeWidget):
    defaults = [
        ("text_format", "<b>{title}</b> | {artist} | <i>{album}</i>", "Format string to present text."),
        ("mpris_player", None, "MPRIS 2 compatible player identifier."),
        ("track_playback_progress", True, "Whether or not to track playback progress."),
        ("track_player_state", True, "Whether or not to listen to app state changes. Use it to update widget when app closes and opens."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(GenericPlayerIcon.defaults)
        self.metadata = {}
        self.track_info = {}
        self.playback_status = "Stopped"
        self.playback_position = 0
        self._active = False

    async def _config_async(self):
        subscribe = await add_signal_receiver(
            lambda msg: asyncio.create_task(self._update_properties_changed(*msg.body)),
            session_bus=True,
            signal_name="PropertiesChanged",
            bus_name=self.mpris_player,
            path="/org/mpris/MediaPlayer2",
            dbus_interface="org.freedesktop.DBus.Properties",
        )
        if not subscribe:
            _logger.warning("Failed to add 'PropertiesChanged' signal to %s", self.mpris_player)

        if self.track_player_state:
            subscribe = await add_signal_receiver(
                lambda msg: asyncio.create_task(self._update_player_state(*msg.body)),
                session_bus=True,
                signal_name="NameOwnerChanged",
                dbus_interface="org.freedesktop.DBus",
            )
            if not subscribe:
                _logger.warning("Failed to add 'NameOwnerChanged' signal to %s", self.mpris_player)

    def _update_player_state(self, name, _, new):
        if name != self.mpris_player:
            return
        self._active = len(new) > 0
        self.update()

    def _update_properties_changed(self, _, updated, __):
        if not self.configured:
            return
        if "Metadata" in updated:
            self._update_track_info(updated["Metadata"].value)
        if "PlaybackStatus" in updated:
            self.playback_status = updated["PlaybackStatus"].value
        self._active = True

        # data = ["%s - %s" % (key, value) for key, value in self.metadata.items()]
        # info = ["%s - %s" % (key, value) for key, value in self.track_info.items()]
        #
        # _logger.debug("Received updated properties:\nMETADATA\n\t%s\nINFO\n\t%s\nSTATUS\n\t%s",
        #               "\n\t".join(data), "\n\t".join(info), self.playback_status)

    def _update_track_info(self, metadata):
        self.metadata = {}
        self.track_info = {}

        for key, variant in metadata.items():
            value = variant.value
            if not key.startswith("xesam:"):
                self.metadata[key] = value
                continue
            prop = key.split(":")[1]
            if isinstance(value, list):
                value = "/".join((v for v in value if isinstance(v, str)))
            self.track_info[prop] = value if not isinstance(value, str) else self.escape_text(value)

    async def _refresh_metadata(self):
        data = {
            "Metadata": Variant("a{sv}", await self.get_player_property("Metadata")),
            "PlaybackStatus": Variant("s", await self.get_player_property("PlaybackStatus")),
        }
        self._update_properties_changed(None, data, None)

    async def _refresh_playback_progress(self):
        position = await self.get_player_property("Position")
        self.playback_position = position or 0

    async def get_player_property(self, property):
        bus, message = await _send_dbus_message(
            True,
            MessageType.METHOD_CALL,
            self.mpris_player,
            "org.freedesktop.DBus.Properties",
            "/org/mpris/MediaPlayer2",
            "Get",
            "ss",
            ["org.mpris.MediaPlayer2.Player", property],
        )

        if bus:
            bus.disconnect()

        if message.message_type != MessageType.METHOD_RETURN:
            _logger.warning("Failed to retrieve '%s' of player %s.", property, self.mpris_player)
            return None

        return message.body[0].value

    def is_update_required(self):
        return self._active or not self.track_player_state

    def get_text(self):
        if not self._active or not self.track_info:
            return ""
        return self.text_format.format(**self.track_info)

    def update(self):
        self.progress = 0
        if self._active and not self.metadata:
            asyncio.create_task(self._refresh_metadata(), name="qaw_gpq_refresh_metadata")
        if self._active and self.track_playback_progress and "mpris:length" in self.metadata:
            asyncio.create_task(self._refresh_playback_progress(), name="qaw_gpi_refresh_playback_progress")
            length = self.metadata["mpris:length"]
            self.progress = length and float(self.playback_position / length * 100) or 0
        super().update()
