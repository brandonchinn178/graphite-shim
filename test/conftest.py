from pathlib import Path
from unittest.mock import MagicMock

import pytest

from graphite_shim.config import Config
from graphite_shim.git import GitClientMocked
from graphite_shim.store import Store, StoreManager


@pytest.fixture(name="git_mocked")
def fixture_git_mocked() -> GitClientMocked:
    return GitClientMocked(
        root=Path("."),
        git_dir=Path(".git"),
    )


@pytest.fixture(name="config")
def fixture_config(git_mocked: GitClientMocked) -> Config:
    return Config(
        git_dir=git_mocked.git_dir,
        trunk="main",
    )


@pytest.fixture(name="store")
def fixture_store(config: Config) -> Store:
    return StoreManager.new(config=config)
