import argparse

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError
from graphite_shim.utils.term import print


class CommandParent(Command):
    """Show the parent branch."""

    def run(self, args: argparse.Namespace) -> None:
        curr = self._git.get_curr_branch()
        branch = self._store.get_branch(curr)
        if branch.is_trunk:
            raise UserError("Cannot get the parent of the trunk branch.")
        print(branch.parent)
