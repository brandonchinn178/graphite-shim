import argparse
import dataclasses
from collections.abc import Callable, Iterable
from typing import Literal, Self

from graphite_shim.commands.base import Command
from graphite_shim.store import Store
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class LogArgs:
    command: Literal["short", "long", None]
    only_stack: bool


class CommandLog(Command[LogArgs]):
    """Display git history / branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], LogArgs]:
        parser.add_argument("command", choices=["short", "long"], nargs="?")
        parser.add_argument("--stack", action="store_true")

        return lambda args: LogArgs(
            command=args.command,
            only_stack=args.stack,
        )

    def run(self, args: LogArgs) -> None:
        curr = self._git.get_curr_branch()

        match args.command:
            case None:
                if not args.only_stack:
                    raise NotImplementedError  # not using this yet

                branches = list(self._store.get_stack(curr))
                for branch in reversed(branches):
                    print(branch.name)
                    parent = branch.parent if not branch.is_trunk else f"{branch.name}~1"
                    self._git.run(["log", "--oneline", "--no-decorate", f"{parent}...{branch.name}"])
            case "short":
                graph = Graph.build(
                    self._config.trunk,
                    branch_filter=[curr] if args.only_stack else None,
                    curr_branch=curr,
                    store=self._store,
                )
                for line in graph.lines():
                    print(line)
            case "long":
                raise NotImplementedError  # not using this yet


@dataclasses.dataclass(frozen=True)
class Graph:
    branches: list[tuple[int, str]]
    curr_branch: str

    @classmethod
    def build(
        cls,
        trunk: str,
        *,
        branch_filter: list[str] | None,
        curr_branch: str,
        store: Store,
    ) -> Self:
        def _build(
            branch: str,
            *,
            path_filter: list[str] | None,
            column: int,
        ) -> Iterable[tuple[int, str]]:
            children = store.get_children(branch)
            for i, child in enumerate(children):
                if path_filter is not None:
                    if path_filter[:1] == [child.name]:
                        path_filter = path_filter[1:]
                    else:
                        continue
                yield from _build(
                    child.name,
                    path_filter=path_filter,
                    column=column + i,
                )
            yield (column, branch)

        path_filter = None
        if branch_filter is not None:
            path_filter = [branch.name for branch in store.get_stack(curr_branch)]

        branches = _build(trunk, path_filter=path_filter, column=0)
        return cls(
            branches=list(branches),
            curr_branch=curr_branch,
        )

    def lines(self) -> Iterable[str]:
        for col, branch in self.branches:
            out = f"○ {branch}"
            if branch == self.curr_branch:
                out = f"@(cyan){out}"

            prefix = ""
            if col > 0:
                prefix = "├" + ("─" * (col - 1))
            yield prefix + out
