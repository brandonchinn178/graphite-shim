import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError


@dataclasses.dataclass(frozen=True)
class UntrackArgs:
    branch: str | None


class CommandUntrack(Command[UntrackArgs]):
    """Stop tracking a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], UntrackArgs]:
        parser.add_argument("branch")
        return lambda args: UntrackArgs(
            branch=args.branch,
        )

    def run(self, args: UntrackArgs) -> None:
        curr = args.branch or self._git.get_curr_branch()
        if curr == self._config.trunk:
            raise UserError(f"{curr} is the trunk branch")

        self._store.remove_branch(curr)
