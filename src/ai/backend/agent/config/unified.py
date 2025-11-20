"""
Agent Configuration Schema
--------------------------
"""

from __future__ import annotations

import enum
import ipaddress
import logging
import os
import sys
import textwrap
from decimal import Decimal
from pathlib import Path
from typing import (
    Any,
    Mapping,
    Optional,
    Self,
    Sequence,
)
from uuid import uuid4

from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    FilePath,
    PrivateAttr,
    ValidationInfo,
    field_validator,
    model_validator,
)

from ai.backend.agent.utils import get_arch_name
from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.configs.validation_context import BaseConfigValidationContext
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.typed_validators import (
    AutoDirectoryPath,
    GroupID,
    HostPortPair,
    UserID,
)
from ai.backend.common.types import (
    BinarySize,
    BinarySizeField,
    ResourceGroupType,
    ServiceDiscoveryType,
    SlotName,
    SlotNameField,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.config import LoggingConfig

from ..affinity_map import AffinityPolicy
from ..stats import StatModes
from ..types import AgentBackend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class EventLoopType(enum.StrEnum):
    ASYNCIO = "asyncio"
    UVLOOP = "uvloop"


class ContainerSandboxType(enum.StrEnum):
    DOCKER = "docker"
    JAIL = "jail"


class ScratchType(enum.StrEnum):
    HOSTDIR = "hostdir"
    HOSTFILE = "hostfile"
    MEMORY = "memory"
    K8S_NFS = "k8s-nfs"


class ResourceAllocationMode(enum.StrEnum):
    SHARED = "shared"
    AUTO_SPLIT = "auto-split"
    MANUAL = "manual"


class AgentConfigValidationContext(BaseConfigValidationContext):
    is_invoked_subcommand: bool


class SyncContainerLifecyclesConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=True,
        description="Whether to enable container lifecycle synchronization",
        examples=[True, False],
    )
    interval: float = Field(
        default=10.0,
        ge=0,
        description="Synchronization interval in seconds",
        examples=[10.0, 30.0],
    )


class PyroscopeConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="Whether to enable Pyroscope profiling",
        examples=[True, False],
    )
    app_name: Optional[str] = Field(
        default=None,
        description="Application name to use in Pyroscope",
        examples=["backendai-agent"],
        validation_alias=AliasChoices("app-name", "app_name"),
        serialization_alias="app-name",
    )
    server_addr: Optional[str] = Field(
        default=None,
        description="Address of the Pyroscope server",
        examples=["http://localhost:4040"],
        validation_alias=AliasChoices("server-addr", "server_addr"),
        serialization_alias="server-addr",
    )
    sample_rate: Optional[int] = Field(
        default=None,
        description="Sampling rate for Pyroscope profiling",
        examples=[10, 100],
        validation_alias=AliasChoices("sample-rate", "sample_rate"),
        serialization_alias="sample-rate",
    )


class OTELConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="Whether to enable OpenTelemetry",
        examples=[True, False],
    )
    log_level: str = Field(
        default="INFO",
        description="Log level for OpenTelemetry",
        examples=["DEBUG", "INFO", "WARN", "ERROR"],
        validation_alias=AliasChoices("log-level", "log_level"),
        serialization_alias="log-level",
    )
    endpoint: str = Field(
        default="http://127.0.0.1:4317",
        description="OTLP endpoint for sending traces",
        examples=["http://127.0.0.1:4317"],
    )


class ServiceDiscoveryConfig(BaseConfigSchema):
    type: ServiceDiscoveryType = Field(
        default=ServiceDiscoveryType.REDIS,
        description="Type of service discovery to use",
        examples=[item.value for item in ServiceDiscoveryType],
    )


class CoreDumpConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="Whether to enable core dump collection",
        examples=[True, False],
    )
    path: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("./coredumps"),
        description="Directory path for storing core dumps",
        examples=["./coredumps"],
    )
    backup_count: int = Field(
        default=10,
        ge=1,
        description="Number of core dump backups to retain",
        examples=[10, 20],
        validation_alias=AliasChoices("backup-count", "backup_count"),
        serialization_alias="backup-count",
    )
    size_limit: BinarySizeField = Field(
        default=BinarySize.finite_from_str("64M"),
        description="Maximum size limit for core dumps",
        examples=["64M", "128M"],
        validation_alias=AliasChoices("size-limit", "size_limit"),
        serialization_alias="size-limit",
    )
    _core_path: Optional[Path] = PrivateAttr(default=None)

    @property
    def core_path(self) -> Path:
        """
        Get the core path for core dumps.
        If not set, it returns the default path.
        """
        if self._core_path is None:
            raise ValueError(
                "Core path is not set. Please call set_core_path() before accessing core_path."
            )
        return self._core_path

    @core_path.setter
    def core_path(self, core_path: Path) -> None:
        """
        Set the core path for core dumps.
        This is used to set the core pattern file path.
        """
        self._core_path = core_path

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @model_validator(mode="after")
    def _set_coredump_path(self, info: ValidationInfo) -> Self:
        if self.enabled:
            context = AgentConfigValidationContext.get_config_validation_context(info)
            if context is None:
                raise ValueError("context must be specified in model_validate()")
            if context.is_invoked_subcommand and not sys.platform.startswith("linux"):
                raise ValueError("Storing container coredumps is only supported in Linux.")

            core_pattern = Path("/proc/sys/kernel/core_pattern").read_text().strip()
            if core_pattern.startswith("|") or not core_pattern.startswith("/"):
                raise ValueError(
                    "/proc/sys/kernel/core_pattern must be an absolute path to enable container coredumps.",
                )

            self._core_path = Path(core_pattern).parent
        return self


class DebugConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="Master switch for debug mode",
        examples=[True, False],
    )
    asyncio: bool = Field(
        default=False,
        description="Whether to enable asyncio debug mode",
        examples=[True, False],
    )
    kernel_runner: bool = Field(
        default=False,
        description="Whether to enable kernel runner debug mode",
        examples=[True, False],
        validation_alias=AliasChoices("kernel-runner", "kernel_runner"),
        serialization_alias="kernel-runner",
    )
    enhanced_aiomonitor_task_info: bool = Field(
        default=False,
        description="Enable enhanced task information in aiomonitor",
        examples=[True, False],
        validation_alias=AliasChoices(
            "enhanced-aiomonitor-task-info", "enhanced_aiomonitor_task_info"
        ),
        serialization_alias="enhanced-aiomonitor-task-info",
    )
    skip_container_deletion: bool = Field(
        default=False,
        description="Whether to skip container deletion for debugging",
        examples=[True, False],
        validation_alias=AliasChoices("skip-container-deletion", "skip_container_deletion"),
        serialization_alias="skip-container-deletion",
    )
    log_stats: bool = Field(
        default=False,
        description="Whether to log statistics",
        examples=[True, False],
        validation_alias=AliasChoices("log-stats", "log_stats"),
        serialization_alias="log-stats",
    )
    log_kernel_config: bool = Field(
        default=False,
        description="Whether to log kernel configuration",
        examples=[True, False],
        validation_alias=AliasChoices("log-kernel-config", "log_kernel_config"),
        serialization_alias="log-kernel-config",
    )
    log_alloc_map: bool = Field(
        default=False,
        description="Whether to log allocation map",
        examples=[True, False],
        validation_alias=AliasChoices("log-alloc-map", "log_alloc_map"),
        serialization_alias="log-alloc-map",
    )
    log_events: bool = Field(
        default=False,
        description="Whether to log all internal events",
        examples=[True, False],
        validation_alias=AliasChoices("log-events", "log_events"),
        serialization_alias="log-events",
    )
    log_heartbeats: bool = Field(
        default=False,
        description="Whether to log heartbeats",
        examples=[True, False],
        validation_alias=AliasChoices("log-heartbeats", "log_heartbeats"),
        serialization_alias="log-heartbeats",
    )
    heartbeat_interval: float = Field(
        default=20.0,
        description="Heartbeat interval in seconds",
        examples=[20.0, 30.0],
        validation_alias=AliasChoices("heartbeat-interval", "heartbeat_interval"),
        serialization_alias="heartbeat-interval",
    )
    log_docker_events: bool = Field(
        default=False,
        description="Whether to log Docker events",
        examples=[True, False],
        validation_alias=AliasChoices("log-docker-events", "log_docker_events"),
        serialization_alias="log-docker-events",
    )
    coredump: CoreDumpConfig = Field(
        default_factory=CoreDumpConfig,
        description="Core dump configuration",
    )

    @field_validator("enabled", mode="before")
    @classmethod
    def _set_enabled(cls, v: Any, info: ValidationInfo) -> Any:
        context = AgentConfigValidationContext.get_config_validation_context(info)
        if context is None:
            # Likely in tests, command line args do not need to be set.
            return v
        return context.debug


class CommonAgentConfig(BaseConfigSchema):
    """
    Agent settings that cannot be overridden per-agent.
    """

    backend: AgentBackend = Field(
        description=textwrap.dedent("""
        Backend type for the agent.
        This determines how the agent interacts with the underlying infrastructure.
        Available options are:
        - `docker`: Uses Docker as the backend.
        - `kubernetes`: Uses Kubernetes as the backend.
        - `dummy`: A dummy backend for testing purposes.
        """),
        examples=[item.value for item in AgentBackend],
        validation_alias=AliasChoices("backend", "mode"),
        serialization_alias="backend",
    )
    rpc_listen_addr: HostPortPair = Field(
        default=HostPortPair(host="0.0.0.0", port=6001),
        description="RPC listen address and port",
        examples=[{"host": "", "port": 6001}],
        validation_alias=AliasChoices("rpc-listen-addr", "rpc_listen_addr"),
        serialization_alias="rpc-listen-addr",
    )
    internal_addr: HostPortPair = Field(
        default=HostPortPair(host="0.0.0.0", port=6003),
        description="Service address and port",
        validation_alias=AliasChoices("service-addr", "internal-addr", "service_addr"),
        serialization_alias="internal-addr",
    )
    announce_internal_addr: HostPortPair = Field(
        default=HostPortPair(host="host.docker.internal", port=6003),
        description="Announce address and port",
        validation_alias=AliasChoices("announce-addr", "announce-internal-addr", "announce_addr"),
        serialization_alias="announce-internal-addr",
    )
    ssl_enabled: bool = Field(
        default=False,
        description="Whether to enable SSL",
        examples=[True, False],
        validation_alias=AliasChoices("ssl-enabled", "ssl_enabled"),
        serialization_alias="ssl-enabled",
    )
    ssl_cert: Optional[FilePath] = Field(
        default=None,
        description="Path to SSL certificate file",
        examples=["/path/to/cert.pem"],
        validation_alias=AliasChoices("ssl-cert", "ssl_cert"),
        serialization_alias="ssl-cert",
    )
    ssl_key: Optional[FilePath] = Field(
        default=None,
        description="Path to SSL private key file",
        examples=["/path/to/key.pem"],
        validation_alias=AliasChoices("ssl-key", "ssl_key"),
        serialization_alias="ssl-key",
    )
    advertised_rpc_addr: Optional[HostPortPair] = Field(
        default=None,
        description="Advertised RPC address and port",
        examples=[{"host": "192.168.1.100", "port": 6001}],
        validation_alias=AliasChoices("advertised-rpc-addr", "advertised_rpc_addr"),
        serialization_alias="advertised-rpc-addr",
    )
    rpc_auth_manager_public_key: Optional[FilePath] = Field(
        default=None,
        description="Path to RPC auth manager public key",
        examples=["/path/to/public.key"],
        validation_alias=AliasChoices("rpc-auth-manager-public-key", "rpc_auth_manager_public_key"),
        serialization_alias="rpc-auth-manager-public-key",
    )
    rpc_auth_agent_keypair: Optional[FilePath] = Field(
        default=None,
        description="Path to RPC auth agent keypair",
        examples=["/path/to/keypair.key"],
        validation_alias=AliasChoices("rpc-auth-agent-keypair", "rpc_auth_agent_keypair"),
        serialization_alias="rpc-auth-agent-keypair",
    )
    ipc_base_path: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
        description="Base path for IPC",
        examples=["/tmp/backend.ai/ipc"],
        validation_alias=AliasChoices("ipc-base-path", "ipc_base_path"),
        serialization_alias="ipc-base-path",
    )
    var_base_path: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("./var/lib/backend.ai"),
        description="Base path for variable data",
        examples=["./var/lib/backend.ai"],
        validation_alias=AliasChoices("var-base-path", "var_base_path"),
        serialization_alias="var-base-path",
    )
    mount_path: Optional[AutoDirectoryPath] = Field(
        default=None,
        description="Mount path for containers",
        examples=["/mnt/backend.ai"],
        validation_alias=AliasChoices("mount-path", "mount_path"),
        serialization_alias="mount-path",
    )
    cohabiting_storage_proxy: bool = Field(
        default=True,
        description="Whether to enable cohabiting storage proxy",
        examples=[True, False],
        validation_alias=AliasChoices("cohabiting-storage-proxy", "cohabiting_storage_proxy"),
        serialization_alias="cohabiting-storage-proxy",
    )
    public_host: Optional[str] = Field(
        default=None,
        description="Public host address",
        examples=["backend.ai"],
        validation_alias=AliasChoices("public-host", "public_host"),
        serialization_alias="public-host",
    )
    region: Optional[str] = Field(
        default=None,
        description="Region name",
        examples=["us-east-1"],
    )
    instance_type: Optional[str] = Field(
        default=None,
        description="Instance type",
        examples=["m5.large"],
        validation_alias=AliasChoices("instance-type", "instance_type"),
        serialization_alias="instance-type",
    )
    pid_file: Path = Field(
        default=Path(os.devnull),
        description="Path to PID file",
        examples=["/var/run/agent.pid"],
        validation_alias=AliasChoices("pid-file", "pid_file"),
        serialization_alias="pid-file",
    )
    event_loop: EventLoopType = Field(
        default=EventLoopType.ASYNCIO,
        description="Event loop type",
        examples=[item.value for item in EventLoopType],
        validation_alias=AliasChoices("event-loop", "event_loop"),
        serialization_alias="event-loop",
    )
    skip_manager_detection: bool = Field(
        default=False,
        description="Whether to skip manager detection",
        examples=[True, False],
        validation_alias=AliasChoices("skip-manager-detection", "skip_manager_detection"),
        serialization_alias="skip-manager-detection",
    )
    aiomonitor_termui_port: int = Field(
        default=38200,
        ge=1,
        le=65535,
        description="Port for aiomonitor terminal UI",
        examples=[38200],
        validation_alias=AliasChoices(
            "aiomonitor-termui-port", "aiomonitor-port", "aiomonitor_termui_port"
        ),
        serialization_alias="aiomonitor-termui-port",
    )
    aiomonitor_webui_port: int = Field(
        default=39200,
        ge=1,
        le=65535,
        description="Port for aiomonitor web UI",
        examples=[39200],
        validation_alias=AliasChoices("aiomonitor-webui-port", "aiomonitor_webui_port"),
        serialization_alias="aiomonitor-webui-port",
    )
    metadata_server_bind_host: str = Field(
        default="0.0.0.0",
        description="Metadata server bind host",
        examples=["0.0.0.0"],
        validation_alias=AliasChoices("metadata-server-bind-host", "metadata_server_bind_host"),
        serialization_alias="metadata-server-bind-host",
    )
    metadata_server_port: int = Field(
        default=40128,
        ge=1,
        le=65535,
        description="Metadata server port",
        examples=[40128],
        validation_alias=AliasChoices("metadata-server-port", "metadata_server_port"),
        serialization_alias="metadata-server-port",
    )
    allow_compute_plugins: Optional[set[str]] = Field(
        default=None,
        description="Allowed compute plugins",
        examples=[{"ai.backend.activator.agent", "ai.backend.accelerator.cuda_open"}],
        validation_alias=AliasChoices("allow-compute-plugins", "allow_compute_plugins"),
        serialization_alias="allow-compute-plugins",
    )
    block_compute_plugins: Optional[set[str]] = Field(
        default=None,
        description="Blocked compute plugins",
        examples=[{"ai.backend.accelerator.mock"}],
        validation_alias=AliasChoices("block-compute-plugins", "block_compute_plugins"),
        serialization_alias="block-compute-plugins",
    )
    allow_network_plugins: Optional[set[str]] = Field(
        default=None,
        description="Allowed network plugins",
        examples=[{"ai.backend.manager.network.overlay"}],
        validation_alias=AliasChoices("allow-network-plugins", "allow_network_plugins"),
        serialization_alias="allow-network-plugins",
    )
    block_network_plugins: Optional[set[str]] = Field(
        default=None,
        description="Blocked network plugins",
        examples=[{"ai.backend.manager.network.overlay"}],
        validation_alias=AliasChoices("block-network-plugins", "block_network_plugins"),
        serialization_alias="block-network-plugins",
    )
    image_commit_path: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("./tmp/backend.ai/commit"),
        description="Path for image commit",
        examples=["./tmp/backend.ai/commit"],
        validation_alias=AliasChoices("image-commit-path", "image_commit_path"),
        serialization_alias="image-commit-path",
    )
    abuse_report_path: Optional[Path] = Field(
        default=None,
        description="Path for abuse reports",
        examples=["/var/log/backend.ai/abuse"],
        validation_alias=AliasChoices("abuse-report-path", "abuse_report_path"),
        serialization_alias="abuse-report-path",
    )
    use_experimental_redis_event_dispatcher: bool = Field(
        default=False,
        description="Whether to use experimental Redis event dispatcher",
        examples=[True, False],
        validation_alias=AliasChoices(
            "use-experimental-redis-event-dispatcher", "use_experimental_redis_event_dispatcher"
        ),
        serialization_alias="use-experimental-redis-event-dispatcher",
    )
    docker_mode: Optional[str] = Field(
        default=None,
        description="Docker mode detected based on kernel version (linuxkit/native)",
        examples=["linuxkit", "native"],
        validation_alias=AliasChoices("docker-mode", "docker_mode"),
        serialization_alias="docker-mode",
    )
    mount_path_uid_gid: Optional[str] = Field(
        default=None,
        description="Owner uid:gid of the mount directory",
        examples=["root:root", "bai:bai"],
        validation_alias=AliasChoices("mount-path-uid-gid", "mount_path_uid_gid"),
        serialization_alias="mount-path-uid-gid",
    )

    def real_mount_path(self, directory_path: str) -> Path:
        if self.mount_path is None:
            return Path("./", directory_path)
        return Path(self.mount_path, directory_path)

    model_config = ConfigDict(
        extra="allow",
    )

    @field_validator("rpc_listen_addr", mode="after")
    @classmethod
    def _validate_rpc_listen_addr(cls, rpc_listen_addr: HostPortPair) -> HostPortPair:
        try:
            rpc_host = ipaddress.ip_address(rpc_listen_addr.host)
        except ValueError:
            return rpc_listen_addr
        if rpc_host.is_link_local:
            raise ValueError("Cannot use link-local IP address as the RPC listening host.")
        return rpc_listen_addr


class OverridableAgentConfig(BaseConfigSchema):
    """
    Agent settings that can be overridden per-agent in multi-agent mode.
    """

    id: Optional[str] = Field(
        default=None,
        description="Agent ID",
        examples=["agent-001"],
    )
    agent_sock_port: int = Field(
        default=6007,
        ge=1024,
        le=65535,
        description="Agent socket port",
        examples=[6007],
        validation_alias=AliasChoices("agent-sock-port", "agent_sock_port"),
        serialization_alias="agent-sock-port",
    )
    scaling_group: str = Field(
        default="default",
        description="Scaling group name",
        examples=["default", "gpu-group"],
        validation_alias=AliasChoices("scaling-group", "scaling_group"),
        serialization_alias="scaling-group",
    )
    scaling_group_type: ResourceGroupType = Field(
        default=ResourceGroupType.COMPUTE,
        description="Scaling group type",
        examples=[item.value for item in ResourceGroupType],
        validation_alias=AliasChoices("scaling-group-type", "scaling_group_type"),
        serialization_alias="scaling-group-type",
    )
    force_terminate_abusing_containers: bool = Field(
        default=False,
        description="Whether to force terminate abusing containers",
        examples=[True, False],
        validation_alias=AliasChoices(
            "force-terminate-abusing-containers", "force_terminate_abusing_containers"
        ),
        serialization_alias="force-terminate-abusing-containers",
    )
    kernel_creation_concurrency: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Kernel creation concurrency",
        examples=[4, 8],
        validation_alias=AliasChoices("kernel-creation-concurrency", "kernel_creation_concurrency"),
        serialization_alias="kernel-creation-concurrency",
    )
    sync_container_lifecycles: SyncContainerLifecyclesConfig = Field(
        default_factory=SyncContainerLifecyclesConfig,
        description="Container lifecycle synchronization config",
        validation_alias=AliasChoices("sync-container-lifecycles", "sync_container_lifecycles"),
        serialization_alias="sync-container-lifecycles",
    )

    model_config = ConfigDict(
        extra="allow",
    )

    @property
    def defaulted_id(self) -> str:
        if self.id is None:
            self.id = f"agent-{uuid4()}"
        return self.id


class AgentConfig(CommonAgentConfig, OverridableAgentConfig):
    """
    Complete agent configuration (common + overridable).
    """

    pass


class CommonContainerConfig(BaseConfigSchema):
    """
    Container settings that cannot be overridden per-agent.
    """

    bind_host: str = Field(
        default="",
        description="Bind host for containers",
        examples=["0.0.0.0", ""],
        validation_alias=AliasChoices("bind-host", "bind_host", "kernel-host"),
        serialization_alias="bind-host",
    )
    advertised_host: Optional[str] = Field(
        default=None,
        description="Advertised host for containers",
        examples=["192.168.1.100"],
        validation_alias=AliasChoices("advertised-host", "advertised_host"),
        serialization_alias="advertised-host",
    )
    krunner_volumes: Optional[Mapping[str, str]] = Field(
        default=None,
        description=textwrap.dedent("""
        KRunner volumes configuration, mapping container names to host paths.
        This is used to specify volumes that should be mounted into containers
        when using the KRunner backend.
        This fields is filled by the agent at runtime based on the
        `krunner_volumes` configuration in the agent's environment.
        It is not intended to be set in the configuration file.
        """),
        examples=[],
        validation_alias=AliasChoices("krunner-volumes", "krunner_volumes"),
        serialization_alias="krunner-volumes",
    )

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )


class OverridableContainerConfig(BaseConfigSchema):
    """
    Container settings that can be overridden per-agent in multi-agent mode.
    """

    kernel_uid: UserID = Field(
        default=UserID(-1),
        description="Kernel user ID",
        examples=[1000, -1],
        validation_alias=AliasChoices("kernel-uid", "kernel_uid"),
        serialization_alias="kernel-uid",
    )
    kernel_gid: GroupID = Field(
        default=GroupID(-1),
        description="Kernel group ID",
        examples=[1000, -1],
        validation_alias=AliasChoices("kernel-gid", "kernel_gid"),
        serialization_alias="kernel-gid",
    )
    port_range: tuple[int, int] = Field(
        default=(30000, 31000),
        description=textwrap.dedent("""
        Port range for containers.
        If multiple agents are used, user must ensure that the port ranges
        do not overlap between the agent, else it may cause subtle issues
        late into the agent's runtime.
         """),
        examples=[(30000, 31000)],
        validation_alias=AliasChoices("port-range", "port_range"),
        serialization_alias="port-range",
    )
    stats_type: Optional[StatModes] = Field(
        default=StatModes.DOCKER,
        description="Statistics type",
        examples=[item.value for item in StatModes],
        validation_alias=AliasChoices("stats-type", "stats_type"),
        serialization_alias="stats-type",
    )
    sandbox_type: ContainerSandboxType = Field(
        default=ContainerSandboxType.DOCKER,
        description="Sandbox type",
        examples=[item.value for item in ContainerSandboxType],
        validation_alias=AliasChoices("sandbox-type", "sandbox_type"),
        serialization_alias="sandbox-type",
    )
    jail_args: list[str] = Field(
        default_factory=list,
        description="Jail arguments",
        examples=[["--mount", "/tmp"]],
        validation_alias=AliasChoices("jail-args", "jail_args"),
        serialization_alias="jail-args",
    )
    scratch_type: ScratchType = Field(
        default=ScratchType.HOSTDIR,
        description="Scratch type",
        examples=[item.value for item in ScratchType],
        validation_alias=AliasChoices("scratch-type", "scratch_type"),
        serialization_alias="scratch-type",
    )
    scratch_root: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("./scratches"),
        description="Scratch root directory",
        examples=["./scratches"],
        validation_alias=AliasChoices("scratch-root", "scratch_root"),
        serialization_alias="scratch-root",
    )
    scratch_size: BinarySizeField = Field(
        default=BinarySize.finite_from_str("0"),
        description="Scratch size",
        examples=["1G", "500M"],
        validation_alias=AliasChoices("scratch-size", "scratch_size"),
        serialization_alias="scratch-size",
    )
    scratch_nfs_address: Optional[str] = Field(
        default=None,
        description="Scratch NFS address",
        examples=["192.168.1.100:/export"],
        validation_alias=AliasChoices("scratch-nfs-address", "scratch_nfs_address"),
        serialization_alias="scratch-nfs-address",
    )
    scratch_nfs_options: Optional[str] = Field(
        default=None,
        description="Scratch NFS options",
        examples=["rw,sync"],
        validation_alias=AliasChoices("scratch-nfs-options", "scratch_nfs_options"),
        serialization_alias="scratch-nfs-options",
    )
    alternative_bridge: Optional[str] = Field(
        default=None,
        description="Alternative bridge network",
        examples=["br-backend"],
        validation_alias=AliasChoices("alternative-bridge", "alternative_bridge"),
        serialization_alias="alternative-bridge",
    )
    swarm_enabled: bool = Field(
        default=False,
        description=textwrap.dedent("""
        Whether to enable Docker Swarm mode.
        This allows the agent to manage containers in a Docker Swarm cluster.
        When enabled, the agent will use Docker Swarm APIs to manage containers,
        networks, and services.
        This field is only used when backend is set to 'docker'.
        """),
        examples=[True, False],
        validation_alias=AliasChoices("swarm-enabled", "swarm_enabled"),
        serialization_alias="swarm-enabled",
    )

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )

    @field_validator("port_range", mode="before")
    @classmethod
    def _parse_port_range(cls, v: Any) -> tuple[int, int]:
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return (int(v[0]), int(v[1]))
        raise ValueError("port_range must be a tuple of two integers")

    @field_validator("sandbox_type", mode="after")
    @classmethod
    def _validate_sandbox_type(cls, sandbox_type: ContainerSandboxType) -> ContainerSandboxType:
        # FIXME: Remove this after ARM64 support lands on Jail
        if sandbox_type == ContainerSandboxType.JAIL:
            current_arch = get_arch_name()
            if current_arch != "x86_64":
                raise ValueError(f"Jail sandbox is not supported on architecture {current_arch}")
        return sandbox_type

    @field_validator("stats_type", mode="after")
    @classmethod
    def _validate_stats_type(cls, stats_type: StatModes) -> StatModes:
        if stats_type == StatModes.CGROUP:
            if os.getuid() != 0:
                raise ValueError(
                    "Cannot use cgroup statistics collection mode unless the agent runs as root."
                )
        return stats_type

    @field_validator("scratch_type", mode="after")
    @classmethod
    def _validate_scratch_type(cls, scratch_type: ScratchType) -> ScratchType:
        if scratch_type == ScratchType.HOSTFILE:
            if os.getuid() != 0:
                raise ValueError("Cannot use hostfile scratch type unless the agent runs as root.")
        return scratch_type

    def validate_kubernetes_nfs(self) -> None:
        is_scratch_k8s_nfs = self.scratch_type == ScratchType.K8S_NFS
        is_nfs_address_missing = self.scratch_nfs_address is None
        is_nfs_options_missing = self.scratch_nfs_options is None

        if is_scratch_k8s_nfs and (is_nfs_address_missing or is_nfs_options_missing):
            raise ValueError("scratch-nfs-address and scratch-nfs-options are required for k8s-nfs")


class ContainerConfig(CommonContainerConfig, OverridableContainerConfig):
    """
    Complete container configuration (common + overridable).
    """

    pass


class ResourceAllocationConfig(BaseConfigSchema):
    cpu: int = Field(
        description=textwrap.dedent("""
        Hard CPU allocation for this agent (e.g., 8 cores).
        Only used in MANUAL allocation mode.
        All agents must specify this value when allocation-mode is MANUAL.
        """),
        examples=[8, 16],
    )
    mem: BinarySizeField = Field(
        description=textwrap.dedent("""
        Hard memory allocation for this agent (e.g., "32G").
        Only used in MANUAL allocation mode.
        All agents must specify this value when allocation-mode is MANUAL.
        """),
        examples=["32G", "64G"],
    )
    devices: Mapping[SlotNameField, Decimal] = Field(
        default_factory=dict,
        description=textwrap.dedent("""
        Device-specific per-slot resource allocations.
        Only used in MANUAL allocation mode.
        """),
        examples=[{"cuda.mem": "0.3", "cuda.shares": "0.5"}],
    )

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )

    @model_validator(mode="after")
    def validate_values_are_positive(self) -> Self:
        if self.cpu is not None and self.cpu < 0:
            raise ValueError(f"Allocated cpu must not be a negative value, but given {self.cpu}")
        if self.mem is not None and self.mem < 0:
            raise ValueError(f"Allocated mem must not be a negative value, but given {self.mem}")
        if any(value < 0 for value in self.devices.values()):
            raise ValueError("All allocated device resource values must not be a negative value")
        return self


class ResourceConfig(BaseConfigSchema):
    reserved_cpu: int = Field(
        default=1,
        description="The number of CPU cores reserved for the operating system and the agent service.",
        examples=[1, 2],
        validation_alias=AliasChoices("reserved-cpu", "reserved_cpu"),
        serialization_alias="reserved-cpu",
    )
    reserved_mem: BinarySizeField = Field(
        default=BinarySize.finite_from_str("1G"),
        description=(
            "The memory space reserved for the operating system and the agent service. "
            "It is subtracted from the reported main memory size and not available for user workload allocation. "
            "Depending on the memory-align-size option and system configuration, "
            "this may not be the exact value but have slightly less or more values within the memory-align-size."
        ),
        examples=["1G", "2G"],
        validation_alias=AliasChoices("reserved-mem", "reserved_mem"),
        serialization_alias="reserved-mem",
    )
    reserved_disk: BinarySizeField = Field(
        default=BinarySize.finite_from_str("8G"),
        description=(
            "The disk space reserved for the operating system and the agent service. "
            "Currently this value is unused. "
            "In future releases, it may be used to preserve the minimum disk space "
            "from the scratch disk allocation via loopback files."
        ),
        examples=["8G", "16G"],
        validation_alias=AliasChoices("reserved-disk", "reserved_disk"),
        serialization_alias="reserved-disk",
    )
    allocation_mode: ResourceAllocationMode = Field(
        default=ResourceAllocationMode.SHARED,
        description=textwrap.dedent("""
        Resource allocation mode for multi-agent scenarios.
        - `shared`: All agents share the full resource pool (default, backward compatible).
        - `auto-split`: Automatically divide resources equally (1/N) among all agents.
        - `manual`: Manually specify per-agent resource allocations via config.
        """),
        examples=[item.value for item in ResourceAllocationMode],
        validation_alias=AliasChoices("allocation-mode", "allocation_mode"),
        serialization_alias="allocation-mode",
    )
    allocations: Optional[ResourceAllocationConfig] = Field(
        default=None,
        description=textwrap.dedent("""
        Resource allocations.
        Only used in MANUAL allocation mode.
        """),
    )
    memory_align_size: BinarySizeField = Field(
        default=BinarySize.finite_from_str("16M"),
        description=(
            "The alignment of the reported main memory size to absorb tiny deviations "
            "from per-node firmware/hardware settings. "
            "Recommended to be multiple of the page/hugepage size (e.g., 2 MiB)."
        ),
        examples=["2M", "32M"],
        validation_alias=AliasChoices("memory-align-size", "memory_align_size"),
        serialization_alias="memory-align-size",
    )
    allocation_order: list[str] = Field(
        default=["cuda", "rocm", "tpu", "cpu", "mem"],
        description="Resource allocation order",
        examples=[["cuda", "rocm", "tpu", "cpu", "mem"]],
        validation_alias=AliasChoices("allocation-order", "allocation_order"),
        serialization_alias="allocation-order",
    )
    affinity_policy: AffinityPolicy = Field(
        default=AffinityPolicy.INTERLEAVED,
        description="Affinity policy",
        examples=[item.name for item in AffinityPolicy],
        validation_alias=AliasChoices("affinity-policy", "affinity_policy"),
        serialization_alias="affinity-policy",
    )

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )

    @field_validator("affinity_policy", mode="before")
    @classmethod
    def _parse_affinity_policy(cls, v: Any) -> AffinityPolicy:
        if isinstance(v, str):
            try:
                return AffinityPolicy[v.upper()]
            except KeyError:
                raise ValueError(f"Invalid affinity policy: {v}")
        return v


class EtcdConfig(BaseConfigSchema):
    namespace: str = Field(
        description="Etcd namespace",
        examples=["local", "backend"],
    )
    addr: HostPortPair | list[HostPortPair] = Field(
        description="Etcd address and port",
        examples=[
            {"host": "127.0.0.1", "port": 2379},  # single endpoint
            [
                {"host": "127.0.0.4", "port": 2379},
                {"host": "127.0.0.5", "port": 2379},
            ],  # multiple endpoints
        ],
    )
    user: Optional[str] = Field(
        default=None,
        description="Etcd username",
        examples=["backend"],
    )
    password: Optional[str] = Field(
        default=None,
        description="Etcd password",
        examples=["PASSWORD"],
    )

    def to_dataclass(self) -> EtcdConfigData:
        return EtcdConfigData(
            namespace=self.namespace,
            addrs=self.addr if isinstance(self.addr, list) else [self.addr],
            user=self.user,
            password=self.password,
        )


class ContainerLogsConfig(BaseConfigSchema):
    max_length: BinarySizeField = Field(
        default=BinarySize.finite_from_str("10M"),
        description="Maximum length of container logs",
        examples=["10M", "50M"],
        validation_alias=AliasChoices("max-length", "max_length"),
        serialization_alias="max-length",
    )
    chunk_size: BinarySizeField = Field(
        default=BinarySize.finite_from_str("64K"),
        description="Chunk size for container logs",
        examples=["64K", "128K"],
        validation_alias=AliasChoices("chunk-size", "chunk_size"),
        serialization_alias="chunk-size",
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class APIConfig(BaseConfigSchema):
    pull_timeout: Optional[float] = Field(
        default=7200.0,  # 2 hours
        ge=0,
        description="Image pull timeout in seconds",
        examples=[7200.0, 3600.0],
        validation_alias=AliasChoices("pull-timeout", "pull_timeout"),
        serialization_alias="pull-timeout",
    )
    commit_timeout: Optional[float] = Field(
        default=None,
        ge=0,
        description="Image commit timeout in seconds",
        examples=[7200.0, 3600.0],
        validation_alias=AliasChoices("commit-timeout", "commit_timeout"),
        serialization_alias="commit-timeout",
    )
    push_timeout: Optional[float] = Field(
        default=None,
        ge=0,
        description="Image push timeout in seconds",
        examples=[7200.0, 3600.0],
        validation_alias=AliasChoices("push-timeout", "push_timeout"),
        serialization_alias="push-timeout",
    )


class KernelLifecyclesConfig(BaseConfigSchema):
    init_polling_attempt: int = Field(
        default=10,
        description="Number of init polling attempts",
        examples=[10, 20],
        validation_alias=AliasChoices("init-polling-attempt", "init_polling_attempt"),
        serialization_alias="init-polling-attempt",
    )
    init_polling_timeout_sec: float = Field(
        default=60.0,
        description="Init polling timeout in seconds",
        examples=[60.0, 120.0],
        validation_alias=AliasChoices("init-polling-timeout-sec", "init_polling_timeout_sec"),
        serialization_alias="init-polling-timeout-sec",
    )
    init_timeout_sec: float = Field(
        default=60.0,
        description="Init timeout in seconds",
        examples=[60.0, 120.0],
        validation_alias=AliasChoices("init-timeout-sec", "init_timeout_sec"),
        serialization_alias="init-timeout-sec",
    )


class DockerExtraConfig(BaseConfigSchema):
    """
    For checking additional Docker configurations
    """

    swarm_enabled: bool = Field(
        default=False,
        description="Whether Docker Swarm is enabled",
        examples=[True, False],
        validation_alias=AliasChoices("swarm-enabled", "swarm_enabled"),
        serialization_alias="swarm-enabled",
    )


class AgentGlobalConfig(BaseConfigSchema):
    """
    Configuration shared across all agents (logging, etcd, API, etc.).
    """

    # Local config
    pyroscope: PyroscopeConfig = Field(
        default_factory=PyroscopeConfig,
        description="Pyroscope configuration",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration",
    )
    otel: OTELConfig = Field(
        default_factory=OTELConfig,
        description="OpenTelemetry configuration",
    )
    service_discovery: ServiceDiscoveryConfig = Field(
        default_factory=ServiceDiscoveryConfig,
        description="Service discovery configuration",
        validation_alias=AliasChoices("service-discovery", "service_discovery"),
        serialization_alias="service-discovery",
    )
    debug: DebugConfig = Field(
        default_factory=DebugConfig,
        description="Debug configuration",
    )
    etcd: EtcdConfig = Field(
        description="Etcd configuration",
    )

    # Etcd config
    container_logs: ContainerLogsConfig = Field(
        default_factory=ContainerLogsConfig,
        description="Container logs configuration",
        validation_alias=AliasChoices("container-logs", "container_logs"),
        serialization_alias="container-logs",
    )
    api: APIConfig = Field(
        default_factory=APIConfig,
        description="API configuration",
    )
    kernel_lifecycles: KernelLifecyclesConfig = Field(
        default_factory=KernelLifecyclesConfig,
        description="Kernel lifecycles configuration",
        validation_alias=AliasChoices("kernel-lifecycles", "kernel_lifecycles"),
        serialization_alias="kernel-lifecycles",
    )
    plugins: Any = Field(
        default_factory=lambda: {},
        description=textwrap.dedent("""
        Plugins configuration.
        This field is injected at runtime based on etcd configuration.
        It is not intended to be set in the configuration file.
        """),
    )
    redis: Optional[RedisConfig] = Field(
        default=None,
        description=textwrap.dedent("""
        Redis configuration.
        This field is injected at runtime based on etcd configuration.
        It is not intended to be set in the other way.
        """),
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )


class AgentSpecificConfig(BaseConfigSchema):
    """
    Default values for agent, container, and resource config.
    """

    agent: AgentConfig = Field(
        description=textwrap.dedent("""
        Agent configuration.
        If agents field is populated, this field indicates the default values for all agents.
        """),
    )
    container: ContainerConfig = Field(
        description=textwrap.dedent("""
        Container configuration.
        If agents field is populated, this field indicates the default values for all agents.
        """),
    )
    resource: ResourceConfig = Field(
        description=textwrap.dedent("""
        Resource configuration.
        If agents field is populated, this field indicates the default values for all agents.
        """),
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )

    def validate_agent_specific_config(self) -> None:
        match self.agent.backend:
            case AgentBackend.KUBERNETES:
                self.container.validate_kubernetes_nfs()
            case AgentBackend.DOCKER:
                DockerExtraConfig.model_validate(self.container.model_dump())
            case AgentBackend.DUMMY:
                pass


class AgentOverrideConfig(BaseConfigSchema):
    """
    Per-agent overrides in multi-agent mode.
    """

    agent: OverridableAgentConfig = Field(
        description=textwrap.dedent("""
        Agent config overrides for the individual agent.
        All fields except Agent ID are by default optional.
        Only override fields if necessary.
        """),
    )
    container: Optional[OverridableContainerConfig] = Field(
        default=None,
        description="Container config overrides for the individual agent",
    )
    resource: Optional[ResourceAllocationConfig] = Field(
        default=None,
        description="Resource config overrides for the individual agent",
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )

    def construct_unified_config(self, *, default: AgentUnifiedConfig) -> AgentUnifiedConfig:
        agent_updates: dict[str, Any] = {}
        if self.agent is not None:
            agent_override_fields = self.agent.model_dump(include=self.agent.model_fields_set)
            agent_updates["agent"] = default.agent.model_copy(update=agent_override_fields)
        if self.container is not None:
            container_override_fields = self.container.model_dump(
                include=self.container.model_fields_set
            )
            agent_updates["container"] = default.container.model_copy(
                update=container_override_fields
            )
        if self.resource is not None:
            default_allocations = default.resource.allocations
            override_allocations = self.resource
            if default_allocations is None:
                merged_allocations = override_allocations
            else:
                merged_allocations = default_allocations.model_copy(
                    update=override_allocations.model_dump(
                        include=override_allocations.model_fields_set
                    )
                )
            agent_updates["resource"] = default.resource.model_copy(
                update={"allocations": merged_allocations}
            )
        return default.model_copy(update=agent_updates)


class AgentUnifiedConfig(AgentGlobalConfig, AgentSpecificConfig):
    agents: list[AgentOverrideConfig] = Field(
        default_factory=list,
        description=textwrap.dedent("""
        Configuration overrides for multiple agents.
        Use this field only to define 2 or more agents, as defining only one
        agent using this field is redundant. Use the fields agent, container,
        and resource to define the configuration at a global level.
        Any field populated in the agents config will be treated as an
        override to the global default values. Thus the global fields must still
        be provided when defining multiple agents.
        """),
    )

    # TODO: Remove me after changing config injection logic
    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
    )

    @property
    def agent_common(self) -> CommonAgentConfig:
        return self.agent

    @property
    def agent_default(self) -> OverridableAgentConfig:
        return self.agent

    def get_agent_configs(self) -> Sequence[AgentUnifiedConfig]:
        agent_configs = [agent.construct_unified_config(default=self) for agent in self.agents]
        if not agent_configs:
            agent_configs = [self]
        return agent_configs

    def update(
        self,
        *,
        agent_update: Optional[Mapping[str, Any]] = None,
        container_update: Optional[Mapping[str, Any]] = None,
    ) -> None:
        # TODO: Replace setting update values with something like LoaderChain used in Manager.
        if agent_update:
            self.agent = self.agent.model_copy(update=agent_update)
        if container_update:
            self.container = self.container.model_copy(update=container_update)

    def overwrite(
        self,
        *,
        container_logs: Optional[ContainerLogsConfig] = None,
        api: Optional[APIConfig] = None,
        kernel_lifecycles: Optional[KernelLifecyclesConfig] = None,
        redis: Optional[RedisConfig] = None,
        plugins: Optional[Mapping[str, Any]] = None,
    ) -> None:
        # TODO: Replace setting update values with something like LoaderChain used in Manager.
        if container_logs:
            self.container_logs = container_logs
        if api:
            self.api = api
        if kernel_lifecycles:
            self.kernel_lifecycles = kernel_lifecycles
        if redis:
            self.redis = redis
        if plugins:
            self.plugins = plugins

    @field_validator("agents", mode="after")
    @classmethod
    def _validate_min_agents(cls, agents: list[AgentOverrideConfig]) -> list[AgentOverrideConfig]:
        if len(agents) == 1:
            raise ValueError(
                "agents should not be specified with only 1 agent configuration. "
                "Please use the default single agent mode if only 1 agent is needed."
            )

        return agents

    @field_validator("agents", mode="after")
    @classmethod
    def _validate_agent_id_uniqueness(
        cls, agents: list[AgentOverrideConfig]
    ) -> list[AgentOverrideConfig]:
        agents_with_ids = [agent for agent in agents if agent.agent.id is not None]
        agent_ids = {agent.agent.id for agent in agents_with_ids}
        if len(agent_ids) != len(agents_with_ids):
            raise ValueError("Duplicate agent IDs found!")
        return agents

    @model_validator(mode="after")
    def _validate_agent_configs(self) -> Self:
        for config in self.get_agent_configs():
            config.validate_agent_specific_config()

        return self

    @model_validator(mode="after")
    def _validate_resource_allocation_mode(self) -> Self:
        agent_configs = self.get_agent_configs()

        match self.resource.allocation_mode:
            case ResourceAllocationMode.SHARED | ResourceAllocationMode.AUTO_SPLIT:
                for config in agent_configs:
                    if config.resource.allocations is not None:
                        raise ValueError(
                            "On non-MANUAL mode, config must not specify manual resource allocations"
                        )

            case ResourceAllocationMode.MANUAL:
                slot_names: list[set[SlotName]] = []
                for config in agent_configs:
                    if config.resource.allocations is None:
                        raise ValueError(
                            "On MANUAL mode, config must specify cpu and mem resource allocations"
                        )

                    slot_names.append(set(config.resource.allocations.devices.keys()))

                if not all(slot_name == slot_names[0] for slot_name in slot_names):
                    raise ValueError("All agents must have the same slots defined in the devices!")

        return self
