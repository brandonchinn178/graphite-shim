import pytest

from graphite_shim.branch_tree import BranchInfo, BranchTree, NonTrunkBranchInfo
from test.utils.branch_tree import mk_parent


def get_parent_name(branch: BranchInfo) -> str | None:
    if isinstance(branch, NonTrunkBranchInfo):
        return branch.parent.name
    else:
        return None


class TestRemoveBranch:
    def test_removes_branch(self) -> None:
        branches = BranchTree(
            trunk="main",
            parent_map={
                "A": mk_parent("main"),
            },
        )
        branches.remove_branch("A")
        with pytest.raises(ValueError):
            branches.get_branch("A")

    def test_updates_removed_branch_children(self) -> None:
        branches = BranchTree(
            trunk="main",
            parent_map={
                "A": mk_parent("main"),
                "B": mk_parent("A"),
            },
        )
        assert get_parent_name(branches.get_branch("B")) == "A"
        branches.remove_branch("A")
        assert get_parent_name(branches.get_branch("B")) == "main"


class TestSetParent:
    def test_updates_get_parent(self) -> None:
        branches = BranchTree(
            trunk="main",
            parent_map={
                "A": mk_parent("main"),
                "B": mk_parent("main"),
            },
        )
        branches.set_parent("C", parent=mk_parent("A"))
        assert get_parent_name(branches.get_branch("C")) == "A"
        branches.set_parent("C", parent=mk_parent("B"))
        assert get_parent_name(branches.get_branch("C")) == "B"

    def test_errors_on_trunk(self) -> None:
        branches = BranchTree(trunk="my_trunk")
        with pytest.raises(ValueError):
            branches.set_parent("my_trunk", parent=mk_parent("foo"))


class TestGetAncestors:
    def test_returns_correct_order(self) -> None:
        branches = BranchTree(
            trunk="main",
            parent_map={
                "A": mk_parent("main"),
                "B": mk_parent("A"),
                "C": mk_parent("B"),
            },
        )
        assert [branch.name for branch in branches.get_ancestors("C")] == ["B", "A", "main"]
