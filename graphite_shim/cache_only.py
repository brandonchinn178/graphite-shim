"""
Define a subset of graphite commands using only the Graphite cache.

Some graphite commands are slow because they always run remote requests.
But in cases where performance matters, we want to only use local cached
data.
"""

import functools
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from graphite_shim.exception import UserError


class CacheOnlyRunner:
    def __init__(self, *, git_dir: Path, curr_branch: str) -> None:
        self._git_dir = git_dir
        self._curr_branch = curr_branch

    @functools.cached_property
    def _cache_data(self) -> Mapping[str, Any]:
        try:
            data: dict[str, Any] = json.loads((self._git_dir / ".graphite_cache_persist").read_text())
            return data
        except FileNotFoundError:
            raise UserError("Could not find graphite cache") from None

    @functools.cached_property
    def _branch_map(self) -> Mapping[str, Mapping[str, Any]]:
        return dict(self._cache_data["branches"])

    def get_trunk(self) -> str:
        curr = self._curr_branch
        while info := self._branch_map.get(curr):
            if info["validationResult"] == "TRUNK":
                return curr
            curr = info["parentBranchName"]
        raise Exception("Could not find trunk")

    def get_parent(self) -> str:
        parent: str = self._branch_map[self._curr_branch]["parentBranchName"]
        return parent
