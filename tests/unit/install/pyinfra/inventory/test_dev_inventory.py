"""Tests for DevInventoryBuilder and shared_defaults."""

from __future__ import annotations

import pytest

from ai.backend.install.pyinfra.configs.cores import (
    AppProxyConfig,
    ControlPanelConfig,
    LicenseServerConfig,
    ManagerConfig,
    StorageProxyConfig,
    WebserverConfig,
)
from ai.backend.install.pyinfra.configs.halfstack import (
    EtcdConfig,
    PostgreSQLConfig,
    RedisConfig,
)
from ai.backend.install.pyinfra.configs.pro import FastTrackConfig
from ai.backend.install.pyinfra.inventory.dev_inventory import DevInventoryBuilder
from ai.backend.install.pyinfra.inventory.shared_defaults import (
    APPPROXY_COORDINATOR_PORT,
    APPPROXY_WORKER_INTERACTIVE_PORT,
    APPPROXY_WORKER_INTERACTIVE_RANGE,
    APPPROXY_WORKER_TCP_PORT,
    APPPROXY_WORKER_TCP_RANGE,
    DEFAULT_VERSIONS,
    DEV_DEFAULTS,
    HALFSTACK_PORTS,
)


class TestSharedDefaults:
    def test_halfstack_ports_are_ints(self) -> None:
        for name, port in HALFSTACK_PORTS.items():
            assert isinstance(port, int), f"{name} should be int"

    def test_appproxy_port_ranges(self) -> None:
        assert APPPROXY_WORKER_INTERACTIVE_RANGE[0] < APPPROXY_WORKER_INTERACTIVE_RANGE[1]
        assert APPPROXY_WORKER_TCP_RANGE[0] < APPPROXY_WORKER_TCP_RANGE[1]

    def test_default_versions_has_traefik(self) -> None:
        assert "traefik" in DEFAULT_VERSIONS
        assert "traefik_plugin" in DEFAULT_VERSIONS

    def test_dev_defaults_has_credentials(self) -> None:
        assert "postgres_password" in DEV_DEFAULTS
        assert "superadmin_password" in DEV_DEFAULTS
        assert "appproxy_db_user" in DEV_DEFAULTS


class TestDevInventoryBuilder:
    @pytest.fixture()
    def builder(self) -> DevInventoryBuilder:
        return DevInventoryBuilder()

    @pytest.fixture()
    def inventory(self, builder: DevInventoryBuilder) -> dict:
        return builder.build()

    def test_build_returns_dict(self, inventory: dict) -> None:
        assert isinstance(inventory, dict)

    def test_node_groups_present(self, inventory: dict) -> None:
        expected_groups = [
            "mgmt",
            "compute",
            "agent",
            "mgr",
            "web",
            "sp",
            "apc",
            "apw",
            "dashboard",
        ]
        for group in expected_groups:
            assert group in inventory, f"Missing node group: {group}"

    def test_mgmt_has_one_local_node(self, inventory: dict) -> None:
        mgmt = inventory["mgmt"]
        assert len(mgmt) == 1
        host, data = mgmt[0]
        assert host == "@local"
        assert isinstance(data, dict)

    def test_compute_is_empty(self, inventory: dict) -> None:
        assert inventory["compute"] == []
        assert inventory["agent"] == []

    def test_host_data_has_required_keys(self, inventory: dict) -> None:
        _, data = inventory["mgmt"][0]
        required = [
            "bai_home_dir",
            "bai_user",
            "bai_user_id",
            "bai_user_group_id",
            "python_version",
            "bai_version",
            "bai_default_versions",
            "services",
            "mode",
            "internal_ip",
            "public_ip",
        ]
        for key in required:
            assert key in data, f"Missing host data key: {key}"

    def test_services_dict_has_all_services(self, inventory: dict) -> None:
        _, data = inventory["mgmt"][0]
        services = data["services"]
        expected = [
            "postgres",
            "redis",
            "etcd",
            "bai_core",
            "manager",
            "webserver",
            "storage_proxy",
            "appproxy",
            "hive_gateway",
            "agent",
            "license_server",
            "control_panel",
            "fasttrack",
        ]
        for svc in expected:
            assert svc in services, f"Missing service: {svc}"

    def test_service_types(self, inventory: dict) -> None:
        _, data = inventory["mgmt"][0]
        services = data["services"]
        assert isinstance(services["postgres"], PostgreSQLConfig)
        assert isinstance(services["redis"], RedisConfig)
        assert isinstance(services["etcd"], EtcdConfig)
        assert isinstance(services["manager"], ManagerConfig)
        assert isinstance(services["webserver"], WebserverConfig)
        assert isinstance(services["storage_proxy"], StorageProxyConfig)
        assert isinstance(services["appproxy"], AppProxyConfig)

    def test_enterprise_stubs_disabled(self, inventory: dict) -> None:
        _, data = inventory["mgmt"][0]
        services = data["services"]
        assert isinstance(services["license_server"], LicenseServerConfig)
        assert services["license_server"].enabled is False
        assert isinstance(services["control_panel"], ControlPanelConfig)
        assert services["control_panel"].enabled is False
        assert isinstance(services["fasttrack"], FastTrackConfig)
        assert services["fasttrack"].enabled is False

    def test_ports_match_halfstack(self, inventory: dict) -> None:
        _, data = inventory["mgmt"][0]
        services = data["services"]
        assert services["postgres"].port == HALFSTACK_PORTS["postgres"]
        assert services["redis"].port == HALFSTACK_PORTS["redis"]
        assert services["etcd"].advertised_client_port == HALFSTACK_PORTS["etcd"]

    def test_appproxy_ports(self, inventory: dict) -> None:
        _, data = inventory["mgmt"][0]
        appproxy = data["services"]["appproxy"]
        assert appproxy.coordinator_port == APPPROXY_COORDINATOR_PORT
        assert appproxy.worker_interactive_port == APPPROXY_WORKER_INTERACTIVE_PORT
        assert appproxy.worker_tcp_port == APPPROXY_WORKER_TCP_PORT

    def test_credentials_from_shared_defaults(self, inventory: dict) -> None:
        _, data = inventory["mgmt"][0]
        services = data["services"]
        assert services["postgres"].password == DEV_DEFAULTS["postgres_password"]
        assert services["manager"].superadmin_password == DEV_DEFAULTS["superadmin_password"]
        assert services["appproxy"].db_user == DEV_DEFAULTS["appproxy_db_user"]

    def test_config_objects_in_inventory(self, inventory: dict) -> None:
        config_keys = [
            "postgresConfig",
            "redisConfig",
            "etcdConfig",
            "backendAICoreConfig",
            "managerConfig",
            "webserverConfig",
            "storageProxyConfig",
            "appProxyConfig",
        ]
        for key in config_keys:
            assert key in inventory, f"Missing config object: {key}"

    def test_custom_public_facing_address(self) -> None:
        builder = DevInventoryBuilder(public_facing_address="192.168.1.100")
        inv = builder.build()
        _, data = inv["mgmt"][0]
        assert data["internal_ip"] == "192.168.1.100"
        services = data["services"]
        assert services["appproxy"].coordinator_hostname == "192.168.1.100"

    def test_default_versions_in_host_data(self, inventory: dict) -> None:
        _, data = inventory["mgmt"][0]
        versions = data["bai_default_versions"]
        assert "traefik" in versions
        assert versions["traefik"] == DEFAULT_VERSIONS["traefik"]

    def test_secrets_are_unique(self) -> None:
        builder1 = DevInventoryBuilder()
        builder2 = DevInventoryBuilder()
        assert builder1.api_secret != builder2.api_secret
        assert builder1.jwt_secret != builder2.jwt_secret
