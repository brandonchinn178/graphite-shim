import argparse
import dataclasses
from collections.abc import Callable
from typing import Any

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
        self._run(self, args)

    @staticmethod
    def _run(cmd: Command[Any], args: UpArgs) -> None:
        curr = cmd._git.get_curr_branch()
        branch = cmd._store.get_branch(curr)

        steps = args.steps
        while steps > 0:
            children = list(cmd._store.get_children(branch.name))
            if len(children) == 0:
                break
            elif len(children) == 1:
                branch = children[0]
            else:
                if cmd._prompter is None:
                    raise ValueError("Multiple children available")
                branch = cmd._prompter.ask_oneof(
                    "Select child to go to",
                    children,
                    render=lambda child: child.name,
                )
            steps -= 1

        cmd._git.run(["switch", branch.name])
