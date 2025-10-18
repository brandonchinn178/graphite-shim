import dataclasses
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Self

from graphite_shim.config import Config

STORE_FILE = ".graphite_shim/store.json"

@dataclasses.dataclass
class Store:
    """The database for graphite_shim."""

    _config: Config

    # Tracked branches to their parent
    branches: dict[str, str]

    @classmethod
    def init(cls, *, config: Config) -> Self:
        return cls(
            _config=config,
            branches={},
        )

    @classmethod
    def load(cls, *, config: Config) -> Self:
        data = json.loads((config.git_dir / STORE_FILE).read_text())
        return cls(
            _config=config,
            branches=data["branches"],
        )

    def save(self) -> None:
        data = {
            "branches": self.branches,
        }
        (self._config.git_dir / STORE_FILE).write_text(json.dumps(data))

    def get_descendants(self, branch: str) -> Sequence[str]:
        """Get downstream branches, where [0] is trunk and [-1] is branch's parent."""
        def get_parents() -> Generator[str]:
            curr = branch
            while curr != self._config.trunk:
                parent = self.branches[curr]
                yield parent
                curr = parent

        return list(reversed(get_parents()))
