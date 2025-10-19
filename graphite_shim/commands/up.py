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
        parser.add_argument("steps", metavar="n", default=1)

        return lambda args: UpArgs(
            steps=args.steps,
        )

    def run(self, args: UpArgs) -> None:
        print("TODO: up")
