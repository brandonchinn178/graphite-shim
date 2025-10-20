import pytest

from graphite_shim.commands.down import CommandDown, DownArgs
from graphite_shim.config import Config
from graphite_shim.git import GitTestClient
from graphite_shim.store import Store


@pytest.fixture(name="cmd")
def fixture_cmd(git: GitTestClient, config: Config, store: Store) -> CommandDown:
    return CommandDown(git=git, config=config, store=store)


def test_with_steps(cmd: CommandDown, git: GitTestClient, store: Store) -> None:
    store.set_parent("A", parent="main")
    store.set_parent("B", parent="A")
    store.set_parent("C", parent="B")
    store.set_parent("D", parent="C")

    with git.expect(
        git.on(["branch", "--show-current"]).stdout("D"),
        git.on(["switch", ...]),
    ):
        cmd.run(DownArgs(steps=2))

    assert git.call_args[1] == ["switch", "B"]


def test_with_trunk(cmd: CommandDown, git: GitTestClient, store: Store, capsys: pytest.CaptureFixture[str]) -> None:
    with git.expect(
        git.on(["branch", "--show-current"]).stdout("main"),
    ):
        cmd.run(DownArgs())

    assert capsys.readouterr().out == "Already on main\n"


def test_overflow(cmd: CommandDown, git: GitTestClient, store: Store) -> None:
    store.set_parent("A", parent="main")
    store.set_parent("B", parent="A")

    with git.expect(
        git.on(["branch", "--show-current"]).stdout("B"),
        git.on(["switch", ...]),
    ):
        cmd.run(DownArgs(steps=100))

    assert git.call_args[1] == ["switch", "main"]


def test_e2e() -> None:
    pass  # TODO: set up tmpdir with git repo
