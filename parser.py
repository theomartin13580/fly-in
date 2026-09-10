from models import Connection, DroneMap, Zone, ZoneType

import re

_NB_DRONES_LINE = re.compile(r"^nb_drones:\s+(?P<value>\d+)\s*$")
_START_HUB_LINE = re.compile(
    r"^(?P<kind>start_hub|end_hub|hub):\s+(?P<name>\w+)\s+(?P<x>-?\d+)\s+(?P<y>-?\d+)"
    r"(?:\s+\[(?P<meta>.*)\])?\s*$"
)

_CONNECTION_LINE = re.compile(
    r"^connection:\s+(?P<a>[^\s\-]+)-(?P<b>[^\s\-]+)"
    r"(?:\s+\[(?P<meta>.*)\])?\s*$"
)


class ParserError(Exception):
    def __init__(self, no_line: int, error: str):
        super().__init__(f"line {no_line}: {error}")
        self.no_line = no_line
        self.error = error


class Parser:

    def _parse_meta(self, meta_str: str | None, line_no: int) -> dict[str, str]:
        if meta_str is None:
            return {}
        meta: dict[str, str] = {}
        for token in meta_str.split():
            parts = token.split("=")
            if len(parts) != 2:
                raise ParserError(
                    line_no, f"Invalid metadata token: {token!r}")
            meta[parts[0]] = parts[1]
        return meta

    def _parse_nb_drones(self, line: str, line_no: int) -> int:
        match = _NB_DRONES_LINE.match(line)
        if match is None:
            raise ParserError(
                line_no, f"Invalid nb_drones declaration: {line!r}")
        result = int(match.group("value"))
        if result <= 0:
            raise ParserError(
                line_no, f"Invalid number, numbers must be positive integers: {line!r}")
        return result

    def _parse_hub(self, line: str, line_no: int, drone_map: DroneMap) -> None:
        match = _START_HUB_LINE.match(line)
        if match is None:
            raise ParserError(line_no, f"Invalid hub declaration: {line!r}")
        kind = match.group("kind")
        name = match.group("name")
        x = match.group("x")
        y = match.group("y")
        meta = self._parse_meta(match.group("meta"), line_no)
        try:
            zone = Zone(
                name=name,
                x=int(x),
                y=int(y),
                zone_type=ZoneType(meta.get("zone", "normal")),
                color=meta.get("color"),
                max_drones=int(meta.get("max_drones", "1")),
                is_start=(kind == "start_hub"),
                is_end=(kind == "end_hub"),
            )
            drone_map.add_zone(zone)
        except Exception as e:
            raise ParserError(line_no, f" {e}: {line!r}")

    def _parse_connection(self, line: str, line_no: int, drone_map: DroneMap) -> None:
        match = _CONNECTION_LINE.match(line)
        if match is None:
            raise ParserError(
                line_no, f"Invalid connection declaration: {line!r}")
        zone_a = match.group("a")
        zone_b = match.group("b")
        meta = self._parse_meta(match.group("meta"), line_no)

        try:
            connection = Connection(
                zone_a=zone_a,
                zone_b=zone_b,
                max_link_capacity=int(meta.get("max_link_capacity", "1")),
            )
            drone_map.add_connection(connection)
        except Exception as e:
            raise ParserError(line_no, f"{e}: {line!r}")

    def parse_lines(self, lines: list[str]) -> DroneMap:
        drone_map: DroneMap | None = None
        line_no = 0

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.split('#', 1)[0]
            line = line.strip()

            if not line:
                continue

            if line.startswith("nb_drones"):
                nb_drones = self._parse_nb_drones(line, line_no)
                drone_map = DroneMap(nb_drones)
                continue

            if drone_map is None:
                raise ParserError(
                    line_no, f"Nb_drones bust be the first line : {line_no!r}")

            if line.startswith("connection"):
                self._parse_connection(line, line_no, drone_map)
            else:
                self._parse_hub(line, line_no, drone_map)

        if drone_map is None:
            raise ParserError(
                line_no, "No nb_drones declaration found in file")

        if drone_map.start_zone is None or drone_map.end_zone is None:
            raise ParserError(
                line_no, f"End and start zone is required: {line_no!r}")

        return drone_map

    def parse_file(self, path: str) -> DroneMap:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        return self.parse_lines(lines)
