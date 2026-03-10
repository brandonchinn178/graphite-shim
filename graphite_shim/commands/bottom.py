import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.commands.down import CommandDown, DownArgs


@dataclasses.dataclass(frozen=True)
class BottomArgs:
    pass


class CommandBottom(Command[BottomArgs]):
    """Checkout the bottom-most branch in the stack (just above the trunk)."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], BottomArgs]:
        return lambda _: BottomArgs()

    def run(self, args: BottomArgs) -> None:
        CommandDown._run(self, DownArgs(steps=10000), include_main=False)
