import argparse

from graphite_shim.commands.base import Command

class CommandReorder(Command):
    """Reorder branches in a stack."""

    def run(self, args: argparse.Namespace) -> None:
        print("TODO: reorder")
