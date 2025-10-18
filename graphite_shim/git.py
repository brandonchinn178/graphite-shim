import dataclasses
import subprocess
from pathlib import Path
from typing import Any, Self


def _git(args: list[str | Path], **kwargs: Any) -> subprocess.CompletedProcess:
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
    def load(cls, cwd: Path) -> Self | None:
        git_toplevel_proc = _git(["rev-parse", "--show-toplevel"], capture_output=True, cwd=cwd)
        git_dir_proc = _git(["rev-parse", "--git-common-dir"], capture_output=True, cwd=cwd)

        return cls(
            root=Path(git_toplevel_proc.stdout.strip()),
            git_dir=Path(git_dir_proc.stdout.strip()),
        )

    # ----- Primary API ----- #

    def query(self, args: list[str | Path], **kwargs: Any) -> str:
        return self.run(args, capture_output=True, **kwargs).stdout.strip()

    def run(self, args: list[str | Path], **kwargs: Any) -> subprocess.CompletedProcess:
        kwargs = {
            "cwd": self.root,
            **kwargs,
        }
        return _git(args, **kwargs)

    # ----- Helpers ----- #

    def is_ff(self, *, from_: str, to: str) -> bool:
        """Is it a fast forward from the given commit to the other?"""
        proc = self.run(["merge-base", "--is-ancestor", from_, to], check=False)
        return proc.returncode == 0
