import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.commands.up import CommandUp, UpArgs


@dataclasses.dataclass(frozen=True)
class TopArgs:
    pass


class CommandTop(Command[TopArgs]):
    """Checkout the top-most branch in the stack."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], TopArgs]:
        return lambda _: TopArgs()

    def run(self, args: TopArgs) -> None:
        CommandUp._run(self, UpArgs(steps=10000))
