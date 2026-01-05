from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from ai.backend.agent.affinity_map import AffinityPolicy
from ai.backend.agent.config.unified import (
    AgentBackend,
    AgentConfig,
    AgentConfigValidationContext,
    AgentGlobalConfig,
    AgentUnifiedConfig,
    ContainerConfig,
    ContainerSandboxType,
    CoreDumpConfig,
    DebugConfig,
    ResourceAllocationMode,
    ResourceConfig,
    ScratchType,
)
from ai.backend.agent.stats import StatModes
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.common.types import SlotName
from ai.backend.logging.config import (
    LoggingConfig,
    LogLevel,
    default_pkg_ns,
)

RawConfigT = dict[str, Any]


CONTEXT_DEFAULT_DEBUG = False
CONTEXT_DEFAULT_LOG_LEVEL = LogLevel.DEBUG


@pytest.fixture
def default_context() -> AgentConfigValidationContext:
    return AgentConfigValidationContext(
        debug=CONTEXT_DEFAULT_DEBUG,
        log_level=CONTEXT_DEFAULT_LOG_LEVEL,
        is_invoked_subcommand=False,
    )


class LoggingConfigTest:
    CONFIG_DEFAULT_LOG_LEVEL = LogLevel.INFO

    @pytest.fixture
    def default_raw_config(self) -> RawConfigT:
        return {
            "level": self.CONFIG_DEFAULT_LOG_LEVEL,
            "drivers": ["console"],
        }

    def test_level_field_uses_context_log_level(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        config = LoggingConfig.model_validate(default_raw_config, context=default_context)

        assert config.level == CONTEXT_DEFAULT_LOG_LEVEL

    def test_level_field_without_context(self, default_raw_config: RawConfigT) -> None:
        raw_config = {**default_raw_config, "level": LogLevel.WARNING}
        config = LoggingConfig.model_validate(raw_config, context=None)

        assert config.level == LogLevel.WARNING

    def test_level_field_with_notset_context(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        context = default_context.model_copy(update={"log_level": LogLevel.NOTSET})
        config = LoggingConfig.model_validate(default_raw_config, context=context)

        assert config.level == self.CONFIG_DEFAULT_LOG_LEVEL

    def test_pkg_ns_field_updates_ai_backend_from_context(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        raw_config = {**default_raw_config, "pkg-ns": None}
        config = LoggingConfig.model_validate(raw_config, context=default_context)

        assert "ai.backend" in config.pkg_ns
        assert config.pkg_ns["ai.backend"] == CONTEXT_DEFAULT_LOG_LEVEL

        # When value explicitly set, validator creates new dict with just "ai.backend"
        assert config.pkg_ns.keys() != default_pkg_ns.keys()

    def test_pkg_ns_field_merges_with_existing_values(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        raw_config = {**default_raw_config, "pkg-ns": {"aiohttp": LogLevel.ERROR}}
        context = default_context.model_copy(update={"log_level": LogLevel.WARNING})
        config = LoggingConfig.model_validate(raw_config, context=context)

        assert "ai.backend" in config.pkg_ns
        assert config.pkg_ns["ai.backend"] == LogLevel.WARNING
        assert "aiohttp" in config.pkg_ns
        assert config.pkg_ns["aiohttp"] == LogLevel.ERROR

    def test_pkg_ns_field_without_context(self, default_raw_config: RawConfigT) -> None:
        raw_config = {**default_raw_config, "pkg-ns": {"aiohttp": LogLevel.WARNING}}
        config = LoggingConfig.model_validate(raw_config, context=None)

        assert config.pkg_ns == {"aiohttp": LogLevel.WARNING}

    def test_pkg_ns_field_with_notset_context(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        raw_config = {**default_raw_config, "pkg-ns": {"aiohttp": LogLevel.WARNING}}
        context = default_context.model_copy(update={"log_level": LogLevel.NOTSET})
        config = LoggingConfig.model_validate(raw_config, context=context)

        assert config.pkg_ns == {"aiohttp": LogLevel.WARNING}


class CoreDumpConfigTest:
    @pytest.fixture
    def default_raw_config(self) -> RawConfigT:
        return {"enabled": True}

    @pytest.fixture
    def default_context(self) -> AgentConfigValidationContext:
        return AgentConfigValidationContext(
            debug=True,
            log_level=CONTEXT_DEFAULT_LOG_LEVEL,
            is_invoked_subcommand=False,
        )

    @patch.object(sys, "platform", "linux")
    def test_coredump_enabled_requires_absolute_core_pattern(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        # core_pattern with pipe pattern
        with patch("pathlib.Path.read_text", return_value="|/usr/lib/systemd/systemd-coredump"):
            with pytest.raises(ValidationError) as exc_info:
                CoreDumpConfig.model_validate(default_raw_config, context=default_context)

            assert "core_pattern must be an absolute path" in str(exc_info.value)

        # core_pattern with relative path
        with patch("pathlib.Path.read_text", return_value="core.%p"):
            with pytest.raises(ValidationError) as exc_info:
                CoreDumpConfig.model_validate(default_raw_config, context=default_context)

            assert "core_pattern must be an absolute path" in str(exc_info.value)

    @patch.object(sys, "platform", "linux")
    def test_coredump_enabled_succeeds_with_absolute_core_pattern_on_linux(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        with patch("pathlib.Path.read_text", return_value="/var/lib/coredumps/core.%p"):
            config = CoreDumpConfig.model_validate(default_raw_config, context=default_context)

        assert config.enabled is True
        assert config.core_path == Path("/var/lib/coredumps")

    @patch.object(sys, "platform", "darwin")
    def test_coredump_enabled_fails_on_non_linux_darwin(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CoreDumpConfig.model_validate(default_raw_config, context=default_context)

        assert "only supported in Linux" in str(exc_info.value)

    @patch.object(sys, "platform", "win32")
    def test_coredump_enabled_fails_on_non_linux_windows(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CoreDumpConfig.model_validate(default_raw_config, context=default_context)

        assert "only supported in Linux" in str(exc_info.value)

    def test_coredump_disabled_does_not_validate_core_pattern(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        raw_config = {**default_raw_config, "enabled": False}

        # Should not raise even without mocking core_pattern file
        config = CoreDumpConfig.model_validate(raw_config, context=default_context)

        assert config.enabled is False

    def test_coredump_enabled_requires_context(self, default_raw_config: RawConfigT) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CoreDumpConfig.model_validate(default_raw_config, context=None)

        assert "context must be specified" in str(exc_info.value)


class DebugConfigTest:
    CONFIG_DEFAULT_ENABLED = True

    @pytest.fixture
    def default_raw_config(self) -> RawConfigT:
        return {"enabled": True}

    def test_enabled_field_uses_context_debug_value(
        self,
        default_raw_config: RawConfigT,
        default_context: AgentConfigValidationContext,
    ) -> None:
        config = DebugConfig.model_validate(
            default_raw_config,
            context=default_context,
        )

        assert self.CONFIG_DEFAULT_ENABLED != CONTEXT_DEFAULT_DEBUG
        assert config.enabled == CONTEXT_DEFAULT_DEBUG

    def test_enabled_field_without_context(self, default_raw_config: RawConfigT) -> None:
        config = DebugConfig.model_validate(default_raw_config, context=None)
        assert config.enabled == self.CONFIG_DEFAULT_ENABLED

        raw_config = {**default_raw_config, "enabled": not self.CONFIG_DEFAULT_ENABLED}
        config = DebugConfig.model_validate(raw_config, context=None)
        assert config.enabled == (not self.CONFIG_DEFAULT_ENABLED)


class AgentConfigTest:
    def test_rpc_listen_addr_accepts_unspecified_ipv4(self) -> None:
        config = AgentConfig.model_validate({
            "backend": "docker",
            "rpc-listen-addr": HostPortPair(host="0.0.0.0", port=6001),
        })

        assert config.rpc_listen_addr.host == "0.0.0.0"

    def test_rpc_listen_addr_accepts_unspecified_ipv6(self) -> None:
        config = AgentConfig.model_validate({
            "backend": "docker",
            "rpc-listen-addr": HostPortPair(host="::", port=6001),
        })

        assert config.rpc_listen_addr.host == "::"

    def test_rpc_listen_addr_rejects_link_local_ipv4(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig.model_validate({
                "backend": "docker",
                "rpc-listen-addr": HostPortPair(host="169.254.1.1", port=6001),
            })

        assert "link-local" in str(exc_info.value)

    def test_rpc_listen_addr_rejects_link_local_ipv6(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig.model_validate({
                "backend": "docker",
                "rpc-listen-addr": HostPortPair(host="fe80::1", port=6001),
            })

        assert "link-local" in str(exc_info.value)

    def test_rpc_listen_addr_accepts_valid_ips(self) -> None:
        config = AgentConfig.model_validate({
            "backend": "docker",
            "rpc-listen-addr": HostPortPair(host="127.0.0.1", port=6001),
        })

        assert config.rpc_listen_addr.host == "127.0.0.1"

        config = AgentConfig.model_validate({
            "backend": "docker",
            "rpc-listen-addr": HostPortPair(host="::1", port=6001),
        })

        assert config.rpc_listen_addr.host == "::1"

    def test_rpc_listen_addr_accepts_hostname(self) -> None:
        config = AgentConfig.model_validate({
            "backend": "docker",
            "rpc-listen-addr": HostPortPair(host="localhost", port=6001),
        })

        assert config.rpc_listen_addr.host == "localhost"

    def test_rpc_listen_addr_accepts_public_ips(self) -> None:
        config = AgentConfig.model_validate({
            "backend": "docker",
            "rpc-listen-addr": HostPortPair(host="192.168.1.100", port=6001),
        })

        assert config.rpc_listen_addr.host == "192.168.1.100"

    def test_internal_addr_alias_for_service_addr(self) -> None:
        """Test that internal-addr works as an alias for service-addr."""
        config = AgentConfig.model_validate({
            "backend": "docker",
            "internal-addr": HostPortPair(host="10.0.1.100", port=6003),
        })

        assert config.internal_addr.host == "10.0.1.100"
        assert config.internal_addr.port == 6003

    def test_announce_internal_addr_alias_for_announce_addr(self) -> None:
        """Test that announce-internal-addr works as an alias for announce-addr."""
        config = AgentConfig.model_validate({
            "backend": "docker",
            "announce-internal-addr": HostPortPair(host="10.0.2.200", port=6003),
        })

        assert config.announce_internal_addr.host == "10.0.2.200"
        assert config.announce_internal_addr.port == 6003

    def test_service_addr_and_internal_addr_produce_same_result(self) -> None:
        """Test that service-addr and internal-addr are equivalent."""
        config_with_service_addr = AgentConfig.model_validate({
            "backend": "docker",
            "service-addr": HostPortPair(host="192.168.1.50", port=7003),
        })

        config_with_internal_addr = AgentConfig.model_validate({
            "backend": "docker",
            "internal-addr": HostPortPair(host="192.168.1.50", port=7003),
        })

        assert config_with_service_addr.internal_addr == config_with_internal_addr.internal_addr

    def test_announce_addr_and_announce_internal_addr_produce_same_result(self) -> None:
        """Test that announce-addr and announce-internal-addr are equivalent."""
        config_with_announce_addr = AgentConfig.model_validate({
            "backend": "docker",
            "announce-addr": HostPortPair(host="192.168.2.60", port=7003),
        })

        config_with_announce_internal_addr = AgentConfig.model_validate({
            "backend": "docker",
            "announce-internal-addr": HostPortPair(host="192.168.2.60", port=7003),
        })

        assert (
            config_with_announce_addr.announce_internal_addr
            == config_with_announce_internal_addr.announce_internal_addr
        )

    def test_service_addr_serialization_uses_canonical_name(self) -> None:
        """Test that serialization uses the canonical internal-addr name."""
        config = AgentConfig.model_validate({
            "backend": "docker",
            "service-addr": HostPortPair(host="10.0.1.100", port=6003),
        })

        serialized = config.model_dump(by_alias=True)
        assert "internal-addr" in serialized
        assert "service-addr" not in serialized
        assert serialized["internal-addr"]["host"] == "10.0.1.100"
        assert serialized["internal-addr"]["port"] == 6003

    def test_announce_addr_serialization_uses_canonical_name(self) -> None:
        """Test that serialization uses the canonical announce-internal-addr name."""
        config = AgentConfig.model_validate({
            "backend": "docker",
            "announce-addr": HostPortPair(host="10.0.2.200", port=6003),
        })

        serialized = config.model_dump(by_alias=True)
        assert "announce-internal-addr" in serialized
        assert "announce-addr" not in serialized
        assert serialized["announce-internal-addr"]["host"] == "10.0.2.200"
        assert serialized["announce-internal-addr"]["port"] == 6003


class ContainerConfigTest:
    ROOT_UID = 0
    NON_ROOT_UID = 1000

    class MakeRawConfig(Protocol):
        def __call__(
            self,
            scratch_type: ScratchType = ScratchType.HOSTDIR,
            sandbox_type: ContainerSandboxType | None = None,
            stats_type: StatModes | None = None,
            port_range: Any | None = None,
        ) -> RawConfigT: ...

    @pytest.fixture
    def make_raw_config() -> MakeRawConfig:
        def _make(
            scratch_type: ScratchType = ScratchType.HOSTDIR,
            sandbox_type: ContainerSandboxType | None = None,
            stats_type: StatModes | None = None,
            port_range: Any | None = None,
        ) -> RawConfigT:
            raw_config: RawConfigT = {"scratch-type": scratch_type}
            if sandbox_type is not None:
                raw_config["sandbox-type"] = sandbox_type
            if stats_type is not None:
                raw_config["stats-type"] = stats_type
            if port_range is not None:
                raw_config["port-range"] = port_range
            return raw_config

        return _make

    @patch("ai.backend.agent.utils.get_arch_name", return_value="x86_64")
    def test_sandbox_type_jail_works_on_x86_64(self, make_raw_config: MakeRawConfig) -> None:
        raw_config = make_raw_config(sandbox_type=ContainerSandboxType.JAIL)
        config = ContainerConfig.model_validate(raw_config)

        assert config.sandbox_type == ContainerSandboxType.JAIL

    @patch("ai.backend.agent.utils.get_arch_name", return_value="aarch64")
    def test_sandbox_type_jail_fails_on_arm64(self, make_raw_config: MakeRawConfig) -> None:
        with pytest.raises(ValidationError) as exc_info:
            raw_config = make_raw_config(sandbox_type=ContainerSandboxType.JAIL)
            ContainerConfig.model_validate(raw_config)

        assert "not supported on architecture" in str(exc_info.value)
        assert "aarch64" in str(exc_info.value)

    @pytest.mark.parametrize("arch", ["aarch64", "x86_64", "x86"])
    def test_sandbox_type_docker_allowed_on_any_arch(
        self,
        make_raw_config: MakeRawConfig,
        arch: str,
    ) -> None:
        with patch("ai.backend.agent.utils.get_arch_name", return_value=arch):
            raw_config = make_raw_config(sandbox_type=ContainerSandboxType.DOCKER)
            config = ContainerConfig.model_validate(raw_config)

        assert config.sandbox_type == ContainerSandboxType.DOCKER

    @patch("os.getuid", return_value=NON_ROOT_UID)
    def test_stats_type_cgroup_fails_for_non_root(self, make_raw_config: MakeRawConfig) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig.model_validate(make_raw_config(stats_type=StatModes.CGROUP))

        assert "unless the agent runs as root" in str(exc_info.value)

    @patch("os.getuid", return_value=ROOT_UID)
    def test_stats_type_cgroup_allowed_for_root(self, make_raw_config: MakeRawConfig) -> None:
        config = ContainerConfig.model_validate(make_raw_config(stats_type=StatModes.CGROUP))

        assert config.stats_type == StatModes.CGROUP

    @patch("os.getuid", return_value=NON_ROOT_UID)
    def test_stats_type_docker_allowed_for_non_root(self, make_raw_config: MakeRawConfig) -> None:
        config = ContainerConfig.model_validate(make_raw_config(stats_type=StatModes.DOCKER))

        assert config.stats_type == StatModes.DOCKER

    @patch("os.getuid", return_value=NON_ROOT_UID)
    def test_scratch_type_hostfile_fails_for_non_root(self, make_raw_config: MakeRawConfig) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig.model_validate(make_raw_config(scratch_type=ScratchType.HOSTFILE))

        assert "unless the agent runs as root" in str(exc_info.value)

    @patch("os.getuid", return_value=ROOT_UID)
    def test_scratch_type_hostfile_allowed_for_root(self, make_raw_config: MakeRawConfig) -> None:
        config = ContainerConfig.model_validate(make_raw_config(scratch_type=ScratchType.HOSTFILE))

        assert config.scratch_type == ScratchType.HOSTFILE

    @patch("os.getuid", return_value=NON_ROOT_UID)
    def test_scratch_type_hostdir_allowed_for_non_root(
        self,
        make_raw_config: MakeRawConfig,
    ) -> None:
        config = ContainerConfig.model_validate(make_raw_config(scratch_type=ScratchType.HOSTDIR))

        assert config.scratch_type == ScratchType.HOSTDIR

    def test_port_range_validation(self, make_raw_config: MakeRawConfig) -> None:
        config = ContainerConfig.model_validate(make_raw_config(port_range=[30000, 31000]))
        assert config.port_range == (30000, 31000)

        config = ContainerConfig.model_validate(make_raw_config(port_range=[40000, 41000]))
        assert config.port_range == (40000, 41000)

    def test_port_range_validation_invalid(self, make_raw_config: MakeRawConfig) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig.model_validate(
                make_raw_config(
                    port_range=[30000],  # Only one element
                )
            )

        assert "must be a tuple of two integers" in str(exc_info.value)


class TestResourceConfigValidation:
    def test_affinity_policy_parses_string(self) -> None:
        config = ResourceConfig.model_validate({
            "affinity-policy": AffinityPolicy.INTERLEAVED.name.lower(),
        })

        assert config.affinity_policy == AffinityPolicy.INTERLEAVED

        config = ResourceConfig.model_validate({
            "affinity-policy": AffinityPolicy.PREFER_SINGLE_NODE.name.upper(),
        })

        assert config.affinity_policy == AffinityPolicy.PREFER_SINGLE_NODE

    def test_affinity_policy_accepts_enum(self) -> None:
        config = ResourceConfig.model_validate({
            "affinity-policy": AffinityPolicy.INTERLEAVED,
        })

        assert config.affinity_policy == AffinityPolicy.INTERLEAVED

    def test_affinity_policy_rejects_invalid_string(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ResourceConfig.model_validate({
                "affinity-policy": "invalid_policy",
            })

        assert "Invalid affinity policy" in str(exc_info.value)


class TestAgentUnifiedConfigValidation:
    @pytest.fixture
    def default_raw_config(self) -> RawConfigT:
        return {
            "agent": {
                "backend": AgentBackend.KUBERNETES,
                "rpc-listen-addr": HostPortPair(host="127.0.0.1", port=6001),
            },
            "container": {
                "scratch-type": "k8s-nfs",
                "scratch-nfs-address": "nfs.example.com:/exports",
                "scratch-nfs-options": "nfsvers=4.1,rsize=1048576",
            },
            "resource": {},
            "etcd": {
                "namespace": "test",
                "addr": HostPortPair(host="127.0.0.1", port=2379),
            },
        }

    def test_kubernetes_backend_requires_nfs_config_for_k8s_nfs(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = default_raw_config.copy()
        raw_config["container"] = {
            "scratch-type": "k8s-nfs",
            # Missing scratch-nfs-address and scratch-nfs-options
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "scratch-nfs-address and scratch-nfs-options are required" in str(exc_info.value)

    def test_kubernetes_backend_succeeds_with_nfs_config(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        config = AgentUnifiedConfig.model_validate(default_raw_config)

        assert config.agent.backend == AgentBackend.KUBERNETES
        assert config.container.scratch_type == ScratchType.K8S_NFS

    def test_kubernetes_backend_with_other_scratch_types(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = default_raw_config.copy()
        raw_config["container"] = {
            "scratch-type": "hostdir",
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        assert config.agent.backend == AgentBackend.KUBERNETES
        assert config.container.scratch_type == ScratchType.HOSTDIR

    def test_kubernetes_nfs_requires_only_address(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = default_raw_config.copy()
        raw_config["container"] = {
            "scratch-type": "k8s-nfs",
            "scratch-nfs-options": "nfsvers=4.1",
            # Missing scratch-nfs-address
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "scratch-nfs-address and scratch-nfs-options are required" in str(exc_info.value)

    def test_kubernetes_nfs_requires_only_options(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = default_raw_config.copy()
        raw_config["container"] = {
            "scratch-type": "k8s-nfs",
            "scratch-nfs-address": "nfs.example.com:/exports",
            # Missing scratch-nfs-options
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "scratch-nfs-address and scratch-nfs-options are required" in str(exc_info.value)

    def test_docker_backend_validates_swarm_config(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = default_raw_config.copy()
        # Valid Docker config with swarm-enabled
        raw_config["agent"] = {
            "backend": AgentBackend.DOCKER,
            "rpc-listen-addr": HostPortPair(host="127.0.0.1", port=6001),
        }
        raw_config["container"] = {
            "scratch-type": ScratchType.HOSTDIR,
            "swarm-enabled": True,
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        assert config.agent.backend == AgentBackend.DOCKER
        assert config.container.swarm_enabled is True

    def test_docker_backend_with_swarm_disabled(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = default_raw_config.copy()
        # Valid Docker config with swarm disabled
        raw_config["agent"] = {
            "backend": AgentBackend.DOCKER,
            "rpc-listen-addr": HostPortPair(host="127.0.0.1", port=6001),
        }
        raw_config["container"] = {
            "scratch-type": ScratchType.HOSTDIR,
            "swarm-enabled": False,
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        assert config.agent.backend == AgentBackend.DOCKER
        assert config.container.swarm_enabled is False

    def test_agent_backend_property(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = default_raw_config.copy()
        raw_config["agent"]["backend"] = AgentBackend.DOCKER
        raw_config["container"] = {
            "scratch-type": ScratchType.HOSTDIR,
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        assert config.agent.backend == AgentBackend.DOCKER

        raw_config["agent"]["backend"] = AgentBackend.KUBERNETES
        config = AgentUnifiedConfig.model_validate(raw_config)
        assert config.agent.backend == AgentBackend.KUBERNETES


class TestAgentUnifiedConfigSingleAgentMode:
    @pytest.fixture
    def default_raw_config(self) -> RawConfigT:
        return {
            "agent": {
                "backend": AgentBackend.DOCKER,
                "rpc-listen-addr": HostPortPair(host="127.0.0.1", port=6001),
            },
            "container": {
                "scratch-type": ScratchType.HOSTDIR,
                "port-range": [30000, 31000],
            },
            "resource": {},
            "etcd": {
                "namespace": "test",
                "addr": HostPortPair(host="127.0.0.1", port=2379),
            },
        }

    def test_single_agent_mode_uses_global_config(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        config = AgentUnifiedConfig.model_validate(default_raw_config)

        agent_configs = config.get_agent_configs()
        assert len(agent_configs) == 1
        assert agent_configs[0].agent.backend == AgentBackend.DOCKER
        assert agent_configs[0].container.port_range == (30000, 31000)

    def test_single_agent_mode_rejects_single_agent_in_agents_list(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                }
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "should not be specified with only 1 agent" in str(exc_info.value)

    def test_global_config_property_returns_global_fields(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        config = AgentUnifiedConfig.model_validate(default_raw_config)

        # AgentUnifiedConfig itself inherits from AgentGlobalConfig
        assert isinstance(config, AgentGlobalConfig)


class TestMultipleAgentsConfigValidation:
    @pytest.fixture
    def default_raw_config(self) -> RawConfigT:
        return {
            "agent": {
                "backend": AgentBackend.DOCKER,
                "rpc-listen-addr": HostPortPair(host="127.0.0.1", port=6001),
                "kernel-creation-concurrency": 4,
            },
            "container": {
                "scratch-type": ScratchType.HOSTDIR,
                "port-range": [30000, 31000],
            },
            "resource": {
                "reserved-cpu": 1,
            },
            "etcd": {
                "namespace": "test",
                "addr": HostPortPair(host="127.0.0.1", port=2379),
            },
        }

    def test_multiple_agents_inherit_global_config(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agents": [
                {"agent": {"id": "agent-1"}},
                {"agent": {"id": "agent-2"}},
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert len(agent_configs) == 2
        for agent_config in agent_configs:
            assert agent_config.agent.backend == AgentBackend.DOCKER
            assert agent_config.container.port_range == (30000, 31000)
            assert agent_config.resource.reserved_cpu == 1

    def test_agent_overrides_agent_fields(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agents": [
                {
                    "agent": {
                        "id": "agent-1",
                        "kernel-creation-concurrency": 8,
                    }
                },
                {"agent": {"id": "agent-2"}},
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].agent.id == "agent-1"
        assert agent_configs[0].agent.kernel_creation_concurrency == 8
        assert agent_configs[1].agent.id == "agent-2"
        assert agent_configs[1].agent.kernel_creation_concurrency == 4

    def test_agent_overrides_container_port_range(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "container": {"port-range": [31000, 32000]},
                },
                {
                    "agent": {"id": "agent-2"},
                    "container": {"port-range": [32000, 33000]},
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].container.port_range == (31000, 32000)
        assert agent_configs[1].container.port_range == (32000, 33000)

    def test_agent_overrides_resource_config(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 2,
                        "mem": "8G",
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 1,
                        "mem": "8G",
                    },
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].resource.allocations is not None
        assert agent_configs[0].resource.allocations.cpu == 2
        assert agent_configs[1].resource.allocations is not None
        assert agent_configs[1].resource.allocations.cpu == 1

    def test_agent_partial_override_preserves_other_fields(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agent": {
                **default_raw_config["agent"],
                "allow-compute-plugins": {"plugin1", "plugin2"},
            },
            "agents": [
                {
                    "agent": {
                        "id": "agent-1",
                        "kernel-creation-concurrency": 8,
                    }
                },
                {
                    "agent": {"id": "agent-2"},
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].agent.kernel_creation_concurrency == 8
        assert agent_configs[0].agent.allow_compute_plugins == {"plugin1", "plugin2"}

    def test_multiple_agents_validate_backend_specific_config(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agent": {
                "backend": AgentBackend.KUBERNETES,
                "rpc-listen-addr": HostPortPair(host="127.0.0.1", port=6001),
            },
            "container": {
                "scratch-type": "k8s-nfs",
                "scratch-nfs-address": "nfs.example.com:/exports",
                "scratch-nfs-options": "nfsvers=4.1",
            },
            "agents": [
                {"agent": {"id": "agent-1"}},
                {"agent": {"id": "agent-2"}},
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].agent.backend == AgentBackend.KUBERNETES
        assert agent_configs[1].agent.backend == AgentBackend.KUBERNETES

    def test_multiple_agents_with_mixed_overrides(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
                "allocations": {
                    "cpu": 1,
                    "mem": "8G",
                },
            },
            "agents": [
                {
                    "agent": {
                        "id": "agent-1",
                        "kernel-creation-concurrency": 8,
                    },
                    "container": {"port-range": [31000, 32000]},
                    "resource": {
                        "cpu": 2,
                        "mem": "8G",
                    },
                },
                {
                    "agent": {
                        "id": "agent-2",
                    },
                    "container": {"port-range": [32000, 33000]},
                },
                {
                    "agent": {"id": "agent-3"},
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert len(agent_configs) == 3
        assert agent_configs[0].agent.kernel_creation_concurrency == 8
        assert agent_configs[0].resource.allocations is not None
        assert agent_configs[0].resource.allocations.cpu == 2
        assert agent_configs[1].agent.kernel_creation_concurrency == 4
        assert agent_configs[1].resource.allocations is not None
        assert agent_configs[1].resource.allocations.cpu == 1
        assert agent_configs[2].agent.kernel_creation_concurrency == 4

    def test_agent_with_only_id_inherits_all_fields(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agent": {
                **default_raw_config["agent"],
                "agent-sock-port": 6007,
                "allow-compute-plugins": {"plugin1", "plugin2"},
            },
            "agents": [
                {"agent": {"id": "agent-1"}},
                {"agent": {"id": "agent-2"}},
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        for agent_config in config.get_agent_configs():
            assert agent_config.agent.backend == AgentBackend.DOCKER
            assert agent_config.agent.kernel_creation_concurrency == 4
            assert agent_config.agent.agent_sock_port == 6007
            assert agent_config.agent.allow_compute_plugins == {"plugin1", "plugin2"}
            assert agent_config.container.port_range == (30000, 31000)
            assert agent_config.resource.reserved_cpu == 1

    def test_agent_with_empty_container_override_inherits_global(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "container": {},
                },
                {"agent": {"id": "agent-2"}},
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].container.port_range == (30000, 31000)
        assert agent_configs[0].container.scratch_type == ScratchType.HOSTDIR
        assert agent_configs[1].container.port_range == (30000, 31000)
        assert agent_configs[1].container.scratch_type == ScratchType.HOSTDIR

    def test_agent_with_empty_resource_override_inherits_global(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                "reserved-cpu": 2,
                "reserved-mem": "2G",
                "reserved-disk": "10G",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                },
                {"agent": {"id": "agent-2"}},
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].resource.reserved_cpu == 2
        assert agent_configs[1].resource.reserved_cpu == 2

    def test_agent_with_empty_resource_dict_is_rejected(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        """Empty resource dict should be rejected - omit the field instead."""
        raw_config = {
            **default_raw_config,
            "resource": {
                "reserved-cpu": 2,
                "reserved-mem": "2G",
                "reserved-disk": "10G",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {},  # Empty dict should be invalid
                },
                {"agent": {"id": "agent-2"}},
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "Field required" in str(exc_info.value)

    def test_overridable_agent_config_defaults_when_not_in_global(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "agents": [
                {"agent": {"id": "agent-1"}},
                {
                    "agent": {
                        "id": "agent-2",
                        "force-terminate-abusing-containers": True,
                    },
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].agent.agent_sock_port == 6007
        assert agent_configs[0].agent.force_terminate_abusing_containers is False
        assert agent_configs[0].agent.use_experimental_redis_event_dispatcher is False

        assert agent_configs[1].agent.force_terminate_abusing_containers is True
        assert agent_configs[1].agent.agent_sock_port == 6007

    def test_overridable_container_config_defaults_when_not_in_global(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "container": {
                "scratch-type": ScratchType.HOSTDIR,
                "port-range": [30000, 31000],
            },
            "agents": [
                {"agent": {"id": "agent-1"}},
                {
                    "agent": {"id": "agent-2"},
                    "container": {"port-range": [32000, 33000]},
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].container.port_range == (30000, 31000)
        assert agent_configs[0].container.scratch_type == ScratchType.HOSTDIR

        assert agent_configs[1].container.port_range == (32000, 33000)
        assert agent_configs[1].container.scratch_type == ScratchType.HOSTDIR

    def test_agent_ids_must_be_unique(self, default_raw_config: RawConfigT) -> None:
        raw_config = {
            **default_raw_config,
            "agents": [
                {"agent": {"id": "agent-1"}},
                {"agent": {"id": "agent-1"}},
            ],
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "duplicate" in str(exc_info.value).lower()

    def test_different_scaling_groups_per_agent(self, default_raw_config: RawConfigT) -> None:
        raw_config = {
            **default_raw_config,
            "agents": [
                {
                    "agent": {
                        "id": "agent-1",
                        "scaling-group": "default",
                    }
                },
                {
                    "agent": {
                        "id": "agent-2",
                        "scaling-group": "gpu",
                    }
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)

        agent_configs = config.get_agent_configs()
        assert agent_configs[0].agent.scaling_group == "default"
        assert agent_configs[1].agent.scaling_group == "gpu"


class TestResourceAllocationModes:
    """Test the new resource allocation modes: SHARED, AUTO_SPLIT, and MANUAL."""

    @pytest.fixture
    def default_raw_config(self) -> RawConfigT:
        return {
            "agent": {
                "backend": AgentBackend.DOCKER,
                "rpc-listen-addr": HostPortPair(host="127.0.0.1", port=6001),
            },
            "container": {
                "scratch-type": ScratchType.HOSTDIR,
                "port-range": [30000, 31000],
            },
            "resource": {
                "reserved-cpu": 2,
                "reserved-mem": "2G",
                "reserved-disk": "10G",
            },
            "etcd": {
                "namespace": "test",
                "addr": HostPortPair(host="127.0.0.1", port=2379),
            },
        }

    def test_allocation_mode_defaults_to_shared(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        config = AgentUnifiedConfig.model_validate(default_raw_config)
        assert config.resource.allocation_mode == ResourceAllocationMode.SHARED

    def test_shared_mode_single_agent(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "shared",
            },
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        assert config.resource.allocation_mode == ResourceAllocationMode.SHARED

    def test_shared_mode_multiple_agents_no_allocations(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "shared",
            },
            "agents": [
                {"agent": {"id": "agent-1"}},
                {"agent": {"id": "agent-2"}},
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        assert config.resource.allocation_mode == ResourceAllocationMode.SHARED
        assert len(config.get_agent_configs()) == 2

    def test_shared_mode_rejects_allocated_cpu(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "shared",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "8G",
                    },
                },
                {"agent": {"id": "agent-2"}},
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "must not specify manual resource" in str(exc_info.value)

    def test_shared_mode_rejects_allocated_devices(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "shared",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "8G",
                        "devices": {
                            SlotName("cuda.mem"): 0.5,
                        },
                    },
                },
                {"agent": {"id": "agent-2"}},
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "must not specify manual resource" in str(exc_info.value)

    def test_auto_split_mode_multiple_agents(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "auto-split",
            },
            "agents": [
                {"agent": {"id": "agent-1"}},
                {"agent": {"id": "agent-2"}},
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        assert config.resource.allocation_mode == ResourceAllocationMode.AUTO_SPLIT

    def test_auto_split_mode_rejects_allocated_cpu(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "auto-split",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "8G",
                    },
                },
                {"agent": {"id": "agent-2"}},
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "must not specify manual resource" in str(exc_info.value)

    def test_manual_mode_requires_allocated_cpu_mem_disk(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        # Missing mem - this should fail because mem is required
                    },
                },
                {"agent": {"id": "agent-2"}},
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "Field required" in str(exc_info.value)

    def test_manual_mode_valid_configuration(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 4,
                        "mem": "32G",
                    },
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        assert config.resource.allocation_mode == ResourceAllocationMode.MANUAL
        agent_configs = config.get_agent_configs()
        assert agent_configs[0].resource.allocations is not None
        assert agent_configs[0].resource.allocations.cpu == 8
        assert agent_configs[1].resource.allocations is not None
        assert agent_configs[1].resource.allocations.cpu == 4

    def test_manual_mode_with_allocated_devices(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("cuda.mem"): 0.3,
                        },
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("cuda.mem"): 0.7,
                        },
                    },
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        agent_configs = config.get_agent_configs()
        assert agent_configs[0].resource.allocations is not None
        assert agent_configs[0].resource.allocations.devices[SlotName("cuda.mem")] == Decimal("0.3")
        assert agent_configs[1].resource.allocations is not None
        assert agent_configs[1].resource.allocations.devices[SlotName("cuda.mem")] == Decimal("0.7")

    def test_manual_mode_agents_with_same_slots_allowed(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        """Test that agents with the same slot names are allowed in MANUAL mode."""
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("cuda.mem"): 0.3,
                            SlotName("cuda.shares"): 1.0,
                        },
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 4,
                        "mem": "16G",
                        "devices": {
                            SlotName("cuda.mem"): 0.7,
                            SlotName("cuda.shares"): 2.0,
                        },
                    },
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        agent_configs = config.get_agent_configs()

        # Check that both agents have the same slot names
        assert agent_configs[0].resource.allocations is not None
        assert set(agent_configs[0].resource.allocations.devices.keys()) == {
            SlotName("cuda.mem"),
            SlotName("cuda.shares"),
        }
        assert agent_configs[1].resource.allocations is not None
        assert set(agent_configs[1].resource.allocations.devices.keys()) == {
            SlotName("cuda.mem"),
            SlotName("cuda.shares"),
        }

        # Check that values can differ
        assert agent_configs[0].resource.allocations.devices[SlotName("cuda.mem")] == Decimal("0.3")
        assert agent_configs[1].resource.allocations.devices[SlotName("cuda.mem")] == Decimal("0.7")

    def test_manual_mode_agents_with_different_slots_rejected(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        """Test that agents with different slot names are rejected in MANUAL mode."""
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("cuda.mem"): 0.7,
                        },
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("cuda.shares"): 0.6,
                        },
                    },
                },
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "All agents must have the same slots defined" in str(exc_info.value)

    def test_manual_mode_agents_with_subset_of_slots_rejected(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        """Test that agents where one has a subset of slots are rejected in MANUAL mode."""
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("cuda.mem"): 0.5,
                            SlotName("cuda.shares"): 1.0,
                        },
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("cuda.mem"): 0.5,
                        },
                    },
                },
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "All agents must have the same slots defined" in str(exc_info.value)

    def test_manual_mode_agents_with_empty_devices_on_some_agents(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        """Test that agents with empty allocated_devices on some agents are rejected."""
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("cuda.mem"): 0.5,
                        },
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        # No devices specified
                    },
                },
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "All agents must have the same slots defined" in str(exc_info.value)

    def test_manual_mode_agents_all_with_empty_devices_allowed(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        """Test that all agents with empty allocated_devices are allowed."""
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        # No devices specified
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 4,
                        "mem": "16G",
                        # No devices specified
                    },
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        agent_configs = config.get_agent_configs()

        # Both should have empty allocated_devices
        assert agent_configs[0].resource.allocations is not None
        assert agent_configs[0].resource.allocations.devices == {}
        assert agent_configs[1].resource.allocations is not None
        assert agent_configs[1].resource.allocations.devices == {}

    def test_allocated_devices_parses_decimal_strings(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("foo"): "0.25",  # String value
                        },
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("foo"): 0.75,  # Numeric value
                        },
                    },
                },
            ],
        }
        config = AgentUnifiedConfig.model_validate(raw_config)
        agent_configs = config.get_agent_configs()
        assert agent_configs[0].resource.allocations is not None
        assert float(agent_configs[0].resource.allocations.devices[SlotName("foo")]) == 0.25
        assert agent_configs[1].resource.allocations is not None
        assert float(agent_configs[1].resource.allocations.devices[SlotName("foo")]) == 0.75

    def test_allocated_devices_rejects_negative_values(
        self,
        default_raw_config: RawConfigT,
    ) -> None:
        raw_config = {
            **default_raw_config,
            "resource": {
                **default_raw_config["resource"],
                "allocation-mode": "manual",
            },
            "agents": [
                {
                    "agent": {"id": "agent-1"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                        "devices": {
                            SlotName("foo"): "-1",
                        },
                    },
                },
                {
                    "agent": {"id": "agent-2"},
                    "resource": {
                        "cpu": 8,
                        "mem": "32G",
                    },
                },
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AgentUnifiedConfig.model_validate(raw_config)

        assert "must not be a negative value" in str(exc_info.value)
