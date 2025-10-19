import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command


@dataclasses.dataclass(frozen=True)
class RestackArgs:
    only_current: bool
    only_downstream: bool


class CommandRestack(Command[RestackArgs]):
    """Restack a stack of branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], RestackArgs]:
        parser.add_argument("--only")
        parser.add_argument("--downstream")

        return lambda args: RestackArgs(
            only_current=args.only,
            only_downstream=args.downstream,
        )

    def run(self, args: RestackArgs) -> None:
        print("TODO: restack")
