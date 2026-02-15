import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command


@dataclasses.dataclass(frozen=True)
class UpArgs:
    steps: int = 1


class CommandUp(Command[UpArgs]):
    """Checkout a branch up the stack (towards descendants)."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], UpArgs]:
        parser.add_argument("steps", metavar="n", nargs="?", type=int, default=1)

        return lambda args: UpArgs(
            steps=args.steps,
        )

    def run(self, args: UpArgs) -> None:
        curr = self._git.get_curr_branch()
        branch = self._store.get_branch(curr)

        steps = args.steps
        while steps > 0:
            children = list(self._store.get_children(branch.name))
            if len(children) == 0:
                break
            elif len(children) == 1:
                branch = children[0]
            else:
                if self._prompter is None:
                    raise ValueError("Multiple children available")
                branch = self._prompter.ask_oneof(
                    "Select child to go to",
                    {child.name: child for child in children},
                )
            steps -= 1

        self._git.run(["switch", branch.name])
