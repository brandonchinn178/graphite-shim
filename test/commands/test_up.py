import textwrap
from collections.abc import Callable

import pytest

from graphite_shim.commands.up import CommandUp, UpArgs
from graphite_shim.store import Store
from test.utils.git import GitTestClient
from test.utils.prompter import TestPrompter


@pytest.fixture(name="cmd")
def fixture_cmd(init_cmd: Callable[[type[CommandUp]], CommandUp]) -> CommandUp:
    return init_cmd(CommandUp)


def test_with_steps(cmd: CommandUp, git: GitTestClient, store: Store) -> None:
    store.set_parent("A", parent="main")
    store.set_parent("B", parent="A")
    store.set_parent("C", parent="B")
    store.set_parent("D", parent="C")

    with git.expect(
        git.on.get_curr_branch().returns("main"),
        git.on.run(["switch", ...]),
    ):
        cmd.run(UpArgs(steps=2))

    assert git.calls[1].args[0] == ["switch", "B"]


def test_multiple_children(
    cmd: CommandUp,
    prompter: TestPrompter,
    git: GitTestClient,
    store: Store,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store.set_parent("A", parent="main")
    store.set_parent("B", parent="main")

    with (
        prompter.expect(prompter.on.input("@(yellow)Select branch: ").returns("B")),
        git.expect(
            git.on.get_curr_branch().returns("main"),
            git.on.run(["switch", ...]),
        ),
    ):
        cmd.run(UpArgs())

    assert git.calls[1].args[0] == ["switch", "B"]
    assert capsys.readouterr().out == textwrap.dedent(
        """\
        Multiple children available:
          - A
          - B
        Select branch: """
    )


def test_overflow(cmd: CommandUp, git: GitTestClient, store: Store) -> None:
    store.set_parent("A", parent="main")
    store.set_parent("B", parent="A")

    with git.expect(
        git.on.get_curr_branch().returns("main"),
        git.on.run(["switch", ...]),
    ):
        cmd.run(UpArgs(steps=100))

    assert git.calls[1].args[0] == ["switch", "B"]


def test_e2e() -> None:
    pass  # TODO: set up tmpdir with git repo
