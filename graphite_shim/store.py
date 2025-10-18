import dataclasses
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Self

from graphite_shim.config import Config
from graphite_shim.exception import UserError

STORE_FILE = ".graphite_shim/store.json"

@dataclasses.dataclass
class Store:
    """The database for graphite_shim."""

    config: Config

    # Tracked branches to their parent
    branches: dict[str, str]

    @classmethod
    def init(cls, *, config: Config) -> Self:
        return cls(
            config=config,
            branches={},
        )

    @classmethod
    def load(cls, *, config: Config) -> Self:
        data = json.loads((config.git_dir / STORE_FILE).read_text())
        return cls(
            config=config,
            branches=data["branches"],
        )

    def save(self) -> None:
        data = {
            "branches": self.branches,
        }
        (self.config.git_dir / STORE_FILE).write_text(json.dumps(data))

    def get_parent(self, branch: str) -> str:
        """
        Get the parent of the given branch.

        Throws an error if branch is trunk.
        """
        if branch == self.config.trunk:
            raise UserError("Cannot get the parent of the trunk branch.")
        return self.branches[branch]

    def get_ancestors(self, branch: str) -> Sequence[str]:
        """
        Get upstream branches, where [0] is trunk and [-1] is branch's parent.

        Returns an empty list if the branch is trunk.
        """
        def get_parents() -> Iterable[str]:
            curr = branch
            while curr != self.config.trunk:
                parent = self.branches[curr]
                yield parent
                curr = parent

        return list(reversed(list(get_parents())))

    def get_all_descendents(self, branch: str) -> Sequence[str]:
        """Get all descendents, topologically sorted, but otherwise arbitrarily ordered."""
        def descendents(branch: str) -> Iterable[str]:
            children = [child for child, parent in self.branches.items() if parent == branch]
            for child in children:
                yield child
                yield from descendents(child)

        return list(descendents(branch))
