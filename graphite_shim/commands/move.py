import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class MoveArgs:
    onto: str


class CommandMove(Command[MoveArgs]):
    """Move a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], MoveArgs]:
        parser.add_argument("--onto", required=True)

        return lambda args: MoveArgs(
            onto=args.onto,
        )

    def run(self, args: MoveArgs) -> None:
        curr = self._git.get_curr_branch()
        curr_branch = self._store.get_branch(curr)
        if curr_branch.is_trunk:
            raise UserError("Cannot move the trunk branch")

        if args.onto == curr_branch.parent:
            print(f"@(green){args.onto} is already the parent")
            return

        proc = self._git.run(
            ["-c", "rebase.autoStash=true", "rebase", "-i", curr_branch.parent, "--onto", args.onto],
            check=False,
        )
        if proc.returncode > 0:
            self._git.run(["rebase", "--abort"], capture_output=True, check=False)
            raise UserError("Rebase failed")
        self._store.set_parent(curr, parent=args.onto)
