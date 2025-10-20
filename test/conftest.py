import pytest

from graphite_shim.config import Config
from graphite_shim.git import GitTestClient
from graphite_shim.store import Store, StoreManager


@pytest.fixture(name="git")
def fixture_git() -> GitTestClient:
    return GitTestClient()


@pytest.fixture(name="config")
def fixture_config(git: GitTestClient) -> Config:
    return Config(
        git_dir=git.git_dir,
        trunk="main",
    )


@pytest.fixture(name="store")
def fixture_store(config: Config) -> Store:
    return StoreManager.new(config=config)
