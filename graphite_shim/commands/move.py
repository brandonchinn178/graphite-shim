import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command


@dataclasses.dataclass(frozen=True)
class MoveArgs:
    onto: str


class CommandMove(Command[MoveArgs]):
    """Move a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], MoveArgs]:
        parser.add_argument("--onto")

        return lambda args: MoveArgs(
            onto=args.onto,
        )

    def run(self, args: MoveArgs) -> None:
        print("TODO: move")
