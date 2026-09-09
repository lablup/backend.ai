"""The Docker locator's connection lifetime.

The privnet holds one client for its whole life, so the two moments that matter are what happens
when `open()` is called twice and what happens when it fails.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import pytest

import ai.backend.agent.docker.locator as locator_mod
from ai.backend.agent.docker.locator import DockerContainerLocator
from ai.backend.agent.errors.network import ContainerSourceUnwired


class _FakeDocker:
    """One aiodocker client, as much of it as `open()` touches."""

    def __init__(self, *, works: bool = True) -> None:
        self.works = works
        self.closed = False
        self.versions = 0

    async def version(self) -> Mapping[str, Any]:
        self.versions += 1
        if not self.works:
            raise ConnectionRefusedError("the daemon is not there")
        return {"Version": "29.1.3"}

    async def close(self) -> None:
        self.closed = True


def _spawning(clients: list[_FakeDocker], monkeypatch: pytest.MonkeyPatch) -> None:
    made = iter(clients)
    monkeypatch.setattr(locator_mod, "Docker", lambda *a, **k: next(made))


class TestOpeningTwice:
    """The privnet's entry point used to open the runtime before handing it to the server, which
    opened it again."""

    async def test_the_first_client_is_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        first, second = _FakeDocker(), _FakeDocker()
        _spawning([first, second], monkeypatch)
        loc = DockerContainerLocator()
        await loc.open()
        await loc.open()
        assert first.closed, "its aiohttp session over the daemon socket was leaked"

    async def test_the_live_client_is_the_second(self, monkeypatch: pytest.MonkeyPatch) -> None:
        first, second = _FakeDocker(), _FakeDocker()
        _spawning([first, second], monkeypatch)
        loc = DockerContainerLocator()
        await loc.open()
        await loc.open()
        await loc.close()
        assert second.closed and not second.versions > 1


class TestAnOpenThatFails:
    async def test_it_closes_the_client_it_could_not_use(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        broken = _FakeDocker(works=False)
        _spawning([broken], monkeypatch)
        with pytest.raises(ConnectionRefusedError):
            await DockerContainerLocator().open()
        assert broken.closed

    async def test_a_working_client_survives_a_failed_re_open(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Assigning first meant a failed second open replaced a client that was answering with one
        # that never had.
        good, broken = _FakeDocker(), _FakeDocker(works=False)
        _spawning([good, broken], monkeypatch)
        loc = DockerContainerLocator()
        await loc.open()
        with pytest.raises(ConnectionRefusedError):
            await loc.open()
        assert not good.closed
        assert cast(Any, loc._client()) is good


class TestClosing:
    async def test_it_is_idempotent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = _FakeDocker()
        _spawning([client], monkeypatch)
        loc = DockerContainerLocator()
        await loc.open()
        await loc.close()
        await loc.close()
        assert client.closed

    async def test_using_it_unopened_says_so(self) -> None:
        with pytest.raises(ContainerSourceUnwired, match="before open"):
            DockerContainerLocator()._client()
