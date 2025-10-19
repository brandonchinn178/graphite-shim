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
        ancestors = list(self._store.get_ancestors(curr))

        if len(ancestors) == 0:
            print(f"Already on @(green){self._config.trunk}")
            return
        elif steps > len(ancestors):
            dest = ancestors[-1]
        else:
            dest = ancestors[steps - 1]

        self._git.run(["switch", dest.name])
