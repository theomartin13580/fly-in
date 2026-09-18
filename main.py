"""Command line entry point of the fly-in simulation.

Usage::

    python3 main.py <map_file> [--visual]
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
        self.args = arg_parser.parse_args(argv)

    def run(self) -> int:
        """Run the program and return the process exit code."""
        try:
            drone_map = Parser().parse_file(self.args.map)
            log = Simulation(drone_map).run()
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
        return 0


if __name__ == "__main__":
    sys.exit(App(sys.argv[1:]).run())
