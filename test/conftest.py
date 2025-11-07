from collections.abc import Callable

import pytest

from graphite_shim.commands.base import Command
from graphite_shim.config import Config
from graphite_shim.git import GitTestClient
from graphite_shim.store import Store, StoreManager


@pytest.fixture(name="git")
def fixture_git() -> GitTestClient:
    return GitTestClient()


@pytest.fixture(name="config")
def fixture_config(git: GitTestClient) -> Config:
    return Config(
        config_dir=git.git_common_dir,
        trunk="main",
    )


@pytest.fixture(name="store")
def fixture_store(config: Config) -> Store:
    return StoreManager.new(config=config)


@pytest.fixture(name="init_cmd")
def fixture_init_cmd[Args](
    git: GitTestClient,
    config: Config,
    store: Store,
) -> Callable[[type[Command[Args]]], Command[Args]]:
    return lambda cmd_cls: cmd_cls(
        prompter=None,
        git=git,
        config=config,
        store=store,
    )
