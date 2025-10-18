import argparse
import itertools

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print

class CommandSubmit(Command):
    """Submit a stack to the remote."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--stack")

    def run(self, args: argparse.Namespace) -> None:
        submit_stack: bool = args.stack

        # branches to submit, starting from trunk
        curr = self._git.get_curr_branch()
        branches = [*self._store.get_ancestors(curr), curr]
        if submit_stack:
            branches = [*branches, *self._store.get_all_descendents(curr)]

        print("@(blue)Found branches:")
        for branch in branches:
            print(f"- @(cyan){branch}")

        print("\n@(blue)Pushing branches to remote...")
        self._git.run(["push", "--atomic", "--force-with-lease", "origin", *branches])
