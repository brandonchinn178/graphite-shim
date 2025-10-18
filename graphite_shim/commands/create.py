import argparse

from graphite_shim.commands.base import Command

class CommandCreate(Command):
    """Create a branch."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("name")

    def run(self, args: argparse.Namespace) -> None:
        name: str = args.name

        curr = self._git.query(["branch", "--show-current"])
        self._git.run(["switch", "-c", name])
        self._store.branches[name] = curr
