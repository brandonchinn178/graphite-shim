import argparse

from graphite_shim.commands.base import Command

class CommandLog(Command):
    """Display git history / branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("type", choices=["short", "long"])
        parser.add_argument("--stack")

    def run(self, args: argparse.Namespace) -> None:
        print("TODO: log")
