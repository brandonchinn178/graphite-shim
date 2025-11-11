import argparse
import dataclasses
from collections.abc import Callable
from typing import Literal

from graphite_shim.commands.base import Command


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
                    branches = [branch.name for branch in self._store.get_stack(curr)]
                else:
                    branches = [
                        self._config.trunk,
                        *(branch.name for branch in self._store.get_all_descendants(self._config.trunk)),
                    ]

                # TODO: render graph
                for branch in reversed(branches):
                    print(branch)
            case "long":
                raise NotImplementedError  # not using this yet
