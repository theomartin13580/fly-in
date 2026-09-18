"""Terminal output of a simulation log, plain or with ANSI colors."""

from models import DroneMap, ZoneType


class Renderer:
    """Print the turn-by-turn log of a simulation.

    ``render_plain`` writes the exact format required by the subject.
    ``render_visual`` adds turn numbers, the color of each zone and a
    short summary so the run is easier to follow in a terminal.
    """

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
        "white": (255, 255, 255),
        "black": (0, 0, 0),
    }
    _RAINBOW = ["red", "orange", "yellow", "lime", "blue", "violet"]
    _RESET = "\033[0m"
    _BOLD = "\033[1m"
    _DIM = "\033[2m"

    def __init__(self, drone_map: DroneMap) -> None:
        self.drone_map = drone_map

    def render_plain(self, log: list[str]) -> None:
        """Print one line per turn, exactly as required by the subject."""
        for line in log:
            print(line)

    def render_visual(self, log: list[str]) -> None:
        """Print a colored, numbered view of the log with a summary."""
        self._print_legend()
        for turn_no, line in enumerate(log, start=1):
            tokens = [self._colorize(token) for token in line.split()]
            print(f"{self._BOLD}Turn {turn_no:>3}{self._RESET}: "
                  + " ".join(tokens))
        self._print_summary(log)

    def _print_legend(self) -> None:
        """Print the zones with their color and type."""
        print(f"{self._BOLD}Zones{self._RESET}")
        for zone in self.drone_map.zones.values():
            tag = ""
            if zone.is_start:
                tag = " (start)"
            elif zone.is_end:
                tag = " (end)"
            elif zone.zone_type is not ZoneType.NORMAL:
                tag = f" ({zone.zone_type.value})"
            capacity = ""
            if not zone.unlimited and zone.max_drones > 1:
                capacity = f" x{zone.max_drones}"
            print(f"  {self._paint(zone.name, zone.color)}"
                  f"{self._DIM}{tag}{capacity}{self._RESET}")
        print()

    def _print_summary(self, log: list[str]) -> None:
        """Print the turn count and the secondary metrics."""
        moves = sum(len(line.split()) for line in log)
        turns = len(log)
        nb_drones = self.drone_map.nb_drones
        print()
        print(f"{self._BOLD}Summary{self._RESET}")
        print(f"  turns:           {turns}")
        print(f"  drones:          {nb_drones}")
        if turns:
            print(f"  moves per turn:  {moves / turns:.2f}")
        print(f"  moves per drone: {moves / nb_drones:.2f}")

    def _ansi(self, color: str) -> str:
        """Return the escape sequence setting a palette color."""
        r, g, b = self._PALETTE[color]
        return f"\033[38;2;{r};{g};{b}m"

    def _paint(self, text: str, color: str | None) -> str:
        """Wrap text in the escape codes of a color, if it is known."""
        if color is None:
            return text
        if color == "rainbow":
            return "".join(
                f"{self._ansi(self._RAINBOW[i % len(self._RAINBOW)])}{char}"
                for i, char in enumerate(text)
            ) + self._RESET
        if color in self._PALETTE:
            return f"{self._ansi(color)}{text}{self._RESET}"
        return text

    def _colorize(self, token: str) -> str:
        """Color a ``D<id>-<zone>`` token with the color of its zone."""
        zone = self.drone_map.zones.get(token.split("-")[-1])
        if zone is None:
            return token
        return self._paint(token, zone.color)
