*This project has been created as part of the 42 curriculum by theomart.*

# Fly-in

## Description

Fly-in routes a fleet of drones from a start zone to an end zone across a
network of connected zones, in as few simulation turns as possible.

The map is a graph read from a text file. Each zone has a type (`normal`,
`restricted`, `priority` or `blocked`), an optional color and a capacity.
Each connection has a capacity too. Every turn, a drone may move to an
adjacent zone, wait, or start a two-turn move toward a restricted zone.
The program prints, for each turn, the moves of every drone.

## Instructions

Python 3.10 or later is required. No third-party library is used at run
time; `flake8` and `mypy` are only needed for linting.

```sh
make install                      # create .venv and install flake8 + mypy
make run MAP=01_linear_path.txt   # colored run of a map
make debug MAP=01_linear_path.txt # same, under pdb
make lint                         # flake8 + mypy
make lint-strict                  # flake8 + mypy --strict
make clean                        # remove caches
```

Direct use:

```sh
.venv/bin/python3 main.py <map_file>            # plain output (subject format)
.venv/bin/python3 main.py <map_file> --visual   # colored output with summary
```

Errors (unreadable file, malformed line, unreachable end zone) are
reported on stderr with the line number and the program exits with 1.

## Example

Input (`01_linear_path.txt`):

```
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Output:

```
D1-mid1
D1-mid2 D2-mid1
D1-goal D2-mid2
D2-goal
```

A move toward a restricted zone is printed as `D1-origin-target` on the
first turn (the drone is on the connection) and `D1-target` on the next.

## Algorithm

### Overview

The drones are planned one after the other with a **time-expanded
search**, a form of prioritized cooperative pathfinding:

1. A **reservation table** stores, for every turn, how many drones occupy
   each zone and each connection.
2. For each drone, a **breadth-first search over states `(zone, turn)`**
   finds the earliest arrival at the end zone. From a state the drone can
   wait, move to a neighbor in one turn, or start a two-turn move toward a
   restricted zone. A move is only allowed if the reservation table shows
   free capacity at that turn.
3. The path found is booked in the table, then the next drone is planned.

Because turns are explored in increasing order, the first time the end
zone is reached is the earliest possible arrival for that drone given the
previous bookings.

### Rules handled

- **Zone capacity** (`max_drones`): a drone leaving a zone frees its place
  for the same turn; a zone is counted at the end of a turn. Start and end
  zones are unlimited.
- **Connection capacity** (`max_link_capacity`): counted per turn and per
  edge, whatever the direction.
- **Restricted zones**: the drone books the connection for two turns and
  the zone at arrival; it can never wait on the connection.
- **Blocked zones** are never expanded.
- **Priority zones**: neighbors are ordered so that priority zones are
  tried first, which makes them win every tie.
- **Deadlocks**: impossible by construction, since every booked path is
  fully consistent with the bookings made before it.

### Complexity

- Zones: `Z`, connections: `E`, drones: `D`, horizon (max turn): `T`.
- One drone: `O(T * (Z + E))` time, `O(T * Z)` memory for the visited
  states. Paths are computed once and cached in the reservation table;
  nothing is recomputed.
- All drones: `O(D * T * (Z + E))`. The impossible dream map (25 drones,
  43 turns) is solved in under 0.1 s.

### Results on the provided maps

| Map | Turns | Target |
|---|---|---|
| 01_linear_path | 4 | ≤ 6 |
| 02_simple_fork | 4 | ≤ 8 |
| 03_basic_capacity | 4 | ≤ 6 |
| 01_dead_end_trap | 8 | ≤ 12 |
| 02_circular_loop | 15 | ≤ 15 |
| 03_priority_puzzle | 7 | ≤ 12 |
| 01_maze_nightmare | 13 | ≤ 30 |
| 02_capacity_hell | 16 | ≤ 35 |
| 03_ultimate_challenge | 26 | ≤ 45 |
| 01_the_impossible_dream | 43 | record 45 |

## Visual representation

With `--visual` (used by `make run`), the output shows:

- a legend of the zones, each printed in its own color with its type and
  capacity, so the reader knows which zones are restricted, priority or
  wide;
- one numbered line per turn where each `D<id>-<zone>` token takes the
  color of its destination zone, which makes the flow through the map
  readable at a glance (for example, all drones passing through a red
  bottleneck stand out);
- a summary with the number of turns, drones, moves per turn and moves
  per drone, the secondary metrics of the subject.

Without the flag, the output is exactly the format required by the
subject and can be piped to a file or a checker.

## Code structure

| File | Role |
|---|---|
| `main.py` | `App`: command line, error handling, exit code |
| `parser.py` | `Parser`, `ParserError`: file format validation |
| `models.py` | `Zone`, `ZoneType`, `Connection`, `DroneMap` |
| `simulation.py` | `ReservationTable`, `PathFinder`, `Simulation`, `Drone`, `Step` |
| `renderer.py` | `Renderer`: plain and colored terminal output |

## Resources

- Silver, D., *Cooperative Pathfinding* (AIIDE 2005): reservation tables
  and time-expanded A* for multiple agents.
- Wikipedia, *Breadth-first search* and *Multi-agent pathfinding*.
- Python documentation: `re`, `argparse`, `enum`, `typing`.
- PEP 8, PEP 257, PEP 484 for style, docstrings and type hints.

### Use of AI

AI (Claude) was used to:

- review the code against the subject and list the missing checks of the
  parser;
- generate test cases for invalid map files and an independent checker
  that replays the output log against the rules;
- help write the docstrings and this README.

The algorithm design, the pathfinding and the simulation engine were
written and are understood by the author.
