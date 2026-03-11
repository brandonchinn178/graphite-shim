from __future__ import annotations

import abc
import contextlib
import dataclasses
import functools
import itertools
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, Self

from graphite_shim.git import GitClient


class BranchTree:
    def __init__(
        self,
        *,
        trunk: str = "main",
        parent_map: Mapping[str, ParentInfo] = {},
    ) -> None:
        self._trunk = trunk
        self._parent_map_unsafe = parent_map

    @property
    def _parent_map(self) -> Mapping[str, ParentInfo]:
        return self._parent_map_unsafe

    @_parent_map.setter
    def _parent_map(self, parent_map: Mapping[str, ParentInfo]) -> None:
        self._parent_map_unsafe = parent_map
        with contextlib.suppress(AttributeError):
            del self._branch_infos  # clear cache

    @functools.cached_property
    def _branch_infos(self) -> Mapping[str, BranchInfo]:
        children_map = defaultdict(list)
        for branch, parent in self._parent_map.items():
            children_map[parent.name].append(branch)
        return {
            self._trunk: TrunkBranchInfo(
                name=self._trunk,
                children=children_map[self._trunk],
            ),
        } | {
            branch: NonTrunkBranchInfo(
                name=branch,
                parent=parent,
                children=children_map[branch],
            )
            for branch, parent in self._parent_map.items()
        }

    # ----- Serialization ---- #

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        return cls(
            trunk=data["trunk"],
            parent_map={k: ParentInfo.deserialize(v) for k, v in data["branches"].items()},
        )

    def serialize(self) -> dict[str, Any]:
        return {
            "trunk": self._trunk,
            "branches": {k: v.serialize() for k, v in self._parent_map_unsafe.items()},
        }

    # ----- Public API ---- #

    def get_branch(self, branch: str) -> BranchInfo:
        """Get the parent of the given branch."""
        try:
            return self._branch_infos[branch]
        except KeyError:
            raise ValueError(f"Branch does not exist: {branch}") from None

    def get_branches(self) -> Sequence[BranchInfo]:
        """Get the parent of the given branch."""
        return list(self._branch_infos.values())

    def rename_branch(self, *, from_: str, to: str) -> None:
        """Rename the given branch."""
        info = self.get_branch(from_)
        if info.is_trunk:
            return
        self._parent_map = {to: info.parent} | {
            # ruff-keep-multiline
            k: v
            for k, v in self._parent_map.items()
            if k != from_
        }

    def remove_branch(self, branch: str) -> None:
        info = self.get_branch(branch)
        if info.is_trunk:
            raise ValueError("Cannot remove trunk branch")
        self._parent_map = {
            k: (
                v
                if v.name != branch
                # if the parent is being removed, replace the parent
                # with the removed branch's parent
                else dataclasses.replace(v, name=info.parent.name)
            )
            for k, v in self._parent_map.items()
            if k != branch
        }

    def set_parent(self, branch: str, *, parent: ParentInfo) -> None:
        """Set the parent of the given branch."""
        if branch == self._trunk:
            raise ValueError("Cannot set the parent of the trunk branch")
        self._parent_map = {**self._parent_map, branch: parent}

    def update_parent_commit(self, branch: str, *, commit: str) -> None:
        """Update the commit of the parent of the given branch."""
        if branch == self._trunk:
            raise ValueError("Cannot set the parent of the trunk branch")
        parent = self._parent_map[branch]
        self._parent_map = {
            **self._parent_map,
            branch: dataclasses.replace(parent, last_commit=commit),
        }

    def get_ancestors(self, branch: str) -> Iterator[BranchInfo]:
        """Get upstream branches, starting from the branch's parent to the trunk."""
        curr = self._branch_infos[branch]
        while isinstance(curr, NonTrunkBranchInfo):
            curr = self._branch_infos[curr.parent.name]
            yield curr

    def get_children(self, branch: str) -> Iterator[BranchInfo]:
        """Get immediate children of the given branch."""

        info = self._branch_infos[branch]
        for child in info.children:
            yield self._branch_infos[child]

    def get_all_descendants(self, branch: str) -> Iterator[BranchInfo]:
        """Get all descendants, in topological order."""

        for child in self.get_children(branch):
            yield child
            yield from self.get_all_descendants(child.name)

    def get_stack(
        self,
        branch: str,
        *,
        descendants: bool = True,
        include_trunk: bool = True,
    ) -> Iterator[BranchInfo]:
        """Get the stack for the given branch, starting at the trunk."""
        ancestor_branches: Iterator[BranchInfo] = reversed(list(self.get_ancestors(branch)))
        if not include_trunk:
            ancestor_branches = itertools.islice(ancestor_branches, 1, None)

        descendant_branches = self.get_all_descendants(branch) if descendants else []

        yield from ancestor_branches
        yield self._branch_infos[branch]
        yield from descendant_branches


@dataclasses.dataclass(frozen=True, kw_only=True)
class ParentInfo:
    name: str
    # The commit of the parent we last rebased on top of
    last_commit: str

    # ----- Serialization ---- #

    @classmethod
    def deserialize(cls, data: Any) -> Self:
        if isinstance(data, str):
            git = GitClient(cwd=Path.cwd())
            branch = data
            return cls(
                name=branch,
                last_commit=git.resolve_commit(branch),
            )

        return cls(
            name=data["name"],
            last_commit=data["last_commit"],
        )

    def serialize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "last_commit": self.last_commit,
        }


type BranchInfo = TrunkBranchInfo | NonTrunkBranchInfo


@dataclasses.dataclass(frozen=True, kw_only=True)
class BranchInfoBase(abc.ABC):
    name: str
    children: list[str]


@dataclasses.dataclass(frozen=True, kw_only=True)
class TrunkBranchInfo(BranchInfoBase):
    is_trunk: Literal[True] = True
    parent: None = None


@dataclasses.dataclass(frozen=True, kw_only=True)
class NonTrunkBranchInfo(BranchInfoBase):
    is_trunk: Literal[False] = False
    parent: ParentInfo
