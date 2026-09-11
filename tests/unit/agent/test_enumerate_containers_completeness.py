"""
Tests for the refusal a partial container listing now raises.

`enumerate_containers` describes every container it listed. A container it could not describe is
missing from the result but not from the host, and every caller reads the result as the whole
truth -- it releases that container's host ports, drops its kernel from the registry at startup,
and destroys it as unknown. Only a 404 between the listing and the describe is absence.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiodocker.exceptions import DockerError

import ai.backend.agent.docker.agent as docker_agent
from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors.backend import ContainerEnumerationIncomplete
from ai.backend.agent.utils import raise_if_enumeration_incomplete
from ai.backend.common.docker import LabelName
from ai.backend.common.types import AgentId, KernelId


class TestRaiseIfEnumerationIncomplete:
    def test_a_complete_listing_is_accepted(self) -> None:
        raise_if_enumeration_incomplete([None, None])

    def test_an_empty_listing_is_accepted(self) -> None:
        raise_if_enumeration_incomplete([])

    def test_one_failure_refuses_the_whole_listing(self) -> None:
        with pytest.raises(ContainerEnumerationIncomplete) as exc_info:
            raise_if_enumeration_incomplete([None, RuntimeError("boom"), None])
        assert "1 of the listed container(s)" in str(exc_info.value)

    def test_the_first_failure_is_named(self) -> None:
        with pytest.raises(ContainerEnumerationIncomplete) as exc_info:
            raise_if_enumeration_incomplete([OSError("first"), RuntimeError("second")])
        message = str(exc_info.value)
        assert "2 of the listed container(s)" in message
        assert "first" in message

    def test_cancellation_is_propagated_as_cancellation(self) -> None:
        """A cancelled enumeration is being torn down, not answering incompletely."""
        with pytest.raises(asyncio.CancelledError):
            raise_if_enumeration_incomplete([asyncio.CancelledError()])


class TestReconstructResourceUsageSkipsAPartialListing:
    async def test_a_partial_listing_leaves_the_alloc_maps_untouched(self) -> None:
        """It runs on teardown paths, and it has not cleared anything yet when the listing fails.

        Raising here would strand a CLEAN over a transient backend hiccup; skipping keeps the
        maps as they were, which is the state that is still correct.
        """
        agent = MagicMock()
        agent.enumerate_containers = AsyncMock(
            side_effect=ContainerEnumerationIncomplete("could not describe 1")
        )
        computer_ctx = MagicMock()
        agent.computers = {"cpu": computer_ctx}
        agent.resource_lock = asyncio.Lock()

        await AbstractAgent.reconstruct_resource_usage(agent)

        computer_ctx.alloc_map.clear.assert_not_called()

    async def test_a_complete_listing_still_reconstructs(self) -> None:
        agent = MagicMock()
        agent.enumerate_containers = AsyncMock(return_value=[])
        computer_ctx = MagicMock()
        agent.computers = {"cpu": computer_ctx}
        agent.resource_lock = asyncio.Lock()

        await AbstractAgent.reconstruct_resource_usage(agent)

        computer_ctx.alloc_map.clear.assert_called_once()


class TestDockerEnumerateContainers:
    """The docker backend narrows from the listing, then describes only its own kernels."""

    @staticmethod
    def _entry(
        kernel_id: KernelId | None,
        *,
        state: str = "running",
        owner: str = "test-agent",
        show: Any = None,
    ) -> MagicMock:
        container = MagicMock()
        container._id = f"cid-{kernel_id}"
        container.show = show if show is not None else AsyncMock()
        name = f"/kernel.{kernel_id}" if kernel_id is not None else "/some-other-container"
        payload = {"Names": [name], "State": state, "Labels": {LabelName.OWNER_AGENT: owner}}
        container.__getitem__ = lambda _self, key: payload[key]
        return container

    def _agent(self, monkeypatch: pytest.MonkeyPatch, entries: list[MagicMock]) -> Any:
        agent = MagicMock()
        agent.id = AgentId("test-agent")
        docker = MagicMock()
        docker.containers.list = AsyncMock(return_value=entries)
        docker.close = AsyncMock()
        monkeypatch.setattr(docker_agent, "Docker", lambda *a, **kw: docker)
        monkeypatch.setattr(docker_agent, "container_from_docker_container", lambda c: MagicMock())
        return agent, docker

    async def test_only_our_kernels_are_described(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The listing already says which containers are ours; the rest cost nothing."""
        mine = self._entry(KernelId(uuid4()))
        theirs = self._entry(KernelId(uuid4()), owner="another-agent")
        not_a_kernel = self._entry(None)
        exited = self._entry(KernelId(uuid4()), state="exited")
        agent, _ = self._agent(monkeypatch, [mine, theirs, not_a_kernel, exited])

        result = await docker_agent.DockerAgent.enumerate_containers(agent)

        assert len(result) == 1
        mine.show.assert_awaited_once()
        for skipped in (theirs, not_a_kernel, exited):
            skipped.show.assert_not_awaited()

    async def test_a_kernel_that_cannot_be_described_refuses_the_listing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        good = self._entry(KernelId(uuid4()))
        bad = self._entry(
            KernelId(uuid4()), show=AsyncMock(side_effect=RuntimeError("inspect failed"))
        )
        agent, _ = self._agent(monkeypatch, [good, bad])

        with pytest.raises(ContainerEnumerationIncomplete):
            await docker_agent.DockerAgent.enumerate_containers(agent)

    async def test_a_kernel_removed_mid_listing_is_absence_not_a_refusal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gone = self._entry(
            KernelId(uuid4()),
            show=AsyncMock(side_effect=DockerError(HTTPStatus.NOT_FOUND, "no such container")),
        )
        agent, _ = self._agent(monkeypatch, [gone])

        assert await docker_agent.DockerAgent.enumerate_containers(agent) == []

    async def test_a_failing_listing_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        agent, docker = self._agent(monkeypatch, [])
        docker.containers.list = AsyncMock(side_effect=RuntimeError("docker is unreachable"))

        with pytest.raises(RuntimeError):
            await docker_agent.DockerAgent.enumerate_containers(agent)
