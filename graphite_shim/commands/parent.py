import argparse

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print

class CommandParent(Command):
    """Show the parent branch."""

    def run(self, args: argparse.Namespace) -> None:
        curr = self._git.get_curr_branch()
        print(self._store.get_parent(curr))
