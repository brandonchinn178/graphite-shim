from graphite_shim.branch_tree import ParentInfo


def mk_parent(name: str) -> ParentInfo:
    return ParentInfo(name=name, last_commit="123456")
