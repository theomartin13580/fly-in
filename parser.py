"""Parser of the map file format described in the subject.

A map file starts with ``nb_drones: <n>``, then declares zones with
``start_hub:``, ``end_hub:`` and ``hub:`` lines, and edges with
``connection:`` lines. Everything after ``#`` is a comment.
"""

import re

from models import Connection, DroneMap, Zone, ZoneType

_NAME = r"[^\s\-\[\]]+"
_NB_DRONES_LINE = re.compile(r"^nb_drones:\s+(?P<value>\S+)\s*$")
_HUB_LINE = re.compile(
    rf"^(?P<kind>start_hub|end_hub|hub):\s+(?P<name>{_NAME})"
    r"\s+(?P<x>-?[0-9]+)\s+(?P<y>-?[0-9]+)"
    r"(?:\s+\[(?P<meta>[^\[\]]*)\])?\s*$"
)
_CONNECTION_LINE = re.compile(
    rf"^connection:\s+(?P<a>{_NAME})-(?P<b>{_NAME})"
    r"(?:\s+\[(?P<meta>[^\[\]]*)\])?\s*$"
)
_HUB_KINDS = ("start_hub", "end_hub", "hub")
_HUB_META_KEYS = frozenset({"zone", "color", "max_drones"})
_CONNECTION_META_KEYS = frozenset({"max_link_capacity"})


class ParserError(Exception):
    """Error raised when a map file is malformed.

    Attributes:
        line_no: Number of the faulty line (1-based, 0 when unknown).
        reason: Human readable cause of the error.
    """

    def __init__(self, line_no: int, reason: str) -> None:
        super().__init__(f"line {line_no}: {reason}")
        self.line_no = line_no
        self.reason = reason


class Parser:
    """Turn the lines of a map file into a DroneMap."""

    def parse_file(self, path: str) -> DroneMap:
        """Read and parse a map file.

        Raises:
            ParserError: If the file cannot be read or is malformed.
        """
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            raise ParserError(0, f"cannot read {path!r}: {e.strerror}")
        except UnicodeDecodeError:
            raise ParserError(0, f"{path!r} is not a UTF-8 text file")
        return self.parse_lines(lines)

    def parse_lines(self, lines: list[str]) -> DroneMap:
        """Parse the lines of a map.

        Raises:
            ParserError: On the first malformed line.
        """
        drone_map: DroneMap | None = None
        line_no = 0
        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            kind = line.split(":", 1)[0]
            if kind == "nb_drones":
                if drone_map is not None:
                    raise ParserError(
                        line_no, "nb_drones is declared more than once")
                drone_map = DroneMap(self._parse_nb_drones(line, line_no))
            elif drone_map is None:
                raise ParserError(
                    line_no, "the first line must be 'nb_drones: <number>'")
            elif kind == "connection":
                self._parse_connection(line, line_no, drone_map)
            elif kind in _HUB_KINDS:
                self._parse_hub(line, line_no, drone_map)
            else:
                raise ParserError(
                    line_no, f"unknown declaration {line!r} (expected "
                    "start_hub:, end_hub:, hub: or connection:)")

        if drone_map is None:
            raise ParserError(line_no, "no nb_drones declaration found")
        if drone_map.start_zone is None:
            raise ParserError(line_no, "missing start_hub declaration")
        if drone_map.end_zone is None:
            raise ParserError(line_no, "missing end_hub declaration")
        return drone_map

    def _parse_nb_drones(self, line: str, line_no: int) -> int:
        """Parse the ``nb_drones: <n>`` line."""
        match = _NB_DRONES_LINE.match(line)
        if match is None:
            raise ParserError(
                line_no, f"invalid nb_drones declaration {line!r} "
                "(expected 'nb_drones: <number>')")
        return self._positive_int(match.group("value"), "nb_drones", line_no)

    def _parse_hub(
        self, line: str, line_no: int, drone_map: DroneMap
    ) -> None:
        """Parse a ``start_hub:``, ``end_hub:`` or ``hub:`` line."""
        match = _HUB_LINE.match(line)
        if match is None:
            raise ParserError(
                line_no, f"invalid zone declaration {line!r} "
                "(expected '<kind>: <name> <x> <y> [metadata]')")
        kind = match.group("kind")
        is_start = kind == "start_hub"
        is_end = kind == "end_hub"
        meta = self._parse_meta(match.group("meta"), _HUB_META_KEYS, line_no)

        type_name = meta.get("zone", "normal")
        try:
            zone_type = ZoneType(type_name)
        except ValueError:
            raise ParserError(
                line_no, f"unknown zone type {type_name!r} (allowed: "
                + ", ".join(t.value for t in ZoneType) + ")")
        if zone_type is ZoneType.BLOCKED and (is_start or is_end):
            raise ParserError(line_no, f"{kind} cannot be a blocked zone")

        max_drones = 1
        if "max_drones" in meta and not (is_start or is_end):
            max_drones = self._positive_int(
                meta["max_drones"], "max_drones", line_no)

        zone = Zone(
            name=match.group("name"),
            x=int(match.group("x")),
            y=int(match.group("y")),
            zone_type=zone_type,
            color=meta.get("color"),
            max_drones=max_drones,
            is_start=is_start,
            is_end=is_end,
        )
        try:
            drone_map.add_zone(zone)
        except ValueError as e:
            raise ParserError(line_no, str(e))

    def _parse_connection(
        self, line: str, line_no: int, drone_map: DroneMap
    ) -> None:
        """Parse a ``connection: <a>-<b> [metadata]`` line."""
        match = _CONNECTION_LINE.match(line)
        if match is None:
            raise ParserError(
                line_no, f"invalid connection declaration {line!r} "
                "(expected 'connection: <zone1>-<zone2> [metadata]')")
        zone_a = match.group("a")
        zone_b = match.group("b")
        for name in (zone_a, zone_b):
            if name not in drone_map.zones:
                raise ParserError(
                    line_no, f"connection refers to undefined zone {name!r} "
                    "(zones must be declared before the connections "
                    "using them)")
        if zone_a == zone_b:
            raise ParserError(
                line_no, f"a zone cannot be connected to itself: {zone_a!r}")
        meta = self._parse_meta(
            match.group("meta"), _CONNECTION_META_KEYS, line_no)

        capacity = 1
        if "max_link_capacity" in meta:
            capacity = self._positive_int(
                meta["max_link_capacity"], "max_link_capacity", line_no)
        try:
            drone_map.add_connection(Connection(zone_a, zone_b, capacity))
        except ValueError as e:
            raise ParserError(line_no, str(e))

    def _parse_meta(
        self, meta_str: str | None, allowed: frozenset[str], line_no: int
    ) -> dict[str, str]:
        """Parse the ``key=value`` tokens of a metadata block.

        Args:
            meta_str: Text found between the brackets, or None.
            allowed: Keys accepted for this kind of line.
            line_no: Line number, used in error messages.

        Returns:
            The metadata as a dictionary.

        Raises:
            ParserError: On a malformed token or an unknown or
                duplicated key.
        """
        meta: dict[str, str] = {}
        if meta_str is None:
            return meta
        for token in meta_str.split():
            key, sep, value = token.partition("=")
            if not sep or not key or not value or "=" in value:
                raise ParserError(
                    line_no, f"invalid metadata token {token!r} "
                    "(expected key=value)")
            if key not in allowed:
                raise ParserError(
                    line_no, f"unknown metadata key {key!r} (allowed: "
                    + ", ".join(sorted(allowed)) + ")")
            if key in meta:
                raise ParserError(
                    line_no, f"metadata key {key!r} given twice")
            meta[key] = value
        return meta

    def _positive_int(self, value: str, what: str, line_no: int) -> int:
        """Convert a string to a strictly positive integer."""
        if not (value.isascii() and value.isdigit()) or int(value) <= 0:
            raise ParserError(
                line_no, f"{what} must be a positive integer, got {value!r}")
        return int(value)
