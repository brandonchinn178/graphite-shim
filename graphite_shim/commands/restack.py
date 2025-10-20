import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError


@dataclasses.dataclass(frozen=True)
class RestackArgs:
    only_current: bool
    only_downstream: bool


class CommandRestack(Command[RestackArgs]):
    """Restack a stack of branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], RestackArgs]:
        parser.add_argument("--only", action="store_true")
        parser.add_argument("--downstream", action="store_true")

        return lambda args: RestackArgs(
            only_current=args.only,
            only_downstream=args.downstream,
        )

    def run(self, args: RestackArgs) -> None:
        if args.only_downstream:
            raise NotImplementedError("restack --downstream isn't implemented yet")

        # TODO: make this logic only run with --only, and restack the whole stack by default.
        # Not implementing this now because I don't want to mess up the git reflog history by
        # checking out all the branches
        curr = self._store.get_branch(self._git.get_curr_branch())
        if curr.is_trunk:
            return
        parent = self._store.get_branch(curr.parent)
        rebase = self._git.run(["rebase", parent.name], check=False)
        if rebase.returncode > 0:
            raise UserError("Rebase failed, resolve conflicts and run `gt continue`")
