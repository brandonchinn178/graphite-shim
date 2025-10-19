import pytest

from graphite_shim.branch_tree import BranchTree

class TestSetParent:
    def test_updates_get_parent(self) -> None:
        branches = BranchTree(
            trunk="main",
            parent_map={
                "A": "main",
                "B": "main",
            }
        )
        branches.set_parent("C", parent="A")
        assert branches.get_branch("C").parent == "A"
        branches.set_parent("C", parent="B")
        assert branches.get_branch("C").parent == "B"

    def test_errors_on_trunk(self) -> None:
        branches = BranchTree(trunk="my_trunk")
        with pytest.raises(ValueError):
            branches.set_parent("my_trunk", parent="foo")


class TestGetAncestors:
    def test_returns_correct_order(self) -> None:
        branches = BranchTree(
            trunk="main",
            parent_map={
                "A": "main",
                "B": "A",
                "C": "B",
            },
        )
        assert [branch.name for branch in branches.get_ancestors("C")] == ["B", "A", "main"]
