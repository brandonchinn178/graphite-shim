import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class TrunkArgs:
    pass


class CommandTrunk(Command[TrunkArgs]):
    """Show the trunk branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], TrunkArgs]:
        return lambda args: TrunkArgs()

    def run(self, args: TrunkArgs) -> None:
        print(self._config.trunk)
