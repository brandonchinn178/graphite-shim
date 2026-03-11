import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.commands.restack import CommandRestack


@dataclasses.dataclass(frozen=True)
class ContinueArgs:
    pass


class CommandContinue(Command[ContinueArgs]):
    """Continue the restack operation."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], ContinueArgs]:
        return lambda args: ContinueArgs()

    def run(self, args: ContinueArgs) -> None:
        CommandRestack._restack(self, targets=None)
