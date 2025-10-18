import argparse

from graphite_shim.commands.base import Command

class CommandSubmit(Command):
    """Submit a stack to the remote."""

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--stack")

    def run(self, args: argparse.Namespace) -> None:
        submit_stack: bool = args.stack
