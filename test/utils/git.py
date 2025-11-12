from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import test.utils.expector as expector
from graphite_shim.git import GitClient


class GitTestClient(expector.ExpectorMixin, GitClient):
    def __init__(self) -> None:
        super().__init__(cwd=Path("/non_existent"))

    @property
    def root(self) -> Path:
        return Path(".")

    @property
    def git_common_dir(self) -> Path:
        return Path(".git")

    @property
    def git_dir(self) -> Path:
        return Path(".git")

    @expector.mocked
    def _get_curr_branch(
        self,
        *,
        MOCK_returns: str = "",
    ) -> str:
        return MOCK_returns

    @expector.mocked
    def _run(
        self,
        args: list[str],
        *,
        MOCK_returncode: int = 0,
        MOCK_stdout: str = "",
        MOCK_stderr: str = "",
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=MOCK_returncode,
            stdout=MOCK_stdout,
            stderr=MOCK_stderr,
        )
