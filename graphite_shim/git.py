from __future__ import annotations

import contextlib
import dataclasses
import functools
import re
import subprocess
from collections.abc import Generator, Iterator, Sequence
from pathlib import Path
from types import EllipsisType
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
    def git_dir(self) -> Path:
        # shortcut, to avoid shelling out
        if (self.cwd / ".git").is_dir(follow_symlinks=False):
            return self.cwd / ".git"

        proc = _git(["rev-parse", "--git-common-dir"], capture_output=True, cwd=self.cwd)
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


# ----- Test helpers ----- #


class GitTestClient(GitClient):
    def __init__(self) -> None:
        self._expectations: list[GitExpectation] | None = None
        self._call_args: list[list[str]] = []

    @property
    def root(self) -> Path:
        return Path(".")

    @property
    def git_dir(self) -> Path:
        return Path(".git")

    @property
    def call_args(self) -> Sequence[Sequence[str]]:
        return self._call_args

    @contextlib.contextmanager
    def expect(self, *expectations: GitExpectation) -> Generator[None]:
        self._expectations = list(expectations)
        yield
        if self._expectations:
            raise RuntimeError(f"Expectations were not used: {self._expectations}")
        self._expectations = None

    def on(self, args: list[str | EllipsisType]) -> GitExpectation:
        return GitExpectation(args=args)

    def run(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if self._expectations is None:
            raise RuntimeError("git was invoked without expectations")
        if not self._expectations:
            raise RuntimeError("Ran out of expectations!")

        expectation = self._expectations.pop(0)
        self._call_args.append(args)

        if Ellipsis not in expectation.args:
            assert args == expectation.args
        else:
            for actual_arg, expected_arg in zip(args, expectation.args, strict=False):
                if expected_arg is Ellipsis:
                    break
                if actual_arg != expected_arg:
                    raise AssertionError(f"Got unexpected call:\nExpected: {expectation.args}\nGot: {args}")

        return subprocess.CompletedProcess(
            args=args,
            returncode=expectation._returncode,
            stdout=expectation._stdout,
            stderr=expectation._stderr,
        )


@dataclasses.dataclass
class GitExpectation:
    args: list[str | EllipsisType]
    _returncode: int = 0
    _stdout: str = ""
    _stderr: str = ""

    def returncode(self, returncode: int) -> GitExpectation:
        self._returncode = returncode
        return self

    def stdout(self, stdout: str) -> GitExpectation:
        self._stdout = stdout
        return self

    def stderr(self, stderr: str) -> GitExpectation:
        self._stderr = stderr
        return self
