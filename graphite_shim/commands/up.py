import argparse

from graphite_shim.commands.base import Command


class CommandUp(Command):
    """Checkout a branch up the stack (towards descendants)."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("steps", metavar="n", default=1)

    def run(self, args: argparse.Namespace) -> None:
        steps: int = args.steps
        print(f"TODO: up {steps}")
