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
                targets = list(self._store.get_stack(curr.name))[1:]
            case RestackTargets.ONLY_DOWNSTREAM:
                targets = list(self._store.get_all_descendants(curr.name))
            case RestackTargets.ONLY_CURRENT:
                targets = [curr]

        plan = RebasePlan(
            git_dir=self._git.git_dir,
            targets=[branch.name for branch in targets],
        )

        self._restack(self, start_plan=plan)

    @staticmethod
    def _restack(cmd: Command[Any], *, start_plan: RebasePlan | None) -> None:
        if start_plan:
            plan = start_plan
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

            print(f"@(blue)Restacking {curr.name}...")
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

        plan.clear()


@dataclasses.dataclass(frozen=True)
class RebasePlan:
    git_dir: Path
    targets: list[str]

    FILE: ClassVar[str] = ".graphite_shim/rebase_plan.json"

    @classmethod
    def load(cls, *, git_dir: Path) -> Self:
        data = json.loads((git_dir / cls.FILE).read_text())
        return cls(
            git_dir=git_dir,
            targets=data["targets"],
        )

    def save(self) -> None:
        data = {
            "targets": self.targets,
        }
        (self.git_dir / self.FILE).write_text(json.dumps(data))

    def clear(self) -> None:
        (self.git_dir / self.FILE).unlink(missing_ok=True)
