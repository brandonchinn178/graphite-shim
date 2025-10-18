import argparse

from graphite_shim.commands.base import Command

class CommandDown(Command):
    """Checkout a branch down the stack (towards ancestors)."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("steps", metavar="n", default=1)

    def run(self, args: argparse.Namespace) -> None:
        steps: int = args.steps

        curr = self._git.get_curr_branch()
        descendants = self._store.get_descendants(curr)
        index = max(len(descendants) - steps, 0)
        dest = descendants[index]

        self._git.run(["switch", dest])
