"""Tests for Docker container enumeration completeness."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.agent.types import ContainerEnumerationResult
from ai.backend.common.docker import LabelName
from ai.backend.common.types import AgentId, ContainerStatus, KernelId


@pytest.fixture
def agent() -> DockerAgent:
    instance = object.__new__(DockerAgent)
    instance.id = AgentId("test-agent")
    return instance


@pytest.fixture
def failed_inspection(mocker: MockerFixture, agent: DockerAgent) -> RuntimeError:
    kernel_id = KernelId(uuid4())
    error = RuntimeError("container inspection failed")
    container = MagicMock()
    container._id = "container-id"
    container.show = AsyncMock(side_effect=error)
    container.__getitem__.side_effect = {
        "State": {"Status": ContainerStatus.RUNNING},
        "Config": {"Labels": {LabelName.OWNER_AGENT: str(agent.id)}},
    }.__getitem__

    docker = MagicMock()
    docker.containers.list = AsyncMock(return_value=[container])
    docker.close = AsyncMock()
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker)
    mocker.patch(
        "ai.backend.agent.docker.agent.get_kernel_id_from_container",
        AsyncMock(return_value=kernel_id),
    )
    return error


class TestEnumerateContainers:
    async def test_inspection_failure_marks_the_listing_incomplete(
        self,
        agent: DockerAgent,
        failed_inspection: RuntimeError,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        result = await agent.enumerate_containers()

        assert result == ContainerEnumerationResult(containers=[], complete=False)
        warning = next(
            record
            for record in caplog.records
            if "incomplete container enumeration" in record.getMessage()
        )
        assert warning.exc_info is not None
        assert warning.exc_info[1] is failed_inspection

    async def test_first_failure_cancels_and_awaits_sibling_fetches(
        self,
        mocker: MockerFixture,
        agent: DockerAgent,
    ) -> None:
        slow_started = asyncio.Event()
        slow_cancelled = asyncio.Event()

        async def _fail_show() -> None:
            await slow_started.wait()
            raise RuntimeError("container inspection failed")

        async def _slow_show() -> None:
            slow_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                slow_cancelled.set()
                raise

        def _container(container_id: str, show: AsyncMock) -> MagicMock:
            container = MagicMock()
            container._id = container_id
            container.show = show
            container.__getitem__.side_effect = {
                "State": {"Status": ContainerStatus.RUNNING},
                "Config": {"Labels": {LabelName.OWNER_AGENT: str(agent.id)}},
            }.__getitem__
            return container

        failing = _container("failing", AsyncMock(side_effect=_fail_show))
        slow = _container("slow", AsyncMock(side_effect=_slow_show))
        kernel_ids = {
            failing._id: KernelId(uuid4()),
            slow._id: KernelId(uuid4()),
        }

        async def _get_kernel_id(container: MagicMock) -> KernelId:
            return kernel_ids[container._id]

        docker = MagicMock()
        docker.containers.list = AsyncMock(return_value=[failing, slow])
        docker.close = AsyncMock()
        mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker)
        mocker.patch(
            "ai.backend.agent.docker.agent.get_kernel_id_from_container",
            side_effect=_get_kernel_id,
        )

        result = await agent.enumerate_containers()

        assert result == ContainerEnumerationResult(containers=[], complete=False)
        assert slow_cancelled.is_set()
        docker.close.assert_awaited_once()
