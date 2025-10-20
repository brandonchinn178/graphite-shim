import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command


@dataclasses.dataclass(frozen=True)
class InitArgs:
    pass


class CommandInit(Command[InitArgs]):
    """Initialize graphite_shim."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], InitArgs]:
        return lambda args: InitArgs()

    def run(self, args: InitArgs) -> None:
        pass
