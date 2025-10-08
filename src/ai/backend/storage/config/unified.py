from __future__ import annotations

import enum
import os
from pathlib import Path, PurePath
from typing import Any, Literal, Optional, Self, Union

from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    FilePath,
    model_validator,
)

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.exception import GenericNotImplementedError, InvalidConfigError
from ai.backend.common.typed_validators import (
    AutoDirectoryPath,
    GroupID,
    HostPortPair,
    TimeDuration,
    UserID,
)
from ai.backend.common.types import ServiceDiscoveryType
from ai.backend.logging.config import LoggingConfig
from ai.backend.storage.types import VolumeInfo

_max_cpu_count = os.cpu_count()
try:
    _file_perm = (Path(__file__).parent.parent / "server.py").stat()
    _default_uid = _file_perm.st_uid
    _default_gid = _file_perm.st_gid
except IOError:
    _default_uid = os.getuid()
    _default_gid = os.getgid()


class EventLoopType(enum.StrEnum):
    asyncio = "asyncio"
    uvloop = "uvloop"


class VolumeInfoConfig(BaseConfigSchema):
    backend: str = Field(
        description="""
        Storage backend type to use for this volume.
        Determines how files are stored and accessed.
        """,
        examples=["vfs", "purestorage", "cephfs"],
    )
    path: Path = Field(
        description="""
        Root path for this volume.
        Must be a directory that exists and is accessible.
        """,
        examples=["/var/lib/backend.ai/volumes"],
    )
    fsprefix: Optional[PurePath] = Field(
        default=PurePath("."),
        description="""
        Filesystem prefix path for this volume.
        Used as a subdirectory within the volume path.
        """,
        examples=[".", "data"],
    )
    options: Optional[dict[str, Any]] = Field(
        default=None,
        description="""
        Backend-specific options for this volume.
        Configuration parameters specific to the chosen backend.
        """,
        examples=[{}],
    )

    def to_dataclass(self) -> VolumeInfo:
        return VolumeInfo(
            backend=self.backend,
            path=self.path,
            fsprefix=self.fsprefix,
            options=self.options,
        )


class EtcdConfig(BaseConfigSchema):
    namespace: str = Field(
        default="ETCD_NAMESPACE",
        description="""
        Namespace prefix for etcd keys used by Backend.AI.
        Allows multiple Backend.AI clusters to share the same etcd cluster.
        All Backend.AI related keys will be stored under this namespace.
        """,
        examples=["local", "backend"],
    )
    addr: HostPortPair | list[HostPortPair] = Field(
        default=HostPortPair(host="127.0.0.1", port=2379),
        description="""
        Network address of the etcd server.
        Default is the standard etcd port on localhost.
        In production, should point to one or more etcd instance endpoint(s).
        """,
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
        description="""
        Username for authenticating with etcd.
        Optional if etcd doesn't require authentication.
        Should be set along with password for secure deployments.
        """,
        examples=["backend", "manager"],
    )
    password: Optional[str] = Field(
        default=None,
        description="""
        Password for authenticating with etcd.
        Optional if etcd doesn't require authentication.
        Can be a direct password or environment variable reference.
        """,
        examples=["develove", "ETCD_PASSWORD"],
    )

    def to_dataclass(self) -> EtcdConfigData:
        return EtcdConfigData(
            namespace=self.namespace,
            addrs=self.addr if isinstance(self.addr, list) else [self.addr],
            user=self.user,
            password=self.password,
        )


class PyroscopeConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="""
        Whether to enable Pyroscope profiling.
        When enabled, performance profiling data will be sent to a Pyroscope server.
        Useful for debugging performance issues, but adds some overhead.
        """,
        examples=[True, False],
    )
    app_name: Optional[str] = Field(
        default=None,
        description="""
        Application name to use in Pyroscope.
        This name will identify this storage-proxy instance in Pyroscope UI.
        Required if Pyroscope is enabled.
        """,
        examples=["backendai-storage-proxy"],
        validation_alias=AliasChoices("app-name", "app_name"),
        serialization_alias="app-name",
    )
    server_addr: Optional[str] = Field(
        default=None,
        description="""
        Address of the Pyroscope server.
        Must include the protocol (http or https) and port if non-standard.
        Required if Pyroscope is enabled.
        """,
        examples=["http://localhost:4040"],
        validation_alias=AliasChoices("server-addr", "server_addr"),
        serialization_alias="server-addr",
    )
    sample_rate: Optional[int] = Field(
        default=None,
        description="""
        Sampling rate for Pyroscope profiling.
        Higher values collect more data but increase overhead.
        Balance based on your performance monitoring needs.
        """,
        examples=[10, 100, 1000],
        validation_alias=AliasChoices("sample-rate", "sample_rate"),
        serialization_alias="sample-rate",
    )


class ClientAPIConfig(BaseConfigSchema):
    service_addr: HostPortPair = Field(
        default=HostPortPair(host="127.0.0.1", port=6021),
        description="""
        Network address and port where the client API service will listen.
        This is the address accessible by clients for file operations.
        """,
        validation_alias=AliasChoices("service-addr", "service_addr"),
        serialization_alias="service-addr",
    )
    ssl_enabled: bool = Field(
        description="""
        Whether to enable SSL/TLS for client API connections.
        Required for secure communication with clients.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("ssl-enabled", "ssl_enabled"),
        serialization_alias="ssl-enabled",
    )
    ssl_cert: Optional[FilePath] = Field(
        default=None,
        description="""
        Path to the SSL certificate file for client API.
        Required if ssl_enabled is True.
        """,
        examples=["/etc/ssl/certs/storage-proxy.crt"],
        validation_alias=AliasChoices("ssl-cert", "ssl_cert"),
        serialization_alias="ssl-cert",
    )
    ssl_privkey: Optional[FilePath] = Field(
        default=None,
        description="""
        Path to the SSL private key file for client API.
        Required if ssl_enabled is True.
        """,
        examples=["/etc/ssl/private/storage-proxy.key"],
        validation_alias=AliasChoices("ssl-privkey", "ssl_privkey"),
        serialization_alias="ssl-privkey",
    )


class ManagerAPIConfig(BaseConfigSchema):
    service_addr: HostPortPair = Field(
        default=HostPortPair(host="127.0.0.1", port=6022),
        description="""
        Network address and port where the manager API service will listen.
        This is the address accessible by managers for control operations.
        """,
        validation_alias=AliasChoices("service-addr", "service_addr"),
        serialization_alias="service-addr",
    )
    announce_addr: HostPortPair = Field(
        default=HostPortPair(host="127.0.0.1", port=6022),
        description="""
        Address and port to announce to managers for service discovery.
        Should be accessible by other manager components.
        """,
        validation_alias=AliasChoices("announce-addr", "announce_addr"),
        serialization_alias="announce-addr",
    )
    announce_internal_addr: HostPortPair = Field(
        default=HostPortPair(host="host.docker.internal", port=6023),
        description="""
        Address and port to announce for internal manager API requests.
        Used for service discovery within container environments.
        """,
        validation_alias=AliasChoices("announce-internal-addr", "announce_internal_addr"),
        serialization_alias="announce-internal-addr",
    )
    internal_addr: HostPortPair = Field(
        default=HostPortPair(host="127.0.0.1", port=16023),
        description="""
        Internal address where manager API listens for internal requests.
        Used for internal communication between services.
        """,
        validation_alias=AliasChoices("internal-addr", "internal_addr"),
        serialization_alias="internal-addr",
    )
    ssl_enabled: bool = Field(
        description="""
        Whether to enable SSL/TLS for manager API connections.
        Required for secure communication with managers.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("ssl-enabled", "ssl_enabled"),
        serialization_alias="ssl-enabled",
    )
    ssl_cert: Optional[FilePath] = Field(
        default=None,
        description="""
        Path to the SSL certificate file for manager API.
        Required if ssl_enabled is True.
        """,
        examples=["/etc/ssl/certs/storage-proxy.crt"],
        validation_alias=AliasChoices("ssl-cert", "ssl_cert"),
        serialization_alias="ssl-cert",
    )
    ssl_privkey: Optional[FilePath] = Field(
        default=None,
        description="""
        Path to the SSL private key file for manager API.
        Required if ssl_enabled is True.
        """,
        examples=["/etc/ssl/private/storage-proxy.key"],
        validation_alias=AliasChoices("ssl-privkey", "ssl_privkey"),
        serialization_alias="ssl-privkey",
    )
    secret: str = Field(
        description="""
        Secret key for authenticating managers with the storage-proxy.
        Must be shared between manager and storage-proxy instances.
        """,
        examples=["manager-secret-key"],
    )


class APIConfig(BaseConfigSchema):
    client: ClientAPIConfig = Field(
        description="""
        Configuration for the client-facing API.
        Handles file operations requested by users.
        """,
    )
    manager: ManagerAPIConfig = Field(
        description="""
        Configuration for the manager-facing API.
        Handles control operations from manager services.
        """,
    )


class DebugConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="""
        Master switch for debug mode.
        When enabled, activates various debugging features.
        Should be disabled in production for security and performance.
        """,
        examples=[True, False],
    )
    asyncio: bool = Field(
        default=False,
        description="""
        Whether to enable asyncio debug mode.
        Helps detect problems like coroutines never awaited.
        Adds significant overhead, use only during development.
        """,
        examples=[True, False],
    )
    enhanced_aiomonitor_task_info: bool = Field(
        default=False,
        description="""
        Enable enhanced task information in aiomonitor.
        Provides more detailed information about running asyncio tasks.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "enhanced-aiomonitor-task-info", "enhanced_aiomonitor_task_info"
        ),
        serialization_alias="enhanced-aiomonitor-task-info",
    )
    log_events: bool = Field(
        default=False,
        description="""
        Whether to log all internal events.
        Very verbose, but useful for debugging event-related issues.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("log-events", "log_events"),
        serialization_alias="log-events",
    )


class OTELConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="""
        Whether to enable OpenTelemetry for tracing or logging.
        When enabled, traces or logs will be collected and sent to the configured OTLP endpoint.
        """,
        examples=[True, False],
    )
    log_level: str = Field(
        default="INFO",
        description="""
        Log level for OpenTelemetry.
        Controls the verbosity of logs generated by OpenTelemetry.
        """,
        examples=["DEBUG", "INFO", "WARN", "ERROR"],
        validation_alias=AliasChoices("log-level", "log_level"),
        serialization_alias="log-level",
    )
    endpoint: str = Field(
        default="http://127.0.0.1:4317",
        description="""
        OTLP endpoint for sending traces.
        Should include the protocol, host and port of the OTLP receiver.
        """,
        examples=["http://localhost:4317", "http://otel-collector:4317"],
    )


class ServiceDiscoveryConfig(BaseConfigSchema):
    type: ServiceDiscoveryType = Field(
        default=ServiceDiscoveryType.REDIS,
        description="""
        Type of service discovery to use.
        """,
        examples=[item.value for item in ServiceDiscoveryType],
    )


class StorageProxyConfig(BaseConfigSchema):
    ipc_base_path: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
        description="""
        Base directory path for inter-process communication files.
        Used for Unix domain sockets and other IPC mechanisms.
        """,
        examples=["/tmp/backend.ai/ipc"],
        validation_alias=AliasChoices("ipc-base-path", "ipc_base_path"),
        serialization_alias="ipc-base-path",
    )
    node_id: str = Field(
        description="""
        Unique identifier for this storage-proxy node.
        Used for service discovery and coordination.
        """,
        examples=["storage-proxy-1"],
        validation_alias=AliasChoices("node-id", "node_id"),
        serialization_alias="node-id",
    )
    num_proc: int = Field(
        default=_max_cpu_count or 1,
        ge=1,
        le=_max_cpu_count or 1,
        description="""
        Number of worker processes to spawn.
        Defaults to the number of CPU cores available.
        """,
        examples=[1, 4],
        validation_alias=AliasChoices("num-proc", "num_proc"),
        serialization_alias="num-proc",
    )
    pid_file: Path = Field(
        default=Path(os.devnull),
        description="""
        Path to the file where the process ID will be written.
        Set to /dev/null to disable this feature.
        """,
        examples=["/var/run/storage-proxy.pid"],
        validation_alias=AliasChoices("pid-file", "pid_file"),
        serialization_alias="pid-file",
    )
    event_loop: EventLoopType = Field(
        default=EventLoopType.asyncio,
        description="""
        Event loop implementation to use.
        'asyncio' is the standard library implementation.
        'uvloop' is a faster alternative but may have compatibility issues.
        """,
        examples=[item.value for item in EventLoopType],
        validation_alias=AliasChoices("event-loop", "event_loop"),
        serialization_alias="event-loop",
    )
    scandir_limit: int = Field(
        default=1000,
        ge=0,
        description="""
        Maximum number of entries to scan in directory operations.
        Prevents excessive memory usage when scanning large directories.
        """,
        examples=[1000, 5000],
        validation_alias=AliasChoices("scandir-limit", "scandir_limit"),
        serialization_alias="scandir-limit",
    )
    max_upload_size: str = Field(
        default="100g",
        description="""
        Maximum size allowed for file uploads.
        Prevents storage exhaustion from large uploads.
        """,
        examples=["100g", "500g"],
        validation_alias=AliasChoices("max-upload-size", "max_upload_size"),
        serialization_alias="max-upload-size",
    )
    secret: str = Field(
        description="""
        Secret key for generating JWT tokens.
        Used for authenticating client requests.
        """,
        examples=["jwt-secret-key"],
    )
    session_expire: TimeDuration = Field(
        description="""
        Session expiration time.
        Controls how long JWT tokens remain valid.
        """,
        examples=["1h", "24h"],
        validation_alias=AliasChoices("session-expire", "session_expire"),
        serialization_alias="session-expire",
    )
    user: Optional[UserID] = Field(
        default=UserID(_default_uid),
        description="""
        User ID to run the storage-proxy process as.
        Defaults to the UID of the current file's owner.
        """,
        examples=[_default_uid],
    )
    group: Optional[GroupID] = Field(
        default=GroupID(_default_gid),
        description="""
        Group ID to run the storage-proxy process as.
        Defaults to the GID of the current file's owner.
        """,
        examples=[_default_gid],
    )
    aiomonitor_termui_port: int = Field(
        default=38300,
        ge=1,
        le=65535,
        description="""
        Port for the aiomonitor terminal UI.
        Allows connecting to a debugging console.
        """,
        examples=[38300],
        validation_alias=AliasChoices(
            "aiomonitor-termui-port", "aiomonitor_termui_port", "aiomonitor-port"
        ),
        serialization_alias="aiomonitor-termui-port",
    )
    aiomonitor_webui_port: int = Field(
        default=39300,
        ge=1,
        le=65535,
        description="""
        Port for the aiomonitor web UI.
        Provides a web-based monitoring interface.
        """,
        examples=[39300],
        validation_alias=AliasChoices("aiomonitor-webui-port", "aiomonitor_webui_port"),
        serialization_alias="aiomonitor-webui-port",
    )
    watcher_insock_path_prefix: Optional[str] = Field(
        default=None,
        description="""
        Path prefix for watcher input sockets.
        Used for communication with watcher processes.
        """,
        examples=["/tmp/backend.ai/watcher"],
        validation_alias=AliasChoices("watcher-insock-path-prefix", "watcher_insock_path_prefix"),
        serialization_alias="watcher-insock-path-prefix",
    )
    watcher_outsock_path_prefix: Optional[str] = Field(
        default=None,
        description="""
        Path prefix for watcher output sockets.
        Used for communication with watcher processes.
        """,
        examples=["/tmp/backend.ai/watcher"],
        validation_alias=AliasChoices("watcher-outsock-path-prefix", "watcher_outsock_path_prefix"),
        serialization_alias="watcher-outsock-path-prefix",
    )
    use_watcher: bool = Field(
        default=False,
        description="""
        Whether to use watcher processes.
        Enables additional monitoring capabilities.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("use-watcher", "use_watcher"),
        serialization_alias="use-watcher",
    )
    use_experimental_redis_event_dispatcher: bool = Field(
        default=False,
        description="""
        Whether to use experimental Redis-based event dispatcher.
        May provide better performance for event handling.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "use-experimental-redis-event-dispatcher", "use_experimental_redis_event_dispatcher"
        ),
        serialization_alias="use-experimental-redis-event-dispatcher",
    )


class PresignedUploadConfig(BaseConfigSchema):
    min_size: Optional[int] = Field(
        default=None,
        description="""
        Minimum file size for multipart uploads.
        If None, no minimum size limit is enforced.
        """,
        examples=[5 * 1024 * 1024, 10 * 1024 * 1024],
        validation_alias=AliasChoices("min-size", "min_size"),
        serialization_alias="min-size",
    )
    max_size: Optional[int] = Field(
        default=None,
        description="""
        Maximum file size for uploads.
        If None, no maximum size limit is enforced.
        """,
        examples=[5 * 1024 * 1024 * 1024, 10 * 1024 * 1024 * 1024],
        validation_alias=AliasChoices("max-size", "max_size"),
        serialization_alias="max-size",
    )
    expiration: int = Field(
        default=60 * 5,  # 5 minutes
        description="""
        Expiration time (in seconds) for presigned URLs.
        """,
        examples=[3600, 7200],
    )


class PresignedDownloadConfig(BaseConfigSchema):
    expiration: int = Field(
        default=60 * 5,  # 5 minutes
        description="""
        Expiration time (in seconds) for presigned URLs.
        """,
        examples=[3600, 7200],
    )


class VFSStorageConfig(BaseConfigSchema):
    base_path: Path = Field(
        description="""
        Base filesystem path for VFS storage.
        This directory will serve as the root for all VFS operations.
        """,
        examples=["/data/ai-models", "/shared/datasets"],
        validation_alias=AliasChoices("base-path", "base_path"),
        serialization_alias="base-path",
    )
    subpath: Optional[str] = Field(
        default=None,
        description="""
        Optional subdirectory path appended to base_path.
        Used to further organize storage within the base directory.
        """,
        examples=["models", "datasets", "user-data"],
    )
    upload_chunk_size: int = Field(
        default=65536,  # 64KB
        ge=1024,  # Minimum 1KB
        description="""
        Chunk size (in bytes) for streaming file upload operations.
        Controls how data is buffered during file uploads.
        """,
        examples=[8192, 65536, 1048576],
        validation_alias=AliasChoices("upload-chunk-size", "upload_chunk_size"),
        serialization_alias="upload-chunk-size",
    )
    download_chunk_size: int = Field(
        default=65536,  # 64KB
        ge=1024,  # Minimum 1KB
        description="""
        Chunk size (in bytes) for streaming file download operations.
        Controls how data is buffered during file downloads.
        """,
        examples=[8192, 65536, 1048576],
        validation_alias=AliasChoices("download-chunk-size", "download_chunk_size"),
        serialization_alias="download-chunk-size",
    )
    max_file_size: Optional[int] = Field(
        default=None,
        description="""
        Maximum file size (in bytes) allowed for uploads.
        If None, no size limit is enforced.
        """,
        examples=[1073741824, 10737418240],  # 1GB, 10GB
        validation_alias=AliasChoices("max-file-size", "max_file_size"),
        serialization_alias="max-file-size",
    )


# TODO: Remove this after migrating this to database
class ObjectStorageConfig(BaseConfigSchema):
    endpoint: str = Field(
        description="""
        Endpoint URL for the object storage service.
        Should include the protocol (http or https) and port if non-standard.
        """,
        examples=["http://localhost:9000", "https://storage.example.com"],
    )
    access_key: str = Field(
        description="""
        Access key for authenticating with the object storage service.
        Required for services that use access keys for authentication.
        """,
        examples=["my-access-key"],
        validation_alias=AliasChoices("access-key", "access_key"),
        serialization_alias="access-key",
    )
    secret_key: str = Field(
        description="""
        Secret key for authenticating with the object storage service.
        Required for services that use secret keys for authentication.
        """,
        examples=["my-secret-key"],
        validation_alias=AliasChoices("secret-key", "secret_key"),
        serialization_alias="secret-key",
    )
    buckets: list[str] = Field(
        default_factory=list,
        description="""
        List of bucket names managed by this storage configuration.
        """,
        examples=["my-bucket"],
    )
    region: str = Field(
        description="""
        Region where the object storage service is located.
        Required for services that require region specification.
        """,
        examples=["us-west-1", "eu-central-1"],
    )
    presigned_upload: PresignedUploadConfig = Field(
        default_factory=PresignedUploadConfig,
        description="""
        Configuration for presigned upload URLs.
        Controls parameters like expiration time and size limits.
        """,
        validation_alias=AliasChoices("presigned-upload", "presigned_upload"),
        serialization_alias="presigned-upload",
    )
    presigned_download: PresignedDownloadConfig = Field(
        default_factory=PresignedDownloadConfig,
        description="""
        Configuration for presigned download URLs.
        Controls parameters like expiration time.
        """,
        validation_alias=AliasChoices("presigned-download", "presigned_download"),
        serialization_alias="presigned-download",
    )
    upload_chunk_size: int = Field(
        default=5 * 1024 * 1024,
        ge=5 * 1024 * 1024,
        description="""
        Chunk size (in bytes) for uploading files to the object storage.
        Should be greater than or equal to 5 MiB due to S3 requirements.
        """,
        examples=[5 * 1024 * 1024],
        validation_alias=AliasChoices("upload-chunk-size", "upload_chunk_size"),
        serialization_alias="upload-chunk-size",
    )
    download_chunk_size: int = Field(
        default=8192,
        description="""
        Chunk size (in bytes) for downloading files from the object storage.
        """,
        examples=[8192],
        validation_alias=AliasChoices("download-chunk-size", "download_chunk_size"),
        serialization_alias="download-chunk-size",
    )
    reservoir_download_chunk_size: int = Field(
        default=8192,
        description="""
        Chunk size (in bytes) for downloading files from the remote reservoir storage.
        """,
        examples=[8192],
        validation_alias=AliasChoices(
            "reservoir-download-chunk-size", "reservoir_download_chunk_size"
        ),
        serialization_alias="reservoir-download-chunk-size",
    )


class LegacyObjectStorageConfig(ObjectStorageConfig):
    name: str = Field(
        description="""
        Name of the object storage configuration.
        Used to identify this storage in the system.
        """,
        examples=["s3-storage", "minio-storage"],
    )


class HuggingfaceConfig(BaseConfigSchema):
    endpoint: str = Field(
        default="https://huggingface.co",
        description="""
        Custom endpoint for HuggingFace API.
        If not provided, defaults to the official HuggingFace API endpoint.
        Useful for connecting to self-hosted HuggingFace instances.
        """,
        examples=["https://huggingface.co"],
    )
    token: Optional[str] = Field(
        default=None,
        description="""
        HuggingFace API token for authentication.
        You cannot access the gated repositories without this token.
        """,
    )
    download_chunk_size: int = Field(
        default=8192,
        description="""
        Chunk size (in bytes) for downloading files from the HuggingFace API.
        """,
        examples=[8192],
        validation_alias=AliasChoices("download-chunk-size", "download_chunk_size"),
        serialization_alias="download-chunk-size",
    )


# TODO: Remove legacy config classes
class LegacyHuggingfaceConfig(HuggingfaceConfig):
    registry_type: Literal["huggingface"] = Field(
        description="""
        Type of the registry configuration.
        This is used to identify the specific registry type.
        """,
        alias="type",
    )


class ReservoirConfig(BaseConfigSchema):
    endpoint: str = Field(
        default="https://huggingface.co",
        description="""
        Custom endpoint for the reservoir registry API.
        """,
        examples=["https://huggingface.co"],
    )
    object_storage_access_key: Optional[str] = Field(
        default=None,
        description="""
        Access key for authenticating with the reservoir registry's object storage API.
        """,
        validation_alias=AliasChoices("object-storage-access-key", "object_storage_access_key"),
        serialization_alias="object-storage-access-key",
    )
    object_storage_secret_key: Optional[str] = Field(
        default=None,
        description="""
        Secret key for authenticating with the reservoir registry's object storage API.
        """,
        validation_alias=AliasChoices("object-storage-secret-key", "object_storage_secret_key"),
        serialization_alias="object-storage-secret-key",
    )
    object_storage_region: Optional[str] = Field(
        default=None,
        description="""
        Region for the reservoir registry's object storage.
        """,
        validation_alias=AliasChoices("object-storage-region", "object_storage_region"),
        serialization_alias="object-storage-region",
    )


class LegacyReservoirConfig(ReservoirConfig):
    registry_type: Literal["reservoir"] = Field(
        description="""
        Type of the registry configuration.
        This is used to identify the specific registry type.
        """,
        alias="type",
    )


class ArtifactRegistryStorageConfig(BaseConfigSchema):
    storage_type: ArtifactStorageType = Field(
        description="""
        Type of the artifact storage.
        Determines how to interact with the storage service.
        """,
        examples=[typ.value for typ in ArtifactStorageType],
        alias="type",
    )
    object_storage: Optional[ObjectStorageConfig] = Field(
        default=None,
        description="""
        Object storage configuration.
        """,
        validation_alias=AliasChoices("object-storage", "object_storage"),
        serialization_alias="object-storage",
    )
    vfs: Optional[VFSStorageConfig] = Field(
        default=None,
        description="""
        VFS storage configuration.
        """,
    )

    @model_validator(mode="after")
    def _validate_storage_config(self) -> Self:
        match self.storage_type:
            case ArtifactStorageType.OBJECT_STORAGE:
                if self.object_storage is None:
                    raise InvalidConfigError(
                        "object_storage config is required when storage_type is 'object_storage'"
                    )
            case ArtifactStorageType.VFS:
                if self.vfs is None:
                    raise InvalidConfigError("vfs config is required when storage_type is 'vfs'")
            case ArtifactStorageType.GIT_LFS:
                raise GenericNotImplementedError("git_lfs is not supported yet")

        return self


LegacyRegistrySpecificConfig = Union[LegacyHuggingfaceConfig, LegacyReservoirConfig]


class LegacyArtifactRegistryConfig(BaseConfigSchema):
    name: str = Field(
        description="""
        Name of the artifact registry configuration.
        Used to identify this registry in the system.
        """,
        examples=[typ.value for typ in ArtifactRegistryType],
    )
    config: LegacyRegistrySpecificConfig = Field(
        discriminator="registry_type",
        description="""
        Configuration for the artifact registry.
        """,
    )


class ArtifactRegistryConfig(BaseConfigSchema):
    registry_type: ArtifactRegistryType = Field(
        description="""
        Type of the artifact registry.
        Determines how to interact with the registry service.
        """,
        examples=[typ.value for typ in ArtifactRegistryType],
        alias="type",
    )
    huggingface: Optional[HuggingfaceConfig] = Field(
        default=None,
        description="""
        HuggingFace registry configuration.
        """,
    )
    reservoir: Optional[ReservoirConfig] = Field(
        default=None,
        description="""
        Reservoir registry configuration.
        """,
    )

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
    storage_proxy: StorageProxyConfig = Field(
        description="""
        Core storage-proxy service configuration.
        Controls how the storage-proxy operates and communicates.
        """,
        validation_alias=AliasChoices("storage-proxy", "storage_proxy"),
        serialization_alias="storage-proxy",
    )
    pyroscope: PyroscopeConfig = Field(
        default_factory=PyroscopeConfig,
        description="""
        Pyroscope profiling configuration.
        Controls integration with the Pyroscope performance profiling tool.
        """,
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="""
        Logging system configuration.
        Controls how logs are formatted, filtered, and stored.
        """,
    )
    api: APIConfig = Field(
        description="""
        API configuration for client and manager interfaces.
        Controls how the storage-proxy serves requests.
        """,
    )
    volume: dict[str, VolumeInfoConfig] = Field(
        description="""
        Volume configuration.
        Defines available storage backends and their settings.
        """,
    )
    debug: DebugConfig = Field(
        default_factory=DebugConfig,
        description="""
        Debugging options configuration.
        Controls various debugging features and tools.
        """,
    )
    service_discovery: ServiceDiscoveryConfig = Field(
        default_factory=ServiceDiscoveryConfig,
        description="""
        Service discovery configuration.
        Controls how services are discovered and connected.
        """,
        validation_alias=AliasChoices("service-discovery", "service_discovery"),
        serialization_alias="service-discovery",
    )
    otel: OTELConfig = Field(
        default_factory=OTELConfig,
        description="""
        OpenTelemetry configuration.
        Controls how tracing and logging are handled.
        """,
    )
    etcd: EtcdConfig = Field(
        default_factory=EtcdConfig,
        description="""
        Etcd configuration settings.
        Used for distributed coordination.
        """,
    )
    storages: list[LegacyObjectStorageConfig] = Field(
        default_factory=list,
        description="""
        Deprecated, use `artifact_storages` instead.

        List of object storage configurations.
        Each configuration defines how to connect to and use an object storage service.
        """,
    )
    registries: list[LegacyArtifactRegistryConfig] = Field(
        default_factory=list,
        description="""
        Deprecated, use `artifact_registries` instead.

        List of artifact registry configurations.
        Each configuration defines how to connect to and use an artifact registry service.
        """,
    )

    artifact_storages: dict[str, ArtifactRegistryStorageConfig] = Field(
        default_factory=dict,
        description="""
        Dictionary of artifact storage configurations keyed by name.
        Each configuration defines how to connect to and use an artifact storage service.
        """,
        validation_alias=AliasChoices("artifact-storages", "artifact_storages"),
        serialization_alias="artifact-storages",
    )
    artifact_registries: dict[str, ArtifactRegistryConfig] = Field(
        default_factory=dict,
        description="""
        Dictionary of artifact registry configurations keyed by name.
        Each configuration defines how to connect to and use an artifact registry service.
        """,
        validation_alias=AliasChoices("artifact-registries", "artifact_registries"),
        serialization_alias="artifact-registries",
    )

    # TODO: Remove me after changing config injection logic
    model_config = ConfigDict(
        extra="allow",
    )
