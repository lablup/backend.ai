"""What the Docker container listing tells about a container that fails to be inspected."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from aiodocker.containers import DockerContainer
from aiodocker.exceptions import DockerError
from aiohttp import ClientConnectionError

from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.common.types import AgentId, KernelId

_KERNEL_ID = KernelId(UUID("9f8aa407-fbe4-46b3-b62e-f8641b255c9a"))


@dataclass(frozen=True)
class _InspectFailureCase:
    description: str
    inspect_error: Exception
    expected_failed_kernel_ids: frozenset[KernelId] = field(default_factory=frozenset)


class TestListingAContainerThatFailsToBeInspected:
    @pytest.fixture
    def docker_agent(self, case: _InspectFailureCase) -> Iterator[DockerAgent]:
        docker = MagicMock()
        docker.close = AsyncMock()
        container = DockerContainer(
            docker, Id="container-1", Names=[f"/kernel.python.{_KERNEL_ID}"], State="running"
        )
        docker.containers.list = AsyncMock(return_value=[container])
        with (
            patch("ai.backend.agent.docker.agent.Docker", return_value=docker),
            patch.object(container, "show", AsyncMock(side_effect=case.inspect_error)),
        ):
            agent = object.__new__(DockerAgent)
            agent.id = AgentId("test-agent")
            yield agent

    @pytest.mark.parametrize(
        "case",
        [
            _InspectFailureCase(
                description="the container is gone",
                inspect_error=DockerError(HTTPStatus.NOT_FOUND, "no such container"),
            ),
            _InspectFailureCase(
                description="Docker answers an error",
                inspect_error=DockerError(
                    HTTPStatus.INTERNAL_SERVER_ERROR, "context deadline exceeded"
                ),
                expected_failed_kernel_ids=frozenset({_KERNEL_ID}),
            ),
            _InspectFailureCase(
                description="Docker does not answer",
                inspect_error=ClientConnectionError("server disconnected"),
                expected_failed_kernel_ids=frozenset({_KERNEL_ID}),
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_only_a_kernel_whose_container_is_not_gone_is_reported(
        self, case: _InspectFailureCase, docker_agent: DockerAgent
    ) -> None:
        enumeration_result = await docker_agent.enumerate_containers()

        assert enumeration_result.containers == []
        assert enumeration_result.failed_kernel_ids == case.expected_failed_kernel_ids
