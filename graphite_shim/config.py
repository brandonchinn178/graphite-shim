from __future__ import annotations

import dataclasses
import functools
import json
import typing
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Self

from graphite_shim.aliases import load_aliases
from graphite_shim.find_graphite import find_graphite
from graphite_shim.git import GitClient
from graphite_shim.utils.term import Prompter

CONFIG_FILE = ".graphite_shim/config.json"


class ConfigManager:
    @staticmethod
    def setup(*, git: GitClient, prompter: Prompter) -> UseGraphiteConfig | Config:
        (git.git_dir / CONFIG_FILE).parent.mkdir(parents=True, exist_ok=True)

        inferred_config = InferredConfig.load(git=git)

        if inferred_config.graphite_installed:
            use_graphite = prompter.ask_yesno("Use `gt`?", default=inferred_config.use_graphite)
        else:
            use_graphite = False

        if use_graphite:
            return UseGraphiteConfig()
        else:
            return Config.setup(inferred_config, prompter=prompter)

    @staticmethod
    def load(*, config_dir: Path) -> UseGraphiteConfig | Config | None:
        try:
            data = json.loads((config_dir / CONFIG_FILE).read_text())
        except FileNotFoundError:
            return None

        match data.pop("type"):
            case "graphite":
                return UseGraphiteConfig()
            case "non-graphite":
                return Config.load(data, config_dir=config_dir)
            case ty:
                raise ValueError(f"Unknown config type: {ty}")

    @staticmethod
    def save(config: UseGraphiteConfig | Config, *, config_dir: Path) -> None:
        match config:
            case UseGraphiteConfig():
                data = {"type": "graphite"}
            case Config():
                data = {"type": "non-graphite", **config.serialize()}
            case _:
                typing.assert_never(config)
        (config_dir / CONFIG_FILE).write_text(json.dumps(data))


class UseGraphiteConfig:
    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class Config:
    config_dir: Path

    trunk: str

    @functools.cached_property
    def aliases(self) -> Mapping[str, Sequence[str]]:
        return load_aliases()

    @classmethod
    def setup(cls, inferred_config: InferredConfig, *, prompter: Prompter) -> Self:
        trunk = prompter.ask("Trunk branch", default=inferred_config.trunk)
        data = {
            "trunk": trunk,
        }
        return cls.load(data, config_dir=inferred_config.config_dir)

    @classmethod
    def load(
        cls,
        data: dict[str, Any],
        *,
        config_dir: Path,
    ) -> Self:
        return cls(
            config_dir=config_dir,
            trunk=data["trunk"],
        )

    def serialize(self) -> dict[str, Any]:
        return {
            "trunk": self.trunk,
        }


# ----- Setup helpers ----- #


@dataclasses.dataclass(frozen=True)
class InferredConfig:
    config_dir: Path
    graphite_installed: bool
    use_graphite: bool
    trunk: str

    @classmethod
    def load(cls, *, git: GitClient) -> Self:
        graphite_installed = find_graphite() is not None
        origin_url = git.query(["config", "remote.origin.url"])
        use_graphite = graphite_installed and "github.com" in origin_url

        trunk = git.query(["rev-parse", "--abbrev-ref", "origin/HEAD"]).removeprefix("origin/")

        return cls(
            config_dir=git.git_dir,
            graphite_installed=graphite_installed,
            use_graphite=use_graphite,
            trunk=trunk,
        )
