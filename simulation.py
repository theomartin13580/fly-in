from enum import Enum
from models import DroneMap, ZoneType
from parser import ParserError

class DroneStatus(Enum):
    AT_HUB = "at_hub"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"


class Drone:
    def __init__(self, drone_id: str, start_zone: str) -> None:
        self.drone_id = drone_id
        self.current_zone = start_zone
        self.status = DroneStatus.AT_HUB
        self.destination: str | None = None
        self.turn_remaining = 0
        self.path_index: int = 0

    def is_arrived(self) -> bool:
        if self.status == DroneStatus.ARRIVED:
            return True
        else:
            return False

    def __repr__(self) -> str:
        return f" Drone :{self.drone_id}, at{self.current_zone}, is {self.status} "


class PathFinder:
    def find_path(self, drone_map: DroneMap, start: str, end: str) -> list[str]:

        distances: dict[str, float] = {}
        for zone_name in drone_map.zones:
            distances[zone_name] = float("inf")
        distances[start] = 0

        previous: dict[str, str] = {}

        unvisited: set[str] = set()
        for zone_name in drone_map.zones:
            unvisited.add(zone_name)

        while unvisited:
            current = min(unvisited, key=lambda zone: distances[zone])
            unvisited.remove(current)
            if current == end:
                break

            for connection in drone_map.neighbors(current):
                neighbor = connection.other(current)
                neighbor_zone = drone_map.zones[neighbor]

                if neighbor_zone.zone_type == ZoneType.BLOCKED:
                    continue
                cost = distances[current] + neighbor_zone.zone_type.move_cost
                if cost < distances[neighbor]:
                    distances[neighbor] = cost
                    previous[neighbor] = current

        if end not in previous and end != start:
            raise ValueError(f"no path found between {start!r} and {end!r}")

        path = [end]
        while path[-1] != start:
            path.append(previous[path[-1]])
        path.reverse()
        print(path)
        return path


class Simulation:
    def __init__(self, drone_map: DroneMap) -> None:
        self.drone_map = drone_map
        self.pathfinder = PathFinder()
        self.path: list[str] = self.pathfinder.find_path(
            drone_map, drone_map.start_zone, drone_map.end_zone)
        self.zone_occupancy: dict[str, int] = {
            drone_map.start_zone: drone_map.nb_drones}

        self.drones: list[Drone] = []
        for i in range(1, drone_map.nb_drones + 1):
            self.drones.append(
                Drone(drone_id=f"D{i}", start_zone=drone_map.start_zone))

        self.connection_occupancy: dict[tuple[str, str], int] = {}
        self.log: list[str] = []

    def run(self) -> list[str]:
        while not all(drone.is_arrived() for drone in self.drones):
            self._step()
        return self.log

    def _step(self) -> None:
        moves_this_turn: list[str] = []
        just_arrived: set[Drone] = set()

        for drone in self.drones:
            if drone.status != DroneStatus.IN_TRANSIT:
                continue
            destination = drone.destination
            assert destination is not None

            key = tuple(sorted((drone.current_zone, destination)))
            self.connection_occupancy[key] = self.connection_occupancy.get(
                key, 0) - 1

            drone.current_zone = destination
            drone.path_index += 1
            drone.destination = None
            drone.status = (
                DroneStatus.ARRIVED if destination == self.drone_map.end_zone
                else DroneStatus.AT_HUB
            )
            self.zone_occupancy[destination] = self.zone_occupancy.get(
                destination, 0) + 1
            moves_this_turn.append(f"{drone.drone_id}-{destination}")
            just_arrived.add(drone)

        intentions: dict[Drone, str] = {}
        reserved_zone: dict[str, int] = {}
        reserved_conn: dict[tuple[str, str], int] = {}

        for drone in self.drones:
            if drone.status != DroneStatus.AT_HUB or drone in just_arrived:
                continue
            next_zone_name = self.path[drone.path_index + 1]
            next_zone = self.drone_map.zones[next_zone_name]

            zone_current = self.zone_occupancy.get(
                next_zone_name, 0) + reserved_zone.get(next_zone_name, 0)
            if zone_current >= next_zone.max_drones:
                continue

            if next_zone.zone_type == ZoneType.RESTRICTED:
                connection = None
                for c in self.drone_map.neighbors(drone.current_zone):
                    if c.other(drone.current_zone) == next_zone_name:
                        connection = c
                        break
                conn_key = tuple(sorted((drone.current_zone, next_zone_name)))
                conn_current = self.connection_occupancy.get(conn_key, 0) + reserved_conn.get(conn_key, 0)
                if conn_current >= connection.max_link_capacity:
                    continue
                reserved_conn[conn_key] = reserved_conn.get(conn_key, 0) + 1

            reserved_zone[next_zone_name] = reserved_zone.get(
                next_zone_name, 0) + 1
            intentions[drone] = next_zone_name

        for drone, next_zone_name in intentions.items():
            next_zone = self.drone_map.zones[next_zone_name]

            if next_zone.zone_type == ZoneType.RESTRICTED:
                conn_key = tuple(sorted((drone.current_zone, next_zone_name)))
                self.connection_occupancy[conn_key] = self.connection_occupancy.get(conn_key, 0) + 1 
                drone.status = DroneStatus.IN_TRANSIT
                drone.destination = next_zone_name
                moves_this_turn.append(f"{drone.drone_id}-{drone.current_zone}-{next_zone_name}")

            else:
                self.zone_occupancy[drone.current_zone] = self.zone_occupancy.get(drone.current_zone, 0) - 1
                self.zone_occupancy[next_zone_name] = self.zone_occupancy.get(next_zone_name, 0) + 1

                drone.current_zone = next_zone_name
                drone.path_index += 1

                if next_zone_name == self.drone_map.end_zone:
                    drone.status = DroneStatus.ARRIVED

                moves_this_turn.append(f"{drone.drone_id}-{next_zone_name}")


        if moves_this_turn:
            self.log.append(" ".join(moves_this_turn))


if __name__ == "__main__":
    from parser import Parser
    from simulation import Simulation
    from renderer import Renderer

    dm = Parser().parse_file("fichier.txt")
    sim = Simulation(dm)
    log = sim.run()

    renderer = Renderer()
    renderer.render(log, dm)