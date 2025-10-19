import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command


@dataclasses.dataclass(frozen=True)
class ReorderArgs:
    pass


class CommandReorder(Command[ReorderArgs]):
    """Reorder branches in a stack."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], ReorderArgs]:
        return lambda args: ReorderArgs()

    def run(self, args: ReorderArgs) -> None:
        print("TODO: reorder")
