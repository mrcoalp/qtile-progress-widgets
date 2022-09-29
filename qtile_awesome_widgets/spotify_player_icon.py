from .generic_player_icon import GenericPlayerIcon


class SpotifyPlayerIcon(GenericPlayerIcon):
    defaults = [
        ("icons", [
            ((0, 100), "\uf1bc"),
        ], "Icons to present inside progress bar, based on progress limits."),
        ("text_mode", "with_icon", "Show text mode. Use 'with_icon' or 'without_icon'. Empty to not show."),
        ("mpris_player", "org.mpris.MediaPlayer2.spotify", "MPRIS 2 compatible player identifier."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(SpotifyPlayerIcon.defaults)
