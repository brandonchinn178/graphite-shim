import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.commands.log import CommandLog


@dataclasses.dataclass(frozen=True)
class CheckoutArgs:
    pass


class CommandCheckout(Command[CheckoutArgs]):
    """Interactively select branch to checkout."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], CheckoutArgs]:
        return lambda _: CheckoutArgs()

    def run(self, args: CheckoutArgs) -> None:
        if not self._prompter:
            raise Exception("gt checkout cannot be run non-interactively")
        curr = self._git.get_curr_branch()
        graph = CommandLog._build_graph(self, curr_branch=curr)
        branches = [
            *(b for b, _, _ in graph.branches),
            *graph.untracked_branches,
        ]
        branch_lines = dict(graph.branch_lines()) | dict(graph.untracked_branch_lines())
        branch = self._prompter.ask_oneof(
            "Select branch to checkout",
            branches,
            render=branch_lines.__getitem__,
            start_index=branches.index(curr),
        )
        self._git.run(["switch", branch])
