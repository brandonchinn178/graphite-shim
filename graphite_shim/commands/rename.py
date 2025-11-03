import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command


@dataclasses.dataclass(frozen=True)
class RenameArgs:
    name: str


class CommandRename(Command[RenameArgs]):
    """Rename the current branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], RenameArgs]:
        parser.add_argument("name")

        return lambda args: RenameArgs(
            name=args.name,
        )

    def run(self, args: RenameArgs) -> None:
        curr = self._git.get_curr_branch()
        self._git.run(["branch", "-m", curr, args.name])
        self._store.rename_branch(from_=curr, to=args.name)
