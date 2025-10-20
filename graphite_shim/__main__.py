"""
A minimal implementation of the Graphite CLI.
"""

import argparse
import contextlib
import os
import sys
import traceback
import typing
from collections.abc import Generator
from pathlib import Path

from graphite_shim.cache_only import CacheOnlyRunner
from graphite_shim.commands import get_all_commands
from graphite_shim.config import Config, ConfigManager, UseGraphiteConfig
from graphite_shim.exception import UserError
from graphite_shim.find_graphite import find_graphite
from graphite_shim.git import GitClient
from graphite_shim.store import StoreManager
from graphite_shim.utils.term import Prompter, print, printerr


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
    try:
        no_interactive_index = sys.argv.index("--no-interactive")
        sys.argv.pop(no_interactive_index)
        prompter = None
    except ValueError:
        prompter = Prompter()

    git = GitClient.load(Path.cwd())
    config = ConfigManager.load(git_dir=git.git_dir)
    if config is None:
        if prompter is None:
            raise UserError("gt not configured")

        print("@(blue)graphite_shim has not been configured on this repo yet.")
        config = ConfigManager.setup(git=git, prompter=prompter)
        ConfigManager.save(config, git_dir=git.git_dir)
        if isinstance(config, Config):
            store = StoreManager.new(config=config)
            StoreManager.save(store, git_dir=git.git_dir)
        print("")
        print("@(green)graphite_shim configured!")
        print("~" * 80)

    match config:
        case UseGraphiteConfig():
            if os.environ.get("CACHE_ONLY", "").lower() == "true":
                run_cache_only(git=git)
                return

            graphite = find_graphite()
            if graphite is None:
                raise UserError("`gt` is not installed!")
            os.execvp(graphite, sys.argv)
        case Config():
            run_shim(prompter=prompter, git=git, config=config)
        case _:
            typing.assert_never(config)


def run_shim(*, prompter: Prompter | None, git: GitClient, config: Config) -> None:
    store = StoreManager.load(git_dir=git.git_dir)

    parser = argparse.ArgumentParser(prog="gt", description=__doc__)
    subparsers = parser.add_subparsers(title="commands", required=True, metavar="command")
    for name, cmd_cls in get_all_commands().items():
        cmd = cmd_cls(prompter=prompter, git=git, config=config, store=store)
        cmd_parser = subparsers.add_parser(
            name,
            help=cmd.__doc__,
            description=cmd.__doc__,
        )
        args_parser = cmd.add_args(cmd_parser)
        cmd_parser.set_defaults(cmd=cmd, parse_args=args_parser)

    # add aliases
    for alias, alias_args in config.aliases.items():
        description = f"Alias for `{' '.join(alias_args)}`"
        alias_parser = subparsers.add_parser(
            alias,
            help=description,
            description=description,
        )
        alias_parser.set_defaults(alias_args=alias_args)

    def parse_args(args: list[str]) -> argparse.Namespace:
        ns = parser.parse_args(args)
        if hasattr(ns, "alias_args"):
            return parse_args(ns.alias_args)
        return ns

    args = parse_args(sys.argv[1:])
    if not hasattr(args, "cmd"):
        parser.error("No command provided")

    cmd_args = args.parse_args(args)
    args.cmd.run(cmd_args)
    StoreManager.save(store, git_dir=git.git_dir)


def run_cache_only(*, git: GitClient) -> None:
    """
    Run a subset of graphite commands using only the Graphite cache.

    Some graphite commands are slow because they always run remote requests.
    But in cases where performance matters, we want to only use local cached
    data.
    """
    runner = CacheOnlyRunner(
        git_dir=git.git_dir,
        curr_branch=git.get_curr_branch(),
    )

    parser = argparse.ArgumentParser(prog="gt", description=__doc__)
    subparsers = parser.add_subparsers(title="commands", required=True, metavar="command")
    subparsers.add_parser("parent").set_defaults(func=runner.get_parent)
    subparsers.add_parser("trunk").set_defaults(func=runner.get_trunk)

    # Show nicer error message on invalid command
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        subparsers.add_parser(cmd).set_defaults(func=None, cmd=cmd)

    args = parser.parse_args()
    if args.func is None:
        parser.error(f"Graphite command not supported with CACHE_ONLY: {args.cmd}")
    args.func()


if __name__ == "__main__":
    main()
