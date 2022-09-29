import asyncio
import json

from dbus_next.constants import MessageType
from dbus_next.signature import Variant
from libqtile.utils import _send_dbus_message, add_signal_receiver

from .awesome_widget import AwesomeWidget
from .logger import create_logger

_logger = create_logger("GENERIC_PLAYER_ICON")


class GenericPlayerIcon(AwesomeWidget):
    defaults = [
        (
            "text_format",
            "<b>{xesam_title}</b> | {xesam_artist} | <i>{xesam_album}</i>",
            "Format string to present text."
        ),
        ("mpris_player", None, "MPRIS 2 compatible player identifier."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(GenericPlayerIcon.defaults)
        self.metadata = {}
        self.playback_status = "Stopped"
        self.playback_position = 0
        self._active = False
        self._state_change_pending = False

    async def _config_async(self):
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

        # listen to dbus appp state updates, to react when our client state changes
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

        self._check_draw_call_on_signal()

    def _on_name_owner_changed(self, name, _, new):
        if name != self.mpris_player:
            return

        self._active = len(new) > 0
        # to be handled on next update
        self._state_change_pending = True

        _logger.debug("%s changed state: %s", self.mpris_player, self._active)

        self._check_draw_call_on_signal()

    def _check_draw_call_on_signal(self):
        # when timeout is set, no action is required. handled in next loop tick
        if self.timeout > 0:
            return
        # else, we check for required draw call
        self.check_draw_call()

    def _update_metadata(self, metadata):
        self.metadata = {}
        for key, variant in metadata.items():
            value = variant.value
            # replace colons in key, to ease out the process of text formatting
            prop = key.replace(":", "_")
            if isinstance(value, list):
                value = "/".join((v for v in value if isinstance(v, str)))
            self.metadata[prop] = value if not isinstance(value, str) else self.escape_text(value)

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
        return self._state_change_pending or self._active

    def get_text(self):
        if not self._active or not self.metadata:
            return ""
        return self.text_format.format(**self.metadata)

    def update(self):
        # reset state change on update
        if self._state_change_pending:
            self._state_change_pending = False
        # clear data when player is not active
        if not self._active:
            self.progress = 0
            self.metadata = {}
        # refresh metadata when active
        if self._active and not self.metadata:
            asyncio.create_task(self._refresh_metadata(), name="qaw_gpq_refresh_metadata")
        # refresh playback progress when active and option enabled
        if self._active and self.show_progress_bar and "mpris_length" in self.metadata:
            asyncio.create_task(self._refresh_playback_progress(), name="qaw_gpi_refresh_playback_progress")
        # update widget
        super().update()
