from __future__ import annotations

import abc
import dataclasses
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, ClassVar, Self

from graphite_shim.git import GitClient
from graphite_shim.utils.term import input

CONFIG_FILE = ".graphite_shim.conf"


@dataclasses.dataclass(frozen=True)
class Config(abc.ABC):
    __REGISTRY: ClassVar[dict[str, type[Config]]] = {}
    type: ClassVar[str]

    def __init_subclass__(cls) -> None:
        cls.__REGISTRY[cls.type] = cls

    @classmethod
    def init(cls, *, git: GitClient) -> Self:
        inferred_config = InferredConfig.load(git=git)
        use_graphite = ask_yesno("Use `gt`?", default=inferred_config.use_graphite)
        if use_graphite:
            return GraphiteConfig._init(inferred_config)
        else:
            return NonGraphiteConfig._init(inferred_config)

    @classmethod
    @abc.abstractmethod
    def _init(cls, inferred_config: InferredConfig) -> Self:
        pass

    @classmethod
    def load(cls, *, git_dir: Path) -> Self | None:
        try:
            data = json.loads((git_dir / CONFIG_FILE).read_text())
            return cls.deserialize(data)
        except FileNotFoundError:
            return None

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        config_cls = cls.__REGISTRY.get(data["type"])
        if config_cls is None:
            raise ValueError(f"Unknown config type: {data["type"]}")

        return config_cls.deserialize(data)

    def dump(self, *, git_dir: Path) -> None:
        data = self.serialize()
        data["type"] = self.type
        (git_dir / CONFIG_FILE).write_text(json.dumps(data))

    @abc.abstractmethod
    def serialize(self) -> dict[str, Any]:
        pass


@dataclasses.dataclass(frozen=True)
class GraphiteConfig(Config):
    type: ClassVar[str] = "graphite"

    @classmethod
    def _init(cls, inferred_config: InferredConfig) -> Self:
        return cls()

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        return cls()

    def serialize(self) -> dict[str, Any]:
        return {}


@dataclasses.dataclass(frozen=True)
class NonGraphiteConfig(Config):
    type: ClassVar[str] = "non-graphite"

    trunk: str

    @classmethod
    def _init(cls, inferred_config: InferredConfig) -> Self:
        trunk = ask("Trunk branch", default=inferred_config.trunk)
        return cls(trunk=trunk)

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        return cls(trunk=data["trunk"])

    def serialize(self) -> dict[str, Any]:
        return {
            "trunk": self.trunk,
        }


# ----- Initialization helpers ----- #


@dataclasses.dataclass(frozen=True)
class InferredConfig:
    use_graphite: bool
    trunk: str

    @classmethod
    def load(cls, *, git: GitClient) -> Self:
        graphite_installed = shutil.which("gt") is not None
        origin_url = git.query(["config", "remote.origin.url"])
        use_graphite = graphite_installed and "github.com" in origin_url

        trunk = git.query(["rev-parse", "--abbrev-ref", "origin/HEAD"]).removeprefix("origin/")

        return cls(use_graphite=use_graphite, trunk=trunk)


def ask(prompt: str, *, default: str) -> str:
    resp = input(f"@(yellow){prompt} [{default}] ").strip()
    return resp if resp else default


def ask_yesno(prompt: str, *, default: bool) -> bool:
    default_disp = "Y/n" if default else "y/N"
    resp = ask(prompt, default=default_disp)
    if resp == default_disp:
        return default
    return resp.lower() in ("y", "yes")
