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
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Optional,
    Self,
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

from ai.backend.agent.affinity_map import AffinityPolicy
from ai.backend.agent.stats import StatModes
from ai.backend.agent.types import AgentBackend
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.configs import (
    EtcdConfig,
    OTELConfig,
    PyroscopeConfig,
    ServiceDiscoveryConfig,
)
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
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
    SlotName,
    SlotNameField,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.config import LoggingConfig
from ai.backend.logging.validation_context import BaseConfigValidationContext

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
    enabled: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description=(
                "Controls whether the agent synchronizes container lifecycle states with the manager. "
                "When enabled, the agent periodically checks container states (running, stopped, etc.) "
                "and reports discrepancies to the manager for reconciliation. Useful for detecting "
                "orphaned containers or missed lifecycle events."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    interval: Annotated[
        float,
        Field(default=10.0, ge=0),
        BackendAIConfigMeta(
            description=(
                "Time interval in seconds between container lifecycle synchronization checks. "
                "Lower values provide faster detection of container state changes but increase "
                "system overhead. Higher values reduce overhead but may delay detection of issues."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="10.0", prod="30.0"),
        ),
    ]


class CoreDumpConfig(BaseConfigSchema):
    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enables collection of container core dumps when containers crash unexpectedly. "
                "When enabled, the agent captures core dump files for debugging crashed containers. "
                "Requires Linux with specific kernel settings. Only enable when debugging container crashes."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    path: Annotated[
        AutoDirectoryPath,
        Field(default=AutoDirectoryPath("./coredumps")),
        BackendAIConfigMeta(
            description=(
                "Directory path where container core dump files are stored. "
                "This directory is created automatically if it doesn't exist. "
                "Ensure sufficient disk space is available for storing core dumps."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="./coredumps", prod="/var/lib/backend.ai/coredumps"),
        ),
    ]
    backup_count: Annotated[
        int,
        Field(
            default=10,
            ge=1,
            validation_alias=AliasChoices("backup-count", "backup_count"),
            serialization_alias="backup-count",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of core dump backups to retain. "
                "When this limit is exceeded, older core dump files are automatically deleted "
                "to free up disk space. Increase this value if you need more historical dumps for debugging."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="10", prod="20"),
        ),
    ]
    size_limit: Annotated[
        BinarySizeField,
        Field(
            default=BinarySize.finite_from_str("64M"),
            validation_alias=AliasChoices("size-limit", "size_limit"),
            serialization_alias="size-limit",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum size limit for individual core dump files. "
                "Core dumps larger than this limit are truncated. "
                "Use binary size format (e.g., '64M', '128M', '1G'). "
                "Larger values capture more debugging information but require more storage."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="64M", prod="256M"),
        ),
    ]
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
    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Master switch for debug mode. When enabled, activates additional debugging features "
                "and verbose logging across the agent. This setting is typically overridden by "
                "command-line debug flag. Only enable in development or when troubleshooting issues."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    asyncio: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enables Python asyncio debug mode which provides detailed information about "
                "unawaited coroutines, slow callbacks, and other async programming issues. "
                "Significantly impacts performance and should only be used for debugging async bugs."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    kernel_runner: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("kernel-runner", "kernel_runner"),
            serialization_alias="kernel-runner",
        ),
        BackendAIConfigMeta(
            description=(
                "Enables debug mode for the kernel runner component which handles communication "
                "between the agent and session containers. Produces verbose logs about code execution "
                "requests, input/output handling, and container communication. Use for debugging "
                "session execution issues."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    enhanced_aiomonitor_task_info: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "enhanced-aiomonitor-task-info", "enhanced_aiomonitor_task_info"
            ),
            serialization_alias="enhanced-aiomonitor-task-info",
        ),
        BackendAIConfigMeta(
            description=(
                "Enables enhanced task information in the aiomonitor debugging interface. "
                "Provides more detailed async task state information but adds overhead. "
                "Useful for diagnosing async task leaks or blocking issues."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    skip_container_deletion: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("skip-container-deletion", "skip_container_deletion"),
            serialization_alias="skip-container-deletion",
        ),
        BackendAIConfigMeta(
            description=(
                "Prevents automatic container deletion after session termination. "
                "Useful for post-mortem debugging of container state, filesystem, and logs. "
                "Warning: containers will accumulate and consume resources. Only enable temporarily."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    log_stats: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("log-stats", "log_stats"),
            serialization_alias="log-stats",
        ),
        BackendAIConfigMeta(
            description=(
                "Enables logging of container resource statistics (CPU, memory, GPU usage). "
                "Produces verbose periodic logs showing resource consumption metrics. "
                "Useful for debugging resource tracking and quota enforcement issues."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    log_kernel_config: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("log-kernel-config", "log_kernel_config"),
            serialization_alias="log-kernel-config",
        ),
        BackendAIConfigMeta(
            description=(
                "Logs the kernel configuration sent to containers at startup. "
                "Shows environment variables, mount points, and execution settings. "
                "Helpful for debugging container initialization or configuration issues."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    log_alloc_map: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("log-alloc-map", "log_alloc_map"),
            serialization_alias="log-alloc-map",
        ),
        BackendAIConfigMeta(
            description=(
                "Logs the resource allocation map showing which resources (CPU cores, GPUs) "
                "are assigned to which containers. Useful for debugging resource allocation "
                "conflicts or understanding how resources are distributed."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    log_events: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("log-events", "log_events"),
            serialization_alias="log-events",
        ),
        BackendAIConfigMeta(
            description=(
                "Logs all internal agent events including container lifecycle events, "
                "resource updates, and inter-component communication. Produces high volume "
                "of logs but valuable for understanding agent behavior during issues."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    log_heartbeats: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("log-heartbeats", "log_heartbeats"),
            serialization_alias="log-heartbeats",
        ),
        BackendAIConfigMeta(
            description=(
                "Logs heartbeat messages sent between agent and manager. "
                "Heartbeats contain agent status and resource availability information. "
                "Use for debugging connectivity or status synchronization issues."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    heartbeat_interval: Annotated[
        float,
        Field(
            default=20.0,
            validation_alias=AliasChoices("heartbeat-interval", "heartbeat_interval"),
            serialization_alias="heartbeat-interval",
        ),
        BackendAIConfigMeta(
            description=(
                "Interval in seconds between heartbeat messages sent to the manager. "
                "The manager uses heartbeats to detect agent availability. "
                "Lower values provide faster detection of agent issues but increase network traffic."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="20.0", prod="20.0"),
        ),
    ]
    log_docker_events: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("log-docker-events", "log_docker_events"),
            serialization_alias="log-docker-events",
        ),
        BackendAIConfigMeta(
            description=(
                "Logs Docker daemon events received by the agent (container start/stop/die, etc.). "
                "Useful for debugging container lifecycle issues or understanding Docker behavior. "
                "Only applicable when using Docker backend."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    coredump: Annotated[
        CoreDumpConfig,
        Field(default_factory=CoreDumpConfig),
        BackendAIConfigMeta(
            description=(
                "Configuration for container core dump collection. "
                "Core dumps help debug container crashes by providing memory snapshots at crash time."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

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

    backend: Annotated[
        AgentBackend,
        Field(
            validation_alias=AliasChoices("backend", "mode"),
            serialization_alias="backend",
        ),
        BackendAIConfigMeta(
            description=(
                "Backend type for the agent determining how it interacts with the underlying "
                "container orchestration infrastructure. Available options: "
                "'docker' uses Docker daemon for container management (default for most deployments); "
                "'kubernetes' uses Kubernetes API for container management in K8s clusters; "
                "'dummy' is a mock backend for testing without actual containers."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="docker", prod="docker"),
        ),
    ]
    rpc_listen_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="0.0.0.0", port=6001),
            validation_alias=AliasChoices("rpc-listen-addr", "rpc_listen_addr"),
            serialization_alias="rpc-listen-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Network address and port where the agent listens for RPC calls from the manager. "
                "The manager uses this endpoint to send commands like session creation, termination, "
                "and resource queries. Use '0.0.0.0' to listen on all interfaces."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="0.0.0.0:6001", prod="0.0.0.0:6001"),
        ),
    ]
    internal_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="0.0.0.0", port=6003),
            validation_alias=AliasChoices("service-addr", "internal-addr", "service_addr"),
            serialization_alias="internal-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Network address and port for internal services within the agent. "
                "Used for inter-process communication and internal API endpoints. "
                "This address is typically not exposed externally."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="0.0.0.0:6003", prod="0.0.0.0:6003"),
        ),
    ]
    announce_internal_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="host.docker.internal", port=6003),
            validation_alias=AliasChoices(
                "announce-addr", "announce-internal-addr", "announce_addr"
            ),
            serialization_alias="announce-internal-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Address announced to containers for reaching the agent's internal services. "
                "Containers use this address to communicate back with the agent. "
                "Use 'host.docker.internal' for Docker on macOS/Windows, or the host's actual IP on Linux."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="host.docker.internal:6003", prod="192.168.1.100:6003"),
        ),
    ]
    ssl_enabled: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("ssl-enabled", "ssl_enabled"),
            serialization_alias="ssl-enabled",
        ),
        BackendAIConfigMeta(
            description=(
                "Enables SSL/TLS encryption for RPC communication between the agent and manager. "
                "When enabled, requires ssl_cert and ssl_key to be configured with valid certificates. "
                "Recommended for production deployments to secure inter-component communication."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    ssl_cert: Annotated[
        Optional[FilePath],
        Field(
            default=None,
            validation_alias=AliasChoices("ssl-cert", "ssl_cert"),
            serialization_alias="ssl-cert",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to the SSL/TLS certificate file (PEM format) for encrypted RPC communication. "
                "Required when ssl_enabled is true. The certificate should be valid for the agent's "
                "hostname and signed by a trusted CA or self-signed for internal use."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(local="/path/to/cert.pem", prod="/etc/backend.ai/ssl/agent.crt"),
        ),
    ]
    ssl_key: Annotated[
        Optional[FilePath],
        Field(
            default=None,
            validation_alias=AliasChoices("ssl-key", "ssl_key"),
            serialization_alias="ssl-key",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to the SSL/TLS private key file (PEM format) corresponding to the ssl_cert. "
                "Required when ssl_enabled is true. The key file should have restricted permissions "
                "(e.g., 0600) and be readable only by the agent process."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(local="/path/to/key.pem", prod="/etc/backend.ai/ssl/agent.key"),
        ),
    ]
    advertised_rpc_addr: Annotated[
        Optional[HostPortPair],
        Field(
            default=None,
            validation_alias=AliasChoices("advertised-rpc-addr", "advertised_rpc_addr"),
            serialization_alias="advertised-rpc-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "External address that the agent advertises to the manager for RPC callbacks. "
                "Use when the agent is behind NAT or a load balancer and the listen address "
                "differs from the externally reachable address. If not set, uses rpc_listen_addr."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="192.168.1.100:6001", prod="192.168.1.100:6001"),
        ),
    ]
    rpc_auth_manager_public_key: Annotated[
        Optional[FilePath],
        Field(
            default=None,
            validation_alias=AliasChoices(
                "rpc-auth-manager-public-key", "rpc_auth_manager_public_key"
            ),
            serialization_alias="rpc-auth-manager-public-key",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to the manager's public key file for authenticating RPC messages. "
                "Used with ZeroMQ CURVE authentication to verify messages from the manager. "
                "Part of the RPC security mechanism for preventing unauthorized access."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(
                local="/path/to/public.key", prod="/etc/backend.ai/keys/manager.pub"
            ),
        ),
    ]
    rpc_auth_agent_keypair: Annotated[
        Optional[FilePath],
        Field(
            default=None,
            validation_alias=AliasChoices("rpc-auth-agent-keypair", "rpc_auth_agent_keypair"),
            serialization_alias="rpc-auth-agent-keypair",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to the agent's keypair file for RPC authentication. "
                "Contains both public and private keys used for ZeroMQ CURVE authentication. "
                "The private key must be kept secure as it proves the agent's identity."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(
                local="/path/to/keypair.key", prod="/etc/backend.ai/keys/agent.keypair"
            ),
        ),
    ]
    ipc_base_path: Annotated[
        AutoDirectoryPath,
        Field(
            default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
            validation_alias=AliasChoices("ipc-base-path", "ipc_base_path"),
            serialization_alias="ipc-base-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Base directory path for Unix domain sockets and other IPC mechanisms. "
                "Used for communication between the agent and its child processes. "
                "Directory is created automatically with appropriate permissions."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="/tmp/backend.ai/ipc", prod="/var/run/backend.ai/ipc"),
        ),
    ]
    var_base_path: Annotated[
        AutoDirectoryPath,
        Field(
            default=AutoDirectoryPath("./var/lib/backend.ai"),
            validation_alias=AliasChoices("var-base-path", "var_base_path"),
            serialization_alias="var-base-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Base directory for the agent's variable data including runtime state, "
                "temporary files, and data that persists across restarts but not upgrades. "
                "Ensure sufficient disk space and appropriate permissions."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="./var/lib/backend.ai", prod="/var/lib/backend.ai"),
        ),
    ]
    mount_path: Annotated[
        Optional[AutoDirectoryPath],
        Field(
            default=None,
            validation_alias=AliasChoices("mount-path", "mount_path"),
            serialization_alias="mount-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Base directory path for mounting storage volumes into containers. "
                "Virtual folders and other storage mounts are placed under this path. "
                "Should be on a filesystem with sufficient space for user data."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="/mnt/backend.ai", prod="/mnt/backend.ai"),
        ),
    ]
    cohabiting_storage_proxy: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("cohabiting-storage-proxy", "cohabiting_storage_proxy"),
            serialization_alias="cohabiting-storage-proxy",
        ),
        BackendAIConfigMeta(
            description=(
                "Indicates whether a storage proxy runs on the same host as the agent. "
                "When true, the agent uses local filesystem paths for storage operations, "
                "improving performance. When false, storage is accessed via network protocols."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    public_host: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("public-host", "public_host"),
            serialization_alias="public-host",
        ),
        BackendAIConfigMeta(
            description=(
                "Public hostname or IP address for this agent node. "
                "Used for generating URLs that users can access to reach services "
                "running on this agent, such as web terminals or application proxies."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="backend.ai", prod="compute1.backend.ai"),
        ),
    ]
    region: Annotated[
        Optional[str],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Cloud region identifier where this agent is deployed. "
                "Used for geographic resource allocation and displayed in admin interfaces. "
                "Use standard region codes like 'us-east-1', 'eu-west-1', or custom identifiers."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="us-east-1", prod="us-east-1"),
        ),
    ]
    instance_type: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("instance-type", "instance_type"),
            serialization_alias="instance-type",
        ),
        BackendAIConfigMeta(
            description=(
                "Cloud instance type identifier for this agent's host machine. "
                "Used for cost tracking, capacity planning, and displayed in admin interfaces. "
                "Use cloud provider's instance type names like 'm5.large' or 'n1-standard-4'."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="m5.large", prod="m5.xlarge"),
        ),
    ]
    pid_file: Annotated[
        Path,
        Field(
            default=Path(os.devnull),
            validation_alias=AliasChoices("pid-file", "pid_file"),
            serialization_alias="pid-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to the PID file where the agent writes its process ID. "
                "Used by init systems and monitoring tools to track the agent process. "
                "Set to /dev/null to disable PID file creation."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="/dev/null", prod="/var/run/backend.ai/agent.pid"),
        ),
    ]
    event_loop: Annotated[
        EventLoopType,
        Field(
            default=EventLoopType.ASYNCIO,
            validation_alias=AliasChoices("event-loop", "event_loop"),
            serialization_alias="event-loop",
        ),
        BackendAIConfigMeta(
            description=(
                "Python async event loop implementation to use. "
                "'asyncio' uses the standard library implementation (default, most compatible). "
                "'uvloop' uses a faster libuv-based implementation (better performance, Linux only)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="asyncio", prod="asyncio"),
        ),
    ]
    skip_manager_detection: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("skip-manager-detection", "skip_manager_detection"),
            serialization_alias="skip-manager-detection",
        ),
        BackendAIConfigMeta(
            description=(
                "Skips automatic detection of the manager during agent startup. "
                "When true, the agent starts without verifying manager connectivity. "
                "Useful for testing or when the manager becomes available after the agent starts."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    aiomonitor_termui_port: Annotated[
        int,
        Field(
            default=38200,
            ge=1,
            le=65535,
            validation_alias=AliasChoices(
                "aiomonitor-termui-port", "aiomonitor-port", "aiomonitor_termui_port"
            ),
            serialization_alias="aiomonitor-termui-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port for the aiomonitor terminal UI debugging interface. "
                "Provides real-time inspection of async tasks and event loop state. "
                "Connect via telnet to this port for interactive debugging."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="38200", prod="38200"),
        ),
    ]
    aiomonitor_webui_port: Annotated[
        int,
        Field(
            default=39200,
            ge=1,
            le=65535,
            validation_alias=AliasChoices("aiomonitor-webui-port", "aiomonitor_webui_port"),
            serialization_alias="aiomonitor-webui-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port for the aiomonitor web UI debugging interface. "
                "Provides a browser-based interface for inspecting async tasks. "
                "Access via http://agent-host:port for visual debugging."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="39200", prod="39200"),
        ),
    ]
    metadata_server_bind_host: Annotated[
        str,
        Field(
            default="0.0.0.0",
            validation_alias=AliasChoices("metadata-server-bind-host", "metadata_server_bind_host"),
            serialization_alias="metadata-server-bind-host",
        ),
        BackendAIConfigMeta(
            description=(
                "Bind host for the container metadata server. "
                "Containers connect to this server to retrieve session metadata and configuration. "
                "Use '0.0.0.0' to listen on all interfaces or a specific IP for restricted access."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="0.0.0.0", prod="0.0.0.0"),
        ),
    ]
    metadata_server_port: Annotated[
        int,
        Field(
            default=40128,
            ge=1,
            le=65535,
            validation_alias=AliasChoices("metadata-server-port", "metadata_server_port"),
            serialization_alias="metadata-server-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port for the container metadata server. "
                "Containers access metadata like session ID, access key, and environment variables "
                "through this server. Similar to cloud provider instance metadata services."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="40128", prod="40128"),
        ),
    ]
    allow_compute_plugins: Annotated[
        Optional[set[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("allow-compute-plugins", "allow_compute_plugins"),
            serialization_alias="allow-compute-plugins",
        ),
        BackendAIConfigMeta(
            description=(
                "Allowlist of compute plugin names that can be loaded by this agent. "
                "If set, only plugins in this list are loaded. If null/empty, all discovered "
                "plugins are loaded except those in block_compute_plugins. "
                "Plugin names use Python package notation (e.g., 'ai.backend.accelerator.cuda')."
            ),
            added_version="25.12.0",
            example=ConfigExample(
                local="", prod='["ai.backend.accelerator.cuda", "ai.backend.accelerator.rocm"]'
            ),
        ),
    ]
    block_compute_plugins: Annotated[
        Optional[set[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("block-compute-plugins", "block_compute_plugins"),
            serialization_alias="block-compute-plugins",
        ),
        BackendAIConfigMeta(
            description=(
                "Blocklist of compute plugin names that should not be loaded by this agent. "
                "Plugins in this list are excluded even if discovered. "
                "Use to disable specific accelerators or features on certain nodes."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod='["ai.backend.accelerator.mock"]'),
        ),
    ]
    allow_network_plugins: Annotated[
        Optional[set[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("allow-network-plugins", "allow_network_plugins"),
            serialization_alias="allow-network-plugins",
        ),
        BackendAIConfigMeta(
            description=(
                "Allowlist of network plugin names that can be loaded by this agent. "
                "Network plugins provide custom networking configurations for containers. "
                "If set, only plugins in this list are loaded."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod='["ai.backend.network.overlay"]'),
        ),
    ]
    block_network_plugins: Annotated[
        Optional[set[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("block-network-plugins", "block_network_plugins"),
            serialization_alias="block-network-plugins",
        ),
        BackendAIConfigMeta(
            description=(
                "Blocklist of network plugin names that should not be loaded by this agent. "
                "Use to disable specific network configurations on certain nodes."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod='["ai.backend.network.legacy"]'),
        ),
    ]
    image_commit_path: Annotated[
        AutoDirectoryPath,
        Field(
            default=AutoDirectoryPath("./tmp/backend.ai/commit"),
            validation_alias=AliasChoices("image-commit-path", "image_commit_path"),
            serialization_alias="image-commit-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Directory path for storing temporary image commit data. "
                "Used when users commit their running containers as new images. "
                "Requires sufficient disk space for container filesystem layers."
            ),
            added_version="25.12.0",
            example=ConfigExample(
                local="./tmp/backend.ai/commit", prod="/var/lib/backend.ai/commit"
            ),
        ),
    ]
    abuse_report_path: Annotated[
        Optional[Path],
        Field(
            default=None,
            validation_alias=AliasChoices("abuse-report-path", "abuse_report_path"),
            serialization_alias="abuse-report-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Directory path for storing container abuse reports. "
                "When suspicious or abusive behavior is detected in containers, "
                "detailed reports are written here for review by administrators."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="/var/log/backend.ai/abuse"),
        ),
    ]
    use_experimental_redis_event_dispatcher: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "use-experimental-redis-event-dispatcher", "use_experimental_redis_event_dispatcher"
            ),
            serialization_alias="use-experimental-redis-event-dispatcher",
        ),
        BackendAIConfigMeta(
            description=(
                "Enables the experimental Redis-based event dispatcher for agent-manager communication. "
                "Provides improved event delivery reliability and scalability. "
                "Requires Redis to be configured. Still in experimental phase."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    docker_mode: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("docker-mode", "docker_mode"),
            serialization_alias="docker-mode",
        ),
        BackendAIConfigMeta(
            description=(
                "Docker runtime mode, auto-detected based on the kernel version. "
                "'linuxkit' indicates Docker Desktop with LinuxKit VM (macOS/Windows). "
                "'native' indicates native Docker on Linux. Affects filesystem and networking behavior."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="linuxkit", prod="native"),
        ),
    ]
    mount_path_uid_gid: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("mount-path-uid-gid", "mount_path_uid_gid"),
            serialization_alias="mount-path-uid-gid",
        ),
        BackendAIConfigMeta(
            description=(
                "Owner UID:GID for mounted directories in format 'user:group'. "
                "Controls ownership of files created in mounted volumes. "
                "Use 'root:root' for privileged containers or match container user for unprivileged."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="bai:bai"),
        ),
    ]

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

    id: Annotated[
        Optional[str],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Unique identifier for this agent instance. "
                "If not specified, a random UUID is generated. In multi-agent mode, "
                "each agent must have a unique ID. Used for tracking, logging, and management."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="agent-local-1", prod="agent-prod-001"),
        ),
    ]
    agent_sock_port: Annotated[
        int,
        Field(
            default=6007,
            ge=1024,
            le=65535,
            validation_alias=AliasChoices("agent-sock-port", "agent_sock_port"),
            serialization_alias="agent-sock-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port number for the agent's socket communication with containers. "
                "Containers connect to this port for the kernel runner protocol. "
                "In multi-agent mode, each agent must use a unique port."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="6007", prod="6007"),
        ),
    ]
    scaling_group: Annotated[
        str,
        Field(
            default="default",
            validation_alias=AliasChoices("scaling-group", "scaling_group"),
            serialization_alias="scaling-group",
        ),
        BackendAIConfigMeta(
            description=(
                "Name of the scaling group this agent belongs to. "
                "Scaling groups organize agents into logical clusters for resource allocation. "
                "Users can target specific scaling groups when creating sessions."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="default", prod="gpu-cluster"),
        ),
    ]
    scaling_group_type: Annotated[
        ResourceGroupType,
        Field(
            default=ResourceGroupType.COMPUTE,
            validation_alias=AliasChoices("scaling-group-type", "scaling_group_type"),
            serialization_alias="scaling-group-type",
        ),
        BackendAIConfigMeta(
            description=(
                "Type of resource group this agent serves. "
                "'compute' for general-purpose computation nodes. "
                "'storage' for storage-optimized nodes. "
                "Determines how the agent is used in workload scheduling."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="compute", prod="compute"),
        ),
    ]
    force_terminate_abusing_containers: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "force-terminate-abusing-containers", "force_terminate_abusing_containers"
            ),
            serialization_alias="force-terminate-abusing-containers",
        ),
        BackendAIConfigMeta(
            description=(
                "When enabled, automatically terminates containers that exceed resource limits "
                "or exhibit abusive behavior (e.g., crypto mining, excessive I/O). "
                "Use with caution as it may interrupt legitimate workloads."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    kernel_creation_concurrency: Annotated[
        int,
        Field(
            default=4,
            ge=1,
            le=32,
            validation_alias=AliasChoices(
                "kernel-creation-concurrency", "kernel_creation_concurrency"
            ),
            serialization_alias="kernel-creation-concurrency",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of containers that can be created simultaneously. "
                "Higher values speed up bulk session creation but increase resource usage. "
                "Lower values reduce resource contention during container startup."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="4", prod="8"),
        ),
    ]
    sync_container_lifecycles: Annotated[
        SyncContainerLifecyclesConfig,
        Field(
            default_factory=SyncContainerLifecyclesConfig,
            validation_alias=AliasChoices("sync-container-lifecycles", "sync_container_lifecycles"),
            serialization_alias="sync-container-lifecycles",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for container lifecycle synchronization between agent and manager. "
                "Ensures container states are consistent across the system."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

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

    bind_host: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("bind-host", "bind_host", "kernel-host"),
            serialization_alias="bind-host",
        ),
        BackendAIConfigMeta(
            description=(
                "Host address that containers bind their network ports to. "
                "Empty string means binding to all available interfaces (equivalent to '0.0.0.0'). "
                "Specify a particular IP to restrict container network access."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="0.0.0.0"),
        ),
    ]
    advertised_host: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("advertised-host", "advertised_host"),
            serialization_alias="advertised-host",
        ),
        BackendAIConfigMeta(
            description=(
                "Host address advertised to clients for connecting to container services. "
                "Used when the bind address differs from the externally reachable address, "
                "such as when running behind NAT or in a cloud environment."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="192.168.1.100"),
        ),
    ]
    krunner_volumes: Annotated[
        Optional[Mapping[str, str]],
        Field(
            default=None,
            validation_alias=AliasChoices("krunner-volumes", "krunner_volumes"),
            serialization_alias="krunner-volumes",
        ),
        BackendAIConfigMeta(
            description=(
                "KRunner volumes configuration mapping container paths to host paths. "
                "Specifies volumes to mount into containers for the kernel runner. "
                "This is typically set automatically by the agent based on environment detection "
                "and should not normally be configured manually."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod='{ "/opt/krunner": "/opt/backend.ai/krunner" }'),
        ),
    ]

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )


class OverridableContainerConfig(BaseConfigSchema):
    """
    Container settings that can be overridden per-agent in multi-agent mode.
    """

    kernel_uid: Annotated[
        UserID,
        Field(
            default=UserID(-1),
            validation_alias=AliasChoices("kernel-uid", "kernel_uid"),
            serialization_alias="kernel-uid",
        ),
        BackendAIConfigMeta(
            description=(
                "User ID (UID) for processes running inside containers. "
                "Value of -1 uses the container image's default UID. "
                "Set to match the host user's UID for proper file permissions on mounted volumes."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="-1", prod="1000"),
        ),
    ]
    kernel_gid: Annotated[
        GroupID,
        Field(
            default=GroupID(-1),
            validation_alias=AliasChoices("kernel-gid", "kernel_gid"),
            serialization_alias="kernel-gid",
        ),
        BackendAIConfigMeta(
            description=(
                "Group ID (GID) for processes running inside containers. "
                "Value of -1 uses the container image's default GID. "
                "Set to match the host group's GID for proper file permissions on mounted volumes."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="-1", prod="1000"),
        ),
    ]
    port_range: Annotated[
        tuple[int, int],
        Field(
            default=(30000, 31000),
            validation_alias=AliasChoices("port-range", "port_range"),
            serialization_alias="port-range",
        ),
        BackendAIConfigMeta(
            description=(
                "Range of host ports allocated to containers for network services. "
                "Format is [start, end] inclusive. Containers get ports from this range for "
                "SSH, Jupyter, and other services. In multi-agent mode, ensure non-overlapping ranges."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="[30000, 31000]", prod="[30000, 32000]"),
        ),
    ]
    stats_type: Annotated[
        Optional[StatModes],
        Field(
            default=StatModes.DOCKER,
            validation_alias=AliasChoices("stats-type", "stats_type"),
            serialization_alias="stats-type",
        ),
        BackendAIConfigMeta(
            description=(
                "Method for collecting container resource statistics. "
                "'docker' uses Docker's stats API (most compatible). "
                "'cgroup' reads from cgroup filesystem directly (more accurate, requires root). "
                "'null' disables statistics collection."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="docker", prod="docker"),
        ),
    ]
    sandbox_type: Annotated[
        ContainerSandboxType,
        Field(
            default=ContainerSandboxType.DOCKER,
            validation_alias=AliasChoices("sandbox-type", "sandbox_type"),
            serialization_alias="sandbox-type",
        ),
        BackendAIConfigMeta(
            description=(
                "Container sandbox implementation for process isolation. "
                "'docker' uses Docker containers (standard). "
                "'jail' uses lightweight jailed containers for faster startup (x86_64 Linux only). "
                "Jail provides better performance but with reduced isolation."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="docker", prod="docker"),
        ),
    ]
    jail_args: Annotated[
        list[str],
        Field(
            default_factory=list,
            validation_alias=AliasChoices("jail-args", "jail_args"),
            serialization_alias="jail-args",
        ),
        BackendAIConfigMeta(
            description=(
                "Additional command-line arguments passed to the jail sandbox. "
                "Only applicable when sandbox_type is 'jail'. "
                "Use to customize jail behavior like mount points or resource limits."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod='["--mount=/data", "--limit-mem=4G"]'),
        ),
    ]
    scratch_type: Annotated[
        ScratchType,
        Field(
            default=ScratchType.HOSTDIR,
            validation_alias=AliasChoices("scratch-type", "scratch_type"),
            serialization_alias="scratch-type",
        ),
        BackendAIConfigMeta(
            description=(
                "Type of scratch space provided to containers for temporary data. "
                "'hostdir' uses a directory on the host filesystem. "
                "'hostfile' uses a loopback file with size limits (requires root). "
                "'memory' uses RAM-backed tmpfs for fast but limited storage. "
                "'k8s-nfs' uses NFS-backed storage for Kubernetes."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="hostdir", prod="hostdir"),
        ),
    ]
    scratch_root: Annotated[
        AutoDirectoryPath,
        Field(
            default=AutoDirectoryPath("./scratches"),
            validation_alias=AliasChoices("scratch-root", "scratch_root"),
            serialization_alias="scratch-root",
        ),
        BackendAIConfigMeta(
            description=(
                "Base directory for container scratch space storage. "
                "Each container gets a subdirectory under this path for temporary files. "
                "Should be on a fast filesystem with adequate space."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="./scratches", prod="/var/lib/backend.ai/scratches"),
        ),
    ]
    scratch_size: Annotated[
        BinarySizeField,
        Field(
            default=BinarySize.finite_from_str("0"),
            validation_alias=AliasChoices("scratch-size", "scratch_size"),
            serialization_alias="scratch-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Size limit for each container's scratch space when using 'hostfile' type. "
                "Use binary size format (e.g., '1G', '500M'). "
                "Value of '0' means no limit (only effective with 'hostdir' type)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="0", prod="10G"),
        ),
    ]
    scratch_nfs_address: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("scratch-nfs-address", "scratch_nfs_address"),
            serialization_alias="scratch-nfs-address",
        ),
        BackendAIConfigMeta(
            description=(
                "NFS server address and export path for scratch storage. "
                "Required when scratch_type is 'k8s-nfs'. "
                "Format: 'server-ip:/export/path' or 'server-hostname:/export/path'."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="192.168.1.50:/exports/scratch"),
        ),
    ]
    scratch_nfs_options: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("scratch-nfs-options", "scratch_nfs_options"),
            serialization_alias="scratch-nfs-options",
        ),
        BackendAIConfigMeta(
            description=(
                "NFS mount options for scratch storage. "
                "Required when scratch_type is 'k8s-nfs'. "
                "Common options: 'rw,sync', 'rw,async,soft'."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="rw,sync"),
        ),
    ]
    alternative_bridge: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("alternative-bridge", "alternative_bridge"),
            serialization_alias="alternative-bridge",
        ),
        BackendAIConfigMeta(
            description=(
                "Name of an alternative Docker bridge network for container networking. "
                "If not set, uses the default Docker bridge network. "
                "Use to isolate Backend.AI containers on a dedicated network."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="br-backend"),
        ),
    ]
    swarm_enabled: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("swarm-enabled", "swarm_enabled"),
            serialization_alias="swarm-enabled",
        ),
        BackendAIConfigMeta(
            description=(
                "Enables Docker Swarm mode for container orchestration. "
                "When enabled, the agent uses Docker Swarm APIs for managing containers, networks, "
                "and services across multiple Docker hosts. Only applicable with Docker backend."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]

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
    cpu: Annotated[
        int,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Number of CPU cores allocated to this agent for container workloads. "
                "Only used when resource allocation_mode is 'manual'. "
                "All agents in manual mode must specify this value. "
                "The total allocation across all agents should not exceed available cores."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="4", prod="16"),
        ),
    ]
    mem: Annotated[
        BinarySizeField,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Amount of memory allocated to this agent for container workloads. "
                "Only used when resource allocation_mode is 'manual'. "
                "All agents in manual mode must specify this value. "
                "Use binary size format (e.g., '32G', '64G')."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="8G", prod="64G"),
        ),
    ]
    devices: Annotated[
        Mapping[SlotNameField, Decimal],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description=(
                "Device-specific resource allocations as key-value pairs. "
                "Only used when resource allocation_mode is 'manual'. "
                "Keys are slot names (e.g., 'cuda.mem', 'cuda.shares'), values are decimal amounts. "
                "Use to allocate GPU memory, compute shares, and other accelerator resources."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod='{"cuda.mem": "0.5", "cuda.shares": "0.5"}'),
        ),
    ]

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
    reserved_cpu: Annotated[
        int,
        Field(
            default=1,
            validation_alias=AliasChoices("reserved-cpu", "reserved_cpu"),
            serialization_alias="reserved-cpu",
        ),
        BackendAIConfigMeta(
            description=(
                "Number of CPU cores reserved for the operating system and agent process. "
                "These cores are not available for container workloads. "
                "Increase if the agent or system services need more resources."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="2"),
        ),
    ]
    reserved_mem: Annotated[
        BinarySizeField,
        Field(
            default=BinarySize.finite_from_str("1G"),
            validation_alias=AliasChoices("reserved-mem", "reserved_mem"),
            serialization_alias="reserved-mem",
        ),
        BackendAIConfigMeta(
            description=(
                "Amount of memory reserved for the operating system and agent process. "
                "Subtracted from total memory when reporting available resources to the manager. "
                "The actual reserved amount may vary slightly due to memory_align_size rounding."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1G", prod="4G"),
        ),
    ]
    reserved_disk: Annotated[
        BinarySizeField,
        Field(
            default=BinarySize.finite_from_str("8G"),
            validation_alias=AliasChoices("reserved-disk", "reserved_disk"),
            serialization_alias="reserved-disk",
        ),
        BackendAIConfigMeta(
            description=(
                "Disk space reserved for the operating system and agent operations. "
                "Currently unused but reserved for future features like guaranteed minimum scratch space. "
                "Set based on expected system disk requirements."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="8G", prod="16G"),
        ),
    ]
    allocation_mode: Annotated[
        ResourceAllocationMode,
        Field(
            default=ResourceAllocationMode.SHARED,
            validation_alias=AliasChoices("allocation-mode", "allocation_mode"),
            serialization_alias="allocation-mode",
        ),
        BackendAIConfigMeta(
            description=(
                "Resource allocation strategy for multi-agent deployments. "
                "'shared' allows all agents to see full resources (may overcommit). "
                "'auto-split' divides resources equally among agents (N agents get 1/N each). "
                "'manual' requires explicit resource allocation per agent via allocations config."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="shared", prod="auto-split"),
        ),
    ]
    allocations: Annotated[
        Optional[ResourceAllocationConfig],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Manual resource allocation configuration for this agent. "
                "Required when allocation_mode is 'manual'. "
                "Specifies exact CPU, memory, and device allocations for this agent."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    memory_align_size: Annotated[
        BinarySizeField,
        Field(
            default=BinarySize.finite_from_str("16M"),
            validation_alias=AliasChoices("memory-align-size", "memory_align_size"),
            serialization_alias="memory-align-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Memory alignment granularity for reported memory sizes. "
                "Absorbs small variations in available memory between nodes with similar hardware. "
                "Should be a multiple of the system page size (typically 2MB for huge pages)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="16M", prod="32M"),
        ),
    ]
    allocation_order: Annotated[
        list[str],
        Field(
            default=["cuda", "rocm", "tpu", "cpu", "mem"],
            validation_alias=AliasChoices("allocation-order", "allocation_order"),
            serialization_alias="allocation-order",
        ),
        BackendAIConfigMeta(
            description=(
                "Order in which resources are allocated to containers. "
                "Resources are allocated in this sequence, which can affect placement "
                "when multiple resource types compete for affinity (e.g., GPU and NUMA)."
            ),
            added_version="25.12.0",
            example=ConfigExample(
                local='["cuda", "rocm", "tpu", "cpu", "mem"]',
                prod='["cuda", "rocm", "tpu", "cpu", "mem"]',
            ),
        ),
    ]
    affinity_policy: Annotated[
        AffinityPolicy,
        Field(
            default=AffinityPolicy.INTERLEAVED,
            validation_alias=AliasChoices("affinity-policy", "affinity_policy"),
            serialization_alias="affinity-policy",
        ),
        BackendAIConfigMeta(
            description=(
                "NUMA and device affinity policy for resource allocation. "
                "'INTERLEAVED' spreads allocations across NUMA nodes for balance. "
                "'PACKED' fills one NUMA node before moving to the next for locality. "
                "Affects performance characteristics of multi-socket systems."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="INTERLEAVED", prod="INTERLEAVED"),
        ),
    ]

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
            except KeyError as e:
                raise ValueError(f"Invalid affinity policy: {v}") from e
        return v


class ContainerLogsConfig(BaseConfigSchema):
    max_length: Annotated[
        BinarySizeField,
        Field(
            default=BinarySize.finite_from_str("10M"),
            validation_alias=AliasChoices("max-length", "max_length"),
            serialization_alias="max-length",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum total size of container logs that the agent will retrieve and store. "
                "Logs exceeding this size are truncated from the beginning. "
                "Use binary size format (e.g., '10M', '50M')."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="10M", prod="50M"),
        ),
    ]
    chunk_size: Annotated[
        BinarySizeField,
        Field(
            default=BinarySize.finite_from_str("64K"),
            validation_alias=AliasChoices("chunk-size", "chunk_size"),
            serialization_alias="chunk-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Size of chunks when reading container logs from Docker. "
                "Larger chunks improve throughput but use more memory. "
                "Use binary size format (e.g., '64K', '128K')."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="64K", prod="128K"),
        ),
    ]

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class APIConfig(BaseConfigSchema):
    pull_timeout: Annotated[
        Optional[float],
        Field(
            default=7200.0,  # 2 hours
            ge=0,
            validation_alias=AliasChoices("pull-timeout", "pull_timeout"),
            serialization_alias="pull-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for pulling container images from registries. "
                "Large images or slow networks may require longer timeouts. "
                "Default is 7200 seconds (2 hours)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="7200", prod="7200"),
        ),
    ]
    commit_timeout: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0,
            validation_alias=AliasChoices("commit-timeout", "commit_timeout"),
            serialization_alias="commit-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for committing containers to images. "
                "Used when users save their container state as a new image. "
                "Set to None for no timeout (may be needed for large containers)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="7200"),
        ),
    ]
    push_timeout: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0,
            validation_alias=AliasChoices("push-timeout", "push_timeout"),
            serialization_alias="push-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for pushing committed images to registries. "
                "Used when users push their committed images to external registries. "
                "Set to None for no timeout."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="7200"),
        ),
    ]


class KernelLifecyclesConfig(BaseConfigSchema):
    init_polling_attempt: Annotated[
        int,
        Field(
            default=10,
            validation_alias=AliasChoices("init-polling-attempt", "init_polling_attempt"),
            serialization_alias="init-polling-attempt",
        ),
        BackendAIConfigMeta(
            description=(
                "Number of attempts to poll for container readiness during initialization. "
                "The agent checks container health this many times before giving up. "
                "Increase for containers with slower initialization."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="10", prod="20"),
        ),
    ]
    init_polling_timeout_sec: Annotated[
        float,
        Field(
            default=60.0,
            validation_alias=AliasChoices("init-polling-timeout-sec", "init_polling_timeout_sec"),
            serialization_alias="init-polling-timeout-sec",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum time in seconds to wait between polling attempts during container initialization. "
                "If the container doesn't respond within this time, the attempt fails. "
                "Total initialization time is approximately attempts * timeout."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="60.0", prod="120.0"),
        ),
    ]
    init_timeout_sec: Annotated[
        float,
        Field(
            default=60.0,
            validation_alias=AliasChoices("init-timeout-sec", "init_timeout_sec"),
            serialization_alias="init-timeout-sec",
        ),
        BackendAIConfigMeta(
            description=(
                "Overall timeout in seconds for container initialization. "
                "If the container is not ready within this time, it's considered failed. "
                "Should be large enough for containers with heavy startup processes."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="60.0", prod="120.0"),
        ),
    ]


class DockerExtraConfig(BaseConfigSchema):
    """
    For checking additional Docker configurations
    """

    swarm_enabled: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("swarm-enabled", "swarm_enabled"),
            serialization_alias="swarm-enabled",
        ),
        BackendAIConfigMeta(
            description=(
                "Indicates whether Docker Swarm mode is enabled on this host. "
                "Used internally to verify Swarm compatibility when container.swarm_enabled is true. "
                "This is typically auto-detected and not set manually."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]


class AgentGlobalConfig(BaseConfigSchema):
    """
    Configuration shared across all agents (logging, etcd, API, etc.).
    """

    # Local config
    pyroscope: Annotated[
        PyroscopeConfig,
        Field(default_factory=PyroscopeConfig),  # type: ignore[arg-type]
        BackendAIConfigMeta(
            description=(
                "Pyroscope continuous profiling configuration for the agent. "
                "Pyroscope collects CPU and memory profiles to help identify performance bottlenecks "
                "and memory issues in the agent process."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    logging: Annotated[
        LoggingConfig,
        Field(default_factory=LoggingConfig),
        BackendAIConfigMeta(
            description=(
                "Logging configuration for the agent. Controls log levels, output destinations, "
                "and log formatting. Proper logging setup is essential for debugging and monitoring "
                "agent behavior in production environments."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    otel: Annotated[
        OTELConfig,
        Field(default_factory=OTELConfig),  # type: ignore[arg-type]
        BackendAIConfigMeta(
            description=(
                "OpenTelemetry (OTEL) configuration for distributed tracing and metrics collection. "
                "Enables integration with observability platforms like Jaeger, Zipkin, or Prometheus "
                "for comprehensive monitoring of agent operations."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    service_discovery: Annotated[
        ServiceDiscoveryConfig,
        Field(
            default_factory=ServiceDiscoveryConfig,  # type: ignore[arg-type]
            validation_alias=AliasChoices("service-discovery", "service_discovery"),
            serialization_alias="service-discovery",
        ),
        BackendAIConfigMeta(
            description=(
                "Service discovery configuration for the agent to register itself and discover "
                "other Backend.AI services in the cluster. Enables dynamic service mesh integration "
                "and load balancing across multiple agents."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    debug: Annotated[
        DebugConfig,
        Field(default_factory=DebugConfig),
        BackendAIConfigMeta(
            description=(
                "Debug and development configuration for the agent. Enables features like "
                "asynchronous debugging, memory leak detection, and core dump collection. "
                "Should be carefully configured in production to avoid performance overhead."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    etcd: Annotated[
        EtcdConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "etcd connection configuration for the agent. etcd is used as the distributed "
                "key-value store for cluster coordination, configuration sharing, and service discovery. "
                "All agents in a cluster must connect to the same etcd cluster."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # Etcd config
    container_logs: Annotated[
        ContainerLogsConfig,
        Field(
            default_factory=ContainerLogsConfig,
            validation_alias=AliasChoices("container-logs", "container_logs"),
            serialization_alias="container-logs",
        ),
        BackendAIConfigMeta(
            description=(
                "Container log collection and retention configuration. "
                "Controls how container stdout/stderr logs are collected, stored, and made "
                "available to users. Important for debugging container applications."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    api: Annotated[
        APIConfig,
        Field(default_factory=APIConfig),
        BackendAIConfigMeta(
            description=(
                "API timeout configuration for container image operations. "
                "Defines timeout values for pulling, committing, and pushing container images. "
                "Should be adjusted based on image sizes and network conditions."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    kernel_lifecycles: Annotated[
        KernelLifecyclesConfig,
        Field(
            default_factory=KernelLifecyclesConfig,
            validation_alias=AliasChoices("kernel-lifecycles", "kernel_lifecycles"),
            serialization_alias="kernel-lifecycles",
        ),
        BackendAIConfigMeta(
            description=(
                "Kernel (container) lifecycle timing configuration. "
                "Controls polling intervals and timeouts during container initialization. "
                "Affects how quickly the agent detects container startup success or failure."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    plugins: Annotated[
        Any,
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description=(
                "Plugin configuration injected at runtime from etcd. "
                "This field should not be manually configured in the agent configuration file. "
                "Plugin settings are managed centrally in etcd and distributed to agents automatically."
            ),
            added_version="25.12.0",
        ),
    ]
    redis: Annotated[
        Optional[RedisConfig],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Redis configuration injected at runtime from etcd. "
                "Redis is used for inter-agent communication, caching, and pub/sub messaging. "
                "This field should not be manually configured as it is injected from etcd settings."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

    model_config = ConfigDict(
        validate_assignment=True,
    )


class AgentSpecificConfig(BaseConfigSchema):
    """
    Default values for agent, container, and resource config.
    """

    agent: Annotated[
        AgentConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Agent-specific configuration including network settings, identity, and operational modes. "
                "In multi-agent mode (when 'agents' field is populated), this serves as the default "
                "configuration that individual agents inherit and can override."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    container: Annotated[
        ContainerConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Container runtime configuration including execution modes, user settings, and networking. "
                "In multi-agent mode (when 'agents' field is populated), this serves as the default "
                "configuration that individual agents inherit and can override."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    resource: Annotated[
        ResourceConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Resource allocation configuration including CPU, memory, and accelerator device settings. "
                "In multi-agent mode (when 'agents' field is populated), this serves as the default "
                "configuration that individual agents inherit and can override."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

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

    agent: Annotated[
        OverridableAgentConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Agent configuration overrides for an individual agent in multi-agent mode. "
                "Only the agent ID field is required; all other fields are optional and will "
                "inherit from the global defaults if not specified. Use this to customize "
                "specific settings like network ports or SSL certificates per agent."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    container: Annotated[
        Optional[OverridableContainerConfig],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Container runtime configuration overrides for an individual agent. "
                "Optional field that allows customizing container settings like kernel UID/GID, "
                "port ranges, or scratch directory paths for specific agents."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    resource: Annotated[
        Optional[ResourceAllocationConfig],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Resource allocation overrides for an individual agent. "
                "Optional field that allows assigning specific CPU, memory, and device allocations "
                "to individual agents when using MANUAL resource allocation mode."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

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
    agents: Annotated[
        list[AgentOverrideConfig],
        Field(default_factory=list),
        BackendAIConfigMeta(
            description=(
                "Configuration overrides for running multiple agents from a single configuration file. "
                "Use this field only when defining 2 or more agents; defining only one agent here is "
                "redundant. When this field is populated, the global 'agent', 'container', and "
                "'resource' fields serve as default values that each agent entry can override. "
                "Each agent entry must have a unique agent ID."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

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
