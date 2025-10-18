"""
A minimal implementation of the Graphite CLI.
"""

import argparse
import contextlib
import os
import shutil
import sys
import traceback
from pathlib import Path
from typing import Generator, NoReturn

from graphite_shim.commands import get_all_commands
from graphite_shim.config import Config, GraphiteConfig, NonGraphiteConfig
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
    config = Config.load(git_dir=git.git_dir)
    if config is None:
        print("@(blue)graphite_shim has not been configured on this repo yet.")
        config = Config.init(git=git)
        config.dump(git_dir=git.git_dir)
        Store.init(config=config).dump(git_dir=git.git_dir)
        print("")
        print("@(green)graphite_shim configured!")
        print("~" * 80)

    match config:
        case GraphiteConfig():
            graphite = shutil.which("gt")
            if graphite is None:
                raise UserError("`gt` is not installed!")
            os.execvp(graphite, sys.argv)
        case NonGraphiteConfig():
            run_shim(git=git, config=config)

# TODO: support aliases
def run_shim(*, git: GitClient, config: Config) -> None:
    store = Store.load(git_dir=git.git_dir)

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

    store.dump(git_dir=git.git_dir)


if __name__ == "__main__":
    main()
