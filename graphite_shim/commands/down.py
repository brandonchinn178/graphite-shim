import argparse
import dataclasses
from collections.abc import Callable
from typing import Any

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class DownArgs:
    steps: int = 1


class CommandDown(Command[DownArgs]):
    """Checkout a branch down the stack (towards ancestors)."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], DownArgs]:
        parser.add_argument("steps", metavar="n", nargs="?", type=int, default=1)

        return lambda args: DownArgs(
            steps=args.steps,
        )

    def run(self, args: DownArgs) -> None:
        self._run(self, args, include_main=True)

    @staticmethod
    def _run(cmd: Command[Any], args: DownArgs, *, include_main: bool) -> None:
        curr = cmd._git.get_curr_branch()
        ancestors = list(cmd._store.get_ancestors(curr))

        if len(ancestors) == 0:
            print(f"Already on @(green){cmd._config.trunk}")
            return

        if not include_main:
            if len(ancestors) == 1:
                print("Already on lowest branch in stack")
                return
            ancestors = ancestors[:-1]

        dest = (
            ancestors[args.steps - 1]
            if args.steps <= len(ancestors)
            # ruff-multi-line
            else ancestors[-1]
        )

        cmd._git.run(["switch", dest.name])
