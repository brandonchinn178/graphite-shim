import argparse
import dataclasses
from collections.abc import Callable
from typing import Literal

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class LogArgs:
    command: Literal["short", "long", None]
    only_stack: bool


class CommandLog(Command[LogArgs]):
    """Display git history / branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], LogArgs]:
        parser.add_argument("command", choices=["short", "long"], nargs="?")
        parser.add_argument("--stack", action="store_true")

        return lambda args: LogArgs(
            command=args.command,
            only_stack=args.stack,
        )

    def run(self, args: LogArgs) -> None:
        curr = self._git.get_curr_branch()

        match args.command:
            case None:
                if not args.only_stack:
                    raise NotImplementedError  # not using this yet

                branches = list(self._store.get_stack(curr))
                for branch in reversed(branches):
                    print(branch.name)
                    parent = branch.parent if not branch.is_trunk else f"{branch.name}~1"
                    self._git.run(["log", "--oneline", "--no-decorate", f"{parent}...{branch.name}"])
            case "short":
                if args.only_stack:
                    starts = [curr]
                else:
                    starts = [
                        branch.name
                        for branch in self._store.get_children(self._config.trunk)
                    ]
                    if len(starts) == 0:
                        starts = [self._config.trunk]

                stacks = [
                    list(self._store.get_stack(start))
                    for start in starts
                ]
                for stack in sorted(stacks, key=len, reverse=True):
                    for branch in reversed(stack):
                        out = branch.name
                        if branch.name == curr:
                            out = f"@(cyan){out}"
                        print(out)
                    print("@(gray)" + "─" * 40)
            case "long":
                raise NotImplementedError  # not using this yet
