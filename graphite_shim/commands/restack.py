import argparse

from graphite_shim.commands.base import Command


class CommandRestack(Command):
    """Restack a stack of branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--only")
        parser.add_argument("--downstream")

    def run(self, args: argparse.Namespace) -> None:
        print("TODO: restack")
