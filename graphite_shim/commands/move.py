import argparse

from graphite_shim.commands.base import Command

class CommandMove(Command):
    """Move a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--onto")

    def run(self, args: argparse.Namespace) -> None:
        print("TODO: move")
