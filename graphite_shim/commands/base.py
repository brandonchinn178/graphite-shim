import abc
import argparse
from collections.abc import Callable

from graphite_shim.config import Config
from graphite_shim.git import GitClient
from graphite_shim.store import Store
from graphite_shim.utils.term import Prompter


class Command[Args](abc.ABC):
    __tag__: str

    def __init__(
        self,
        *,
        prompter: Prompter | None,
        git: GitClient,
        config: Config,
        store: Store,
    ) -> None:
        self._prompter = prompter
        self._git = git
        self._config = config
        self._store = store

    def __init_subclass__(cls) -> None:
        if not cls.__name__.startswith("Command"):
            raise Exception("Command subclasses should be named 'CommandFoo'")

        cls.__tag__ = cls.__name__.removeprefix("Command").lower()

    @abc.abstractmethod
    def add_args(self, parser: argparse.ArgumentParser) -> Callable[[argparse.Namespace], Args]:
        pass

    @abc.abstractmethod
    def run(self, args: Args) -> None:
        pass
