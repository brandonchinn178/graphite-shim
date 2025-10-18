import dataclasses
import json
from pathlib import Path
from typing import Self

from graphite_shim.config import Config

STORE_FILE = ".graphite_shim/store.json"

@dataclasses.dataclass
class Store:
    """The database for graphite_shim."""

    # Tracked branches to their parent
    branches: dict[str, str]

    @classmethod
    def init(cls, *, config: Config) -> Self:
        return cls(
            branches={},
        )

    @classmethod
    def load(cls, *, git_dir: Path) -> Self:
        data = json.loads((git_dir / STORE_FILE).read_text())
        return cls(
            branches=data["branches"],
        )

    def dump(self, *, git_dir: Path) -> None:
        data = {
            "branches": self.branches,
        }
        (git_dir / STORE_FILE).write_text(json.dumps(data))
