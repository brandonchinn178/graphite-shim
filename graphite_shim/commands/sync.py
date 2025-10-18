import argparse

from graphite_shim.commands.base import Command

class CommandSync(Command):
    """Syncs with remote and syncs branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--no-restack")

    def run(self, args: argparse.Namespace) -> None:
        print("TODO: sync")
