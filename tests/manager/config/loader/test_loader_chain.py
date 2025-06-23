from types import SimpleNamespace
from typing import Any

from ai.backend.manager.config.loader.loader_chain import LoaderChain


class DummyLoader(SimpleNamespace):
    payload: dict[str, Any]

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload=payload)

    async def load(self):
        return self.payload


async def test_loader_chain():
    l1 = DummyLoader({"a": 1, "nested": {"x": 1}})
    l2 = DummyLoader({"b": 2, "nested": {"x": 99}})

    cfg = await LoaderChain([l1, l2]).load()

    assert cfg == {"a": 1, "b": 2, "nested": {"x": 99}}
