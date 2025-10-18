import argparse

from graphite_shim.commands.base import Command

class CommandCreate(Command):
    """Create a branch."""

    def run(self, args: argparse.Namespace) -> None:
        print("TODO: create")
