from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Protocol
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from ai.backend.agent.affinity_map import AffinityPolicy
from ai.backend.agent.config.unified import (
    AgentBackend,
    AgentConfig,
    AgentUnifiedConfig,
    ContainerConfig,
    ContainerSandboxType,
    CoreDumpConfig,
    DebugConfig,
    ResourceConfig,
    ScratchType,
)
from ai.backend.agent.stats import StatModes
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.logging.config import (
    ConfigValidationContext,
    LoggingConfig,
    LogLevel,
    default_pkg_ns,
)

RawConfigT = dict[str, Any]


CONTEXT_DEFAULT_DEBUG = False
CONTEXT_DEFAULT_LOG_LEVEL = LogLevel.DEBUG


@pytest.fixture
def default_context() -> ConfigValidationContext:
    return ConfigValidationContext(
        debug=CONTEXT_DEFAULT_DEBUG,
        log_level=CONTEXT_DEFAULT_LOG_LEVEL,
        is_not_invoked_subcommand=True,
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
        default_context: ConfigValidationContext,
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
        default_context: ConfigValidationContext,
    ) -> None:
        context = default_context.model_copy(update={"log_level": LogLevel.NOTSET})
        config = LoggingConfig.model_validate(default_raw_config, context=context)

        assert config.level == self.CONFIG_DEFAULT_LOG_LEVEL

    def test_pkg_ns_field_updates_ai_backend_from_context(
        self,
        default_raw_config: RawConfigT,
        default_context: ConfigValidationContext,
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
        default_context: ConfigValidationContext,
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
        default_context: ConfigValidationContext,
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
    def default_context(self) -> ConfigValidationContext:
        return ConfigValidationContext(
            debug=True,
            log_level=CONTEXT_DEFAULT_LOG_LEVEL,
            is_not_invoked_subcommand=True,
        )

    @patch.object(sys, "platform", "linux")
    def test_coredump_enabled_requires_absolute_core_pattern(
        self,
        default_raw_config: RawConfigT,
        default_context: ConfigValidationContext,
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
        default_context: ConfigValidationContext,
    ) -> None:
        with patch("pathlib.Path.read_text", return_value="/var/lib/coredumps/core.%p"):
            config = CoreDumpConfig.model_validate(default_raw_config, context=default_context)

        assert config.enabled is True
        assert config.core_path == Path("/var/lib/coredumps")

    @patch.object(sys, "platform", "darwin")
    def test_coredump_enabled_fails_on_non_linux_darwin(
        self,
        default_raw_config: RawConfigT,
        default_context: ConfigValidationContext,
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CoreDumpConfig.model_validate(default_raw_config, context=default_context)

        assert "only supported in Linux" in str(exc_info.value)

    @patch.object(sys, "platform", "win32")
    def test_coredump_enabled_fails_on_non_linux_windows(
        self,
        default_raw_config: RawConfigT,
        default_context: ConfigValidationContext,
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CoreDumpConfig.model_validate(default_raw_config, context=default_context)

        assert "only supported in Linux" in str(exc_info.value)

    def test_coredump_disabled_does_not_validate_core_pattern(
        self,
        default_raw_config: RawConfigT,
        default_context: ConfigValidationContext,
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
        default_context: ConfigValidationContext,
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
        assert config.agent_backend == AgentBackend.DOCKER

        raw_config["agent"]["backend"] = AgentBackend.KUBERNETES
        config = AgentUnifiedConfig.model_validate(raw_config)
        assert config.agent_backend == AgentBackend.KUBERNETES
