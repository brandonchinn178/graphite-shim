import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError


@dataclasses.dataclass(frozen=True)
class DeleteArgs:
    branch: str


class CommandDelete(Command[DeleteArgs]):
    """Delete a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], DeleteArgs]:
        parser.add_argument("branch")

        return lambda args: DeleteArgs(
            branch=args.branch,
        )

    def run(self, args: DeleteArgs) -> None:
        branch = self._store.get_branch(args.branch)
        if branch.is_trunk:
            raise UserError("Cannot delete the trunk branch")

        self._git.run(["branch", "-D", args.branch])
        self._store.remove_branch(args.branch)
