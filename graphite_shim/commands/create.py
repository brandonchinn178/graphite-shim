import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command


@dataclasses.dataclass(frozen=True)
class CreateArgs:
    name: str


class CommandCreate(Command[CreateArgs]):
    """Create a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], CreateArgs]:
        parser.add_argument("name")

        return lambda args: CreateArgs(
            name=args.name,
        )

    def run(self, args: CreateArgs) -> None:
        curr = self._git.get_curr_branch()
        self._git.run(["switch", "-c", args.name])
        self._store.set_parent(args.name, parent=curr)
