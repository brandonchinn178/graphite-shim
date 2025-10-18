import argparse

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print

class CommandDown(Command):
    """Checkout a branch down the stack (towards ancestors)."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("steps", metavar="n", nargs="?", default=1)

    def run(self, args: argparse.Namespace) -> None:
        steps: int = args.steps

        curr = self._git.get_curr_branch()
        if curr == self._config.trunk:
            print(f"Already on @(green){self._config.trunk}")
            return

        branches = self._store.get_ancestors(curr)
        index = max(len(branches) - steps, 0)
        dest = branches[index]

        self._git.run(["switch", dest])
