import pytest

from graphite_shim.commands.down import CommandDown
from graphite_shim.config import Config
from graphite_shim.git import GitClientMocked
from graphite_shim.store import Store


@pytest.fixture(name="cmd")
def fixture_cmd(git_mocked: GitClientMocked, config: Config, store: Store) -> CommandDown:
    return CommandDown(git=git_mocked, config=config, store=store)


def test_with_steps(cmd: CommandDown) -> None:
    pass


def test_with_trunk(cmd: CommandDown) -> None:
    pass


def test_overflow(cmd: CommandDown) -> None:
    pass


def test_e2e() -> None:
    pass
