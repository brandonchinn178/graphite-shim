import abc
import argparse

from graphite_shim.config import Config
from graphite_shim.git import GitClient
from graphite_shim.store import Store


class Command(abc.ABC):
    def __init__(
        self,
        *,
        git: GitClient,
        config: Config,
        store: Store,
    ) -> None:
        self._git = git
        self._config = config
        self._store = store

    def __init_subclass__(cls) -> None:
        if not cls.__name__.startswith("Command"):
            raise Exception("Command subclasses should be named 'CommandFoo'")

        cls.__tag__ = cls.__name__.removeprefix("Command").lower()

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        return

    @abc.abstractmethod
    def run(self, args: argparse.Namespace) -> None:
        pass
