import json
from pathlib import Path

from graphite_shim.branch_tree import BranchTree
from graphite_shim.config import Config

STORE_FILE = ".graphite_shim/store.json"


type Store = BranchTree


class StoreManager:
    @staticmethod
    def new(*, config: Config) -> Store:
        return BranchTree(trunk=config.trunk)

    @staticmethod
    def load(*, git_dir: Path) -> Store:
        data = json.loads((git_dir / STORE_FILE).read_text())
        return BranchTree.deserialize(data)

    @staticmethod
    def save(store: Store, *, git_dir: Path) -> None:
        data = store.serialize()
        (git_dir / STORE_FILE).write_text(json.dumps(data))
