import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class DownArgs:
    steps: int = 1


class CommandDown(Command[DownArgs]):
    """Checkout a branch down the stack (towards ancestors)."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], DownArgs]:
        parser.add_argument("steps", metavar="n", nargs="?", default=1)
        return lambda args: DownArgs(
            steps=args.steps,
        )

    def run(self, args: DownArgs) -> None:
        curr = self._git.get_curr_branch()
        ancestors = list(self._store.get_ancestors(curr))

        if len(ancestors) == 0:
            print(f"Already on @(green){self._config.trunk}")
            return
        elif args.steps > len(ancestors):
            dest = ancestors[-1]
        else:
            dest = ancestors[args.steps - 1]

        self._git.run(["switch", dest.name])
