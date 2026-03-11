import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError


@dataclasses.dataclass(frozen=True)
class ContinueArgs:
    pass


class CommandContinue(Command[ContinueArgs]):
    """Continue the restack operation."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], ContinueArgs]:
        return lambda args: ContinueArgs()

    def run(self, args: ContinueArgs) -> None:
        new_base = self._git.query(["rev-parse", "rebase-merge/onto"])

        rebase = self._git.run(["-c", "rebase.backend=apply", "rebase", "--continue"], check=False)
        if rebase.returncode > 0:
            raise UserError("Rebase failed, resolve conflicts and run `gt continue`")

        curr = self._git.get_curr_branch()
        self._store.update_parent_commit(curr, commit=new_base)
