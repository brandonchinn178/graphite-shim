from __future__ import annotations

import dataclasses
import functools
import re
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from graphite_shim.exception import UserError


def _git(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    kwargs = {
        "check": True,
        "text": True,
        **kwargs,
    }
    return subprocess.run(["git", *args], **kwargs)


@dataclasses.dataclass(frozen=True)
class GitClient:
    cwd: Path

    @functools.cached_property
    def root(self) -> Path:
        proc = _git(["rev-parse", "--show-toplevel"], capture_output=True, cwd=self.cwd)
        return Path(proc.stdout.strip())

    @functools.cached_property
    def git_common_dir(self) -> Path:
        # shortcut, to avoid shelling out
        if (self.cwd / ".git").is_dir(follow_symlinks=False):
            return self.cwd / ".git"

        proc = _git(["rev-parse", "--git-common-dir"], capture_output=True, cwd=self.cwd)
        return Path(proc.stdout.strip())

    @functools.cached_property
    def git_dir(self) -> Path:
        # shortcut, to avoid shelling out
        if (self.cwd / ".git").is_dir(follow_symlinks=False):
            return self.cwd / ".git"
        elif (self.cwd / ".git").is_file():
            git_content = (self.cwd / ".git").read_text()
            if m := re.match(r"gitdir: (?P<path>.+)", git_content):
                return Path(m.group("path"))

        proc = _git(["rev-parse", "--git-dir"], capture_output=True, cwd=self.cwd)
        return Path(proc.stdout.strip())

    # ----- Primary API ----- #

    def query(self, args: list[str], **kwargs: Any) -> str:
        return self.run(args, capture_output=True, **kwargs).stdout.strip()

    def run(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        kwargs = {
            "cwd": self.root,
            **kwargs,
        }
        return _git(args, **kwargs)

    # ----- Helpers ----- #

    def get_curr_branch(self) -> str:
        """Get the current branch."""
        head_content = (self.git_dir / "HEAD").read_text()
        m = re.match(r"ref: refs/heads/(?P<name>.+)", head_content)
        if not m:
            raise UserError("Not on a branch")
        return m.group("name")

    def is_ff(self, *, from_: str, to: str) -> bool:
        """Is it a fast forward from the given commit to the other?"""
        proc = self.run(["merge-base", "--is-ancestor", from_, to], check=False)
        return proc.returncode == 0

    def does_branch_exist(self, name: str) -> bool:
        return self.query(["branch", "--list", name]) != ""

    def get_merged_branches(self, trunk: str) -> Iterator[str]:
        def get_branches(*extra_args: str) -> list[str]:
            return self.query(["branch", "--format=%(refname:short)", *extra_args]).splitlines()

        # merged branches
        for branch in get_branches("--merged", trunk):
            if branch == trunk:
                continue
            yield branch

        # squashed branches
        for branch in get_branches("--no-merged", trunk):
            # https://github.com/not-an-aardvark/git-delete-squashed
            merge_base = self.query(["merge-base", trunk, branch])
            tree_sha = self.query(["rev-parse", f"{branch}^{{tree}}"])
            test_commit = self.run(["commit-tree", tree_sha, "-p", merge_base, "-m", "_"], capture_output=True)
            test_cherry_pick = self.run(["cherry", trunk, test_commit.stdout.strip()], capture_output=True)
            if test_cherry_pick.stdout.startswith("-"):
                yield branch
