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
    """The real `DockerAgent.enumerate_containers`, with aiodocker stubbed out."""

    @staticmethod
    def _container(kernel_id: KernelId, *, show: Any) -> MagicMock:
        container = MagicMock()
        container._id = f"cid-{kernel_id}"
        container.show = show
        container.__getitem__ = lambda _self, key: {
            "State": {"Status": "running"},
            "Config": {"Labels": {LabelName.OWNER_AGENT: "test-agent"}},
        }[key]
        return container

    def _patch(
        self,
        monkeypatch: pytest.MonkeyPatch,
        pairs: list[tuple[KernelId, MagicMock]],
    ) -> Any:
        agent = MagicMock()
        agent.id = AgentId("test-agent")
        docker = MagicMock()
        docker.containers.list = AsyncMock(return_value=[c for _, c in pairs])
        docker.close = AsyncMock()
        by_container = {id(c): kid for kid, c in pairs}

        async def _kernel_id_of(container: Any) -> KernelId:
            return by_container[id(container)]

        monkeypatch.setattr(docker_agent, "Docker", lambda *a, **kw: docker)
        monkeypatch.setattr(docker_agent, "get_kernel_id_from_container", _kernel_id_of)
        monkeypatch.setattr(docker_agent, "container_from_docker_container", lambda c: MagicMock())
        return agent

    async def test_a_container_that_cannot_be_described_refuses_the_listing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        good_id, bad_id = KernelId(uuid4()), KernelId(uuid4())
        agent = self._patch(
            monkeypatch,
            [
                (good_id, self._container(good_id, show=AsyncMock())),
                (
                    bad_id,
                    self._container(
                        bad_id, show=AsyncMock(side_effect=RuntimeError("inspect failed"))
                    ),
                ),
            ],
        )

        with pytest.raises(ContainerEnumerationIncomplete):
            await docker_agent.DockerAgent.enumerate_containers(agent)

    async def test_a_container_removed_mid_listing_is_absence_not_a_refusal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A 404 between the listing and the describe is the one absence this may infer."""
        gone_id = KernelId(uuid4())
        agent = self._patch(
            monkeypatch,
            [
                (
                    gone_id,
                    self._container(
                        gone_id,
                        show=AsyncMock(
                            side_effect=DockerError(HTTPStatus.NOT_FOUND, "no such container")
                        ),
                    ),
                )
            ],
        )

        assert await docker_agent.DockerAgent.enumerate_containers(agent) == []

    async def test_a_complete_listing_is_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kernel_id = KernelId(uuid4())
        agent = self._patch(
            monkeypatch, [(kernel_id, self._container(kernel_id, show=AsyncMock()))]
        )

        result = await docker_agent.DockerAgent.enumerate_containers(agent)

        assert [kid for kid, _ in result] == [kernel_id]
