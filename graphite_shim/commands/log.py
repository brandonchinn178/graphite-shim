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

        match command:
            case None:
                print("TODO: gt log")
            case "short":
                print("TODO: gt log short")
            case "long":
                raise NotImplementedError  # not using this yet
