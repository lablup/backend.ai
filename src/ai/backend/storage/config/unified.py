from __future__ import annotations

import enum
import os
from pathlib import Path, PurePath
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    FilePath,
    model_validator,
)

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.configs import (
    EtcdConfig,
    OTELConfig,
    PyroscopeConfig,
    ServiceDiscoveryConfig,
)
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.exception import GenericNotImplementedError, InvalidConfigError
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
from ai.backend.common.typed_validators import (
    AutoDirectoryPath,
    GroupID,
    HostPortPair,
    TimeDuration,
    UserID,
)
from ai.backend.logging.config import LoggingConfig
from ai.backend.storage.types import VolumeInfo

_max_cpu_count = os.cpu_count()
try:
    _file_perm = (Path(__file__).parent.parent / "server.py").stat()
    _default_uid = _file_perm.st_uid
    _default_gid = _file_perm.st_gid
except OSError:
    _default_uid = os.getuid()
    _default_gid = os.getgid()


class EventLoopType(enum.StrEnum):
    ASYNCIO = "asyncio"
    UVLOOP = "uvloop"


class VolumeInfoConfig(BaseConfigSchema):
    backend: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The storage backend type for this volume. Common backends include 'vfs' for local "
                "filesystem, 'purestorage' for Pure Storage arrays, and 'cephfs' for Ceph distributed "
                "filesystem. The backend determines how files are stored, accessed, and managed."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="vfs", prod="purestorage"),
        ),
    ]
    path: Annotated[
        Path,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The root filesystem path where this volume's data is stored. Must be an existing "
                "directory with appropriate read/write permissions for the storage-proxy process. "
                "For network storage backends, this is the local mount point."
            ),
            added_version="22.06.0",
            example=ConfigExample(
                local="/var/lib/backend.ai/volumes", prod="/mnt/storage/backend.ai"
            ),
        ),
    ]
    fsprefix: Annotated[
        PurePath | None,
        Field(default=PurePath()),
        BackendAIConfigMeta(
            description=(
                "An optional subdirectory prefix within the volume path. All storage operations "
                "are relative to this prefix. Use '.' for the volume root, or specify a subdirectory "
                "to organize data within the volume."
            ),
            added_version="22.06.0",
            example=ConfigExample(local=".", prod="data"),
        ),
    ]
    options: Annotated[
        dict[str, Any] | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Backend-specific configuration options as key-value pairs. Each storage backend "
                "may support different options for tuning performance, enabling features, or "
                "connecting to external services. Refer to the backend documentation for details."
            ),
            added_version="22.06.0",
        ),
    ]

    def to_dataclass(self) -> VolumeInfo:
        return VolumeInfo(
            backend=self.backend,
            path=self.path,
            fsprefix=self.fsprefix,
            options=self.options,
        )


class ClientAPIConfig(BaseConfigSchema):
    service_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="127.0.0.1", port=6021),
            validation_alias=AliasChoices("service-addr", "service_addr"),
            serialization_alias="service-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "The network address and port where the client-facing API server listens. "
                "Clients connect to this address for file operations like upload, download, "
                "and directory listing. Use '0.0.0.0' to listen on all interfaces in production."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="127.0.0.1:6021", prod="0.0.0.0:6021"),
        ),
    ]
    ssl_enabled: Annotated[
        bool,
        Field(
            validation_alias=AliasChoices("ssl-enabled", "ssl_enabled"),
            serialization_alias="ssl-enabled",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable SSL/TLS encryption for client API connections. When enabled, clients must "
                "connect using HTTPS. Requires ssl_cert and ssl_privkey to be configured. "
                "Strongly recommended for production to protect data in transit."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    ssl_cert: Annotated[
        FilePath | None,
        Field(
            default=None,
            validation_alias=AliasChoices("ssl-cert", "ssl_cert"),
            serialization_alias="ssl-cert",
        ),
        BackendAIConfigMeta(
            description=(
                "The file path to the SSL/TLS certificate in PEM format for the client API. "
                "Required when ssl_enabled is true. Use certificates from a trusted CA "
                "for production deployments."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="", prod="/etc/ssl/certs/storage-proxy.crt"),
        ),
    ]
    ssl_privkey: Annotated[
        FilePath | None,
        Field(
            default=None,
            validation_alias=AliasChoices("ssl-privkey", "ssl_privkey"),
            serialization_alias="ssl-privkey",
        ),
        BackendAIConfigMeta(
            description=(
                "The file path to the SSL/TLS private key in PEM format for the client API. "
                "Required when ssl_enabled is true. Keep this file secure with restricted "
                "permissions (e.g., 0600)."
            ),
            added_version="22.06.0",
            secret=True,
            example=ConfigExample(local="", prod="/etc/ssl/private/storage-proxy.key"),
        ),
    ]


class ManagerAPIConfig(BaseConfigSchema):
    service_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="127.0.0.1", port=6022),
            validation_alias=AliasChoices("service-addr", "service_addr"),
            serialization_alias="service-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "The network address and port where the manager-facing API server listens. "
                "Backend.AI Manager connects to this address for storage control operations "
                "like volume management and quota enforcement."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="127.0.0.1:6022", prod="0.0.0.0:6022"),
        ),
    ]
    announce_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="127.0.0.1", port=6022),
            validation_alias=AliasChoices("announce-addr", "announce_addr"),
            serialization_alias="announce-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "The address announced to the service discovery system for managers to locate "
                "this storage-proxy. In containerized or NAT environments, this should be the "
                "externally routable address, not the bind address."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="127.0.0.1:6022", prod="storage.example.com:6022"),
        ),
    ]
    announce_internal_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="host.docker.internal", port=6023),
            validation_alias=AliasChoices("announce-internal-addr", "announce_internal_addr"),
            serialization_alias="announce-internal-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "The internal address announced for container-to-host communication. "
                "Used when compute kernels need to access storage-proxy from within containers. "
                "'host.docker.internal' is the Docker DNS name for the host machine."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="host.docker.internal:6023", prod="storage-internal:6023"),
        ),
    ]
    internal_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="127.0.0.1", port=16023),
            validation_alias=AliasChoices("internal-addr", "internal_addr"),
            serialization_alias="internal-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "The address where the internal API server listens for requests from compute "
                "containers. This endpoint handles internal file operations from running sessions. "
                "Typically bound to localhost or an internal network interface."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="127.0.0.1:16023", prod="0.0.0.0:16023"),
        ),
    ]
    ssl_enabled: Annotated[
        bool,
        Field(
            validation_alias=AliasChoices("ssl-enabled", "ssl_enabled"),
            serialization_alias="ssl-enabled",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable SSL/TLS encryption for manager API connections. When enabled, managers "
                "must connect using HTTPS. Requires ssl_cert and ssl_privkey to be configured. "
                "Recommended for production deployments."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    ssl_cert: Annotated[
        FilePath | None,
        Field(
            default=None,
            validation_alias=AliasChoices("ssl-cert", "ssl_cert"),
            serialization_alias="ssl-cert",
        ),
        BackendAIConfigMeta(
            description=(
                "The file path to the SSL/TLS certificate in PEM format for the manager API. "
                "Required when ssl_enabled is true. Use certificates from a trusted CA "
                "for production deployments."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="", prod="/etc/ssl/certs/storage-proxy.crt"),
        ),
    ]
    ssl_privkey: Annotated[
        FilePath | None,
        Field(
            default=None,
            validation_alias=AliasChoices("ssl-privkey", "ssl_privkey"),
            serialization_alias="ssl-privkey",
        ),
        BackendAIConfigMeta(
            description=(
                "The file path to the SSL/TLS private key in PEM format for the manager API. "
                "Required when ssl_enabled is true. Keep this file secure with restricted "
                "permissions (e.g., 0600)."
            ),
            added_version="22.06.0",
            secret=True,
            example=ConfigExample(local="", prod="/etc/ssl/private/storage-proxy.key"),
        ),
    ]
    secret: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The shared secret key for authenticating manager requests to the storage-proxy. "
                "Must match the storage-proxy secret configured in the Backend.AI Manager. "
                "Keep this value secure and do not expose in logs."
            ),
            added_version="22.03.0",
            secret=True,
            example=ConfigExample(local="MANAGER_API_SECRET", prod="MANAGER_API_SECRET"),
        ),
    ]


class APIConfig(BaseConfigSchema):
    client: Annotated[
        ClientAPIConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Configuration for the client-facing API endpoints. This section defines how "
                "the storage-proxy accepts connections from end users and client applications "
                "for file operations such as upload, download, and directory listing."
            ),
            added_version="22.06.0",
            composite=CompositeType.FIELD,
        ),
    ]
    manager: Annotated[
        ManagerAPIConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Configuration for the manager-facing API endpoints. This section defines how "
                "the storage-proxy accepts connections from Backend.AI Manager for control "
                "operations such as volume management and quota enforcement."
            ),
            added_version="22.06.0",
            composite=CompositeType.FIELD,
        ),
    ]


class DebugConfig(BaseConfigSchema):
    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Master switch for debug mode. When enabled, activates various debugging features "
                "including detailed logging and diagnostic tools. Should be disabled in production "
                "for security and performance reasons."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    asyncio: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable asyncio debug mode, which helps detect problems like coroutines that "
                "are never awaited, slow callbacks, and other async programming issues. "
                "Adds significant overhead, use only during development."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="true", prod="false"),
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
                "Enable enhanced task information in aiomonitor. Provides more detailed "
                "information about running asyncio tasks including full stack traces and "
                "task creation context. Useful for debugging complex async workflows."
            ),
            added_version="23.09.0",
            example=ConfigExample(local="true", prod="false"),
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
                "Enable logging of all internal events. This is very verbose and generates "
                "substantial log output, but is useful for debugging event-related issues "
                "and understanding the flow of operations through the system."
            ),
            added_version="24.09.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]


class VolumeStatsConfig(BaseConfigSchema):
    """Configuration for volume performance metrics observation and caching."""

    observe_interval: Annotated[
        float,
        Field(
            default=10.0,
            ge=1.0,
            validation_alias=AliasChoices("observe-interval", "observe_interval"),
            serialization_alias="observe-interval",
        ),
        BackendAIConfigMeta(
            description=(
                "Interval in seconds between volume stats observations. The background observer "
                "collects performance metrics from all volumes at this interval and caches them "
                "in Redis for quick API responses."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="10.0", prod="10.0"),
        ),
    ]
    observe_timeout: Annotated[
        float,
        Field(
            default=5.0,
            ge=1.0,
            validation_alias=AliasChoices("observe-timeout", "observe_timeout"),
            serialization_alias="observe-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for each volume's performance metric API call. If a volume's "
                "external API does not respond within this time, the observation is marked as "
                "failed and the observer moves on to the next volume."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="5.0", prod="5.0"),
        ),
    ]
    cache_ttl: Annotated[
        float,
        Field(
            default=30.0,
            ge=1.0,
            validation_alias=AliasChoices("cache-ttl", "cache_ttl"),
            serialization_alias="cache-ttl",
        ),
        BackendAIConfigMeta(
            description=(
                "Time-to-live in seconds for cached volume stats in Redis. Cached metrics "
                "expire after this duration, ensuring stale data is not served. Should be "
                "longer than the observe interval to provide cache coverage between observations."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="30.0", prod="30.0"),
        ),
    ]


class StorageProxyConfig(BaseConfigSchema):
    ipc_base_path: Annotated[
        AutoDirectoryPath,
        Field(
            default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
            validation_alias=AliasChoices("ipc-base-path", "ipc_base_path"),
            serialization_alias="ipc-base-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Base directory path for inter-process communication files such as Unix domain "
                "sockets. This directory is automatically created if it doesn't exist. "
                "Used for low-latency communication between storage-proxy processes."
            ),
            added_version="22.03.4",
            example=ConfigExample(local="/tmp/backend.ai/ipc", prod="/var/run/backend.ai/ipc"),
        ),
    ]
    node_id: Annotated[
        str,
        Field(
            validation_alias=AliasChoices("node-id", "node_id"),
            serialization_alias="node-id",
        ),
        BackendAIConfigMeta(
            description=(
                "Unique identifier for this storage-proxy node within the cluster. Used for "
                "service discovery, log correlation, and coordination among multiple "
                "storage-proxy instances. Should be unique across all storage-proxy nodes."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="storage-proxy-dev", prod="storage-proxy-1"),
        ),
    ]
    num_proc: Annotated[
        int,
        Field(
            default=_max_cpu_count or 1,
            ge=1,
            le=_max_cpu_count or 1,
            validation_alias=AliasChoices("num-proc", "num_proc"),
            serialization_alias="num-proc",
        ),
        BackendAIConfigMeta(
            description=(
                "Number of worker processes to spawn for handling concurrent requests. "
                "Defaults to the number of CPU cores available. Increase for I/O-bound "
                "workloads or decrease to limit resource usage."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="1", prod="4"),
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
                "Path to the file where the process ID will be written. Used by process "
                "managers and init systems to track the running process. Set to /dev/null "
                "to disable this feature."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="/dev/null", prod="/var/run/storage-proxy.pid"),
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
                "Event loop implementation to use for async I/O operations. 'asyncio' is the "
                "standard library implementation with good compatibility. 'uvloop' is a faster "
                "alternative built on libuv but may have compatibility issues with some extensions."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="asyncio", prod="asyncio"),
        ),
    ]
    scandir_limit: Annotated[
        int,
        Field(
            default=1000,
            ge=0,
            validation_alias=AliasChoices("scandir-limit", "scandir_limit"),
            serialization_alias="scandir-limit",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of entries to return in directory listing operations. "
                "Prevents excessive memory usage and response times when scanning large "
                "directories. Set to 0 for unlimited (not recommended)."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="1000", prod="5000"),
        ),
    ]
    max_upload_size: Annotated[
        str,
        Field(
            default="100g",
            validation_alias=AliasChoices("max-upload-size", "max_upload_size"),
            serialization_alias="max-upload-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum size allowed for individual file uploads. Prevents storage exhaustion "
                "from excessively large uploads. Supports size suffixes: k (KB), m (MB), g (GB), "
                "t (TB). Example: '100g' for 100 gigabytes."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="10g", prod="100g"),
        ),
    ]
    secret: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Secret key for generating and validating JWT tokens used to authenticate "
                "client requests. Must be kept secure and shared only with authorized services. "
                "Use a long, random string for production deployments."
            ),
            added_version="22.03.0",
            secret=True,
            example=ConfigExample(local="JWT_SECRET", prod="JWT_SECRET"),
        ),
    ]
    session_expire: Annotated[
        TimeDuration,
        Field(
            validation_alias=AliasChoices("session-expire", "session_expire"),
            serialization_alias="session-expire",
        ),
        BackendAIConfigMeta(
            description=(
                "Duration for which JWT session tokens remain valid. After this period, "
                "clients must re-authenticate. Shorter durations improve security but "
                "require more frequent re-authentication. Supports duration suffixes: s, m, h, d."
            ),
            added_version="22.06.0",
            example=ConfigExample(local="24h", prod="1h"),
        ),
    ]
    user: Annotated[
        UserID | None,
        Field(default=UserID(_default_uid)),
        BackendAIConfigMeta(
            description=(
                "User ID (UID) under which the storage-proxy process runs. Controls file "
                "ownership and access permissions. Defaults to the UID of the current "
                "file's owner. Set to a dedicated service user in production."
            ),
            added_version="22.03.0",
            example=ConfigExample(local="1000", prod="nobody"),
        ),
    ]
    group: Annotated[
        GroupID | None,
        Field(default=GroupID(_default_gid)),
        BackendAIConfigMeta(
            description=(
                "Group ID (GID) under which the storage-proxy process runs. Controls file "
                "ownership and access permissions. Defaults to the GID of the current "
                "file's owner. Set to a dedicated service group in production."
            ),
            added_version="22.03.0",
            example=ConfigExample(local="1000", prod="nogroup"),
        ),
    ]
    aiomonitor_termui_port: Annotated[
        int,
        Field(
            default=38300,
            ge=1,
            le=65535,
            validation_alias=AliasChoices(
                "aiomonitor-termui-port", "aiomonitor_termui_port", "aiomonitor-port"
            ),
            serialization_alias="aiomonitor-termui-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port number for the aiomonitor terminal UI, which provides a console-based "
                "interface for inspecting running asyncio tasks and debugging issues. "
                "Connect via telnet or netcat to this port for interactive debugging."
            ),
            added_version="23.09.0",
            example=ConfigExample(local="38300", prod="38300"),
        ),
    ]
    aiomonitor_webui_port: Annotated[
        int,
        Field(
            default=39300,
            ge=1,
            le=65535,
            validation_alias=AliasChoices("aiomonitor-webui-port", "aiomonitor_webui_port"),
            serialization_alias="aiomonitor-webui-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port number for the aiomonitor web UI, which provides a browser-based "
                "interface for monitoring asyncio tasks and system state. Access via "
                "HTTP to view real-time task information and metrics."
            ),
            added_version="23.09.0",
            example=ConfigExample(local="39300", prod="39300"),
        ),
    ]
    watcher_insock_path_prefix: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices(
                "watcher-insock-path-prefix", "watcher_insock_path_prefix"
            ),
            serialization_alias="watcher-insock-path-prefix",
        ),
        BackendAIConfigMeta(
            description=(
                "Path prefix for watcher input Unix domain sockets. Used when the watcher "
                "feature is enabled to receive commands from the watcher process. "
                "Set to None to disable or use default paths."
            ),
            added_version="23.09.0",
            example=ConfigExample(local="", prod="/var/run/backend.ai/watcher-in"),
        ),
    ]
    watcher_outsock_path_prefix: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices(
                "watcher-outsock-path-prefix", "watcher_outsock_path_prefix"
            ),
            serialization_alias="watcher-outsock-path-prefix",
        ),
        BackendAIConfigMeta(
            description=(
                "Path prefix for watcher output Unix domain sockets. Used when the watcher "
                "feature is enabled to send status updates to the watcher process. "
                "Set to None to disable or use default paths."
            ),
            added_version="23.09.0",
            example=ConfigExample(local="", prod="/var/run/backend.ai/watcher-out"),
        ),
    ]
    use_watcher: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("use-watcher", "use_watcher"),
            serialization_alias="use-watcher",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable the watcher process integration for additional monitoring and "
                "supervision capabilities. When enabled, the storage-proxy communicates "
                "with an external watcher process for health monitoring and management."
            ),
            added_version="23.09.0",
            example=ConfigExample(local="false", prod="true"),
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
                "Enable the experimental Redis-based event dispatcher for inter-process "
                "event communication. May provide better scalability and performance for "
                "event handling in multi-node deployments. Requires Redis configuration."
            ),
            added_version="24.09.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    auto_quota_scope_creation: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices(
                "allow-auto-quota-scope-creation", "auto_quota_scope_creation"
            ),
            serialization_alias="allow-auto-quota-scope-creation",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow automatic creation of quota scopes when creating virtual folders "
                "in non-existent quota scopes. If true, quota scopes are created on demand. "
                "If false, VFolder creation fails when the quota scope doesn't exist."
            ),
            added_version="25.19.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    volume_stats: Annotated[
        VolumeStatsConfig,
        Field(
            default_factory=lambda: VolumeStatsConfig(),
            validation_alias=AliasChoices("volume-stats", "volume_stats"),
            serialization_alias="volume-stats",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for volume performance metrics observation and caching. "
                "Controls the background observer that periodically collects metrics from "
                "storage volumes and caches them in Redis."
            ),
            added_version="25.12.0",
        ),
    ]


class PresignedUploadConfig(BaseConfigSchema):
    min_size: Annotated[
        int | None,
        Field(
            default=None,
            validation_alias=AliasChoices("min-size", "min_size"),
            serialization_alias="min-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Minimum file size in bytes that triggers multipart upload mode. Files smaller "
                "than this are uploaded in a single request. Set to None to use the default "
                "behavior. Typical value is 5MB (5242880 bytes) for S3-compatible storage."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="5242880", prod="5242880"),
        ),
    ]
    max_size: Annotated[
        int | None,
        Field(
            default=None,
            validation_alias=AliasChoices("max-size", "max_size"),
            serialization_alias="max-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum file size in bytes allowed for presigned uploads. Files larger than "
                "this are rejected. Set to None to allow unlimited size (limited only by "
                "storage backend constraints). Use to prevent storage quota abuse."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="5368709120", prod="10737418240"),
        ),
    ]
    expiration: Annotated[
        int,
        Field(default=60 * 5),  # 5 minutes
        BackendAIConfigMeta(
            description=(
                "Expiration time in seconds for presigned upload URLs. After this duration, "
                "the URL becomes invalid and clients must request a new one. Balance security "
                "(shorter) vs. usability for large uploads (longer)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="300", prod="3600"),
        ),
    ]


class PresignedDownloadConfig(BaseConfigSchema):
    expiration: Annotated[
        int,
        Field(default=60 * 5),  # 5 minutes
        BackendAIConfigMeta(
            description=(
                "Expiration time in seconds for presigned download URLs. After this duration, "
                "the URL becomes invalid and clients must request a new one. Balance security "
                "(shorter) vs. usability for slow connections (longer)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="300", prod="3600"),
        ),
    ]


class VFSStorageConfig(BaseConfigSchema):
    base_path: Annotated[
        Path,
        Field(
            validation_alias=AliasChoices("base-path", "base_path"),
            serialization_alias="base-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Base filesystem path for VFS (Virtual File System) storage. This directory "
                "serves as the root for all VFS operations. Must be an existing directory "
                "with appropriate read/write permissions for the storage-proxy process."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="/data/ai-models", prod="/mnt/storage/vfs"),
        ),
    ]
    subpath: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Optional subdirectory path appended to base_path. Used to further organize "
                "storage within the base directory, such as separating models, datasets, "
                "or user data. Set to None to use the base_path directly."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="user-data"),
        ),
    ]
    temporary: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Mark this storage as temporary. When enabled, all files in the storage are "
                "cleared when the server starts. Useful for cache storage or temporary "
                "workspaces that should be cleaned up on restart."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    upload_chunk_size: Annotated[
        int,
        Field(
            default=65536,  # 64KB
            ge=1024,  # Minimum 1KB
            validation_alias=AliasChoices("upload-chunk-size", "upload_chunk_size"),
            serialization_alias="upload-chunk-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Chunk size in bytes for streaming file upload operations. Larger chunks "
                "reduce overhead but increase memory usage. Smaller chunks are better for "
                "low-bandwidth connections. Default is 64KB (65536 bytes)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="65536", prod="1048576"),
        ),
    ]
    download_chunk_size: Annotated[
        int,
        Field(
            default=65536,  # 64KB
            ge=1024,  # Minimum 1KB
            validation_alias=AliasChoices("download-chunk-size", "download_chunk_size"),
            serialization_alias="download-chunk-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Chunk size in bytes for streaming file download operations. Larger chunks "
                "improve throughput for large files. Smaller chunks reduce memory usage and "
                "provide better progress reporting. Default is 64KB (65536 bytes)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="65536", prod="1048576"),
        ),
    ]
    max_file_size: Annotated[
        int | None,
        Field(
            default=None,
            validation_alias=AliasChoices("max-file-size", "max_file_size"),
            serialization_alias="max-file-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum file size in bytes allowed for uploads to this storage. Files "
                "exceeding this size are rejected. Set to None to allow unlimited file "
                "sizes (limited only by available storage space)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1073741824", prod="10737418240"),
        ),
    ]


# TODO: Remove this after migrating this to database
class ObjectStorageConfig(BaseConfigSchema):
    endpoint: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Endpoint URL for the S3-compatible object storage service. Must include "
                "the protocol (http or https) and port if non-standard. Examples: MinIO, "
                "AWS S3, Google Cloud Storage with S3 compatibility enabled."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="http://localhost:9000", prod="https://s3.amazonaws.com"),
        ),
    ]
    access_key: Annotated[
        str,
        Field(
            validation_alias=AliasChoices("access-key", "access_key"),
            serialization_alias="access-key",
        ),
        BackendAIConfigMeta(
            description=(
                "Access key ID for authenticating with the object storage service. "
                "For AWS S3, this is the IAM user's access key. For MinIO, this is "
                "the configured access key. Keep secure and rotate periodically."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(
                local="OBJECT_STORAGE_ACCESS_KEY", prod="OBJECT_STORAGE_ACCESS_KEY"
            ),
        ),
    ]
    secret_key: Annotated[
        str,
        Field(
            validation_alias=AliasChoices("secret-key", "secret_key"),
            serialization_alias="secret-key",
        ),
        BackendAIConfigMeta(
            description=(
                "Secret access key for authenticating with the object storage service. "
                "Must be kept secure and never exposed in logs or error messages. "
                "Pair this with the access_key for authentication."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(
                local="OBJECT_STORAGE_SECRET_KEY", prod="OBJECT_STORAGE_SECRET_KEY"
            ),
        ),
    ]
    buckets: Annotated[
        list[str],
        Field(default_factory=list),
        BackendAIConfigMeta(
            description=(
                "List of bucket names managed by this storage configuration. Each bucket "
                "represents a logical container for storing objects. Buckets must already "
                "exist in the object storage service unless auto-creation is enabled."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="dev-bucket", prod="prod-data-bucket"),
        ),
    ]
    region: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Region identifier where the object storage service is located. For AWS S3, "
                "use region codes like 'us-east-1' or 'ap-northeast-2'. For local MinIO, "
                "use any valid region string (e.g., 'us-east-1')."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="us-east-1", prod="ap-northeast-2"),
        ),
    ]
    presigned_upload: Annotated[
        PresignedUploadConfig,
        Field(
            default_factory=PresignedUploadConfig,
            validation_alias=AliasChoices("presigned-upload", "presigned_upload"),
            serialization_alias="presigned-upload",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for generating presigned upload URLs. Presigned URLs allow "
                "clients to upload directly to object storage without proxying through "
                "the storage-proxy, improving performance for large files."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    presigned_download: Annotated[
        PresignedDownloadConfig,
        Field(
            default_factory=PresignedDownloadConfig,
            validation_alias=AliasChoices("presigned-download", "presigned_download"),
            serialization_alias="presigned-download",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for generating presigned download URLs. Presigned URLs allow "
                "clients to download directly from object storage without proxying through "
                "the storage-proxy, improving performance for large files."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    upload_chunk_size: Annotated[
        int,
        Field(
            default=5 * 1024 * 1024,
            ge=5 * 1024 * 1024,
            validation_alias=AliasChoices("upload-chunk-size", "upload_chunk_size"),
            serialization_alias="upload-chunk-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Chunk size in bytes for multipart upload operations to object storage. "
                "Must be at least 5MiB (5242880 bytes) due to S3 API requirements. "
                "Larger chunks reduce API calls but increase memory usage."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="5242880", prod="10485760"),
        ),
    ]
    download_chunk_size: Annotated[
        int,
        Field(
            default=8192,
            validation_alias=AliasChoices("download-chunk-size", "download_chunk_size"),
            serialization_alias="download-chunk-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Chunk size in bytes for streaming downloads from object storage. "
                "Smaller chunks provide better responsiveness but increase overhead. "
                "Default is 8KB which works well for most use cases."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="8192", prod="65536"),
        ),
    ]
    reservoir_download_chunk_size: Annotated[
        int,
        Field(
            default=8192,
            validation_alias=AliasChoices(
                "reservoir-download-chunk-size", "reservoir_download_chunk_size"
            ),
            serialization_alias="reservoir-download-chunk-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Chunk size in bytes for downloading files from remote reservoir storage. "
                "Reservoir is Backend.AI's artifact registry feature. Adjust based on "
                "network latency and file sizes typically downloaded."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="8192", prod="65536"),
        ),
    ]


class LegacyObjectStorageConfig(ObjectStorageConfig):
    name: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Unique name identifier for this object storage configuration. Used to "
                "reference this storage instance from other configurations and API calls. "
                "Should be descriptive and follow naming conventions (lowercase, hyphens)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="minio-dev", prod="s3-production"),
        ),
    ]


class HuggingfaceConfig(BaseConfigSchema):
    endpoint: Annotated[
        str,
        Field(default="https://huggingface.co"),
        BackendAIConfigMeta(
            description=(
                "API endpoint URL for the HuggingFace service. Defaults to the official "
                "HuggingFace Hub (https://huggingface.co). Change this to connect to "
                "self-hosted HuggingFace instances or enterprise deployments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="https://huggingface.co", prod="https://huggingface.co"),
        ),
    ]
    token: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "HuggingFace API token for authenticating requests. Required to access "
                "gated models and private repositories. Generate tokens at "
                "https://huggingface.co/settings/tokens. Keep this value secure."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(local="", prod="HUGGINGFACE_TOKEN"),
        ),
    ]
    download_chunk_size: Annotated[
        int,
        Field(
            default=8192,
            validation_alias=AliasChoices("download-chunk-size", "download_chunk_size"),
            serialization_alias="download-chunk-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Chunk size in bytes for streaming downloads from HuggingFace. "
                "Larger chunks improve throughput but increase memory usage. "
                "Default is 8KB which provides good balance for most use cases."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="8192", prod="65536"),
        ),
    ]


# TODO: Remove legacy config classes
class LegacyHuggingfaceConfig(HuggingfaceConfig):
    registry_type: Annotated[
        Literal["huggingface"],
        Field(alias="type"),
        BackendAIConfigMeta(
            description=(
                "Type discriminator for registry configuration. Must be 'huggingface' for "
                "this configuration type. Used internally to identify and deserialize "
                "the correct registry configuration class."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="huggingface", prod="huggingface"),
        ),
    ]


class ReservoirConfig(BaseConfigSchema):
    endpoint: Annotated[
        str,
        Field(default="https://huggingface.co"),
        BackendAIConfigMeta(
            description=(
                "API endpoint URL for the Reservoir registry service. Reservoir is Backend.AI's "
                "artifact registry feature for managing ML models and datasets. Can point to "
                "HuggingFace or a self-hosted Reservoir instance."
            ),
            added_version="25.12.0",
            example=ConfigExample(
                local="https://huggingface.co", prod="https://reservoir.example.com"
            ),
        ),
    ]
    object_storage_access_key: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("object-storage-access-key", "object_storage_access_key"),
            serialization_alias="object-storage-access-key",
        ),
        BackendAIConfigMeta(
            description=(
                "Access key for authenticating with the Reservoir registry's underlying object "
                "storage (S3-compatible). Required when the Reservoir uses object storage backend. "
                "Not needed for HuggingFace-backed registries."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(local="", prod="OBJECT_STORAGE_ACCESS_KEY"),
        ),
    ]
    object_storage_secret_key: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("object-storage-secret-key", "object_storage_secret_key"),
            serialization_alias="object-storage-secret-key",
        ),
        BackendAIConfigMeta(
            description=(
                "Secret key for authenticating with the Reservoir registry's underlying object "
                "storage (S3-compatible). Must be kept secure. Pair with object_storage_access_key "
                "for authentication."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(local="", prod="OBJECT_STORAGE_SECRET_KEY"),
        ),
    ]
    object_storage_region: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("object-storage-region", "object_storage_region"),
            serialization_alias="object-storage-region",
        ),
        BackendAIConfigMeta(
            description=(
                "Region identifier for the Reservoir registry's object storage. Required when "
                "using AWS S3 or region-aware S3-compatible storage. Use standard region codes "
                "like 'us-east-1' or 'ap-northeast-2'."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="us-east-1", prod="ap-northeast-2"),
        ),
    ]

    manager_endpoint: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("manager-endpoint", "manager_endpoint"),
            serialization_alias="manager-endpoint",
        ),
        BackendAIConfigMeta(
            description=(
                "API endpoint URL for the Backend.AI Manager when Reservoir uses VFS storage. "
                "Required for VFS-backed registries to handle file operations through Manager. "
                "Not needed when using object storage backend."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="http://localhost:8091", prod="https://api.example.com"),
        ),
    ]
    manager_access_key: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("manager-access-key", "manager_access_key"),
            serialization_alias="manager-access-key",
        ),
        BackendAIConfigMeta(
            description=(
                "Access key for authenticating with Backend.AI Manager API when using VFS-backed "
                "Reservoir. This is a Backend.AI user access key, not an object storage key. "
                "Required when manager_endpoint is specified."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(local="", prod="MANAGER_ACCESS_KEY"),
        ),
    ]
    manager_secret_key: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("manager-secret-key", "manager_secret_key"),
            serialization_alias="manager-secret-key",
        ),
        BackendAIConfigMeta(
            description=(
                "Secret key for authenticating with Backend.AI Manager API when using VFS-backed "
                "Reservoir. Pair with manager_access_key for authentication. "
                "Keep this value secure."
            ),
            added_version="25.12.0",
            secret=True,
            example=ConfigExample(local="", prod="MANAGER_SECRET_KEY"),
        ),
    ]
    manager_api_version: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("manager-api-version", "manager_api_version"),
            serialization_alias="manager-api-version",
        ),
        BackendAIConfigMeta(
            description=(
                "API version to use when communicating with Backend.AI Manager for VFS-backed "
                "Reservoir. Ensures compatibility between storage-proxy and Manager versions. "
                "Example: 'v8' for API version 8."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="v8", prod="v8"),
        ),
    ]
    storage_name: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("storage-name", "storage_name"),
            serialization_alias="storage-name",
        ),
        BackendAIConfigMeta(
            description=(
                "Name of the storage configuration to use with the Reservoir registry. "
                "References a storage defined elsewhere in the configuration. Required when "
                "using VFS-backed Reservoir to identify the target storage."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="vfs-local", prod="vfs-production"),
        ),
    ]


class LegacyReservoirConfig(ReservoirConfig):
    registry_type: Annotated[
        Literal["reservoir"],
        Field(alias="type"),
        BackendAIConfigMeta(
            description=(
                "Type discriminator for registry configuration. Must be 'reservoir' for "
                "this configuration type. Used internally to identify and deserialize "
                "the correct registry configuration class."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="reservoir", prod="reservoir"),
        ),
    ]


class ReservoirClientConfig(BaseConfigSchema):
    timeout_total: Annotated[
        float | None,
        Field(
            default=300.0,
            validation_alias=AliasChoices("timeout-total", "timeout_total"),
            serialization_alias="timeout-total",
        ),
        BackendAIConfigMeta(
            description=(
                "Total timeout in seconds for the entire HTTP request lifecycle, including "
                "connection, sending, and receiving data. Set to None for no timeout. "
                "Default 300 seconds (5 minutes) accommodates large file transfers."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="300", prod="600"),
        ),
    ]
    timeout_connect: Annotated[
        float | None,
        Field(
            default=None,
            validation_alias=AliasChoices("timeout-connect", "timeout_connect"),
            serialization_alias="timeout-connect",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for acquiring a connection from the connection pool. "
                "Limits wait time when all pool connections are in use. Set to None for "
                "no timeout (wait indefinitely for an available connection)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="60"),
        ),
    ]
    timeout_sock_connect: Annotated[
        float | None,
        Field(
            default=30.0,
            validation_alias=AliasChoices("timeout-sock-connect", "timeout_sock_connect"),
            serialization_alias="timeout-sock-connect",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for establishing a TCP connection to the remote server. "
                "Controls how long to wait for the initial connection handshake. "
                "Default 30 seconds is suitable for most network conditions."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="30", prod="60"),
        ),
    ]
    timeout_sock_read: Annotated[
        float | None,
        Field(
            default=None,
            validation_alias=AliasChoices("timeout-sock-read", "timeout_sock_read"),
            serialization_alias="timeout-sock-read",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for reading a chunk of data from the socket. "
                "Controls maximum wait time between data packets. Set to None for no "
                "timeout, useful for slow transfers over unreliable networks."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="300"),
        ),
    ]


class ArtifactRegistryStorageConfig(BaseConfigSchema):
    storage_type: Annotated[
        ArtifactStorageType,
        Field(alias="type"),
        BackendAIConfigMeta(
            description=(
                "Type of storage backend for artifacts. Determines how files are stored and "
                "accessed. Options: 'object_storage' for S3-compatible storage, 'vfs_storage' "
                "for local filesystem, 'git_lfs' for Git LFS (not yet supported)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="vfs_storage", prod="object_storage"),
        ),
    ]
    object_storage: Annotated[
        ObjectStorageConfig | None,
        Field(
            default=None,
            validation_alias=AliasChoices("object-storage", "object_storage"),
            serialization_alias="object-storage",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for S3-compatible object storage backend. Required when "
                "storage_type is 'object_storage'. Provides scalable, distributed storage "
                "suitable for production deployments with large artifact collections."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    vfs_storage: Annotated[
        VFSStorageConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for VFS (Virtual File System) storage backend. Required when "
                "storage_type is 'vfs_storage'. Uses local filesystem for storage, suitable "
                "for development or single-node deployments."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

    @model_validator(mode="after")
    def _validate_storage_config(self) -> Self:
        match self.storage_type:
            case ArtifactStorageType.OBJECT_STORAGE:
                if self.object_storage is None:
                    raise InvalidConfigError(
                        "object_storage config is required when storage_type is 'object_storage'"
                    )
            case ArtifactStorageType.VFS_STORAGE:
                if self.vfs_storage is None:
                    raise InvalidConfigError("vfs config is required when storage_type is 'vfs'")
            case ArtifactStorageType.GIT_LFS:
                raise GenericNotImplementedError("git_lfs is not supported yet")

        return self


LegacyRegistrySpecificConfig = LegacyHuggingfaceConfig | LegacyReservoirConfig


class LegacyArtifactRegistryConfig(BaseConfigSchema):
    name: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Unique name identifier for this artifact registry configuration. Used to "
                "reference this registry from other configurations and API calls. Should be "
                "descriptive and indicate the registry type or purpose."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="huggingface-dev", prod="huggingface-prod"),
        ),
    ]
    config: Annotated[
        LegacyRegistrySpecificConfig,
        Field(discriminator="registry_type"),
        BackendAIConfigMeta(
            description=(
                "Registry-specific configuration. The structure depends on the registry type "
                "(huggingface or reservoir). Uses discriminator field 'type' to determine "
                "which configuration schema to apply."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]


class ArtifactRegistryConfig(BaseConfigSchema):
    registry_type: Annotated[
        ArtifactRegistryType,
        Field(alias="type"),
        BackendAIConfigMeta(
            description=(
                "Type of artifact registry service. Determines how to interact with the "
                "registry for downloading models and datasets. Options: 'huggingface' for "
                "HuggingFace Hub, 'reservoir' for Backend.AI Reservoir."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="huggingface", prod="reservoir"),
        ),
    ]
    huggingface: Annotated[
        HuggingfaceConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for HuggingFace Hub registry. Required when registry_type is "
                "'huggingface'. Connects to HuggingFace Hub for accessing public and private "
                "ML models, datasets, and spaces."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    reservoir: Annotated[
        ReservoirConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for Backend.AI Reservoir registry. Required when registry_type "
                "is 'reservoir'. Reservoir is Backend.AI's native artifact registry for "
                "managing ML models and datasets within your infrastructure."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

    @model_validator(mode="after")
    def _validate_registry_config(self) -> Self:
        match self.registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                if self.huggingface is None:
                    raise InvalidConfigError(
                        "huggingface config is required when registry_type is 'huggingface'"
                    )
            case ArtifactRegistryType.RESERVOIR:
                if self.reservoir is None:
                    raise InvalidConfigError(
                        "reservoir config is required when registry_type is 'reservoir'"
                    )

        return self


class StorageProxyUnifiedConfig(BaseConfigSchema):
    storage_proxy: Annotated[
        StorageProxyConfig,
        Field(
            validation_alias=AliasChoices("storage-proxy", "storage_proxy"),
            serialization_alias="storage-proxy",
        ),
        BackendAIConfigMeta(
            description=(
                "Core storage-proxy service configuration. Contains essential settings for "
                "the storage-proxy including node identification, worker processes, ports, "
                "and authentication secrets. This is the main configuration section."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    pyroscope: Annotated[
        PyroscopeConfig,
        Field(default_factory=PyroscopeConfig),  # type: ignore[arg-type]
        BackendAIConfigMeta(
            description=(
                "Pyroscope continuous profiling configuration. Pyroscope provides real-time "
                "CPU and memory profiling for performance analysis. Enable this to collect "
                "profiling data and send to a Pyroscope server for analysis."
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
                "Logging system configuration. Controls log levels, formats, outputs, and "
                "rotation settings. Proper logging configuration is essential for monitoring "
                "and debugging storage-proxy in production environments."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    api: Annotated[
        APIConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "API endpoints configuration for client and manager interfaces. Defines how "
                "the storage-proxy accepts requests from users (client API) and from "
                "Backend.AI Manager (manager API) including SSL and address settings."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    volume: Annotated[
        dict[str, VolumeInfoConfig],
        Field(),
        BackendAIConfigMeta(
            description=(
                "Storage volume configurations keyed by volume name. Each volume defines a "
                "storage backend and its settings. Multiple volumes can be configured to "
                "provide different storage backends (VFS, Pure Storage, CephFS, etc.)."
            ),
            added_version="25.12.0",
            composite=CompositeType.DICT,
        ),
    ]
    debug: Annotated[
        DebugConfig,
        Field(default_factory=DebugConfig),
        BackendAIConfigMeta(
            description=(
                "Debugging options configuration. Controls various debugging features like "
                "asyncio debug mode, enhanced task monitoring, and verbose event logging. "
                "Should be disabled in production for security and performance."
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
                "Service discovery configuration. Controls how the storage-proxy registers "
                "itself with and discovers other services in the Backend.AI cluster. "
                "Essential for multi-node deployments and automatic failover."
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
                "OpenTelemetry (OTEL) configuration for distributed tracing and metrics. "
                "Enables integration with observability platforms like Jaeger, Zipkin, or "
                "commercial APM solutions for request tracing across services."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    etcd: Annotated[
        EtcdConfig,
        Field(default_factory=EtcdConfig),  # type: ignore[arg-type]
        BackendAIConfigMeta(
            description=(
                "etcd configuration for distributed key-value storage. etcd is used for "
                "cluster coordination, configuration sharing, and service discovery in "
                "Backend.AI. Required for multi-node deployments."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    storages: Annotated[
        list[LegacyObjectStorageConfig],
        Field(default_factory=list),
        BackendAIConfigMeta(
            description=(
                "DEPRECATED: Use 'artifact_storages' instead. Legacy list of object storage "
                "configurations for backward compatibility. Each entry defines connection "
                "settings for an S3-compatible object storage service."
            ),
            added_version="25.12.0",
            deprecated_version="25.10.0",
            deprecation_hint="Use artifact_storages dictionary instead for new deployments.",
        ),
    ]
    registries: Annotated[
        list[LegacyArtifactRegistryConfig],
        Field(default_factory=list),
        BackendAIConfigMeta(
            description=(
                "DEPRECATED: Use 'artifact_registries' instead. Legacy list of artifact "
                "registry configurations for backward compatibility. Each entry defines "
                "connection settings for a model/dataset registry service."
            ),
            added_version="25.12.0",
            deprecated_version="25.10.0",
            deprecation_hint="Use artifact_registries dictionary instead for new deployments.",
        ),
    ]

    artifact_storages: Annotated[
        dict[str, ArtifactRegistryStorageConfig],
        Field(
            default_factory=dict,
            validation_alias=AliasChoices("artifact-storages", "artifact_storages"),
            serialization_alias="artifact-storages",
        ),
        BackendAIConfigMeta(
            description=(
                "Dictionary of artifact storage configurations keyed by storage name. "
                "Defines storage backends for artifact files (models, datasets). Each entry "
                "can be object storage (S3) or VFS depending on deployment requirements."
            ),
            added_version="25.12.0",
            composite=CompositeType.DICT,
        ),
    ]
    artifact_registries: Annotated[
        dict[str, ArtifactRegistryConfig],
        Field(
            default_factory=dict,
            validation_alias=AliasChoices("artifact-registries", "artifact_registries"),
            serialization_alias="artifact-registries",
        ),
        BackendAIConfigMeta(
            description=(
                "Dictionary of artifact registry configurations keyed by registry name. "
                "Defines external registries for discovering and downloading ML artifacts. "
                "Supports HuggingFace Hub and Backend.AI Reservoir registries."
            ),
            added_version="25.12.0",
            composite=CompositeType.DICT,
        ),
    ]
    reservoir_client: Annotated[
        ReservoirClientConfig,
        Field(
            default_factory=ReservoirClientConfig,
            validation_alias=AliasChoices("reservoir-client", "reservoir_client"),
            serialization_alias="reservoir-client",
        ),
        BackendAIConfigMeta(
            description=(
                "HTTP client configuration for Reservoir registry connections. Controls "
                "timeout settings for API calls to Reservoir services. Tune these values "
                "based on network conditions and expected transfer sizes."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # TODO: Remove me after changing config injection logic
    model_config = ConfigDict(
        extra="allow",
    )
