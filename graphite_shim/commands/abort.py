import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command


@dataclasses.dataclass(frozen=True)
class AbortArgs:
    pass


class CommandAbort(Command[AbortArgs]):
    """Abort the restack operation."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], AbortArgs]:
        return lambda args: AbortArgs()

    def run(self, args: AbortArgs) -> None:
        self._git.run(["rebase", "--abort"], check=False)
