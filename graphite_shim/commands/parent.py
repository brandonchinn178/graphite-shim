import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class ParentArgs:
    pass


class CommandParent(Command[ParentArgs]):
    """Show the parent branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], ParentArgs]:
        return lambda args: ParentArgs()

    def run(self, args: ParentArgs) -> None:
        curr = self._git.get_curr_branch()
        branch = self._store.get_branch(curr)
        if branch.is_trunk:
            raise UserError("Cannot get the parent of the trunk branch.")
        print(branch.parent)
