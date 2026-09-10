from models import Connection, DroneMap, ZoneType

State = tuple[str, int]


class Step:
    """One move made by a drone during a given turn.

    A move toward a restricted zone takes two turns: a first step with
    ``in_transit=True`` (the drone is on the connection), then a second
    step when it reaches the zone.
    """

    def __init__(
        self,
        turn: int,
        origin: str,
        target: str,
        connection: Connection,
        in_transit: bool = False,
    ) -> None:
        self.turn = turn
        self.origin = origin
        self.target = target
        self.connection = connection
        self.in_transit = in_transit

    def label(self) -> str:
        """Return the text printed for this move, without the drone id."""
        if self.in_transit:
            return f"{self.origin}-{self.target}"
        return self.target


class Drone:
    """A drone and the moves it has been scheduled to make."""

    def __init__(self, drone_id: str) -> None:
        self.drone_id = drone_id
        self.steps: list[Step] = []

    def arrival_turn(self) -> int:
        """Return the turn during which the drone reaches the end zone."""
        if not self.steps:
            return 0
        return self.steps[-1].turn

    def __repr__(self) -> str:
        return f"Drone({self.drone_id}, {len(self.steps)} moves)"


class ReservationTable:
    """Track how many drones use each zone and connection at each turn.

    Zones are counted at the end of a turn, so a drone leaving a zone
    frees its place for another drone during that same turn.
    """

    def __init__(self, drone_map: DroneMap) -> None:
        self.drone_map = drone_map
        self.zone_usage: dict[State, int] = {}
        self.link_usage: dict[tuple[tuple[str, str], int], int] = {}
        self.last_turn = 0

    def zone_free(self, zone_name: str, turn: int) -> bool:
        """Tell if one more drone can be in the zone at the end of turn."""
        zone = self.drone_map.zones[zone_name]
        if zone.is_start or zone.is_end:
            return True
        used = self.zone_usage.get((zone_name, turn), 0)
        return used < zone.max_drones

    def link_free(self, connection: Connection, turn: int) -> bool:
        """Tell if one more drone can use the connection during turn."""
        used = self.link_usage.get((connection.key(), turn), 0)
        return used < connection.max_link_capacity

    def reserve(self, steps: list[Step]) -> None:
        """Book every zone and connection a drone uses along its steps."""
        for index, step in enumerate(steps):
            link_key = (step.connection.key(), step.turn)
            self.link_usage[link_key] = self.link_usage.get(link_key, 0) + 1
            self.last_turn = max(self.last_turn, step.turn)
            if step.in_transit or index + 1 == len(steps):
                continue
            # the drone stays in the zone until its next move
            for turn in range(step.turn, steps[index + 1].turn):
                zone_key = (step.target, turn)
                self.zone_usage[zone_key] = (
                    self.zone_usage.get(zone_key, 0) + 1)


class PathFinder:
    """Find the earliest route of one drone, turn by turn.

    A state is a pair (zone, turn): being in a zone at turn 3 or at
    turn 5 are two different states. Starting from (start, 0), the
    search lists every state reachable at turn 1, then at turn 2, and
    so on, until the drone can reach the end zone. Moves that would
    break a reservation of the drones planned before are skipped.
    """

    def __init__(self, drone_map: DroneMap) -> None:
        if drone_map.start_zone is None or drone_map.end_zone is None:
            raise ValueError("The map needs a start zone and an end zone")
        self.drone_map = drone_map
        self.start = drone_map.start_zone
        self.end = drone_map.end_zone

        self.links: dict[str, list[Connection]] = {}
        for name in drone_map.zones:
            priority_links: list[Connection] = []
            other_links: list[Connection] = []
            for connection in drone_map.neighbors(name):
                target = drone_map.zones[connection.other(name)]
                if target.zone_type == ZoneType.PRIORITY:
                    priority_links.append(connection)
                else:
                    other_links.append(connection)
            # priority zones are tried first, so they win on a tie
            self.links[name] = priority_links + other_links

    def find_path(self, reservations: ReservationTable) -> list[Step]:
        """Return the moves bringing a drone from start to end the earliest.

        Raises:
            RuntimeError: If the end zone cannot be reached.
        """
        # after the last reservation the map is empty, and a drone needs
        # at most 2 turns per zone to reach the end: no need to go further
        horizon = reservations.last_turn + 2 * len(self.drone_map.zones) + 2

        # for each state reached: the state we came from, and the moves
        came_from: dict[State, tuple[State, list[Step]]] = {}
        # the zones reached at each turn
        reached: dict[int, list[str]] = {0: [self.start]}

        for turn in range(horizon + 1):
            for zone_name in reached.get(turn, []):
                state: State = (zone_name, turn)
                if zone_name == self.end:
                    return self._rebuild(state, came_from)
                for next_state, steps in self._moves(state, reservations):
                    if next_state in came_from:
                        continue
                    came_from[next_state] = (state, steps)
                    next_zone, next_turn = next_state
                    if next_turn not in reached:
                        reached[next_turn] = []
                    reached[next_turn].append(next_zone)

        raise RuntimeError(f"No path from {self.start!r} to {self.end!r}")

    def _moves(
        self, state: State, reservations: ReservationTable
    ) -> list[tuple[State, list[Step]]]:
        """List the states reachable from a state, with the moves used."""
        zone_name, turn = state
        moves: list[tuple[State, list[Step]]] = []

        # staying in place is a move too
        if reservations.zone_free(zone_name, turn + 1):
            moves.append(((zone_name, turn + 1), []))

        for connection in self.links[zone_name]:
            target = connection.other(zone_name)
            zone_type = self.drone_map.zones[target].zone_type
            if zone_type == ZoneType.BLOCKED:
                continue
            if zone_type == ZoneType.RESTRICTED:
                # on the connection during turn + 1, in the zone at turn + 2
                arrival = turn + 2
                if (reservations.link_free(connection, turn + 1)
                        and reservations.link_free(connection, arrival)
                        and reservations.zone_free(target, arrival)):
                    moves.append(((target, arrival), [
                        Step(turn + 1, zone_name, target, connection, True),
                        Step(arrival, zone_name, target, connection),
                    ]))
            elif (reservations.link_free(connection, turn + 1)
                    and reservations.zone_free(target, turn + 1)):
                moves.append(((target, turn + 1), [
                    Step(turn + 1, zone_name, target, connection),
                ]))
        return moves

    def _rebuild(
        self, state: State, came_from: dict[State, tuple[State, list[Step]]]
    ) -> list[Step]:
        """Go back from the end state to the start to list the moves."""
        steps: list[Step] = []
        while state in came_from:
            previous, move_steps = came_from[state]
            steps = move_steps + steps
            state = previous
        return steps


class Simulation:
    """Schedule every drone, then write the turn-by-turn movement log."""

    def __init__(self, drone_map: DroneMap) -> None:
        self.drone_map = drone_map
        self.pathfinder = PathFinder(drone_map)
        self.reservations = ReservationTable(drone_map)
        self.drones: list[Drone] = []
        for i in range(1, drone_map.nb_drones + 1):
            self.drones.append(Drone(f"D{i}"))

    def run(self) -> list[str]:
        """Plan the drones one after the other and return one line per turn.

        Each drone takes the earliest route that respects the zones and
        connections already booked by the drones planned before it.
        """
        for drone in self.drones:
            drone.steps = self.pathfinder.find_path(self.reservations)
            self.reservations.reserve(drone.steps)

        last_turn = 0
        for drone in self.drones:
            last_turn = max(last_turn, drone.arrival_turn())

        log: list[str] = []
        for turn in range(1, last_turn + 1):
            moves: list[str] = []
            for drone in self.drones:
                for step in drone.steps:
                    if step.turn == turn:
                        moves.append(f"{drone.drone_id}-{step.label()}")
            log.append(" ".join(moves))
        return log


if __name__ == "__main__":
    from parser import Parser
    from renderer import Renderer

    dm = Parser().parse_file("03_ultimate_challenge.txt")
    sim = Simulation(dm)
    log = sim.run()

    renderer = Renderer()
    renderer.render(log, dm)
