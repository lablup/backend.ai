from __future__ import annotations

from typing import Any

import tomli

from ai.backend.agent.config.sd_migration import AGENT_MAPPING_RULES
from ai.backend.appproxy.coordinator.sd_migration import COORDINATOR_MAPPING_RULES
from ai.backend.appproxy.worker.sd_migration import WORKER_MAPPING_RULES
from ai.backend.common.configs.migration.migrator import ConfigMigrator
from ai.backend.common.configs.migration.types import (
    DetectedField,
    GeneratedEndpoint,
    MappingRule,
    MigrationResult,
)
from ai.backend.manager.config.sd_migration import MANAGER_MAPPING_RULES
from ai.backend.storage.config.sd_migration import STORAGE_MAPPING_RULES


class TestExtractField:
    """Tests for ConfigMigrator.extract_field."""

    def test_inline_table(self) -> None:
        config = {"agent": {"rpc-listen-addr": {"host": "127.0.0.1", "port": 6001}}}
        result = ConfigMigrator.extract_field(config, "agent.rpc-listen-addr")
        assert result == ("127.0.0.1", 6001)

    def test_nested_table(self) -> None:
        config = {"api": {"manager": {"service-addr": {"host": "0.0.0.0", "port": 6022}}}}
        result = ConfigMigrator.extract_field(config, "api.manager.service-addr")
        assert result == ("0.0.0.0", 6022)

    def test_missing_key_returns_none(self) -> None:
        config = {"agent": {"other-field": "value"}}
        result = ConfigMigrator.extract_field(config, "agent.rpc-listen-addr")
        assert result is None

    def test_deep_missing_key_returns_none(self) -> None:
        config: dict[str, Any] = {"api": {}}
        result = ConfigMigrator.extract_field(config, "api.manager.service-addr")
        assert result is None

    def test_non_mapping_intermediate_returns_none(self) -> None:
        config = {"agent": "not-a-table"}
        result = ConfigMigrator.extract_field(config, "agent.rpc-listen-addr")
        assert result is None

    def test_value_without_host_port_returns_none(self) -> None:
        config: dict[str, Any] = {"agent": {"rpc-listen-addr": "plain-string"}}
        result = ConfigMigrator.extract_field(config, "agent.rpc-listen-addr")
        assert result is None

    def test_single_level_key(self) -> None:
        config = {"service-addr": {"host": "10.0.0.1", "port": 8080}}
        result = ConfigMigrator.extract_field(config, "service-addr")
        assert result == ("10.0.0.1", 8080)

    def test_port_as_string_is_coerced_to_int(self) -> None:
        config = {"agent": {"addr": {"host": "localhost", "port": "8080"}}}
        result = ConfigMigrator.extract_field(config, "agent.addr")
        assert result == ("localhost", 8080)


class TestCheckExistingEndpoints:
    """Tests for ConfigMigrator.check_existing_endpoints."""

    def test_no_sd_section(self) -> None:
        config: dict[str, Any] = {"agent": {"rpc-listen-addr": {"host": "127.0.0.1", "port": 6001}}}
        assert ConfigMigrator.check_existing_endpoints(config) is False

    def test_empty_endpoints(self) -> None:
        config: dict[str, Any] = {"service-discovery": {"endpoints": []}}
        assert ConfigMigrator.check_existing_endpoints(config) is False

    def test_existing_endpoints(self) -> None:
        config: dict[str, Any] = {
            "service-discovery": {
                "endpoints": [
                    {
                        "role": "api",
                        "scope": "cluster",
                        "address": "127.0.0.1",
                        "port": 8080,
                        "protocol": "http",
                    },
                ],
            },
        }
        assert ConfigMigrator.check_existing_endpoints(config) is True

    def test_sd_section_without_endpoints_key(self) -> None:
        config: dict[str, Any] = {"service-discovery": {"type": "redis"}}
        assert ConfigMigrator.check_existing_endpoints(config) is False


class TestMigrate:
    """Tests for ConfigMigrator.migrate."""

    def test_successful_migration(self) -> None:
        config = {
            "manager": {"service-addr": {"host": "0.0.0.0", "port": 8081}},
        }
        rules = [
            MappingRule(
                source="manager.service-addr", role="api", scope="cluster", protocol="http"
            ),
        ]
        migrator = ConfigMigrator(rules)
        result = migrator.migrate(config)

        assert len(result.detected_fields) == 1
        assert len(result.generated_endpoints) == 1
        assert result.skipped_rules == []
        assert result.generated_endpoints[0].role == "api"
        assert result.generated_endpoints[0].address == "0.0.0.0"
        assert result.generated_endpoints[0].port == 8081

    def test_fallback_used(self) -> None:
        config = {
            "agent": {"rpc-listen-addr": {"host": "127.0.0.1", "port": 6001}},
        }
        rules = [
            MappingRule(
                source="agent.advertised-rpc-addr",
                fallback="agent.rpc-listen-addr",
                role="rpc",
                scope="cluster",
                protocol="zmq",
            ),
        ]
        migrator = ConfigMigrator(rules)
        result = migrator.migrate(config)

        assert len(result.detected_fields) == 1
        assert result.detected_fields[0].is_fallback is True
        assert result.detected_fields[0].key_path == "agent.rpc-listen-addr"
        assert len(result.generated_endpoints) == 1

    def test_skip_when_both_missing(self) -> None:
        config: dict[str, Any] = {"agent": {}}
        rules = [
            MappingRule(
                source="agent.advertised-rpc-addr",
                fallback="agent.rpc-listen-addr",
                role="rpc",
                scope="cluster",
                protocol="zmq",
            ),
        ]
        migrator = ConfigMigrator(rules)
        result = migrator.migrate(config)

        assert len(result.detected_fields) == 0
        assert len(result.generated_endpoints) == 0
        assert len(result.skipped_rules) == 1

    def test_multiple_rules(self) -> None:
        config = {
            "manager": {"service-addr": {"host": "0.0.0.0", "port": 8081}},
            "agent": {"rpc-listen-addr": {"host": "127.0.0.1", "port": 6001}},
        }
        rules = [
            MappingRule(
                source="manager.service-addr", role="api", scope="cluster", protocol="http"
            ),
            MappingRule(
                source="agent.rpc-listen-addr", role="rpc", scope="cluster", protocol="zmq"
            ),
        ]
        migrator = ConfigMigrator(rules)
        result = migrator.migrate(config)

        assert len(result.generated_endpoints) == 2

    def test_has_existing_endpoints_flag(self) -> None:
        config: dict[str, Any] = {
            "service-discovery": {
                "endpoints": [
                    {"role": "x", "scope": "y", "address": "a", "port": 1, "protocol": "http"},
                ],
            },
            "manager": {"service-addr": {"host": "0.0.0.0", "port": 8081}},
        }
        rules = [
            MappingRule(
                source="manager.service-addr", role="api", scope="cluster", protocol="http"
            ),
        ]
        migrator = ConfigMigrator(rules)
        result = migrator.migrate(config)
        assert result.has_existing_endpoints is True


class TestGenerateTomlSection:
    """Tests for ConfigMigrator.generate_toml_section."""

    def test_output_is_valid_toml(self) -> None:
        result = _make_result_with_endpoints()
        output = ConfigMigrator.generate_toml_section(result)
        parsed = tomli.loads(output)
        assert "service-discovery" in parsed
        assert len(parsed["service-discovery"]["endpoints"]) == 1
        ep = parsed["service-discovery"]["endpoints"][0]
        assert ep["role"] == "api"
        assert ep["port"] == 8081

    def test_multiple_endpoints(self) -> None:
        result = _make_result_with_multiple_endpoints()
        output = ConfigMigrator.generate_toml_section(result)
        parsed = tomli.loads(output)
        assert len(parsed["service-discovery"]["endpoints"]) == 2


class TestFormatDryRunOutput:
    """Tests for ConfigMigrator.format_dry_run_output."""

    def test_includes_detected_fields_comment(self) -> None:
        result = _make_result_with_endpoints()
        output = ConfigMigrator.format_dry_run_output(result)
        assert "# Detected fields" in output
        assert "manager.service-addr" in output

    def test_includes_skipped_rules(self) -> None:
        rule = MappingRule(source="x.y", role="r", scope="s", protocol="p")
        result = MigrationResult(
            detected_fields=[],
            generated_endpoints=[],
            skipped_rules=[(rule, "field not found: x.y")],
            has_existing_endpoints=False,
        )
        output = ConfigMigrator.format_dry_run_output(result)
        assert "Skipped rules" in output
        assert "field not found" in output

    def test_no_endpoints_message(self) -> None:
        result = MigrationResult(
            detected_fields=[],
            generated_endpoints=[],
            skipped_rules=[],
            has_existing_endpoints=False,
        )
        output = ConfigMigrator.format_dry_run_output(result)
        assert "No endpoints were generated" in output

    def test_fallback_marker_shown(self) -> None:
        result = _make_result_with_fallback()
        output = ConfigMigrator.format_dry_run_output(result)
        assert "(fallback)" in output


class TestAgentMapping:
    """Tests for agent mapping rules against realistic config."""

    def test_agent_full_config(self) -> None:
        config = {
            "agent": {
                "advertised-rpc-addr": {"host": "10.0.0.5", "port": 6001},
                "rpc-listen-addr": {"host": "127.0.0.1", "port": 6001},
                "announce-internal-addr": {"host": "10.0.0.5", "port": 6003},
                "service-addr": {"host": "0.0.0.0", "port": 6003},
            },
        }
        migrator = ConfigMigrator(AGENT_MAPPING_RULES)
        result = migrator.migrate(config)
        assert len(result.generated_endpoints) == 3
        assert all(not f.is_fallback for f in result.detected_fields)

    def test_agent_fallback(self) -> None:
        config = {
            "agent": {
                "rpc-listen-addr": {"host": "127.0.0.1", "port": 6001},
                "service-addr": {"host": "0.0.0.0", "port": 6003},
            },
        }
        migrator = ConfigMigrator(AGENT_MAPPING_RULES)
        result = migrator.migrate(config)
        # Rule 1: advertised-rpc-addr missing → fallback to rpc-listen-addr
        # Rule 2: announce-internal-addr missing → fallback to service-addr
        # Rule 3: announce-internal-addr missing, no fallback → skipped
        assert len(result.generated_endpoints) == 2
        assert len(result.skipped_rules) == 1
        fallback_fields = [f for f in result.detected_fields if f.is_fallback]
        assert len(fallback_fields) == 2


class TestManagerMapping:
    """Tests for manager mapping rules against realistic config."""

    def test_manager_config(self) -> None:
        config = {
            "manager": {"service-addr": {"host": "0.0.0.0", "port": 8081}},
        }
        migrator = ConfigMigrator(MANAGER_MAPPING_RULES)
        result = migrator.migrate(config)
        assert len(result.generated_endpoints) == 1
        assert result.generated_endpoints[0].role == "api"


class TestStorageMapping:
    """Tests for storage-proxy mapping rules against realistic config."""

    def test_storage_full_config(self) -> None:
        config = {
            "api": {
                "manager": {
                    "announce-addr": {"host": "10.0.0.10", "port": 6022},
                    "service-addr": {"host": "0.0.0.0", "port": 6022},
                    "announce-internal-addr": {"host": "10.0.0.10", "port": 16023},
                    "internal-addr": {"host": "0.0.0.0", "port": 16023},
                },
                "client": {
                    "service-addr": {"host": "0.0.0.0", "port": 6021},
                },
            },
        }
        migrator = ConfigMigrator(STORAGE_MAPPING_RULES)
        result = migrator.migrate(config)
        assert len(result.generated_endpoints) == 3

    def test_storage_fallback(self) -> None:
        config = {
            "api": {
                "manager": {
                    "service-addr": {"host": "0.0.0.0", "port": 6022},
                    "internal-addr": {"host": "0.0.0.0", "port": 16023},
                },
                "client": {
                    "service-addr": {"host": "0.0.0.0", "port": 6021},
                },
            },
        }
        migrator = ConfigMigrator(STORAGE_MAPPING_RULES)
        result = migrator.migrate(config)
        assert len(result.generated_endpoints) == 3
        fallback_fields = [f for f in result.detected_fields if f.is_fallback]
        assert len(fallback_fields) == 2


class TestCoordinatorMapping:
    """Tests for app-proxy coordinator mapping rules."""

    def test_coordinator_config(self) -> None:
        config = {
            "proxy_coordinator": {
                "announce_addr": {"host": "10.0.0.20", "port": 8200},
            },
        }
        migrator = ConfigMigrator(COORDINATOR_MAPPING_RULES)
        result = migrator.migrate(config)
        assert len(result.generated_endpoints) == 1
        assert result.generated_endpoints[0].role == "api"

    def test_coordinator_fallback(self) -> None:
        config = {
            "proxy_coordinator": {
                "advertised_addr": {"host": "10.0.0.20", "port": 8200},
            },
        }
        migrator = ConfigMigrator(COORDINATOR_MAPPING_RULES)
        result = migrator.migrate(config)
        assert len(result.generated_endpoints) == 1
        assert result.detected_fields[0].is_fallback is True


class TestWorkerMapping:
    """Tests for app-proxy worker mapping rules."""

    def test_worker_config(self) -> None:
        config = {
            "proxy_worker": {
                "announce_addr": {"host": "10.0.0.30", "port": 8300},
            },
        }
        migrator = ConfigMigrator(WORKER_MAPPING_RULES)
        result = migrator.migrate(config)
        assert len(result.generated_endpoints) == 1

    def test_worker_fallback(self) -> None:
        config = {
            "proxy_worker": {
                "api_advertised_addr": {"host": "10.0.0.30", "port": 8300},
            },
        }
        migrator = ConfigMigrator(WORKER_MAPPING_RULES)
        result = migrator.migrate(config)
        assert len(result.generated_endpoints) == 1
        assert result.detected_fields[0].is_fallback is True


# -- helpers --


def _make_result_with_endpoints() -> MigrationResult:
    field = DetectedField(
        key_path="manager.service-addr", host="0.0.0.0", port=8081, is_fallback=False
    )
    ep = GeneratedEndpoint(
        role="api",
        scope="cluster",
        address="0.0.0.0",
        port=8081,
        protocol="http",
        source_field=field,
    )
    return MigrationResult(
        detected_fields=[field],
        generated_endpoints=[ep],
        skipped_rules=[],
        has_existing_endpoints=False,
    )


def _make_result_with_multiple_endpoints() -> MigrationResult:
    f1 = DetectedField(
        key_path="manager.service-addr", host="0.0.0.0", port=8081, is_fallback=False
    )
    f2 = DetectedField(
        key_path="agent.rpc-listen-addr", host="127.0.0.1", port=6001, is_fallback=False
    )
    e1 = GeneratedEndpoint(
        role="api", scope="cluster", address="0.0.0.0", port=8081, protocol="http", source_field=f1
    )
    e2 = GeneratedEndpoint(
        role="rpc",
        scope="cluster",
        address="127.0.0.1",
        port=6001,
        protocol="zmq",
        source_field=f2,
    )
    return MigrationResult(
        detected_fields=[f1, f2],
        generated_endpoints=[e1, e2],
        skipped_rules=[],
        has_existing_endpoints=False,
    )


def _make_result_with_fallback() -> MigrationResult:
    field = DetectedField(
        key_path="agent.rpc-listen-addr", host="127.0.0.1", port=6001, is_fallback=True
    )
    ep = GeneratedEndpoint(
        role="rpc",
        scope="cluster",
        address="127.0.0.1",
        port=6001,
        protocol="zmq",
        source_field=field,
    )
    return MigrationResult(
        detected_fields=[field],
        generated_endpoints=[ep],
        skipped_rules=[],
        has_existing_endpoints=False,
    )
