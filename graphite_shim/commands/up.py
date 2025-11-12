import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class UpArgs:
    steps: int = 1


class CommandUp(Command[UpArgs]):
    """Checkout a branch up the stack (towards descendants)."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], UpArgs]:
        parser.add_argument("steps", metavar="n", nargs="?", default=1)

        return lambda args: UpArgs(
            steps=args.steps,
        )

    def run(self, args: UpArgs) -> None:
        curr = self._git.get_curr_branch()
        branch = self._store.get_branch(curr)

        steps = args.steps
        while steps > 0:
            children = list(self._store.get_children(branch.name))
            if len(children) == 0:
                break
            elif len(children) == 1:
                branch = children[0]
            else:
                if self._prompter is None:
                    raise ValueError("Multiple children available")

                print("@(yellow)Multiple children available:")
                for child in children:
                    print(f"@(yellow)  - {child.name}")

                while True:
                    child_name = self._prompter.ask("Select branch")
                    try:
                        branch = self._store.get_branch(child_name)
                        break
                    except ValueError:
                        continue
            steps -= 1

        self._git.run(["switch", branch.name])
