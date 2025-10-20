import argparse
import dataclasses
from collections.abc import Callable

from graphite_shim.commands.base import Command
from graphite_shim.utils.term import print


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
        print("@(blue)Fetching from remote...")
        self._git.run(["fetch"])
        self._update_trunk()

        print("\n@(blue)Cleaning up merged branches...")
        for merged_branch in self._git.get_merged_branches():
            print(f"- {merged_branch}")
            self._git.run(["branch", "-D", merged_branch])

        # TODO: Implement after `gt restack` works on multiple branches
        # if args.restack:
        #     print("\n@(blue)Restacking branches...")
        #     for branch in self._store.get_branches():
        #         print(f"TODO: restack {branch}")

    def _update_trunk(self) -> None:
        trunk = self._config.trunk
        old_sha = self._git.query(["rev-parse", f"refs/heads/{trunk}"])
        new_sha = self._git.query(["rev-parse", f"refs/remotes/origin/{trunk}"])

        if old_sha == new_sha:
            print(f"@(green){trunk}@(reset) is up to date.")
        elif self._git.is_ff(from_=old_sha, to=new_sha):
            self._git.run(["update-ref", f"refs/heads/{trunk}", new_sha, old_sha])
            print(f"@(green){trunk}@(reset) fast-forwarded to {new_sha}")
        else:
            print(f"@(yellow)WARNING: {trunk} not updated, not a fast-forward")
