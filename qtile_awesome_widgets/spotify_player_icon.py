from .generic_player_icon import GenericPlayerIcon


class SpotifyPlayerIcon(GenericPlayerIcon):
    defaults = [
        ("icons", [
            ((0, 100), "\uf1bc"),
        ], "Icons to present inside progress bar, based on progress limits."),
        ("text_mode", "with_icon", "Show text mode. Use 'with_icon' or 'without_icon'. Empty to not show."),
        ("states_text", {
            "Playing": "\uf04c",
            "Paused": "\uf04b",
            "Stopped": "\uf1bc",
        }, "Text to prefix track info (or show inside progress bar), per player state."),
        (
            "states_inside_bar",
            True,
            "Whether or not to show states text inside progress bar. When false, states text is show as a prefix to the text."
        ),
        ("show_album_art", True, "Whether or not to show album art for the current playing track."),
        ("mpris_player", "org.mpris.MediaPlayer2.spotify", "MPRIS 2 compatible player identifier."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(SpotifyPlayerIcon.defaults)
