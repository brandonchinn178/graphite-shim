from graphite_shim.store import Store


class TestGetAllDescendants:
    def test_multiple_descendants(self, store: Store) -> None:
        store.branches = {
            "A": "main",
            "B": "A",
            "C": "B",
            "D": "A",
            "E": "D",
        }
        assert store.get_all_descendants("main") == ["A", "B", "C", "D", "E"]
