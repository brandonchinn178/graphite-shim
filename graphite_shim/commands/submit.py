import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class SubmitArgs:
    submit_stack: bool


class CommandSubmit(Command[SubmitArgs]):
    """Submit a stack to the remote."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], SubmitArgs]:
        parser.add_argument("--stack", action="store_true")

        return lambda args: SubmitArgs(
            submit_stack=args.stack,
        )

    def run(self, args: SubmitArgs) -> None:
        # branches to submit, starting from trunk
        curr = self._git.get_curr_branch()
        branches = self._store.get_stack(curr, descendants=args.submit_stack)

        print("@(blue)Found branches:")
        for branch in branches:
            print(f"- @(cyan){branch}")

        print("\n@(blue)Pushing branches to remote...")
        self._git.run(["push", "--atomic", "--force-with-lease", "origin", *branches])
