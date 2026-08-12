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
    @pytest.mark.parametrize(
        ("output", "expected"),
        [
            pytest.param(
                f"ldd (GNU libc) 2.35\n{LDD_GLIBC_TRAILER}",
                "ubuntu22.04",
                id="glibc-banner-on-first-line",
            ),
            pytest.param(
                "\n".join([
                    LDD_PRELOAD_ERROR_LINES,
                    "ldd (Ubuntu GLIBC 2.39-0ubuntu8.7) 2.39",
                    LDD_GLIBC_TRAILER,
                ]),
                "ubuntu24.04",
                id="glibc-banner-after-ld-preload-errors",
            ),
            pytest.param(
                "ERROR: ld.so: ignored.\r\nldd (Ubuntu GLIBC 2.31-0ubuntu9) 2.31\r\n",
                "ubuntu20.04",
                id="glibc-banner-with-carriage-returns",
            ),
            pytest.param(
                "ldd (GNU libc) 2.39.1",
                "ubuntu24.04",
                id="glibc-version-with-patch-component",
            ),
            pytest.param(
                "ldd (GNU libc) 2",
                "centos7.6",
                id="glibc-version-without-minor-component",
            ),
            pytest.param(
                "ldd (GNU libc) 2.33",
                "ubuntu20.04",
                id="glibc-version-between-known-versions",
            ),
            pytest.param(
                "ldd (GNU libc) 2.12",
                "centos7.6",
                id="glibc-version-older-than-known-versions",
            ),
            pytest.param(
                "ldd (GNU libc) 2.41",
                "ubuntu24.04",
                id="glibc-version-newer-than-known-versions",
            ),
            pytest.param(
                "musl libc (x86_64)\nVersion 1.2.4\nDynamic Program Loader",
                "alpine3.8",
                id="musl-banner-on-first-line",
            ),
            pytest.param(
                f"{LDD_PRELOAD_ERROR_LINES}\nmusl libc (x86_64)\nVersion 1.2.4",
                "alpine3.8",
                id="musl-banner-after-ld-preload-errors",
            ),
        ],
    )
    def test_detects_distro_from_libc_banner(self, output: str, expected: str) -> None:
        assert _parse_distro_from_ldd_output(output) == expected

    @pytest.mark.parametrize(
        "output",
        [
            pytest.param("", id="empty-output"),
            pytest.param(
                f"{LDD_PRELOAD_ERROR_LINES}\nldd: command not found",
                id="no-libc-banner",
            ),
            pytest.param("ldd (GNU libc)", id="banner-without-version"),
        ],
    )
    def test_returns_none_without_libc_banner(self, output: str) -> None:
        assert _parse_distro_from_ldd_output(output) is None


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
