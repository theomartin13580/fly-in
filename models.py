"""Data model of a map: zones, connections and the map itself."""

from __future__ import annotations

from enum import Enum


class ZoneType(Enum):
    """Kind of a zone, which sets the cost of moving into it."""

    NORMAL = "normal"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
    PRIORITY = "priority"

    @property
    def move_cost(self) -> int:
        """Number of turns needed to enter a zone of this type.

        Blocked zones cannot be entered at all; the value returned for
        them is never used by the pathfinder.
        """
        if self is ZoneType.RESTRICTED:
            return 2
        return 1


class Zone:
    """A node of the map.

    Attributes:
        name: Unique zone name.
        x: Horizontal coordinate.
        y: Vertical coordinate.
        zone_type: Kind of zone (normal, restricted, blocked, priority).
        color: Optional color used by the renderer.
        max_drones: Number of drones allowed at the same time. It is
            ignored for the start and end zones, which are unlimited.
        is_start: True for the start zone.
        is_end: True for the end zone.
    """

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
        self.max_drones = max_drones
        self.is_start = is_start
        self.is_end = is_end

    @property
    def unlimited(self) -> bool:
        """Tell if the zone has no capacity limit (start and end zones)."""
        return self.is_start or self.is_end

    def __repr__(self) -> str:
        return (f"Zone({self.name}, x={self.x}, y={self.y}, "
                f"zone_type={self.zone_type})")


class Connection:
    """A bidirectional edge between two zones.

    Attributes:
        zone_a: Name of the first zone.
        zone_b: Name of the second zone.
        max_link_capacity: Number of drones allowed on the edge at once.
    """

    def __init__(
        self,
        zone_a: str,
        zone_b: str,
        max_link_capacity: int = 1,
    ) -> None:
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        a, b = sorted((zone_a, zone_b))
        self._key: tuple[str, str] = (a, b)

    def other(self, zone_name: str) -> str:
        """Return the zone at the other end of the connection."""
        if zone_name == self.zone_a:
            return self.zone_b
        return self.zone_a

    def key(self) -> tuple[str, str]:
        """Return a direction-independent identifier of the edge."""
        return self._key

    def __repr__(self) -> str:
        return f"Connection{self.key()}"


class DroneMap:
    """The whole network: zones, connections and number of drones."""

    def __init__(self, nb_drones: int) -> None:
        self.nb_drones = nb_drones
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start_zone: str | None = None
        self.end_zone: str | None = None

    def add_zone(self, zone: Zone) -> None:
        """Register a zone.

        Raises:
            ValueError: If the name, the start or the end is duplicated.
        """
        if zone.name in self.zones:
            raise ValueError(f"duplicated zone name {zone.name!r}")
        if zone.is_start and self.start_zone is not None:
            raise ValueError(
                f"start_hub declared twice ({self.start_zone!r} "
                f"and {zone.name!r})")
        if zone.is_end and self.end_zone is not None:
            raise ValueError(
                f"end_hub declared twice ({self.end_zone!r} "
                f"and {zone.name!r})")
        self.zones[zone.name] = zone
        if zone.is_start:
            self.start_zone = zone.name
        elif zone.is_end:
            self.end_zone = zone.name

    def add_connection(self, connection: Connection) -> None:
        """Register a connection.

        Raises:
            ValueError: If the same pair of zones is already connected.
        """
        if any(connection.key() == c.key() for c in self.connections):
            raise ValueError(
                f"duplicated connection {connection.zone_a}-"
                f"{connection.zone_b}")
        self.connections.append(connection)

    def neighbors(self, zone_name: str) -> list[Connection]:
        """Return every connection touching the given zone."""
        return [c for c in self.connections
                if zone_name in (c.zone_a, c.zone_b)]
