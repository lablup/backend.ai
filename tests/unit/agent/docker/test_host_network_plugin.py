from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.docker.intrinsic import HostNetworkPlugin
from ai.backend.agent.docker.kernel import DockerKernel

SSHD: dict[str, Any] = {"name": "sshd", "protocol": "tcp", "container_ports": (2200,)}
TTYD: dict[str, Any] = {"name": "ttyd", "protocol": "http", "container_ports": (7681,)}
JUPYTER: dict[str, Any] = {"name": "jupyter", "protocol": "http", "container_ports": (8080,)}
MULTI: dict[str, Any] = {"name": "multi", "protocol": "http", "container_ports": (8090, 8091)}

# (host port, container port) in the order `start_container` passes them:
# repl ports first, then each service's `container_ports`.
REPL_PORTS = [(30000, 2000), (30001, 2001)]
ALL_SERVICE_PORTS = [
    *REPL_PORTS,
    (30002, 2200),
    (30003, 7681),
    (30004, 8080),
    (30005, 8090),
    (30006, 8091),
]
MULTI_BEFORE_SSHD_PORTS = [*REPL_PORTS, (30005, 8090), (30006, 8091), (30002, 2200)]


def _make_kernel(service_ports: list[dict[str, Any]]) -> MagicMock:
    kernel = MagicMock(spec=DockerKernel)
    kernel.kernel_id = uuid.uuid4()
    kernel.service_ports = service_ports
    return kernel


@pytest.fixture
def plugin(tmp_path: Path) -> HostNetworkPlugin:
    return HostNetworkPlugin({}, {"container": {"scratch-root": tmp_path}})


@pytest.fixture
def kernel_with_all_services() -> MagicMock:
    return _make_kernel([SSHD, TTYD, JUPYTER, MULTI])


@pytest.fixture
def kernel_without_services() -> MagicMock:
    return _make_kernel([])


@pytest.fixture
def kernel_with_multi_before_sshd() -> MagicMock:
    return _make_kernel([MULTI, SSHD])


def _config_dir(scratch_root: Path, kernel: MagicMock) -> Path:
    config_dir = scratch_root / str(kernel.kernel_id) / "config"
    config_dir.mkdir(parents=True)
    return config_dir


class TestExposePorts:
    async def test_maps_container_ports_to_host_ports(
        self, plugin: HostNetworkPlugin, kernel_with_all_services: MagicMock
    ) -> None:
        info = await plugin.expose_ports(kernel_with_all_services, "10.0.0.1", ALL_SERVICE_PORTS)

        assert info.container_host == "10.0.0.1"
        assert info.services == {
            "replin": {2000: 30000},
            "replout": {2001: 30001},
            "sshd": {2200: 30002},
            "ttyd": {7681: 30003},
            "jupyter": {8080: 30004},
            "multi": {8090: 30005, 8091: 30006},
        }

    async def test_maps_only_repl_ports_without_services(
        self, plugin: HostNetworkPlugin, kernel_without_services: MagicMock
    ) -> None:
        info = await plugin.expose_ports(kernel_without_services, "10.0.0.1", REPL_PORTS)

        assert info.services == {"replin": {2000: 30000}, "replout": {2001: 30001}}


class TestPreparePortForward:
    async def test_writes_intrinsic_host_ports(
        self, plugin: HostNetworkPlugin, kernel_with_all_services: MagicMock, tmp_path: Path
    ) -> None:
        config_dir = _config_dir(tmp_path, kernel_with_all_services)

        await plugin.prepare_port_forward(kernel_with_all_services, "10.0.0.1", ALL_SERVICE_PORTS)

        assert json.loads((config_dir / "intrinsic-ports.json").read_text()) == {
            "replin": 30000,
            "replout": 30001,
            "sshd": 30002,
            "ttyd": 30003,
        }

    async def test_resolves_sshd_after_multi_port_service(
        self, plugin: HostNetworkPlugin, kernel_with_multi_before_sshd: MagicMock, tmp_path: Path
    ) -> None:
        config_dir = _config_dir(tmp_path, kernel_with_multi_before_sshd)

        await plugin.prepare_port_forward(
            kernel_with_multi_before_sshd, "10.0.0.1", MULTI_BEFORE_SSHD_PORTS
        )

        assert json.loads((config_dir / "intrinsic-ports.json").read_text()) == {
            "replin": 30000,
            "replout": 30001,
            "sshd": 30002,
        }
