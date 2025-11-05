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
        curr = self._git.get_curr_branch()
        trunk = self._config.trunk

        print("@(blue)Fetching from remote...")
        self._git.run(["fetch"])
        self._update_trunk(curr=curr, trunk=trunk)

        print("\n@(blue)Cleaning up merged branches...")
        merged_branches = list(self._git.get_merged_branches(trunk))
        if merged_branches:
            for merged_branch in merged_branches:
                print(f"- {merged_branch}")
            if curr in merged_branches:
                self._git.run(["switch", trunk])
            self._git.run(["branch", "-D", *merged_branches])

        # TODO: Implement after `gt restack` works on multiple branches
        # if args.restack:
        #     print("\n@(blue)Restacking branches...")
        #     for branch in self._store.get_branches():
        #         print(f"TODO: restack {branch}")

    def _update_trunk(self, *, curr: str, trunk: str) -> None:
        old_sha = self._git.query(["rev-parse", f"refs/heads/{trunk}"])
        new_sha = self._git.query(["rev-parse", f"refs/remotes/origin/{trunk}"])

        if old_sha == new_sha:
            print(f"@(green){trunk}@(reset) is up to date.")
        elif self._git.is_ff(from_=old_sha, to=new_sha):
            if curr == trunk:
                if self._git.query(["status", "--porcelain"]) != "":
                    print(f"@(yellow)WARNING: {trunk} not updated, uncommitted changes found")
                    return
                self._git.run(["reset", "--hard", new_sha])
            else:
                self._git.run(["update-ref", f"refs/heads/{trunk}", new_sha, old_sha])
            print(f"@(green){trunk}@(reset) fast-forwarded to {new_sha}")
        else:
            print(f"@(yellow)WARNING: {trunk} not updated, not a fast-forward")
