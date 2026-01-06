import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError


@dataclasses.dataclass(frozen=True)
class CreateArgs:
    name: str
    insert: bool


class CommandCreate(Command[CreateArgs]):
    """Create a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], CreateArgs]:
        parser.add_argument("name")
        parser.add_argument("--insert", action="store_true")

        return lambda args: CreateArgs(
            name=args.name,
            insert=args.insert,
        )

    def run(self, args: CreateArgs) -> None:
        if self._git.does_branch_exist(args.name):
            raise UserError(f"Branch already exists: {args.name}")

        curr = self._git.get_curr_branch()

        if args.insert:
            children = list(self._store.get_children(curr))
            if len(children) == 0:
                child = None
            elif len(children) == 1:
                child = children[0]
            else:
                if self._prompter is None:
                    raise ValueError("--insert specified, but current branch has multiple children")
                child = self._prompter.ask_oneof(
                    "Select child to move onto the new branch",
                    {child.name: child for child in children},
                )
        else:
            child = None

        self._git.run(["switch", "-c", args.name])
        self._store.set_parent(args.name, parent=curr)
        if child:
            self._store.set_parent(child.name, parent=args.name)
