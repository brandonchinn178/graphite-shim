from __future__ import annotations

import argparse
import dataclasses
from collections.abc import Callable, Iterable
from typing import Any, Literal, Self

from graphite_shim.commands.base import Command
from graphite_shim.git import GitClient
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
                    print(f"@(green)* {branch.name}")
                    parent = branch.parent.name if not branch.is_trunk else f"{branch.name}~1"
                    self._git.run(["log", "--oneline", "--no-decorate", f"{parent}...{branch.name}"])
            case "short":
                graph = self._build_graph(
                    self,
                    branch_filter=[curr] if args.only_stack else None,
                    curr_branch=curr,
                )
                for _, line in graph.branch_lines():
                    print(line)
                print("")
                print("Untracked branches:")
                for _, line in graph.untracked_branch_lines():
                    print(line)
            case "long":
                raise NotImplementedError  # not using this yet

    @staticmethod
    def _build_graph(
        cmd: Command[Any],
        *,
        branch_filter: list[str] | None = None,
        curr_branch: str,
    ) -> Graph:
        return Graph.build(
            cmd._config.trunk,
            branch_filter=branch_filter,
            curr_branch=curr_branch,
            store=cmd._store,
            git=cmd._git,
        )


@dataclasses.dataclass(frozen=True)
class Graph:
    # List of (branch name, column, number of children)
    branches: list[tuple[str, int, int]]
    untracked_branches: list[str]
    curr_branch: str

    @classmethod
    def build(
        cls,
        trunk: str,
        *,
        branch_filter: list[str] | None = None,
        curr_branch: str,
        store: Store,
        git: GitClient,
    ) -> Self:
        def _build(
            branch: str,
            *,
            path_filter: list[str] | None,
            column: int,
        ) -> Iterable[tuple[str, int, int]]:
            children = list(store.get_children(branch))
            next_calls = [
                (child, path_filter[1:] if path_filter is not None else None)
                for child in children
                if path_filter is None or path_filter[:1] == [child.name]
            ]
            for i, (child, next_path_filter) in enumerate(next_calls):
                yield from _build(
                    child.name,
                    path_filter=next_path_filter,
                    column=column + i,
                )
            yield (branch, column, len(next_calls))

        path_filter = None
        if branch_filter is not None:
            path_filter = [branch.name for branch in store.get_stack(curr_branch)][1:]

        branches = list(_build(trunk, path_filter=path_filter, column=0))

        all_branches = git.query(["branch", "--format=%(refname:short)"]).splitlines()
        untracked_branches = list(set(all_branches) - {b.name for b in store.get_branches()})

        return cls(
            branches=branches,
            untracked_branches=untracked_branches,
            curr_branch=curr_branch,
        )

    def branch_lines(self) -> Iterable[tuple[str, str]]:
        for branch, col, num_children in self.branches:
            color = self._color_curr(branch)
            junctions = "" if num_children <= 1 else "─┴" * (num_children - 2) + "─┘"
            line = ("│ " * col) + color("○") + junctions + " " + color(branch)
            yield branch, line

    def untracked_branch_lines(self) -> Iterable[tuple[str, str]]:
        for branch in self.untracked_branches:
            line = self._color_curr(branch)(f"* {branch}")
            yield branch, line

    def _color_curr(self, branch: str) -> Callable[[str], str]:
        return lambda s: f"@(cyan){s}@(fg-reset)" if branch == self.curr_branch else s
