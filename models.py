from __future__ import annotations

from enum import Enum


class ZoneType(Enum):

    NORMAL = "normal"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
    PRIORITY = "priority"

    @property
    def move_cost(self) -> int:
        if self is ZoneType.RESTRICTED:
            return 3
        elif self is ZoneType.NORMAL:
            return 2
        else:
            return 1


class Zone:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: str | None = None,
        max_drones: int = 1,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:

        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.is_start = is_start
        self.is_end = is_end
        if is_start or is_end:
            self.max_drones = 99
        else:
            self.max_drones = max_drones

    def __repr__(self) -> str:
        return f"Zone({self.name}, x={self.x}, y={self.y}, zone_type={self.zone_type})"


class Connection:

    def __init__(self,
                 zone_a: str,
                 zone_b: str,
                 max_link_capacity: int = 1
                 ) -> None:

        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity

    def other(self, zone_name: str) -> str:
        if zone_name == self.zone_a:
            return self.zone_b
        else:
            return self.zone_a

    def key(self) -> tuple[str, str]:
        a, b = (sorted((self.zone_a, self.zone_b)))
        return (a, b)

    def __repr__(self) -> str:
        return f" Connection{self.key()}"


class DroneMap:
    def __init__(self, nb_drones: int) -> None:
        self.nb_drones = nb_drones
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start_zone: str | None = None
        self.end_zone: str | None = None

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise ValueError(f"Duplicate zone name: {zone.name!r}")
        self.zones[zone.name] = zone

        if zone.is_start:
            if self.start_zone is not None:
                raise ValueError(
                    f"Duplicate start_hub declaration: {zone.name!r}")
            self.start_zone = zone.name
        elif zone.is_end:
            if self.end_zone is not None:
                raise ValueError(
                    f"Duplicate end_hub declaration: {zone.name!r}")
            self.end_zone = zone.name

    def add_connection(self, connection: Connection) -> None:
        if any(connection.key() == c.key() for c in self.connections):
            raise ValueError(
                f"Duplicate connection: {connection.zone_a}-{connection.zone_b}")
        self.connections.append(connection)

    def neighbors(self, zone_name: str) -> list[Connection]:
        neighbors = []

        for elem in self.connections:
            if zone_name == elem.zone_a or zone_name == elem.zone_b:
                neighbors.append(elem)
        return (neighbors)
