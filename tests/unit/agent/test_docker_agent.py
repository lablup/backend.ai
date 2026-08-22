"""
Unit tests for `ai.backend.agent.docker.agent` helpers.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiodocker.exceptions import DockerError

from ai.backend.agent.config.unified import (
    AgentUnifiedConfig,
    ContainerLogDriver,
    ContainerLogsConfig,
)
from ai.backend.agent.docker.agent import (
    DockerKernelCreationContext,
    LogDriverOptions,
    _build_log_config,
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
        assert _parse_distro_from_ldd_output([output]) == expected

    @pytest.mark.parametrize(
        "chunk_size",
        [pytest.param(1, id="one-byte-chunks"), pytest.param(16, id="sixteen-byte-chunks")],
    )
    def test_detects_distro_from_chunked_log(self, chunk_size: int) -> None:
        output = "\r\n".join([
            LDD_PRELOAD_ERROR_LINES,
            "ldd (Ubuntu GLIBC 2.39-0ubuntu8.7) 2.39",
            LDD_GLIBC_TRAILER,
        ])
        chunks = [output[i : i + chunk_size] for i in range(0, len(output), chunk_size)]
        assert _parse_distro_from_ldd_output(chunks) == "ubuntu24.04"

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
        assert _parse_distro_from_ldd_output([output]) is None


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


def _log_config(driver: ContainerLogDriver) -> AgentUnifiedConfig:
    """Only ``container_logs`` is read, so leave the rest of the schema unpopulated."""
    fields: dict[str, Any] = {
        "container_logs": ContainerLogsConfig.model_validate({
            "driver": driver,
            "max_length": "10M",
        }),
    }
    return AgentUnifiedConfig.model_construct(**fields)


class TestBuildLogConfig:
    @pytest.mark.parametrize(
        "driver",
        [ContainerLogDriver.LOCAL, ContainerLogDriver.JSON_FILE],
    )
    def test_drivers_carry_size_options(self, driver: ContainerLogDriver) -> None:
        log_config = _build_log_config(_log_config(driver))

        assert log_config.type == driver
        assert log_config.config == LogDriverOptions(max_size="2m", max_file="5", compress="false")

    @pytest.mark.parametrize(
        ("driver", "expected"),
        [
            (
                ContainerLogDriver.LOCAL,
                {
                    "Type": "local",
                    "Config": {"max-size": "2m", "max-file": "5", "compress": "false"},
                },
            ),
            (
                ContainerLogDriver.JSON_FILE,
                {
                    "Type": "json-file",
                    "Config": {"max-size": "2m", "max-file": "5", "compress": "false"},
                },
            ),
        ],
    )
    def test_dumped_payload_uses_docker_api_keys(
        self, driver: ContainerLogDriver, expected: dict[str, Any]
    ) -> None:
        """The dump is what actually goes into the container creation request."""
        log_config = _build_log_config(_log_config(driver))

        dumped = log_config.model_dump(mode="json", by_alias=True)

        assert dumped == expected
        assert type(dumped["Type"]) is str
