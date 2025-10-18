import argparse

from graphite_shim.commands.base import Command


class CommandLog(Command):
    """Display git history / branches."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("command", choices=["short", "long"], nargs="?")
        parser.add_argument("--stack", action="store_true")

    def run(self, args: argparse.Namespace) -> None:
        command: str = args.command
        only_stack: bool = args.stack

        curr = self._git.get_curr_branch()

        match command:
            case None:
                if not only_stack:
                    raise NotImplementedError  # not using this yet

                print("TODO: gt log --stack")
            case "short":
                if only_stack:
                    branches = self._store.get_stack(curr)
                else:
                    branches = [self._config.trunk, *self._store.get_all_descendants(self._config.trunk)]
                print(branches)
                print("TODO: gt log short")
            case "long":
                raise NotImplementedError  # not using this yet
