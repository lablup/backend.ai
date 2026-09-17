from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import pytest

from ai.backend.install.types import InstallVariable

from .conftest import InstallerHarness


def _read_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text())


class TestConfigureManager:
    async def test_every_substitution_lands(self, harness: InstallerHarness) -> None:
        await harness.configure_manager()

    async def test_ports_come_from_install_info(self, harness: InstallerHarness) -> None:
        await harness.configure_manager()

        config = _read_toml(harness.base_path / "manager.toml")
        service = harness.install_info.service_config
        halfstack = harness.install_info.halfstack_config
        etcd_face = halfstack.etcd_addr[0].face
        postgres_face = halfstack.postgres_addr.face
        assert etcd_face is not None
        assert postgres_face is not None
        assert config["manager"]["service-addr"]["port"] == service.manager_addr.bind.port
        assert config["etcd"]["addr"]["port"] == etcd_face.port
        assert config["db"]["addr"]["port"] == postgres_face.port
        assert config["manager"]["ipc-base-path"] == service.manager_ipc_base_path


class TestConfigureAgent:
    async def test_every_substitution_lands(self, harness: InstallerHarness) -> None:
        await harness.configure_agent()

    async def test_ports_come_from_install_info(self, harness: InstallerHarness) -> None:
        await harness.configure_agent()

        config = _read_toml(harness.base_path / "agent.toml")
        service = harness.install_info.service_config
        assert config["agent"]["rpc-listen-addr"]["port"] == service.agent_rpc_addr.bind.port
        assert config["watcher"]["service-addr"]["port"] == service.agent_watcher_addr.bind.port
        assert config["agent"]["ipc-base-path"] == service.agent_ipc_base_path
        assert config["agent"]["var-base-path"] == service.agent_var_base_path


class TestConfigureSftpAgent:
    @pytest.fixture
    def install_variable(self) -> InstallVariable:
        return InstallVariable(public_facing_address="127.0.0.1", with_sftp_agent=True)

    async def test_every_substitution_lands(self, harness: InstallerHarness) -> None:
        await harness.configure_agent()
        await harness.configure_sftp_agent()

    async def test_identity_is_distinct_from_the_main_agent(
        self, harness: InstallerHarness
    ) -> None:
        await harness.configure_agent()
        await harness.configure_sftp_agent()

        sftp_options = harness.install_info.service_config.sftp_agent
        assert sftp_options is not None
        agent = _read_toml(harness.base_path / "agent.toml")
        sftp = _read_toml(harness.base_path / "agent-sftp.toml")
        assert sftp["agent"]["id"] != agent["agent"].get("id")
        assert sftp["agent"]["rpc-listen-addr"]["port"] == sftp_options.rpc_addr.bind.port
        assert sftp["agent"]["ipc-base-path"] == sftp_options.ipc_base_path


class TestConfigureStorageProxy:
    async def test_every_substitution_lands(self, harness: InstallerHarness) -> None:
        await harness.configure_storage_proxy()

    async def test_facing_addresses_come_from_install_info(self, harness: InstallerHarness) -> None:
        await harness.configure_storage_proxy()

        config = _read_toml(harness.base_path / "storage-proxy.toml")
        service = harness.install_info.service_config
        assert (
            config["api"]["client"]["service-addr"]["port"]
            == service.storage_proxy_client_facing_addr.bind.port
        )
        assert (
            config["api"]["manager"]["service-addr"]["port"]
            == service.storage_proxy_manager_facing_addr.bind.port
        )


class TestConfigureWebserver:
    async def test_every_substitution_lands(self, harness: InstallerHarness) -> None:
        await harness.configure_webserver()


class TestConfigureAppproxy:
    async def test_every_substitution_lands(self, harness: InstallerHarness) -> None:
        await harness.configure_appproxy()

    async def test_worker_ports_stay_distinct(self, harness: InstallerHarness) -> None:
        await harness.configure_appproxy()

        service = harness.install_info.service_config
        http_worker = _read_toml(harness.base_path / "app-proxy-worker.toml")
        tcp_worker = _read_toml(harness.base_path / "app-proxy-worker-tcp.toml")
        http_port = http_worker["proxy_worker"]["api_bind_addr"]["port"]
        tcp_port = tcp_worker["proxy_worker"]["api_bind_addr"]["port"]
        assert http_port != tcp_port
        assert http_port == service.appproxy_worker_addr.bind.port
        assert tcp_port == service.appproxy_tcp_worker_addr.bind.port
        assert http_worker["proxy_worker"]["protocol"] == "http"
        assert tcp_worker["proxy_worker"]["protocol"] == "tcp"
