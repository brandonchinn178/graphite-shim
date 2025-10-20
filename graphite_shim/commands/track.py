import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError


@dataclasses.dataclass(frozen=True)
class TrackArgs:
    parent: str


class CommandTrack(Command[TrackArgs]):
    """Start tracking a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], TrackArgs]:
        parser.add_argument("--parent", "-p", default=self._config.trunk)

        return lambda args: TrackArgs(
            parent=args.parent,
        )

    def run(self, args: TrackArgs) -> None:
        curr = self._git.get_curr_branch()
        if curr == self._config.trunk:
            raise UserError(f"{curr} is the trunk branch")
        else:
            self._store.set_parent(curr, parent=args.parent)
