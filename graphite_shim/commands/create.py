import argparse

from graphite_shim.commands.base import Command


class CommandCreate(Command):
    """Create a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("name")

    def run(self, args: argparse.Namespace) -> None:
        name: str = args.name

        curr = self._git.get_curr_branch()
        self._git.run(["switch", "-c", name])
        self._store.set_parent(name, parent=curr)
