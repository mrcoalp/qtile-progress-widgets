import asyncio

from dbus_next import Message, Variant
from dbus_next.constants import MessageType
from libqtile.log_utils import logger
from libqtile.utils import _send_dbus_message, add_signal_receiver

from .awesome_widget import AwesomeWidget


class GenericPlayerIcon(AwesomeWidget):
    defaults = [
        ("mpris_player", "org.mpris.MediaPlayer2.spotify", "MPRIS 2 compatible player identifier."),
        ("progress_seek", True, "Whether or not to track progress."),
        ("text_format", "<b>{title}</b> | {artist} | <i>{album}</i>", "Format string to present text."),
    ]
    metadata = {}
    track_info = {}
    playback_status = "Stopped"
    _active = False

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(GenericPlayerIcon.defaults)

    async def _config_async(self):
        subscribe = await add_signal_receiver(
            lambda msg: asyncio.create_task(self._parse_properties_changed(*msg.body)),
            session_bus=True,
            signal_name="PropertiesChanged",
            bus_name=self.mpris_player,
            path="/org/mpris/MediaPlayer2",
            dbus_interface="org.freedesktop.DBus.Properties",
        )

        if not subscribe:
            logger.warning("Unable to add signal receiver for Mpris2 players")

    def _parse_properties_changed(self, _, updated, __):
        if not self.configured:
            return
        if "Metadata" in updated:
            self._update_track_info(updated["Metadata"].value)
        if "PlaybackStatus" in updated:
            self.playback_status = updated["PlaybackStatus"].value
        self._active = True

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
                self.track_info[prop] = "/".join((v for v in value if isinstance(v, str)))
            else:
                self.track_info[prop] = value

    def is_update_required(self):
        return self._active

    def get_text(self):
        if not self._active or not self.track_info:
            return ""
        return self.text_format.format(**self.track_info)

    def update(self):
        return super().update()
