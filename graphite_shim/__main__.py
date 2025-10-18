"""
A minimal implementation of the Graphite CLI.
"""

import argparse
import contextlib
import os
import shutil
import sys
import traceback
import typing
from pathlib import Path
from typing import Generator, NoReturn

from graphite_shim.commands import get_all_commands
from graphite_shim.config import ConfigManager, Config, UseGraphiteConfig
from graphite_shim.exception import UserError
from graphite_shim.git import GitClient
from graphite_shim.store import Store
from graphite_shim.utils.term import print, printerr


@contextlib.contextmanager
def handle_errors() -> Generator[None, None, None]:
    try:
        yield
    except Exception as e:
        if isinstance(e, UserError):
            printerr(f"@(red)@(bold)ERROR:@(reset) {e}")
        else:
            printerr("\n" + "*" * 80)
            traceback.print_exc()
            printerr("\n@(red)An unexpected error occurred! Report this as a bug.")

        sys.exit(1)


@handle_errors()
def main() -> None:
    git = GitClient.load(Path.cwd())
    config = ConfigManager.load(git_dir=git.git_dir)
    if config is None:
        print("@(blue)graphite_shim has not been configured on this repo yet.")
        config = ConfigManager.init(git=git)
        ConfigManager.save(config)
        if isinstance(config, Config):
            Store.init(config=config).save()
        print("")
        print("@(green)graphite_shim configured!")
        print("~" * 80)

    match config:
        case UseGraphiteConfig():
            graphite = shutil.which("gt")
            if graphite is None:
                raise UserError("`gt` is not installed!")
            os.execvp(graphite, sys.argv)
        case Config():
            run_shim(git=git, config=config)
        case _:
            typing.assert_never(config)

# TODO: support aliases
def run_shim(*, git: GitClient, config: Config) -> None:
    store = Store.load(config=config)

    parser = argparse.ArgumentParser(prog="gt", description=__doc__)
    subparsers = parser.add_subparsers(title="commands", required=True, metavar="command")
    for name, cmd_cls in get_all_commands().items():
        cmd = cmd_cls(git=git, config=config, store=store)
        cmd_parser = subparsers.add_parser(
            name,
            help=cmd.__doc__,
            description=cmd.__doc__,
        )
        cmd_parser.set_defaults(cmd=cmd)
        cmd.add_args(cmd_parser)

    args = parser.parse_args()
    args.cmd.run(args)

    store.save()


if __name__ == "__main__":
    main()
