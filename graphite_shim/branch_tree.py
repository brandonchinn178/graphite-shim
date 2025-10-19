import abc
import contextlib
import dataclasses
import functools
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Literal, Self

from graphite_shim.exception import UserError

class BranchTree:
    def __init__(
        self,
        *,
        trunk: str = "main",
        parent_map: Mapping[str, str] = {},
    ) -> None:
        self._trunk = trunk
        self._parent_map_unsafe = parent_map

    @property
    def _parent_map(self) -> Mapping[str, str]:
        return self._parent_map_unsafe

    @_parent_map.setter
    def _parent_map(self, parent_map: Mapping[str, str]) -> None:
        self._parent_map_unsafe = parent_map
        with contextlib.suppress(AttributeError):
            del self._branch_infos  # clear cache

    @functools.cached_property
    def _branch_infos(self) -> Mapping[str, BranchInfo]:
        deps_map = defaultdict(list)
        for branch, parent in self._parent_map.items():
            deps_map[parent].append(branch)
        return {
            self._trunk: TrunkBranchInfo(
                name=self._trunk,
                deps=deps_map[self._trunk],
            ),
        } | {
            branch: NonTrunkBranchInfo(
                name=branch,
                parent=parent,
                deps=deps_map[branch],
            )
            for branch, parent in self._parent_map.items()
        }

    # ----- Serialization ---- #

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        return cls(
            trunk=data["trunk"],
            parent_map=data["branches"],
        )

    def serialize(self) -> dict[str, Any]:
        return {
            "trunk": self._trunk,
            "branches": self._parent_map_unsafe,
        }

    # ----- Public API ---- #

    def get_branch(self, branch: str) -> BranchInfo:
        """Get the parent of the given branch."""
        return self._branch_infos[branch]

    def get_branches(self) -> Sequence[BranchInfo]:
        """Get the parent of the given branch."""
        return list(self._branch_infos.values())

    def set_parent(self, branch: str, *, parent: str) -> None:
        """Set the parent of the given branch."""
        if branch == self._trunk:
            raise ValueError("Cannot set the parent of the trunk branch")
        self._parent_map = {**self._parent_map, branch: parent}

    def get_ancestors(self, branch: str) -> Iterator[BranchInfo]:
        """Get upstream branches, starting from the branch's parent to the trunk."""
        curr = self._branch_infos[branch]
        while isinstance(curr, NonTrunkBranchInfo):
            curr = self._branch_infos[curr.parent]
            yield curr

    # def get_all_descendants(self, branch: str) -> Sequence[str]:
    #     """Get all descendants, in topological order."""

    #     def descendants(branch: str) -> Iterable[str]:
    #         children = [child for child, parent in self.branches.items() if parent == branch]
    #         for child in children:
    #             yield child
    #             yield from descendants(child)

    #     return list(descendants(branch))

    # def get_stack(self, branch: str, *, descendants: bool = True) -> Sequence[str]:
    #     branches = [*self.get_ancestors(branch), branch]
    #     if descendants:
    #         branches = [*branches, *self.get_all_descendants(branch)]
    #     return branches


type BranchInfo = TrunkBranchInfo | NonTrunkBranchInfo


@dataclasses.dataclass(frozen=True, kw_only=True)
class BranchInfoBase(abc.ABC):
    name: str
    deps: list[str]


@dataclasses.dataclass(frozen=True, kw_only=True)
class TrunkBranchInfo(BranchInfoBase):
    is_trunk: Literal[True] = True


@dataclasses.dataclass(frozen=True, kw_only=True)
class NonTrunkBranchInfo(BranchInfoBase):
    is_trunk: Literal[False] = False
    parent: str
