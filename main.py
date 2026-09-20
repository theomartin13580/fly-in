"""Command line entry point of the fly-in simulation.

Usage::

    python3 main.py <map_file> [--visual] [--capacity-info]
"""

import argparse
import sys

from parser import Parser, ParserError
from renderer import Renderer
from simulation import Simulation


class App:
    """Parse the arguments, run the simulation and print the result."""

    def __init__(self, argv: list[str]) -> None:
        arg_parser = argparse.ArgumentParser(
            prog="fly-in",
            description="Route a fleet of drones from the start zone to "
                        "the end zone in as few turns as possible.",
        )
        arg_parser.add_argument("map", help="path of the map file")
        arg_parser.add_argument(
            "-v", "--visual", action="store_true",
            help="colored output with turn numbers and a summary",
        )
        """
        arg_parser.add_argument(
            "-c", "--capacity-info", action="store_true",
            help="show the zone and connection capacity used each turn",
        )"""
        self.args = arg_parser.parse_args(argv)

    def run(self) -> int:
        """Run the program and return the process exit code."""
        try:
            drone_map = Parser().parse_file(self.args.map)
            """ simulation = Simulation(drone_map)"""
            log = simulation.run()
        except ParserError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:  # keep the program from crashing
            print(f"Unexpected error: {type(e).__name__}: {e}",
                  file=sys.stderr)
            return 1
        renderer = Renderer(drone_map)
        if self.args.visual:
            renderer.render_visual(log)
        else:
            renderer.render_plain(log)
        """if self.args.capacity_info:
            book = simulation.reservations
            for turn in range(1, book.last_turn + 1):
                print(f"Turn {turn}:")
                for name, zone in drone_map.zones.items():
                    used = book.zone_usage.get((name, turn), 0)
                    if used:
                        print(f"  Zone {name}: "
                              f"{used}/{zone.max_drones} drones")
                for link in drone_map.connections:
                    used = book.link_usage.get((link.key(), turn), 0)
                    if used:
                        print(f"  Connection {link.zone_a}-{link.zone_b}: "
                              f"{used}/{link.max_link_capacity} capacity used")"""
        return 0


if __name__ == "__main__":
    sys.exit(App(sys.argv[1:]).run())
