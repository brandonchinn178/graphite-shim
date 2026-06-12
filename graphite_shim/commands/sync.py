import argparse
import contextlib
import dataclasses
import sys
from collections.abc import Callable
from pathlib import Path

from graphite_shim.commands.base import Command
from graphite_shim.commands.restack import CommandRestack
from graphite_shim.exception import UserError
from graphite_shim.utils.term import print, suppress_output


@dataclasses.dataclass(frozen=True)
class SyncArgs:
    restack: bool


class CommandSync(Command[SyncArgs]):
    """Syncs with remote and syncs branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], SyncArgs]:
        parser.add_argument("--no-restack", dest="restack", action="store_false")

        return lambda args: SyncArgs(
            restack=args.restack,
        )

    def run(self, args: SyncArgs) -> None:
        curr = self._git.get_curr_branch()
        trunk = self._config.trunk

        print("@(blue)Fetching from remote...")
        self._git.run(["fetch"])
        self._update_trunk(curr=curr, trunk=trunk)

        if args.restack:
            print("\n@(blue)Restacking branches...")
            for branch in self._store.get_children(trunk):
                targets = list(self._store.get_stack(branch.name, include_trunk=False))
                try:
                    print(f"@(yellow)Restacking {branch.name}...", end="")
                    sys.stdout.flush()
                    with suppress_output():
                        CommandRestack._restack(self, targets=targets)
                    print(" @(green)OK")
                except UserError:
                    print(" @(red)FAIL@(reset) - skipping...")
                    self._git.run(["rebase", "--abort"])
                    CommandRestack._reset(self)
                except Exception as e:
                    print(f" @(red)ERROR@(reset)\n{str(e).strip()}")
                    self._git.run(["rebase", "--abort"], capture_output=True, check=False)
                    with contextlib.suppress(Exception):
                        CommandRestack._reset(self)

        print("\n@(blue)Cleaning up merged branches...")
        merged_branches = list(self._git.get_merged_branches(trunk))
        if merged_branches:
            for merged_branch in merged_branches:
                print(f"- {merged_branch}")
            if curr in merged_branches:
                self._git.run(["switch", trunk])
            self._git.run(["branch", "-D", *merged_branches])

        print("\n@(blue)Cleaning up old branches from cache...")
        branches = set(self._git.query(["branch", "--format=%(refname:short)"]).splitlines())
        for branch in self._store.get_branches():
            if branch.name not in branches:
                self._store.remove_branch(branch.name)

    def _update_trunk(self, *, curr: str, trunk: str) -> None:
        old_sha = self._git.query(["rev-parse", f"refs/heads/{trunk}"])
        new_sha = self._git.query(["rev-parse", f"refs/remotes/origin/{trunk}"])

        if old_sha == new_sha:
            print(f"@(green){trunk}@(reset) is up to date.")
        elif self._git.is_ff(from_=old_sha, to=new_sha):
            if trunk_worktree := self._find_worktree_for_branch(trunk):
                in_worktree = ["-C", trunk_worktree.as_posix()]
                if self._git.query([*in_worktree, "status", "--porcelain"]) != "":
                    print(f"@(yellow)WARNING: {trunk} not updated, uncommitted changes found")
                    return
                self._git.run([*in_worktree, "reset", "--hard", new_sha])
            else:
                self._git.run(["update-ref", f"refs/heads/{trunk}", new_sha, old_sha])
            print(f"@(green){trunk}@(reset) fast-forwarded to {new_sha}")
        else:
            print(f"@(yellow)WARNING: {trunk} not updated, not a fast-forward")

    def _find_worktree_for_branch(self, branch: str) -> Path | None:
        out = self._git.query(["worktree", "list", "--porcelain"])
        for section in out.split("\n\n"):
            parts = {k: v for line in section.splitlines() for k, v in [line.split(" ", 1)]}
            if parts["branch"] == f"refs/heads/{branch}":
                return Path(parts["worktree"])
        return None
