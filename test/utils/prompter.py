from __future__ import annotations

import test.utils.expector as expector
from graphite_shim.utils.term import Prompter, print


class TestPrompter(expector.ExpectorMixin, Prompter):
    __test__ = False

    @expector.mocked
    def _input(self, prompt: str, *, MOCK_returns: str = "") -> str:
        print(prompt, end="")  # Print it out so it still appears in output
        return MOCK_returns
