import argparse

from graphite_shim.commands.base import Command

class CommandTrunk(Command):
    """Show the trunk branch."""

    def run(self, args: argparse.Namespace) -> None:
        print(self._config.trunk)
