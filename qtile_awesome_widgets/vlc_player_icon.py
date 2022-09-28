from .generic_player_icon import GenericPlayerIcon


class VLCPlayerIcon(GenericPlayerIcon):
    defaults = [
        ("icons", [
            ((0, 100), "\ufa7b"),
        ], "Icons to present inside progress bar, based on progress limits."),
        ("text_mode", "with_icon", "Show text mode. Use 'with_icon' or 'without_icon'. Empty to not show."),
        ("text_format", "{url}", "Format string to present text."),
        ("mpris_player", "org.mpris.MediaPlayer2.vlc", "MPRIS 2 compatible player identifier."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(VLCPlayerIcon.defaults)
