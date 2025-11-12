from __future__ import annotations

import contextlib
import dataclasses
import subprocess
from collections.abc import Generator, Sequence
from pathlib import Path
from types import EllipsisType
from typing import Any

from graphite_shim.git import GitClient


class GitTestClient(GitClient):
    def __init__(self) -> None:
        super().__init__(cwd=Path("/non_existent"))

        self._expectations: list[GitExpectation] | None = None
        self._call_args: list[list[str]] = []

    @property
    def root(self) -> Path:
        return Path(".")

    @property
    def git_common_dir(self) -> Path:
        return Path(".git")

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

    def curr_branch(self, branch: str) -> GitCurrBranchExpectation:
        return GitCurrBranchExpectation(branch=branch)

    def cmd(self, args: list[str | EllipsisType]) -> GitCmdExpectation:
        return GitCmdExpectation(args=args)

    def _next_expectation[T](self, expected_cls: type[T]) -> T:
        if self._expectations is None:
            raise RuntimeError("git was invoked without expectations")
        if not self._expectations:
            raise RuntimeError("Ran out of expectations!")

        expectation = self._expectations.pop(0)
        if not isinstance(expectation, expected_cls):
            raise RuntimeError(f"Expected {expected_cls}, got: {expectation}")

        return expectation

    def get_curr_branch(self) -> str:
        expectation = self._next_expectation(GitCurrBranchExpectation)
        return expectation.branch

    def run(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        expectation = self._next_expectation(GitCmdExpectation)
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


type GitExpectation = GitCurrBranchExpectation | GitCmdExpectation


@dataclasses.dataclass
class GitCurrBranchExpectation:
    branch: str


@dataclasses.dataclass
class GitCmdExpectation:
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
