from __future__ import annotations

import argparse
import dataclasses
import enum
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, Self

from graphite_shim.branch_tree import BranchInfo, NonTrunkBranchInfo
from graphite_shim.commands.base import Command
from graphite_shim.exception import UserError
from graphite_shim.store import StoreManager
from graphite_shim.utils.term import print


@dataclasses.dataclass(frozen=True)
class RestackArgs:
    targets: RestackTargets


class RestackTargets(enum.StrEnum):
    FULL_STACK = enum.auto()
    ONLY_CURRENT = enum.auto()
    ONLY_DOWNSTREAM = enum.auto()


class CommandRestack(Command[RestackArgs]):
    """Restack a stack of branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], RestackArgs]:
        parser.set_defaults(targets=RestackTargets.FULL_STACK)
        for flag, targets in [
            ("--only", RestackTargets.ONLY_CURRENT),
            ("--downstream", RestackTargets.ONLY_DOWNSTREAM),
        ]:
            parser.add_argument(
                flag,
                dest="targets",
                action="store_const",
                const=targets,
            )

        return lambda args: RestackArgs(
            targets=args.targets,
        )

    def run(self, args: RestackArgs) -> None:
        curr = self._store.get_branch(self._git.get_curr_branch())
        if curr.is_trunk:
            return

        targets: list[BranchInfo]
        match args.targets:
            case RestackTargets.FULL_STACK:
                targets = list(self._store.get_stack(curr.name, include_trunk=False))
            case RestackTargets.ONLY_DOWNSTREAM:
                targets = list(self._store.get_all_descendants(curr.name))
            case RestackTargets.ONLY_CURRENT:
                targets = [curr]

        self._restack(self, targets=targets)

    @staticmethod
    def _restack(cmd: Command[Any], *, targets: list[BranchInfo] | None) -> None:
        if targets:
            plan = RebasePlan(
                git_dir=cmd._git.git_dir,
                orig_branch=cmd._git.get_curr_branch(),
                targets=[branch.name for branch in targets],
            )
            is_start = True
        else:
            plan = RebasePlan.load(git_dir=cmd._git.git_dir)
            is_start = False

        def run_one(plan: RebasePlan, *, is_start: bool) -> None:
            assert len(plan.targets) > 0
            curr = cmd._store.get_branch(plan.targets[0])
            assert isinstance(curr, NonTrunkBranchInfo)

            if is_start:
                new_base = cmd._git.resolve_commit(curr.parent.name)
                git_cmd = [
                    "rebase",
                    curr.parent.last_commit,
                    *("--onto", new_base),
                ]
            else:
                new_base = cmd._git.query(["rev-parse", "rebase-merge/onto"])
                git_cmd = [
                    *("-c", "core.editor=true"),
                    "rebase",
                    "--continue",
                ]

            print(f"@(yellow)Restacking {curr.name}...")
            cmd._git.run(["switch", curr.name])
            rebase = cmd._git.run(git_cmd, check=False)
            if rebase.returncode > 0:
                plan.save()
                raise UserError("Rebase failed, resolve conflicts and run `gt continue`")

            cmd._store.update_parent_commit(curr.name, commit=new_base)
            # TODO: Provide better API to allow commands to manually save store, even on failure
            StoreManager.save(cmd._store, store_dir=cmd._git.git_common_dir)

        while len(plan.targets) > 0:
            run_one(plan, is_start=is_start)
            plan = dataclasses.replace(plan, targets=plan.targets[1:])
            is_start = True

        CommandRestack._reset(cmd, plan=plan)

    @staticmethod
    def _reset(cmd: Command[Any], *, plan: RebasePlan | None = None) -> None:
        plan_ = plan or RebasePlan.load(git_dir=cmd._git.git_dir)
        plan_.clear()
        cmd._git.run(["switch", plan_.orig_branch])


@dataclasses.dataclass(frozen=True)
class RebasePlan:
    git_dir: Path
    orig_branch: str
    targets: list[str]

    FILE: ClassVar[str] = ".graphite_shim/rebase_plan.json"

    @classmethod
    def load(cls, *, git_dir: Path) -> Self:
        data = json.loads((git_dir / cls.FILE).read_text())
        return cls(
            git_dir=git_dir,
            orig_branch=data["orig_branch"],
            targets=data["targets"],
        )

    def save(self) -> None:
        data = {
            "orig_branch": self.orig_branch,
            "targets": self.targets,
        }
        (self.git_dir / self.FILE).write_text(json.dumps(data))

    def clear(self) -> None:
        (self.git_dir / self.FILE).unlink(missing_ok=True)
