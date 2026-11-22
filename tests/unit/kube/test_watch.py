from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any, Self

import aiohttp
import pytest
from kubernetes_asyncio import watch as k8s_watch
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube import watch as watch_module
from ai.backend.kube.watch import watch_forever

type Script = list[dict[str, Any]] | BaseException


def _obj(name: str, rv: str) -> dict[str, Any]:
    return {"metadata": {"name": name, "resourceVersion": rv}}


def _event(type_: str, name: str, rv: str) -> dict[str, Any]:
    obj = _obj(name, rv)
    return {"type": type_, "object": obj, "raw_object": obj}


class FakeResponse:
    status: int
    _body: dict[str, Any]

    def __init__(self, items: list[dict[str, Any]], rv: str) -> None:
        self.status = 200
        self._body = {"metadata": {"resourceVersion": rv}, "items": items}

    async def json(self) -> dict[str, Any]:
        return self._body

    async def text(self) -> str:
        return ""

    def release(self) -> None:
        pass


class FakeWatch:
    """Each stream plays the next script: events, or an exception. No script left: cancel."""

    scripts: list[Script] = []
    resource_versions: list[str | None] = []
    _events: list[dict[str, Any]]

    def stream(self, _func: Any, **kwargs: Any) -> Self:
        FakeWatch.resource_versions.append(kwargs.get("resource_version"))
        if not FakeWatch.scripts:
            raise asyncio.CancelledError
        script = FakeWatch.scripts.pop(0)
        if isinstance(script, BaseException):
            raise script
        self._events = script
        return self

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    async def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        for event in self._events:
            yield event


class Recorder:
    lists: int
    relists: list[list[str]]
    events: list[tuple[str, str]]
    fail_on: str | None

    def __init__(self) -> None:
        self.lists = 0
        self.relists = []
        self.events = []
        self.fail_on = None

    async def list_call(self, **_kw: Any) -> FakeResponse:
        self.lists += 1
        return FakeResponse([_obj("a", "1"), _obj("b", "2")], f"rv{self.lists}")

    def on_relist(self, items: list[dict[str, Any]]) -> None:
        self.relists.append([i["metadata"]["name"] for i in items])

    def handler(self, type_: str, obj: dict[str, Any]) -> None:
        if obj["metadata"]["name"] == self.fail_on:
            raise KeyError("broken object")
        self.events.append((type_, obj["metadata"]["name"]))

    async def run(self) -> None:
        with pytest.raises(asyncio.CancelledError):
            await watch_forever(self.list_call, self.handler, on_relist=self.on_relist)


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Iterator[Recorder]:
    async def no_sleep(backoff: float) -> float:
        return backoff

    FakeWatch.scripts = []
    FakeWatch.resource_versions = []
    monkeypatch.setattr(k8s_watch, "Watch", FakeWatch)
    monkeypatch.setattr(watch_module, "_sleep", no_sleep)
    yield Recorder()


class TestWatchForever:
    async def test_lists_first_then_streams_from_the_list(self, recorder: Recorder) -> None:
        FakeWatch.scripts = [[_event("MODIFIED", "a", "5")]]
        await recorder.run()
        assert recorder.relists == [["a", "b"]]
        assert recorder.events == [("ADDED", "a"), ("ADDED", "b"), ("MODIFIED", "a")]
        assert FakeWatch.resource_versions[:2] == ["rv1", "5"]

    async def test_gone_resource_version_relists(self, recorder: Recorder) -> None:
        FakeWatch.scripts = [ApiException(status=410)]
        await recorder.run()
        assert recorder.relists == [["a", "b"], ["a", "b"]]
        assert FakeWatch.resource_versions == ["rv1", "rv2"]

    async def test_connection_errors_resume_from_the_last_version(self, recorder: Recorder) -> None:
        FakeWatch.scripts = [[_event("MODIFIED", "a", "7")], aiohttp.ClientError("reset")]
        await recorder.run()
        assert recorder.lists == 1
        assert FakeWatch.resource_versions == ["rv1", "7", "7"]

    async def test_a_failing_handler_does_not_stop_the_stream(self, recorder: Recorder) -> None:
        recorder.fail_on = "a"
        FakeWatch.scripts = [[_event("MODIFIED", "a", "5"), _event("MODIFIED", "b", "6")]]
        await recorder.run()
        assert ("MODIFIED", "b") in recorder.events

    async def test_bookmarks_advance_the_version_only(self, recorder: Recorder) -> None:
        FakeWatch.scripts = [[_event("BOOKMARK", "", "9")]]
        await recorder.run()
        assert recorder.events == [("ADDED", "a"), ("ADDED", "b")]
        assert FakeWatch.resource_versions == ["rv1", "9"]
