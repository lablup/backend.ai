"""
Unit tests for `ai.backend.agent.docker.agent` helpers.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiodocker.exceptions import DockerError

from ai.backend.agent.docker.agent import (
    DockerKernelCreationContext,
    _parse_distro_from_ldd_output,
)

LDD_PRELOAD_ERROR_LINES = "\n".join([
    "ERROR: ld.so: object '/opt/kernel/libbaihook.so' from LD_PRELOAD cannot be preloaded"
    " (file too short): ignored.",
    "ERROR: ld.so: object '/opt/kernel/libnvmlhook.ubuntu18.04.x86_64.so' from LD_PRELOAD cannot"
    " be preloaded (file too short): ignored.",
    "ERROR: ld.so: object '/opt/kernel/libcudahook.ubuntu18.04.x86_64.so' from /etc/ld.so.preload"
    " cannot be preloaded (file too short): ignored.",
])
LDD_GLIBC_TRAILER = "\n".join([
    "Copyright (C) 2024 Free Software Foundation, Inc.",
    "This is free software; see the source for copying conditions.  There is NO",
    "warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.",
    "Written by Roland McGrath and Ulrich Drepper.",
])


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


class TestParseDistroFromLddOutput:
    def test_glibc_version_on_first_line(self) -> None:
        output = f"ldd (GNU libc) 2.35\n{LDD_GLIBC_TRAILER}"

        assert _parse_distro_from_ldd_output(output) == "ubuntu22.04"

    def test_glibc_version_after_ld_preload_errors(self) -> None:
        output = "\n".join([
            LDD_PRELOAD_ERROR_LINES,
            "ldd (Ubuntu GLIBC 2.39-0ubuntu8.7) 2.39",
            LDD_GLIBC_TRAILER,
        ])

        assert _parse_distro_from_ldd_output(output) == "ubuntu24.04"

    def test_glibc_version_with_carriage_returns(self) -> None:
        output = "ERROR: ld.so: ignored.\r\nldd (Ubuntu GLIBC 2.31-0ubuntu9) 2.31\r\n"

        assert _parse_distro_from_ldd_output(output) == "ubuntu20.04"

    def test_glibc_version_with_patch_component(self) -> None:
        output = "ldd (GNU libc) 2.39.1"

        assert _parse_distro_from_ldd_output(output) == "ubuntu24.04"

    def test_unknown_glibc_version_falls_back_to_lower_known_version(self) -> None:
        output = "ldd (GNU libc) 2.33"

        assert _parse_distro_from_ldd_output(output) == "ubuntu20.04"

    def test_glibc_version_without_minor_component(self) -> None:
        output = "ldd (GNU libc) 2"

        assert _parse_distro_from_ldd_output(output) == "centos7.6"

    def test_glibc_version_older_than_known_versions(self) -> None:
        output = "ldd (GNU libc) 2.12"

        assert _parse_distro_from_ldd_output(output) == "centos7.6"

    def test_glibc_version_newer_than_known_versions(self) -> None:
        output = "ldd (GNU libc) 2.41"

        assert _parse_distro_from_ldd_output(output) == "ubuntu24.04"

    def test_musl_banner_on_first_line(self) -> None:
        output = "musl libc (x86_64)\nVersion 1.2.4\nDynamic Program Loader"

        assert _parse_distro_from_ldd_output(output) == "alpine3.8"

    def test_musl_banner_after_ld_preload_errors(self) -> None:
        output = f"{LDD_PRELOAD_ERROR_LINES}\nmusl libc (x86_64)\nVersion 1.2.4"

        assert _parse_distro_from_ldd_output(output) == "alpine3.8"

    def test_returns_none_when_no_libc_banner_found(self) -> None:
        output = f"{LDD_PRELOAD_ERROR_LINES}\nldd: command not found"

        assert _parse_distro_from_ldd_output(output) is None

    def test_returns_none_for_empty_output(self) -> None:
        assert _parse_distro_from_ldd_output("") is None


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
