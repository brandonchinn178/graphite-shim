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

                print("TODO: gt log --stack")
            case "short":
                if args.only_stack:
                    branches = self._store.get_stack(curr)
                else:
                    branches = [self._config.trunk, *self._store.get_all_descendants(self._config.trunk)]
                print(branches)
                print("TODO: gt log short")
            case "long":
                raise NotImplementedError  # not using this yet
