"""
Unit tests for `DockerKernelCreationContext` helpers.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiodocker.exceptions import DockerError

from ai.backend.agent.docker.agent import DockerKernelCreationContext


def _make_container_show_response(networks: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    return {"NetworkSettings": {"Networks": networks}}


def _make_container_mock(networks: dict[str, dict[str, Any] | None]) -> MagicMock:
    container = MagicMock()
    container._id = "container-id"
    container.show = AsyncMock(return_value=_make_container_show_response(networks))
    return container


def _make_docker_mock(network_get: AsyncMock | None = None) -> MagicMock:
    docker = MagicMock()
    docker.networks = MagicMock()
    docker.networks.get = network_get if network_get is not None else AsyncMock()
    return docker


@pytest.fixture
def context() -> DockerKernelCreationContext:
    # `_attach_additional_networks` does not access any instance state, so we can
    # bypass __init__ and exercise the method on a bare instance.
    return DockerKernelCreationContext.__new__(DockerKernelCreationContext)


class TestAttachAdditionalNetworks:
    async def test_no_requested_networks_skips_inspect(
        self,
        context: DockerKernelCreationContext,
    ) -> None:
        container = _make_container_mock(networks={})
        docker = _make_docker_mock()

        await context._attach_additional_networks(docker, container, set())

        container.show.assert_not_called()
        docker.networks.get.assert_not_called()

    async def test_skips_network_already_attached_by_name(
        self,
        context: DockerKernelCreationContext,
    ) -> None:
        container = _make_container_mock(
            networks={"bridge": {"NetworkID": "bridge-id", "EndpointID": "ep-1"}},
        )
        connect_mock = AsyncMock()
        network = MagicMock()
        network.connect = connect_mock
        docker = _make_docker_mock(network_get=AsyncMock(return_value=network))

        await context._attach_additional_networks(docker, container, {"bridge"})

        container.show.assert_awaited_once()
        docker.networks.get.assert_not_called()
        connect_mock.assert_not_called()

    async def test_skips_network_already_attached_by_id(
        self,
        context: DockerKernelCreationContext,
    ) -> None:
        container = _make_container_mock(
            networks={"bridge": {"NetworkID": "net-abc"}},
        )
        connect_mock = AsyncMock()
        network = MagicMock()
        network.connect = connect_mock
        docker = _make_docker_mock(network_get=AsyncMock(return_value=network))

        await context._attach_additional_networks(docker, container, {"net-abc"})

        docker.networks.get.assert_not_called()
        connect_mock.assert_not_called()

    async def test_attaches_only_unattached_networks(
        self,
        context: DockerKernelCreationContext,
    ) -> None:
        container = _make_container_mock(
            networks={"bridge": {"NetworkID": "bridge-id"}},
        )
        connect_mock = AsyncMock()
        network = MagicMock()
        network.connect = connect_mock
        docker = _make_docker_mock(network_get=AsyncMock(return_value=network))

        await context._attach_additional_networks(docker, container, {"bridge", "macvlan-roce-0"})

        docker.networks.get.assert_awaited_once_with("macvlan-roce-0")
        connect_mock.assert_awaited_once_with({"Container": "container-id"})

    async def test_swallows_403_already_exists_race(
        self,
        context: DockerKernelCreationContext,
    ) -> None:
        # The container.show() snapshot says nothing is attached, but Docker
        # races us and reports the endpoint already exists during connect().
        container = _make_container_mock(networks={})
        connect_mock = AsyncMock(
            side_effect=DockerError(
                HTTPStatus.FORBIDDEN,
                "endpoint with name kernel.x already exists in network bridge",
            )
        )
        network = MagicMock()
        network.connect = connect_mock
        docker = _make_docker_mock(network_get=AsyncMock(return_value=network))

        await context._attach_additional_networks(docker, container, {"bridge"})

        connect_mock.assert_awaited_once()

    async def test_reraises_other_docker_errors(
        self,
        context: DockerKernelCreationContext,
    ) -> None:
        container = _make_container_mock(networks={})
        connect_mock = AsyncMock(
            side_effect=DockerError(
                HTTPStatus.NOT_FOUND,
                "network not found",
            )
        )
        network = MagicMock()
        network.connect = connect_mock
        docker = _make_docker_mock(network_get=AsyncMock(return_value=network))

        with pytest.raises(DockerError):
            await context._attach_additional_networks(docker, container, {"bridge"})

    async def test_tolerates_none_network_entry_in_container_show(
        self,
        context: DockerKernelCreationContext,
    ) -> None:
        """container.show() may return None for a network entry value."""
        container = _make_container_mock(
            networks={"bridge": None},
        )
        connect_mock = AsyncMock()
        network = MagicMock()
        network.connect = connect_mock
        docker = _make_docker_mock(network_get=AsyncMock(return_value=network))

        await context._attach_additional_networks(docker, container, {"macvlan-roce-0"})

        docker.networks.get.assert_awaited_once_with("macvlan-roce-0")
        connect_mock.assert_awaited_once()

    async def test_reraises_403_when_message_does_not_match(
        self,
        context: DockerKernelCreationContext,
    ) -> None:
        container = _make_container_mock(networks={})
        connect_mock = AsyncMock(
            side_effect=DockerError(
                HTTPStatus.FORBIDDEN,
                "permission denied",
            )
        )
        network = MagicMock()
        network.connect = connect_mock
        docker = _make_docker_mock(network_get=AsyncMock(return_value=network))

        with pytest.raises(DockerError):
            await context._attach_additional_networks(docker, container, {"bridge"})
