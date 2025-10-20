from __future__ import annotations

import contextlib
import dataclasses
import subprocess
from collections.abc import Generator, Sequence
from pathlib import Path
from types import EllipsisType
from typing import Any, Self


def _git(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    kwargs = {
        "check": True,
        "text": True,
        **kwargs,
    }
    return subprocess.run(["git", *args], **kwargs)


@dataclasses.dataclass(frozen=True)
class GitClient:
    root: Path
    git_dir: Path

    @classmethod
    def load(cls, cwd: Path) -> Self:
        git_toplevel_proc = _git(["rev-parse", "--show-toplevel"], capture_output=True, cwd=cwd)
        git_dir_proc = _git(["rev-parse", "--git-common-dir"], capture_output=True, cwd=cwd)

        return cls(
            root=Path(git_toplevel_proc.stdout.strip()),
            git_dir=Path(git_dir_proc.stdout.strip()),
        )

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
        return self.query(["branch", "--show-current"])

    def is_ff(self, *, from_: str, to: str) -> bool:
        """Is it a fast forward from the given commit to the other?"""
        proc = self.run(["merge-base", "--is-ancestor", from_, to], check=False)
        return proc.returncode == 0


# ----- Test helpers ----- #


class GitTestClient(GitClient):
    def __init__(self) -> None:
        super().__init__(root=Path("."), git_dir=Path(".git"))

        self._expectations: list[GitExpectation] | None = None
        self._call_args: list[list[str]] = []

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
