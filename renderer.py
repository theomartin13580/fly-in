from models import DroneMap


class Renderer:
    _PALETTE: dict[str, tuple[int, int, int]] = {
        "red": (255, 0, 0),
        "crimson": (220, 20, 60),
        "darkred": (139, 0, 0),
        "maroon": (128, 0, 0),
        "brown": (165, 42, 42),
        "orange": (255, 165, 0),
        "gold": (255, 215, 0),
        "yellow": (255, 255, 0),
        "lime": (0, 255, 0),
        "green": (0, 128, 0),
        "cyan": (0, 255, 255),
        "blue": (0, 0, 255),
        "purple": (128, 0, 128),
        "violet": (238, 130, 238),
        "magenta": (255, 0, 255),
        "gray": (128, 128, 128),
        "black": (0, 0, 0),
    }
    _RAINBOW = ["red", "orange", "yellow", "lime", "blue", "violet"]
    _RESET = "\033[0m"

    def render(self, log: list[str], drone_map: DroneMap) -> None:
        for turn_no, line in enumerate(log, start=1):
            colored_tokens = [self._colorize(
                token, drone_map) for token in line.split()]
            joined = " ".join(colored_tokens)
            print(f"Tour {turn_no}: {joined}")

    def _ansi(self, color: str) -> str:
        r, g, b = self._PALETTE[color]
        return f"\033[38;2;{r};{g};{b}m"

    def _colorize(self, token: str, drone_map: DroneMap) -> str:
        zone_name = token.split("-")[-1]
        zone = drone_map.zones.get(zone_name)
        if zone is None or zone.color is None:
            return token
        if zone.color == "rainbow":
            colored = [
                f"{self._ansi(self._RAINBOW[i % len(self._RAINBOW)])}{char}"
                for i, char in enumerate(token)
            ]
            return "".join(colored) + self._RESET
        if zone.color in self._PALETTE:
            return f"{self._ansi(zone.color)}{token}{self._RESET}"
        return token
