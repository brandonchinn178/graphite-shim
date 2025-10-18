from pathlib import Path

import pytest

from graphite_shim.config import Config
from graphite_shim.store import Store

@pytest.fixture(name="config")
def fixture_config() -> Config:
    return Config(
        git_dir=Path(".git"),
        trunk="main",
    )

@pytest.fixture(name="store")
def fixture_store(config: Config) -> Store:
    return Store(config=config)
