import enum
import os
import secrets
import socket
import sys
from pathlib import Path
from pprint import pformat
from typing import Any, Literal, Mapping, Optional, Self

import click
from pydantic import BaseModel, Field, FilePath

from ai.backend.common import config
from ai.backend.common.lock import EtcdLock, FileLock, RedisLock
from ai.backend.common.typed_validators import AutoDirectoryPath, GroupID, HostPortPair, UserID
from ai.backend.logging.types import LogLevel
from ai.backend.manager.pglock import PgAdvisoryLock

_default_smtp_template = """
Action type: {{ action_type }}
Entity ID: {{ entity_id }}
Status: {{ status }}
Description: {{ description }}
Started at: {{ created_at }}
Finished at: {{ ended_at }}
Duration: {{ duration }} seconds

This email is sent from Backend.AI SMTP Reporter.
"""


class DatabaseType(enum.StrEnum):
    postgresql = "postgresql"


class DatabaseConfig(BaseModel):
    type: Literal["postgresql"] = Field(
        default="postgresql",
        description="""
        Type of the database system to use.
        Currently, only PostgreSQL is supported as the main database backend.
        """,
        examples=["postgresql"],
    )
    addr: HostPortPair = Field(
        default_factory=lambda: HostPortPair(host="127.0.0.1", port=5432),
        description="""
        Network address and port of the database server.
        Default is the standard PostgreSQL port on localhost.
        """,
        examples=[{"host": "127.0.0.1", "port": 5432}],
    )
    name: str = Field(
        min_length=2,
        max_length=64,
        description="""
        Database name to use.
        This database must exist and be accessible by the configured user.
        Length must be between 2 and 64 characters due to database naming constraints.
        """,
        examples=["backend"],
    )
    user: str = Field(
        description="""
        Username for authenticating with the database.
        This user must have sufficient privileges for all database operations.
        """,
        examples=["postgres"],
    )
    password: str = Field(
        description="""
        Password for authenticating with the database.
        Can be a direct password string or an environment variable name.
        For security, using environment variables is recommended in production.
        """,
        examples=["develove", "DB_PASSWORD"],
    )
    pool_size: int = Field(
        default=8,
        ge=1,
        description="""
        Size of the database connection pool.
        Determines how many concurrent database connections to maintain.
        Should be tuned based on expected load and database server capacity.
        """,
        examples=[1, 8],
        alias="pool-size",
    )
    pool_recycle: float = Field(
        default=-1,
        ge=-1,
        description="""
        Maximum lifetime of a connection in seconds before it's recycled.
        Set to -1 to disable connection recycling.
        Useful to handle cases where database connections are closed by the server after inactivity.
        """,
        examples=[-1, 50],
        alias="pool-recycle",
    )
    pool_pre_ping: bool = Field(
        default=False,
        description="""
        Whether to test connections with a lightweight ping before using them.
        Helps detect stale connections before they cause application errors.
        Adds a small overhead but improves reliability.
        """,
        examples=[True, False],
        alias="pool-pre-ping",
    )
    max_overflow: int = Field(
        default=64,
        ge=-1,
        description="""
        Maximum number of additional connections to create beyond the pool_size.
        Set to -1 for unlimited overflow connections.
        These connections are created temporarily when pool_size is insufficient.
        """,
        examples=[-1, 64],
        alias="max-overflow",
    )
    lock_conn_timeout: float = Field(
        default=0,
        ge=0,
        description="""
        Timeout in seconds for acquiring a connection from the pool.
        0 means wait indefinitely.
        If connections cannot be acquired within this time, an exception is raised.
        """,
        examples=[0, 30],
        alias="lock-conn-timeout",
    )


_max_num_proc = os.cpu_count() or 8
_file_perm = (Path(__file__).parent.parent / "server.py").stat()


class EventLoopType(enum.StrEnum):
    asyncio = "asyncio"
    uvloop = "uvloop"


class DistributedLockType(enum.StrEnum):
    filelock = "filelock"
    pg_advisory = "pg_advisory"
    redlock = "redlock"
    etcd = "etcd"
    etcetra = "etcetra"


class EtcdConfig(BaseModel):
    namespace: str = Field(
        default="backend",
        description="""
        Namespace prefix for etcd keys used by Backend.AI.
        Allows multiple Backend.AI clusters to share the same etcd cluster.
        All Backend.AI related keys will be stored under this namespace.
        """,
        examples=["local", "backend"],
    )
    addr: HostPortPair = Field(
        default_factory=lambda: HostPortPair(host="127.0.0.1", port=2379),
        description="""
        Network address of the etcd server.
        Default is the standard etcd port on localhost.
        For production, should point to an etcd cluster endpoint.
        """,
        examples=[{"host": "127.0.0.1", "port": 2379}],
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


class ManagerConfig(BaseModel):
    ipc_base_path: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
        description="""
        Base directory path for inter-process communication files.
        Used for Unix domain sockets and other IPC mechanisms.
        This directory must be writable by the manager process.
        In production environments, consider using /var/run/backend.ai/ipc instead.
        """,
        examples=["/var/run/backend.ai/ipc"],
        alias="ipc-base-path",
    )
    num_proc: int = Field(
        default=_max_num_proc,
        ge=1,
        le=os.cpu_count(),
        description="""
        Number of worker processes to spawn for the manager.
        Defaults to the number of CPU cores available.
        For optimal performance, set this to match your CPU core count.
        """,
        examples=[1, 4],
        alias="num-proc",
    )
    id: str = Field(
        default=f"i-{socket.gethostname()}",
        description="""
        Unique identifier for this manager instance.
        Used to distinguish between multiple manager instances in a cluster.
        By default, uses the hostname with an 'i-' prefix.
        Must be unique across all managers in the same Backend.AI cluster.
        """,
        examples=["i-manager123"],
    )
    user: Optional[UserID] = Field(
        default=UserID(_file_perm.st_uid),
        description="""
        User ID (UID) under which the manager process runs.
        If not specified, defaults to the UID of the server.py file.
        Important for proper file permissions when creating files/sockets.
        """,
        examples=[_file_perm.st_uid],
    )
    group: Optional[GroupID] = Field(
        default=GroupID(_file_perm.st_gid),
        description="""
        Group ID (GID) under which the manager process runs.
        If not specified, defaults to the GID of the server.py file.
        Important for proper file permissions when creating files/sockets.
        """,
        examples=[_file_perm.st_gid],
    )
    service_addr: HostPortPair = Field(
        default_factory=lambda: HostPortPair(host="0.0.0.0", port=8080),
        description="""
        Network address and port where the manager service will listen.
        Default is all interfaces (0.0.0.0) on port 8080.
        For private deployments, consider using 127.0.0.1 instead.
        """,
        examples=[{"host": "127.0.0.1", "port": 8080}],
        alias="service-addr",
    )
    internal_addr: HostPortPair = Field(
        default_factory=lambda: HostPortPair(host="0.0.0.0", port=18080),
        description="""
        Set the internal hostname/port to accept internal API requests.
        """,
        examples=[{"host": "127.0.0.1", "port": 18080}],
        alias="internal-addr",
    )
    rpc_auth_manager_keypair: FilePath = Field(
        default=Path("fixtures/manager/manager.key_secret"),
        description="""
        Path to the keypair file used for RPC authentication.
        This file contains key pairs used for secure communication between manager components.
        In production, should be stored in a secure location with restricted access.
        """,
        examples=["fixtures/manager/manager.key_secret"],
        alias="rpc-auth-manager-keypair",
    )
    heartbeat_timeout: float = Field(
        default=40.0,
        ge=1.0,
        description="""
        Timeout in seconds for agent heartbeat checks.
        If an agent doesn't respond within this time, it's considered offline.
        Should be set higher than the agent's heartbeat interval.
        """,
        examples=[1.0, 40.0],
        alias="heartbeat-timeout",
    )
    secret: Optional[str] = Field(
        default=None,
        description="""
        Secret key for manager authentication and signing.
        Used for securing API tokens and inter-service communication.
        Should be a strong random string in production environments.
        If not provided, one will be generated automatically (not recommended for clusters).
        """,
        examples=["XXXXXXXXXXXXXX"],
    )
    ssl_enabled: bool = Field(
        default=False,
        description="""
        Whether to enable SSL/TLS for secure API communication.
        Strongly recommended for production deployments exposed to networks.
        Requires valid certificate and private key when enabled.
        """,
        examples=[True, False],
        alias="ssl-enabled",
    )
    ssl_cert: Optional[FilePath] = Field(
        default=None,
        description="""
        Path to the SSL certificate file.
        Required if `ssl_enabled` is True.
        Should be a PEM-formatted certificate file, either self-signed or from a CA.
        """,
        examples=["fixtures/manager/manager.crt"],
        alias="ssl-cert",
    )
    ssl_privkey: Optional[str] = Field(
        default=None,
        description="""
        Path to the SSL private key file.
        Required if `ssl_enabled` is True.
        Should be a PEM-formatted private key corresponding to the certificate.
        """,
        examples=["fixtures/manager/manager.key"],
        alias="ssl-privkey",
    )
    event_loop: EventLoopType = Field(
        default=EventLoopType.asyncio,
        description="""
        Event loop implementation to use.
        'asyncio' is the Python standard library implementation.
        'uvloop' is a faster alternative but may have compatibility issues with some libraries.
        """,
        examples=[item.value for item in EventLoopType],
        alias="event-loop",
    )
    distributed_lock: DistributedLockType = Field(
        default=DistributedLockType.pg_advisory,
        description="""
        Distributed lock mechanism to coordinate multiple manager instances.
        - filelock: Simple file-based locks (not suitable for distributed deployments)
        - pg_advisory: PostgreSQL advisory locks (default, good for small/medium clusters)
        - redlock: Redis-based distributed locking (good for large clusters)
        - etcd: etcd-based locks (good for large clusters with etcd)
        - etcetra: etcd v3 API-compatible distributed locking
        """,
        examples=[item.value for item in DistributedLockType],
        alias="distributed-lock",
    )
    pg_advisory_config: Mapping[str, Any] = Field(
        default=PgAdvisoryLock.default_config,
        description="""
        Configuration for PostgreSQL advisory locks.
        This is used when distributed_lock is set to pg_advisory.
        """,
        examples=[],
        alias="pg-advisory-config",
    )
    filelock_config: Mapping[str, Any] = Field(
        default=FileLock.default_config,
        description="""
        Configuration for file-based locks.
        This is used when distributed_lock is set to filelock.
        """,
        examples=[],
        alias="filelock-config",
    )
    redlock_config: Mapping[str, Any] = Field(
        default=RedisLock.default_config,
        description="""
        Configuration for Redis-based distributed locking.
        This is used when distributed_lock is set to redlock.
        """,
        examples=[],
        alias="redlock-config",
    )
    etcdlock_config: Mapping[str, Any] = Field(
        default=EtcdLock.default_config,
        description="""
        Configuration for etcd-based distributed locking.
        This is used when distributed_lock is set to etcd.
        """,
        examples=[],
        alias="etcdlock-config",
    )
    session_schedule_lock_lifetime: float = Field(
        default=30,
        description="""
        Maximum lifetime in seconds for session scheduling locks.
        If scheduling takes longer than this, locks will be automatically released.
        Prevents deadlocks in case a manager fails during scheduling.
        """,
        examples=[30.0, 60.0],
        # Don't use alias for compatibility with the legacy config
    )
    session_check_precondition_lock_lifetime: float = Field(
        default=30,
        description="""
        Maximum lifetime in seconds for session precondition check locks.
        Controls how long the manager can hold a lock while checking if a session can be created.
        Should be balanced to prevent both deadlocks and race conditions.
        """,
        examples=[30.0, 60.0],
        # Don't use alias for compatibility with the legacy config
    )
    session_start_lock_lifetime: float = Field(
        default=30,
        description="""
        Maximum lifetime in seconds for session start locks.
        Controls how long the manager can hold a lock while starting a session.
        Longer values are safer but may block other managers longer on failure.
        """,
        examples=[30.0, 60.0],
        # Don't use alias for compatibility with the legacy config
    )
    pid_file: Path = Field(
        default=Path(os.devnull),
        description="""
        Path to the file where the manager process ID will be written.
        Useful for service management and monitoring.
        Set to /dev/null by default to disable this feature.
        """,
        examples=["/var/run/manager.pid"],
        alias="pid-file",
    )
    allowed_plugins: Optional[set[str]] = Field(
        default=None,
        description="""
        List of explicitly allowed plugins to load.
        If specified, only these plugins will be loaded, even if others are installed.
        Useful for controlling exactly which plugins are active.
        Leave as None to load all available plugins except those in disabled_plugins.
        """,
        examples=[["example.plugin.what.you.want"]],
        alias="allowed-plugins",
    )
    disabled_plugins: Optional[set[str]] = Field(
        default=None,
        description="""
        List of plugins to explicitly disable.
        These plugins won't be loaded even if they're installed.
        Useful for disabling problematic or unwanted plugins without uninstalling them.
        """,
        examples=[["example.plugin.what.you.want"]],
        alias="disabled-plugins",
    )
    hide_agents: bool = Field(
        default=False,
        description="""
        Whether to hide detailed agent information in API responses.
        When enabled, agent details are obscured in user-facing APIs.
        Useful for security in multi-tenant environments.
        """,
        examples=[True, False],
        alias="hide-agents",
    )
    agent_selection_resource_priority: list[str] = Field(
        default=["cuda", "rocm", "tpu", "cpu", "mem"],
        description="""
        Priority order for resources when selecting agents for compute sessions.
        Determines which resources are considered more important during scheduling.
        Default prioritizes GPU resources (CUDA, ROCm) over CPU and memory.
        """,
        examples=[["cuda", "rocm", "tpu", "cpu", "mem"]],
        alias="agent-selection-resource-priority",
    )
    importer_image: str = Field(
        default="lablup/importer:manylinux2010",
        description="""
        Deprecated: Container image used for the importer service.
        The importer handles tasks like installing additional packages.
        Should be compatible with the Backend.AI environment.
        """,
        examples=["lablup/importer:manylinux2010"],
        alias="importer-image",
    )
    max_wsmsg_size: int = Field(
        default=16 * (2**20),  # default: 16 MiB
        description="""
        Maximum WebSocket message size in bytes.
        Controls the largest message that can be sent over WebSocket connections.
        Default is 16 MiB, which should be sufficient for most use cases.
        Increase for applications that need to transfer larger data chunks.
        """,
        examples=[16 * (2**20), 32 * (2**20)],
        alias="max-wsmsg-size",
    )
    aiomonitor_port: Optional[int] = Field(
        default=None,
        ge=1,
        le=65535,
        description="""
        Deprecated: Port for the aiomonitor terminal UI.
        Use `aiomonitor_termui_port` instead.
        """,
        examples=[38100, 38200],
        alias="aiomonitor-port",
    )
    aiomonitor_termui_port: int = Field(
        default=38100,
        ge=1,
        le=65535,
        description="""
        Port for the aiomonitor terminal UI.
        Allows connecting to a debugging console for the manager.
        Should be a port that's not used by other services.
        """,
        examples=[38100, 38200],
        alias="aiomonitor-termui-port",
    )
    aiomonitor_webui_port: int = Field(
        default=39100,
        ge=1,
        le=65535,
        description="""
        Port for the aiomonitor web UI.
        Provides a web-based monitoring interface for the manager.
        Should be a port that's not used by other services.
        """,
        examples=[39100, 39200],
        alias="aiomonitor-webui-port",
    )
    use_experimental_redis_event_dispatcher: bool = Field(
        default=False,
        description="""
        Whether to use the experimental Redis-based event dispatcher.
        May provide better performance for event handling in large clusters.
        Not recommended for production use unless specifically needed.
        """,
        examples=[True, False],
        alias="use-experimental-redis-event-dispatcher",
    )
    status_update_interval: Optional[float] = Field(
        default=None,
        ge=0,
        description="""
        Interval in seconds between status updates.
        Controls how frequently the manager updates its status.
        Smaller values provide more real-time information but increase overhead.
        """,
        examples=[60.0, 120.0],
        alias="status-update-interval",
    )
    status_lifetime: Optional[int] = Field(
        default=None,
        ge=0,
        description="""
        How long in seconds status information is considered valid.
        Status records older than this will be ignored or refreshed.
        Should be greater than the status_update_interval.
        """,
        examples=[60, 120],
        alias="status-lifetime",
    )
    public_metrics_port: Optional[int] = Field(
        default=None,
        ge=1,
        le=65535,
        description="""
        Port for exposing public metrics (e.g., Prometheus endpoint).
        If specified, metrics will be available at this port.
        Leave as None to disable public metrics exposure.
        """,
        examples=[8080, 9090],
        alias="public-metrics-port",
    )

    @property
    def aiomonitor_terminal_ui_port(self) -> int:
        """
        Returns the port for the aiomonitor terminal UI.
        When deprecated aiomonitor_port is set, it will return that value.
        Otherwise, it returns the aiomonitor_termui_port.
        """
        if self.aiomonitor_port is not None:
            return self.aiomonitor_port
        return self.aiomonitor_termui_port


# Deprecated: v20.09
class DockerRegistryConfig(BaseModel):
    ssl_verify: bool = Field(
        default=True,
        description="""
        Deprecated: Whether to verify SSL certificates when connecting to Docker registries.
        Disabling this is not recommended except for testing with self-signed certificates.
        """,
        examples=[True, False],
        alias="ssl-verify",
    )


class PyroscopeConfig(BaseModel):
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
        This name will identify this manager instance in Pyroscope UI.
        Required if Pyroscope is enabled.
        """,
        examples=["backendai-half-manager"],
        alias="app-name",
    )
    server_addr: Optional[str] = Field(
        default=None,
        description="""
        Address of the Pyroscope server.
        Must include the protocol (http or https) and port if non-standard.
        Required if Pyroscope is enabled.
        """,
        examples=["http://localhost:4040"],
        alias="server-addr",
    )
    sample_rate: Optional[int] = Field(
        default=None,
        description="""
        Sampling rate for Pyroscope profiling.
        Higher values collect more data but increase overhead.
        Balance based on your performance monitoring needs.
        """,
        examples=[10, 100, 1000],
        alias="sample-rate",
    )


class SMTPReporterConfig(BaseModel):
    name: str = Field(
        description="""
        Name of the SMTP reporter.
        Used to identify this reporter in the system.
        """,
        examples=["smtp"],
    )
    host: str = Field(
        description="""
        Host address of the service.
        Can be a hostname, IP address, or special addresses like 0.0.0.0 to bind to all interfaces.
        """,
        examples=["smtp.gmail.com"],
    )
    port: int = Field(
        ge=1,
        le=65535,
        description="""
        Port number of the service.
        Must be between 1 and 65535.
        Ports below 1024 require root/admin privileges.
        """,
        examples=[465, 587],
    )
    username: str = Field(
        description="""
        Username for authenticating with the SMTP server.
        This is required for sending emails through the SMTP service.
        """,
        examples=["user@example.com"],
    )
    password: str = Field(
        description="""
        Password for authenticating with the SMTP server.
        This is required for sending emails through the SMTP service.
        """,
        examples=["password"],
    )
    sender: str = Field(
        description="""
        Email address of the sender.
        This is the address that will appear as the sender in emails.
        """,
        examples=["sender@example.com"],
    )
    recipients: list[str] = Field(
        description="""
        List of email addresses to send notifications to.
        Can include multiple recipients separated by commas.
        """,
        examples=[["recipient1@example.com", "recipient2@example.com"]],
    )
    use_tls: bool = Field(
        default=True,
        description="""
        Whether to use TLS for secure communication with the SMTP server.
        Recommended for production environments to protect sensitive information.
        """,
        examples=[True, False],
        alias="use-tls",
    )
    max_workers: int = Field(
        default=5,
        ge=1,
        description="""
        Maximum number of worker threads for sending emails.
        Controls how many emails can be sent concurrently.
        Higher values may improve performance but increase resource usage.
        """,
        examples=[5, 10],
        alias="max-workers",
    )
    template: str = Field(
        default=_default_smtp_template,
        description="""
        Template for the email body.
        Can include placeholders for dynamic content.
        Placeholders will be replaced with actual values when sending emails.
        """,
        examples=[_default_smtp_template],
    )
    trigger_policy: Literal["ALL", "ON_ERROR"] = Field(
        default="ALL",
        description="""
        Policy for triggering email notifications.
        - ALL: Send emails for all events.
        - ON_ERROR: Send emails only for error events.
        Choose based on your notification needs.
        """,
        examples=["ALL", "ON_ERROR"],
        alias="trigger-policy",
    )


class AuditLogConfig(BaseModel):
    name: str = Field(
        description="""
        Name of the audit log reporter.
        Used to identify this reporter in the system.
        """,
        examples=["audit_log"],
    )


class ActionMonitorsConfig(BaseModel):
    subscribed_actions: list[str] = Field(
        description="""
        List of action types to subscribe to for monitoring.
        """,
        examples=[["session.create_from_params", "session.create_cluster"]],
        alias="subscribed-actions",
    )
    reporter: str = Field(
        description="""
        Name of the reporter to use for sending notifications.
        This should match the name of a configured reporter.
        """,
        examples=["smtp", "audit_log"],
    )


class ReporterConfig(BaseModel):
    smtp: list[SMTPReporterConfig] = Field(
        default=[],
        description="""
        SMTP reporter configuration.
        Controls how email notifications are sent.
        Includes settings for SMTP server, authentication, and email templates.
        """,
    )
    audit_log: list[AuditLogConfig] = Field(
        default=[],
        description="""
        Audit log reporter configuration.
        Controls how audit logs are reported.
        """,
        alias="audit-log",
    )
    action_monitors: list[ActionMonitorsConfig] = Field(
        default=[],
        description="""
        Action monitors configuration.
        Each reporter can be configured to subscribe to specific actions.
        """,
        alias="action-monitors",
    )


class DebugConfig(BaseModel):
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
        Helps detect problems like coroutines never awaited or excessive event loop delays.
        Adds significant overhead, use only during development.
        """,
        examples=[True, False],
    )
    enhanced_aiomonitor_task_info: bool = Field(
        default=False,
        description="""
        Enable enhanced task information in aiomonitor.
        Provides more detailed information about running asyncio tasks.
        Useful for debugging complex async issues, but adds overhead.
        """,
        examples=[True, False],
        alias="enhanced-aiomonitor-task-info",
    )
    log_events: bool = Field(
        default=False,
        description="""
        Whether to log all internal events.
        When enabled, all events passing through the system will be logged.
        Very verbose, but useful for debugging event-related issues.
        """,
        examples=[True, False],
        alias="log-events",
    )
    log_scheduler_ticks: bool = Field(
        default=False,
        description="""
        Whether to log scheduler ticks.
        Provides detailed logs about the scheduler's internal operations.
        Useful for debugging scheduling issues, but generates many log entries.
        """,
        examples=[True, False],
        alias="log-scheduler-ticks",
    )
    periodic_sync_stats: bool = Field(
        default=False,
        description="""
        Whether to periodically synchronize and log system statistics.
        When enabled, regularly collects and logs performance metrics.
        Helpful for monitoring system behavior over time.
        """,
        examples=[True, False],
        alias="periodic-sync-stats",
    )


class ManagerLocalConfig(BaseModel):
    _src_config_path: Path

    db: DatabaseConfig = Field(
        description="""
        Database configuration settings.
        Defines how the manager connects to its PostgreSQL database.
        Contains connection details, credentials, and pool settings.
        """,
    )
    etcd: EtcdConfig = Field(
        description="""
        Etcd configuration settings.
        Used for distributed coordination between manager instances.
        Contains connection details and authentication information.
        """,
    )
    manager: ManagerConfig = Field(
        description="""
        Core manager service configuration.
        Controls how the manager operates, communicates, and scales.
        Includes network settings, process management, and service parameters.
        """,
    )
    docker_registry: DockerRegistryConfig = Field(
        default=DockerRegistryConfig.model_validate({"ssl-verify": True}),
        description="""
        Deprecated: Docker registry configuration.
        Contains settings for connecting to Docker registries.
        """,
        alias="docker-registry",
    )
    logging: Any = Field(
        description="""
        Logging system configuration.
        Controls how logs are formatted, filtered, and stored.
        Detailed configuration is handled in ai.backend.logging.
        """,
    )
    pyroscope: PyroscopeConfig = Field(
        description="""
        Pyroscope profiling configuration.
        Controls integration with the Pyroscope performance profiling tool.
        Used for monitoring and analyzing application performance.
        """,
    )
    debug: DebugConfig = Field(
        description="""
        Debugging options configuration.
        Controls various debugging features and tools.
        Should typically be disabled in production environments.
        """,
    )
    reporter: ReporterConfig = Field(
        description="""
        Reporter configuration.
        Controls how notifications and logs are reported.
        Includes settings for Audit Logs, and Action Monitors, and SMTP reporters.
        Each reporter can be configured with its own settings.
        """
    )

    def __repr__(self):
        return pformat(self.model_dump())

    @classmethod
    def load(
        cls,
        config_path: Optional[Path] = None,
        log_level: LogLevel = LogLevel.NOTSET,
    ) -> Self:
        # Determine where to read configuration.
        raw_cfg, cfg_src_path = config.read_from_file(config_path, "manager")

        # Override the read config with environment variables (for legacy).
        config.override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
        config.override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
        config.override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
        config.override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")
        config.override_with_env(raw_cfg, ("db", "addr"), "BACKEND_DB_ADDR")
        config.override_with_env(raw_cfg, ("db", "name"), "BACKEND_DB_NAME")
        config.override_with_env(raw_cfg, ("db", "user"), "BACKEND_DB_USER")
        config.override_with_env(raw_cfg, ("db", "password"), "BACKEND_DB_PASSWORD")
        config.override_with_env(raw_cfg, ("manager", "num-proc"), "BACKEND_MANAGER_NPROC")
        config.override_with_env(raw_cfg, ("manager", "ssl-cert"), "BACKEND_SSL_CERT")
        config.override_with_env(raw_cfg, ("manager", "ssl-privkey"), "BACKEND_SSL_KEY")
        config.override_with_env(raw_cfg, ("manager", "pid-file"), "BACKEND_PID_FILE")
        config.override_with_env(
            raw_cfg, ("manager", "api-listen-addr", "host"), "BACKEND_SERVICE_IP"
        )
        config.override_with_env(
            raw_cfg, ("manager", "api-listen-addr", "port"), "BACKEND_SERVICE_PORT"
        )
        config.override_with_env(
            raw_cfg, ("manager", "event-listen-addr", "host"), "BACKEND_ADVERTISED_MANAGER_HOST"
        )
        config.override_with_env(
            raw_cfg, ("manager", "event-listen-addr", "port"), "BACKEND_EVENTS_PORT"
        )
        config.override_with_env(
            raw_cfg, ("docker-registry", "ssl-verify"), "BACKEND_SKIP_SSLCERT_VALIDATION"
        )

        config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogLevel.DEBUG)
        if log_level != LogLevel.NOTSET:
            config.override_key(raw_cfg, ("logging", "level"), log_level)
            config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)
            config.override_key(raw_cfg, ("logging", "pkg-ns", "aiohttp"), log_level)

        # Validate and fill configurations
        try:
            cfg = cls.model_validate(raw_cfg)
            if cfg.debug.enabled:
                print("== Manager configuration ==", file=sys.stderr)
                print(pformat(cfg), file=sys.stderr)
            cfg._src_config_path = cfg_src_path

            if cfg.manager.secret is None:
                cfg.manager.secret = secrets.token_urlsafe(16)
        except config.ConfigurationError as e:
            print(
                "ConfigurationError: Could not read or validate the manager local config:",
                file=sys.stderr,
            )
            print(pformat(e.invalid_data), file=sys.stderr)
            # TODO: Instead of cli error, raise custom exception
            raise click.Abort()
        else:
            return cfg
