from models import DroneMap

class Renderer:
    _COLOR_CODES: dict[str, str] = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "gray": "\033[90m",
        "cyan": "\033[36m",
        "magenta": "\033[35m",
    }
    _RESET = "\033[0m"

    def render(self, log: list[str], drone_map: DroneMap) -> None:
        for turn_no, line in enumerate(log, start=1):
            colored_tokens = [self._colorize(token, drone_map) for token in line.split()]
            joined = " ".join(colored_tokens)
            print(f"Tour {turn_no}: {joined}")

    def _colorize(self, token: str, drone_map: DroneMap) -> str:
        zone_name = token.split("-")[-1]
        zone = drone_map.zones.get(zone_name)
        if zone and zone.color and zone.color in self._COLOR_CODES:
            return f"{self._COLOR_CODES[zone.color]}{token}{self._RESET}"
        else:
            return token

