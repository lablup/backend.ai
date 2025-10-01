"""
Configuration Schema on etcd
----------------------------

The etcd (v3) itself is a flat key-value storage, but we use its prefix-based filtering
by using a directory-like configuration structure.
At the root, it contains "/sorna/{namespace}" as the common prefix.

In most cases, a single global configurations are sufficient, but cluster administrators
may want to apply different settings (e.g., resource slot types, vGPU sizes, etc.)
to different scaling groups or even each node.

To support such requirements, we add another level of prefix named "configuration scope".
There are three types of configuration scopes:

 * Global
 * Scaling group
 * Node

When reading configurations, the underlying `ai.backend.common.etcd.AsyncEtcd` class
returns a `collections.ChainMap` instance that merges three configuration scopes
in the order of node, scaling group, and global, so that node-level configs override
scaling-group configs, and scaling-group configs override global configs if they exist.

Note that the global scope prefix may be an empty string; this allows use of legacy
etcd databases without explicit migration.  When the global scope prefix is an empty string,
it does not make a new depth in the directory structure, so "{namespace}/config/x" (not
"{namespace}//config/x"!) is recognized as the global config.

Notes on Docker registry configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A registry name contains the host, port (only for non-standards), and the path.
So, they must be URL-quoted (including slashes) to avoid parsing
errors due to intermediate slashes and colons.
Alias keys are also URL-quoted in the same way.

{namespace}
 + ''  # ConfigScoeps.GLOBAL
   + config
     + system
       - timezone: "UTC"  # pytz-compatible timezone names (e.g., "Asia/Seoul")
     + api
       - allow-origins: "*"
       - allow-openapi-schema-introspection: "yes" | "no"  # (default: no)
       - allow-graphql-schema-introspection: "yes" | "no"  # (default: no)
       + resources
         - group_resource_visibility: "true"  # return group resource status in check-presets
                                              # (default: false)
     + docker
       + image
         - auto_pull: "digest" (default) | "tag" | "none"
     + redis
       - addr: "{redis-host}:{redis-port}"
       - password: {password}
     + idle
       - enabled: "timeout,utilization"      # comma-separated list of checker names
       - app-streaming-packet-timeout: "5m"  # in seconds; idleness of app-streaming TCP connections
         # NOTE: idle checkers get activated AFTER the app-streaming packet timeout has passed.
       - checkers
         + "network_timeout"
           - threshold: "10m"  # time duration to stay under the thresholds
         + "utilization"
           + resource-thresholds
             + "cpu_util"
               - average: 30  # in percent
             + "mem"
               - average: 30  # in percent
             + "cuda_util"
               - average: 30  # in percent  # CUDA core utilization
             + "cuda_mem"
               - average: 30  # in percent
               # NOTE: To use "cuda.mem" criteria, user programs must use
               #       an incremental allocation strategy for CUDA memory.
           - thresholds-check-operator: "and"
             # "and" (default, so any other words except the "or"):
             #     garbage collect a session only when ALL of the resources are
             #     under-utilized not exceeding their thresholds.
             #     ex) (cpu < threshold) AND (mem < threshold) AND ...
             # "or":
             #     garbage collect a session when ANY of the resources is
             #     under-utilized not exceeding their thresholds.
             #     ex) (cpu < threshold) OR (mem < threshold) OR ...
           - time-window: "12h"  # time window to average utilization
                                 # a session will not be terminated until this time
           - initial-grace-period: "5m" # time to allow to be idle for first
         # "session_lifetime" does not have etcd config but it is configured via
         # the keypair_resource_polices table.
     + resource_slots
       - {"cuda.device"}: {"count"}
       - {"cuda.mem"}: {"bytes"}
       - {"cuda.smp"}: {"count"}
       ...
     + plugins
       + accelerator
         + "cuda"
           - allocation_mode: "discrete"
           ...
       + network
         + "overlay"
           - mtu: 1500  # Maximum Transmission Unit
       + scheduler
         + "fifo"
         + "lifo"
         + "drf"
         ...
     + network
       + inter-container:
         - default-driver: "overlay"
       + subnet
         - agent: "0.0.0.0/0"
         - container: "0.0.0.0/0"
       + rpc
         - keepalive-timeout: 60  # seconds
     + watcher
       - token: {some-secret}
   + volumes
     - _types     # allowed vfolder types
       + "user"   # enabled if present
       + "group"  # enabled if present
     # 20.09 and later
     - default_host: "{default-proxy}:{default-volume}"
     + proxies:   # each proxy may provide multiple volumes
       + "local"  # proxy name
         - client_api: "http://localhost:6021"
         - manager_api: "http://localhost:6022"
         - secret: "xxxxxx..."       # for manager API
         - ssl_verify: true | false  # for manager API
         - sftp_scaling_groups: "group-1,group-2,..."
       + "mynas1"
         - client_api: "https://proxy1.example.com:6021"
         - manager_api: "https://proxy1.example.com:6022"
         - secret: "xxxxxx..."       # for manager API
         - ssl_verify: true | false  # for manager API
         - sftp_scaling_groups: "group-3,group-4,..."
     # 23.03 and later
       + exposed_volume_info: "percentage"
       ...
     ...
   ...
 + nodes
   + manager
     - {instance-id}: "up"
     ...
   # etcd.get("config/redis/addr") is not None => single redis node
   # etcd.get("config/redis/sentinel") is not None => redis sentinel
   + redis:
     - addr: "tcp://redis:6379"
     - sentinel: {comma-seperated list of sentinel addresses}
     - service_name: "mymanager"
     - password: {redis-auth-password}
   + agents
     + {instance-id}: {"starting","running"}  # ConfigScopes.NODE
       - ip: {"127.0.0.1"}
       - watcher_port: {"6009"}
     ...
 + sgroup
   + {name}  # ConfigScopes.SGROUP
     - swarm-manager/token
     - swarm-manager/host
     - swarm-worker/token
     - iprange          # to choose ethernet iface when creating containers
     - resource_policy  # the name of scaling-group resource-policy in database
     + nodes
       - {instance-id}: 1  # just a membership set
"""

from __future__ import annotations

import enum
import logging
import os
import secrets
import socket
from collections.abc import Mapping
from datetime import datetime, timezone
from ipaddress import IPv4Network
from pathlib import Path
from pprint import pformat
from typing import Any, Literal, Optional, Union

from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    FilePath,
    IPvAnyNetwork,
    field_serializer,
    field_validator,
)

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.defs import DEFAULT_FILE_IO_TIMEOUT
from ai.backend.common.lock import EtcdLock, FileLock, RedisLock
from ai.backend.common.typed_validators import (
    AutoDirectoryPath,
    CommaSeparatedStrList,
    GroupID,
    HostPortPair,
    TimeDuration,
    TimeZone,
    UserID,
    _TimeDurationPydanticAnnotation,
)
from ai.backend.common.types import ServiceDiscoveryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.config import LoggingConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.defs import DEFAULT_METRIC_RANGE_VECTOR_TIMEWINDOW
from ai.backend.manager.pglock import PgAdvisoryLock

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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

_max_num_proc = os.cpu_count() or 8
_file_perm = (Path(__file__).parent.parent / "server.py").stat()


class DatabaseType(enum.StrEnum):
    postgresql = "postgresql"


class DatabaseConfig(BaseConfigSchema):
    type: Literal["postgresql"] = Field(
        default="postgresql",
        description="""
        Type of the database system to use.
        Currently, only PostgreSQL is supported as the main database backend.
        """,
        examples=["postgresql"],
    )
    addr: HostPortPair = Field(
        default=HostPortPair(host="127.0.0.1", port=5432),
        description="""
        Network address and port of the database server.
        Default is the standard PostgreSQL port on localhost.
        """,
    )
    name: str = Field(
        default="DB_NAME",
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
        default="DB_USER",
        description="""
        Username for authenticating with the database.
        This user must have sufficient privileges for all database operations.
        """,
        examples=["postgres"],
    )
    password: Optional[str] = Field(
        default=None,
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
        validation_alias=AliasChoices("pool-size", "pool_size"),
        serialization_alias="pool-size",
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
        validation_alias=AliasChoices("pool-recycle", "pool_recycle"),
        serialization_alias="pool-recycle",
    )
    pool_pre_ping: bool = Field(
        default=False,
        description="""
        Whether to test connections with a lightweight ping before using them.
        Helps detect stale connections before they cause application errors.
        Adds a small overhead but improves reliability.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("pool-pre-ping", "pool_pre_ping"),
        serialization_alias="pool-pre-ping",
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
        validation_alias=AliasChoices("max-overflow", "max_overflow"),
        serialization_alias="max-overflow",
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
        validation_alias=AliasChoices("lock-conn-timeout", "lock_conn_timeout"),
        serialization_alias="lock-conn-timeout",
    )


class EventLoopType(enum.StrEnum):
    asyncio = "asyncio"
    uvloop = "uvloop"


class DistributedLockType(enum.StrEnum):
    filelock = "filelock"
    pg_advisory = "pg_advisory"
    redlock = "redlock"
    etcd = "etcd"
    etcetra = "etcetra"


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


class AuthConfig(BaseConfigSchema):
    max_password_age: Optional[TimeDuration] = Field(
        default=None,
        description="""
        Maximum password age before requiring a change.
        Format is a duration string like "90d" for 90 days.
        Set to None to disable password expiration.
        """,
        examples=[None, "90d", "180d"],
        validation_alias=AliasChoices("max_password_age", "max-password-age"),
        serialization_alias="max_password_age",
    )
    password_hash_algorithm: PasswordHashAlgorithm = Field(
        default=PasswordHashAlgorithm.PBKDF2_SHA256,
        description="""
        The password hashing algorithm to use for new passwords.
        Supported algorithms: bcrypt, sha256, sha3_256, pbkdf2_sha256, pbkdf2_sha3_256.
        Existing passwords with different algorithms will be gradually migrated.
        """,
        examples=[
            PasswordHashAlgorithm.BCRYPT,
            PasswordHashAlgorithm.SHA256,
            PasswordHashAlgorithm.SHA3_256,
            PasswordHashAlgorithm.PBKDF2_SHA256,
            PasswordHashAlgorithm.PBKDF2_SHA3_256,
        ],
        validation_alias=AliasChoices("password-hash-algorithm", "password_hash_algorithm"),
        serialization_alias="password-hash-algorithm",
    )
    password_hash_rounds: int = Field(
        default=600_000,
        ge=1,
        le=2_000_000,
        description="""
        The number of rounds (iterations) for the password hashing algorithm.
        Higher values are more secure but slower.
        - bcrypt: valid range is 4-31 (will be automatically capped at 31)
        - pbkdf2_sha256: recommended 100,000+ (default 100,000)
        - sha256/sha3_256: any positive integer (100,000 may be too high for these)
        The value will be automatically adjusted to fit the algorithm's constraints.
        """,
        examples=[12, 100_000, 600_000],
        validation_alias=AliasChoices("password-hash-rounds", "password_hash_rounds"),
        serialization_alias="password-hash-rounds",
    )
    password_hash_salt_size: int = Field(
        default=32,
        ge=16,
        le=256,
        description="""
        The size of the salt in bytes for password hashing.
        Larger salts provide better protection against rainbow table attacks.
        - Minimum: 16 bytes (128 bits)
        - Default: 32 bytes (256 bits) - recommended for most use cases
        - Maximum: 256 bytes (2048 bits)
        Note: bcrypt manages its own salt internally, so this setting doesn't apply to bcrypt.
        """,
        examples=[16, 32, 64],
        validation_alias=AliasChoices("password-hash-salt-size", "password_hash_salt_size"),
        serialization_alias="password-hash-salt-size",
    )


class ManagerConfig(BaseConfigSchema):
    ipc_base_path: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
        description="""
        Base directory path for inter-process communication files.
        Used for Unix domain sockets and other IPC mechanisms.
        This directory must be writable by the manager process.
        In production, consider using /var/run/backend.ai/ipc instead.
        """,
        examples=["/var/run/backend.ai/ipc"],
        validation_alias=AliasChoices("ipc-base-path", "ipc_base_path"),
        serialization_alias="ipc-base-path",
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
        validation_alias=AliasChoices("num-proc", "num_proc"),
        serialization_alias="num-proc",
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
        default=HostPortPair(host="0.0.0.0", port=8080),
        description="""
        Network address and port where the manager service will listen.
        Default is all interfaces (0.0.0.0) on port 8080.
        For private deployments, consider using 127.0.0.1 instead.
        """,
        validation_alias=AliasChoices("service-addr", "service_addr"),
        serialization_alias="service-addr",
    )
    announce_addr: HostPortPair = Field(
        default=HostPortPair(host="127.0.0.1", port=5432),
        description="""
        Address and port to announce to other components.
        This is used for service discovery and should be accessible by other components.
        """,
        alias="announce-addr",
    )
    announce_internal_addr: HostPortPair = Field(
        default=HostPortPair(host="host.docker.internal", port=18080),
        description="""
        Address and port to announce for internal API requests.
        This is used for service discovery and should be accessible by other components.
        """,
        alias="announce-internal-addr",
    )
    internal_addr: HostPortPair = Field(
        default=HostPortPair(host="0.0.0.0", port=18080),
        description="""
        Set the internal hostname/port to accept internal API requests.
        """,
        validation_alias=AliasChoices("internal-addr", "internal_addr"),
        serialization_alias="internal-addr",
    )
    rpc_auth_manager_keypair: Path = Field(
        default=Path("fixtures/manager/manager.key_secret"),
        description="""
        Path to the keypair file used for RPC authentication.
        This file contains key pairs used for secure communication between manager components.
        In production, should be stored in a secure location with restricted access.
        """,
        validation_alias=AliasChoices("rpc-auth-manager-keypair", "rpc_auth_manager_keypair"),
        serialization_alias="rpc-auth-manager-keypair",
    )
    heartbeat_timeout: float = Field(
        default=40.0,
        ge=1.0,
        description="""
        Timeout in seconds for agent heartbeat checks.
        If an agent doesn't respond within this time, it's considered offline.
        Should be set higher than the agent's heartbeat interval.
        """,
        validation_alias=AliasChoices("heartbeat-timeout", "heartbeat_timeout"),
        serialization_alias="heartbeat-timeout",
    )
    # TODO: Don't use this. Change to use KMS.
    secret: str = Field(
        default_factory=lambda: secrets.token_urlsafe(16),
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
        validation_alias=AliasChoices("ssl-enabled", "ssl_enabled"),
        serialization_alias="ssl-enabled",
    )
    ssl_cert: Optional[FilePath] = Field(
        default=None,
        description="""
        Path to the SSL certificate file.
        Required if `ssl_enabled` is True.
        Should be a PEM-formatted certificate file, either self-signed or from a CA.
        """,
        examples=["fixtures/manager/manager.crt"],
        validation_alias=AliasChoices("ssl-cert", "ssl_cert"),
        serialization_alias="ssl-cert",
    )
    ssl_privkey: Optional[str] = Field(
        default=None,
        description="""
        Path to the SSL private key file.
        Required if `ssl_enabled` is True.
        Should be a PEM-formatted private key corresponding to the certificate.
        """,
        examples=["fixtures/manager/manager.key"],
        validation_alias=AliasChoices("ssl-privkey", "ssl_privkey"),
        serialization_alias="ssl-privkey",
    )
    event_loop: EventLoopType = Field(
        default=EventLoopType.asyncio,
        description="""
        Event loop implementation to use.
        'asyncio' is the Python standard library implementation.
        'uvloop' is a faster alternative but may have compatibility issues with some libraries.
        """,
        examples=[item.value for item in EventLoopType],
        validation_alias=AliasChoices("event-loop", "event_loop"),
        serialization_alias="event-loop",
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
        validation_alias=AliasChoices("distributed-lock", "distributed_lock"),
        serialization_alias="distributed-lock",
    )
    pg_advisory_config: Mapping[str, Any] = Field(
        default=PgAdvisoryLock.default_config,
        description="""
        Configuration for PostgreSQL advisory locks.
        This is used when distributed_lock is set to pg_advisory.
        """,
        examples=[{}],
        validation_alias=AliasChoices("pg-advisory-config", "pg_advisory_config"),
        serialization_alias="pg-advisory-config",
    )
    filelock_config: Mapping[str, Any] = Field(
        default=FileLock.default_config,
        description="""
        Configuration for file-based locks.
        This is used when distributed_lock is set to filelock.
        """,
        examples=[{}],
        validation_alias=AliasChoices("filelock-config", "filelock_config"),
        serialization_alias="filelock-config",
    )
    redlock_config: Mapping[str, Any] = Field(
        default=RedisLock.default_config,
        description="""
        Configuration for Redis-based distributed locking.
        This is used when distributed_lock is set to redlock.
        """,
        examples=[{"lock_retry_interval": 1.0}],
        validation_alias=AliasChoices("redlock-config", "redlock_config"),
        serialization_alias="redlock-config",
    )
    etcdlock_config: Mapping[str, Any] = Field(
        default=EtcdLock.default_config,
        description="""
        Configuration for etcd-based distributed locking.
        This is used when distributed_lock is set to etcd.
        """,
        examples=[{}],
        validation_alias=AliasChoices("etcdlock-config", "etcdlock_config"),
        serialization_alias="etcdlock-config",
    )
    session_schedule_lock_lifetime: float = Field(
        default=30,
        description="""
        Maximum lifetime in seconds for session scheduling locks.
        If scheduling takes longer than this, locks will be automatically released.
        Prevents deadlocks in case a manager fails during scheduling.
        """,
        examples=[30.0, 60.0],
        validation_alias=AliasChoices(
            "session-schedule-lock-lifetime", "session_schedule_lock_lifetime"
        ),
        serialization_alias="session_schedule_lock_lifetime",
    )
    session_check_precondition_lock_lifetime: float = Field(
        default=30,
        description="""
        Maximum lifetime in seconds for session precondition check locks.
        Controls how long the manager can hold a lock while checking if a session can be created.
        Should be balanced to prevent both deadlocks and race conditions.
        """,
        examples=[30.0, 60.0],
        validation_alias=AliasChoices(
            "session-check-precondition-lock-lifetime",
            "session_check_precondition_lock_lifetime",
        ),
        serialization_alias="session_check_precondition_lock_lifetime",
    )
    session_start_lock_lifetime: float = Field(
        default=30,
        description="""
        Maximum lifetime in seconds for session start locks.
        Controls how long the manager can hold a lock while starting a session.
        Longer values are safer but may block other managers longer on failure.
        """,
        examples=[30.0, 60.0],
        validation_alias=AliasChoices("session-start-lock-lifetime", "session_start_lock_lifetime"),
        serialization_alias="session_start_lock_lifetime",
    )
    pid_file: Path = Field(
        default=Path(os.devnull),
        description="""
        Path to the file where the manager process ID will be written.
        Useful for service management and monitoring.
        Set to /dev/null by default to disable this feature.
        """,
        examples=["/var/run/manager.pid"],
        validation_alias=AliasChoices("pid-file", "pid_file"),
        serialization_alias="pid-file",
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
        validation_alias=AliasChoices("allowed-plugins", "allowed_plugins"),
        serialization_alias="allowed-plugins",
    )
    disabled_plugins: Optional[set[str]] = Field(
        default=None,
        description="""
        List of plugins to explicitly disable.
        These plugins won't be loaded even if they're installed.
        Useful for disabling problematic or unwanted plugins without uninstalling them.
        """,
        examples=[["example.plugin.what.you.want"]],
        validation_alias=AliasChoices("disabled-plugins", "disabled_plugins"),
        serialization_alias="disabled-plugins",
    )
    hide_agents: bool = Field(
        default=False,
        description="""
        Whether to hide detailed agent information in API responses.
        When enabled, agent details are obscured in user-facing APIs.
        Useful for security in multi-tenant environments.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("hide-agents", "hide_agents"),
        serialization_alias="hide-agents",
    )
    agent_selection_resource_priority: list[str] = Field(
        default=["cuda", "rocm", "tpu", "cpu", "mem"],
        description="""
        Priority order for resources when selecting agents for compute sessions.
        Determines which resources are considered more important during scheduling.
        Default prioritizes GPU resources (CUDA, ROCm) over CPU and memory.
        """,
        examples=[["cuda", "rocm", "tpu", "cpu", "mem"]],
        validation_alias=AliasChoices(
            "agent-selection-resource-priority", "agent_selection_resource_priority"
        ),
        serialization_alias="agent-selection-resource-priority",
    )
    importer_image: str = Field(
        default="lablup/importer:manylinux2010",
        description="""
        Deprecated: Container image used for the importer service.
        The importer handles tasks like installing additional packages.
        Should be compatible with the Backend.AI environment.
        """,
        examples=["lablup/importer:manylinux2010"],
        validation_alias=AliasChoices("importer-image", "importer_image"),
        serialization_alias="importer-image",
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
        validation_alias=AliasChoices("max-wsmsg-size", "max_wsmsg_size"),
        serialization_alias="max-wsmsg-size",
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
        validation_alias=AliasChoices("aiomonitor-port", "aiomonitor_port"),
        serialization_alias="aiomonitor-port",
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
        validation_alias=AliasChoices("aiomonitor-termui-port", "aiomonitor_termui_port"),
        serialization_alias="aiomonitor-termui-port",
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
        validation_alias=AliasChoices("aiomonitor-webui-port", "aiomonitor_webui_port"),
        serialization_alias="aiomonitor-webui-port",
    )
    use_experimental_redis_event_dispatcher: bool = Field(
        default=False,
        description="""
        Whether to use the experimental Redis-based event dispatcher.
        May provide better performance for event handling in large clusters.
        Not recommended for production use unless specifically needed.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "use-experimental-redis-event-dispatcher", "use_experimental_redis_event_dispatcher"
        ),
        serialization_alias="use-experimental-redis-event-dispatcher",
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
        validation_alias=AliasChoices("status-update-interval", "status_update_interval"),
        serialization_alias="status-update-interval",
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
        validation_alias=AliasChoices("status-lifetime", "status_lifetime"),
        serialization_alias="status-lifetime",
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
        validation_alias=AliasChoices("public-metrics-port", "public_metrics_port"),
        serialization_alias="public-metrics-port",
    )
    use_sokovan: bool = Field(
        default=True,
        description="""
        Whether to use the Sokovan orchestrator for session scheduling.
        When enabled, uses the new Sokovan orchestrator for improved scheduling performance.
        When disabled, falls back to the legacy scheduling system.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("use-sokovan", "use_sokovan"),
        serialization_alias="use-sokovan",
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

    @field_validator("rpc_auth_manager_keypair", mode="before")
    @classmethod
    def _parse_rpc_auth_manager_keypair(cls, v: str) -> str:
        if not Path(v).exists():
            log.warning(
                f'RPC authentication keypair file does not exist: "{v}".',
            )
        return v


# Deprecated: v20.09
class DockerRegistryConfig(BaseConfigSchema):
    ssl_verify: bool = Field(
        default=True,
        description="""
        Deprecated: Whether to verify SSL certificates when connecting to Docker registries.
        Disabling this is not recommended except for testing with self-signed certificates.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("ssl-verify", "ssl_verify"),
        serialization_alias="ssl-verify",
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
        This name will identify this manager instance in Pyroscope UI.
        Required if Pyroscope is enabled.
        """,
        examples=["backendai-half-manager"],
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


class SMTPReporterConfig(BaseConfigSchema):
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
        validation_alias=AliasChoices("use-tls", "use_tls"),
        serialization_alias="use-tls",
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
        validation_alias=AliasChoices("max-workers", "max_workers"),
        serialization_alias="max-workers",
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
        validation_alias=AliasChoices("trigger-policy", "trigger_policy"),
        serialization_alias="trigger-policy",
    )


class ActionMonitorsConfig(BaseConfigSchema):
    subscribed_actions: list[str] = Field(
        default=[],
        description="""
        List of action types to subscribe to for monitoring.
        """,
        examples=[["session:create_from_params", "session:create_cluster"]],
        validation_alias=AliasChoices("subscribed-actions", "subscribed_actions"),
        serialization_alias="subscribed-actions",
    )
    reporter: str = Field(
        description="""
        Name of the reporter to use for sending notifications.
        This should match the name of a configured reporter.
        """,
        examples=["smtp", "audit_log"],
    )


class ReporterConfig(BaseConfigSchema):
    smtp: list[SMTPReporterConfig] = Field(
        default=[],
        description="""
        SMTP reporter configuration.
        Controls how email notifications are sent.
        Includes settings for SMTP server, authentication, and email templates.
        """,
    )
    action_monitors: list[ActionMonitorsConfig] = Field(
        default=[],
        description="""
        Action monitors configuration.
        Each reporter can be configured to subscribe to specific actions.
        """,
        validation_alias=AliasChoices("action-monitors", "action_monitors"),
        serialization_alias="action-monitors",
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
        validation_alias=AliasChoices(
            "enhanced-aiomonitor-task-info", "enhanced_aiomonitor_task_info"
        ),
        serialization_alias="enhanced-aiomonitor-task-info",
    )
    log_events: bool = Field(
        default=False,
        description="""
        Whether to log all internal events.
        When enabled, all events passing through the system will be logged.
        Very verbose, but useful for debugging event-related issues.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("log-events", "log_events"),
        serialization_alias="log-events",
    )
    log_scheduler_ticks: bool = Field(
        default=False,
        description="""
        Whether to log scheduler ticks.
        Provides detailed logs about the scheduler's internal operations.
        Useful for debugging scheduling issues, but generates many log entries.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("log-scheduler-ticks", "log_scheduler_ticks"),
        serialization_alias="log-scheduler-ticks",
    )
    periodic_sync_stats: bool = Field(
        default=False,
        description="""
        Whether to periodically synchronize and log system statistics.
        When enabled, regularly collects and logs performance metrics.
        Helpful for monitoring system behavior over time.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("periodic-sync-stats", "periodic_sync_stats"),
        serialization_alias="periodic-sync-stats",
    )


class SystemConfig(BaseConfigSchema):
    timezone: TimeZone = Field(
        default_factory=lambda: timezone.utc,
        description="""
        Timezone setting for the manager.
        Uses pytz-compatible timezone names.
        """,
        examples=["UTC"],
    )


class ResourcesConfig(BaseConfigSchema):
    group_resource_visibility: bool = Field(
        default=False,
        description="""
        Whether to return group resource status in check-presets.
        If true, group resources are visible to all users in the group.
        """,
        examples=[True, False],
    )


class APIConfig(BaseConfigSchema):
    allow_origins: str = Field(
        default="*",
        description="""
        CORS allow-origins setting.
        Use '*' to allow all origins, or specify comma-separated domain patterns.
        Important for browser-based clients connecting to the API.
        """,
        examples=["*", "https://example.com"],
        validation_alias=AliasChoices("allow_origins", "allow-origins"),
        serialization_alias="allow-origins",
    )
    allow_graphql_schema_introspection: bool = Field(
        default=False,
        description="""
        Whether to allow GraphQL schema introspection.
        Useful for development and debugging, but should be disabled in production.
        When disabled, GraphQL tools like GraphiQL won't be able to explore the schema.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "allow_graphql_schema_introspection", "allow-graphql-schema-introspection"
        ),
        serialization_alias="allow-graphql-schema-introspection",
    )
    allow_openapi_schema_introspection: bool = Field(
        default=False,
        description="""
        Whether to allow OpenAPI schema introspection.
        Useful for development and debugging, but should be disabled in production.
        When disabled, Swagger UI and similar tools won't work.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "allow_openapi_schema_introspection", "allow-openapi-schema-introspection"
        ),
        serialization_alias="allow-openapi-schema-introspection",
    )
    max_gql_query_depth: Optional[int] = Field(
        default=None,
        ge=1,
        description="""
        Maximum depth of GraphQL queries allowed.
        Limits the complexity of queries to prevent abuse.
        Set to None to disable the limit.
        """,
        examples=[None, 10, 15],
        validation_alias=AliasChoices("max_gql_query_depth", "max-gql-query-depth"),
        serialization_alias="max-gql-query-depth",
    )
    max_gql_connection_page_size: Optional[int] = Field(
        default=None,
        ge=1,
        description="""
        Maximum page size for GraphQL connection fields.
        Controls how many items can be retrieved in a single request.
        Set to None to use the default page size.
        """,
        examples=[None, 100, 500],
        validation_alias=AliasChoices(
            "max_gql_connection_page_size", "max-gql-connection-page-size"
        ),
        serialization_alias="max-gql-connection-page-size",
    )
    resources: Optional[ResourcesConfig] = Field(
        default=None,
        description="""
        Resource visibility settings.
        Controls how resources are shared and visible between users and groups.
        """,
        examples=[None, {"group_resource_visibility": True}],
    )


class DockerImageAutoPullPolicy(enum.StrEnum):
    digest = "digest"
    tag = "tag"
    none = "none"


class DockerImageConfig(BaseConfigSchema):
    auto_pull: DockerImageAutoPullPolicy = Field(
        default=DockerImageAutoPullPolicy.digest,
        description="""
        Policy for automatically pulling Docker images.
        'digest': Pull if image digest has changed (most secure)
        'tag': Pull if image tag has changed
        'none': Never pull automatically (manual control)
        """,
        examples=[item.value for item in DockerImageAutoPullPolicy],
        validation_alias=AliasChoices("auto_pull", "auto-pull"),
        serialization_alias="auto_pull",
    )


class DockerConfig(BaseConfigSchema):
    image: DockerImageConfig = Field(
        default_factory=DockerImageConfig,
        description="""
        Docker image management settings.
        Controls how the manager handles Docker images.
        """,
    )


class PluginsConfig(BaseConfigSchema):
    accelerator: dict[str, Any] = Field(
        default_factory=dict,
        description="""
        Accelerator plugin configurations.
        Settings for GPU, TPU, and other acceleration devices.
        Specific configuration depends on installed plugins.
        """,
        examples=[{"cuda": {}}],
    )
    scheduler: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="""
        Scheduler plugin configurations.
        Controls how compute sessions are scheduled across agents.
        Examples include FIFO, LIFO, DRF schedulers.
        """,
        examples=[{"fifo": {"num_retries_to_skip": 3}}],
    )
    agent_selector: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="""
        Agent selector plugin configurations.
        Controls how agents are selected for compute sessions.
        Can implement various selection strategies based on load, resource availability, etc.
        """,
        examples=[{}],
        validation_alias=AliasChoices("agent_selector", "agent-selector"),
        serialization_alias="agent-selector",
    )
    network: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="""
        Network plugin configurations.
        """,
        examples=[{"overlay": {"mtu": 1500}}],
    )


class InterContainerNetworkConfig(BaseConfigSchema):
    default_driver: Optional[str] = Field(
        default="overlay",
        description="""
        Default network driver for inter-container communication.
        'overlay' is typically used for multi-host networking.
        Container communication performance depends on this setting.
        """,
        examples=["overlay", None],
        validation_alias=AliasChoices("default_driver", "default-driver"),
        serialization_alias="default-driver",
    )
    # TODO: Write description
    enabled: bool = Field(
        default=False,
        description="""
        """,
        examples=[True, False],
    )
    # TODO: Write description
    # Need to investigate what kind of setting or type it is.
    plugin: Optional[Any] = Field(
        default=None,
        description="""
        """,
    )


class SubnetNetworkConfig(BaseConfigSchema):
    agent: IPvAnyNetwork = Field(
        default=IPv4Network("0.0.0.0/0"),
        description="""
        IP subnet for agent communications.
        Specifies which subnet is used for agent-to-agent and agent-to-manager traffic.
        Use 0.0.0.0/0 to allow all IPv4 addresses.
        """,
        examples=["0.0.0.0/0", "192.168.0.0/24"],
    )
    container: IPvAnyNetwork = Field(
        default=IPv4Network("0.0.0.0/0"),
        description="""
        IP subnet for containers.
        Specifies which subnet is used for container networks.
        Use 0.0.0.0/0 to allow all IPv4 addresses.
        """,
        examples=["0.0.0.0/0", "172.17.0.0/16"],
    )


class RpcConfig(BaseConfigSchema):
    keepalive_timeout: float = Field(
        default=60.0,
        # TODO: Write description
        description="""
        """,
        examples=[60.0, 120.0],
        validation_alias=AliasChoices("keepalive_timeout", "keepalive-timeout"),
        serialization_alias="keepalive-timeout",
    )


class NetworkConfig(BaseConfigSchema):
    inter_container: InterContainerNetworkConfig = Field(
        default_factory=InterContainerNetworkConfig,
        description="""
        Settings for networks between containers.
        Controls how containers communicate with each other.
        """,
        validation_alias=AliasChoices("inter_container", "inter-container"),
        serialization_alias="inter-container",
    )
    subnet: SubnetNetworkConfig = Field(
        default_factory=SubnetNetworkConfig,
        description="""
        Subnet configurations for the Backend.AI network.
        Defines IP ranges for agents and containers.
        """,
    )
    rpc: RpcConfig = Field(
        default_factory=RpcConfig,
        description="""
        """,
    )


class WatcherConfig(BaseConfigSchema):
    token: Optional[str] = Field(
        default=None,
        description="""
        Authentication token for the watcher service.
        Used to secure communication between manager and watcher.
        Should be a secure random string in production.
        """,
        examples=[None, "random-secure-token"],
    )
    file_io_timeout: float = Field(
        default=DEFAULT_FILE_IO_TIMEOUT,
        description="""
        Timeout in seconds for file I/O operations in watcher.
        Controls how long the watcher waits for file operations to complete.
        Increase for handling large files or slow storage systems.
        """,
        examples=[60.0, 120.0],
        validation_alias=AliasChoices("file_io_timeout", "file-io-timeout"),
        serialization_alias="file-io-timeout",
    )


class HangToleranceThresholdConfig(BaseConfigSchema):
    PREPARING: Optional[datetime] = Field(
        default=None,
        description="""
        Maximum time a session can stay in PREPARING state before considered hung.
        Format is a duration string like "10m" for 10 minutes.
        Controls when the system will attempt recovery actions.
        """,
        examples=[None, "10m", "30m"],
    )
    TERMINATING: Optional[datetime] = Field(
        default=None,
        description="""
        Maximum time a session can stay in TERMINATING state before considered hung.
        Format is a duration string like "10m" for 10 minutes.
        Controls when the system will force-terminate the session.
        """,
        examples=[None, "10m", "30m"],
    )


class HangToleranceConfig(BaseConfigSchema):
    threshold: HangToleranceThresholdConfig = Field(
        default_factory=HangToleranceThresholdConfig,
        description="""
        Threshold settings for detecting hung sessions.
        Defines timeouts for different session states.
        """,
    )


class SessionConfig(BaseConfigSchema):
    hang_tolerance: HangToleranceConfig = Field(
        default_factory=HangToleranceConfig,
        description="""
        Configuration for detecting and handling hung sessions.
        Controls how the system detects and recovers from session failures.
        """,
        validation_alias=AliasChoices("hang_tolerance", "hang-tolerance"),
        serialization_alias="hang-tolerance",
    )


class MetricConfig(BaseConfigSchema):
    address: HostPortPair = Field(
        default=HostPortPair(host="127.0.0.1", port=9090),
        description="""
        Address for the metric collection service.
        """,
        alias="addr",
    )
    timewindow: str = Field(
        default=DEFAULT_METRIC_RANGE_VECTOR_TIMEWINDOW,
        description="""
        Time window for metric collection.
        Controls how often metrics are collected and reported.
        Format is a duration string like "1h" for 1 hour.
        """,
        examples=["1m", "1h"],
    )

    @field_serializer("address")
    def _serialize_addr(self, addr: Optional[HostPortPair], _info: Any) -> Optional[str]:
        return None if addr is None else f"{addr.host}:{addr.port}"


class IdleCheckerConfig(BaseConfigSchema):
    enabled: str = Field(
        default="",
        description="""
        Enabled idle checkers.
        Comma-separated list of checker names.
        """,
        examples=["network_timeout", "utilization"],
    )
    app_streaming_packet_timeout: TimeDuration = Field(
        default=_TimeDurationPydanticAnnotation.time_duration_validator("5m"),
        description="""
        Timeout for app-streaming TCP connections.
        Controls how long the system waits before considering a connection idle.
        """,
        examples=["5m", "10m"],
        validation_alias=AliasChoices(
            "app_streaming_packet_timeout", "app-streaming-packet-timeout"
        ),
        serialization_alias="app_streaming_packet_timeout",
    )
    checkers: dict[str, Any] = Field(
        default_factory=dict,
        description="""
        Idle checkers configurations.
        """,
        examples=[
            {
                "network_timeout": {
                    "threshold": "10m",
                },
                "utilization": {
                    "resource-thresholds": {
                        "cpu_util": {
                            "average": 30,
                        },
                        "mem": {
                            "average": 30,
                        },
                        "cuda_util": {
                            "average": 30,
                        },
                        "cuda_mem": {
                            "average": 30,
                        },
                    }
                },
                "thresholds-check-operator": "and",
                "time-window": "12h",
                "initial-grace-period": "5m",
            }
        ],
    )


class VolumeTypeConfig(BaseConfigSchema):
    user: Optional[dict[str, Any] | str] = Field(
        default=None,
        description="""
        User VFolder type configuration.
        When present, enables user-owned virtual folders.
        Standard folder type for individual users.
        """,
    )
    group: Optional[dict[str, Any] | str] = Field(
        default=None,
        description="""
        Group VFolder type configuration.
        When present, enables group-owned virtual folders.
        Used for sharing files within a group of users.
        """,
    )


class VolumeProxyConfig(BaseConfigSchema):
    client_api: str = Field(
        description="""
        Client-facing API endpoint URL of the volume proxy.
        Used by clients to access virtual folder contents.
        Should include protocol, host and port.
        """,
        examples=["http://localhost:6021", "https://proxy1.example.com:6021"],
        validation_alias=AliasChoices("client_api", "client-api"),
        serialization_alias="client_api",
    )
    manager_api: str = Field(
        description="""
        Manager-facing API endpoint URL of the volume proxy.
        Used by manager to communicate with the volume proxy.
        Should include protocol, host and port.
        """,
        examples=["http://localhost:6022", "https://proxy1.example.com:6022"],
        validation_alias=AliasChoices("manager_api", "manager-api"),
        serialization_alias="manager_api",
    )
    secret: str = Field(
        description="""
        Secret key for authenticating with the volume proxy manager API.
        Must match the secret configured on the volume proxy.
        Should be kept secure and not exposed to clients.
        """,
        examples=["some-secret-key"],
    )
    ssl_verify: bool = Field(
        default=True,
        description="""
        Whether to verify SSL certificates when connecting to the volume proxy.
        Should be enabled in production for security.
        Can be disabled for testing with self-signed certificates.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("ssl_verify", "ssl-verify"),
        serialization_alias="ssl_verify",
    )
    sftp_scaling_groups: Optional[CommaSeparatedStrList] = Field(
        default=None,
        description="""
        List of SFTP scaling groups that the volume is mapped to.
        Controls which scaling groups can create SFTP sessions for this volume.
        """,
        examples=["group-1,group-2"],
        validation_alias=AliasChoices("sftp_scaling_groups", "sftp-scaling-groups"),
        serialization_alias="sftp_scaling_groups",
    )


class VolumesConfig(BaseConfigSchema):
    types: VolumeTypeConfig = Field(
        default_factory=lambda: VolumeTypeConfig(user={}),
        description="""
        Defines which types of virtual folders are enabled.
        Contains configuration for user and group folders.
        """,
        examples=[{"user": {}, "group": {}}],
        alias="_types",
    )
    default_host: Optional[str] = Field(
        default=None,
        description="""
        Default volume host for new virtual folders.
        Format is "proxy_name:volume_name".
        Used when user doesn't explicitly specify a host.
        """,
        examples=["localhost:6021", "local:default", "nas:main-volume"],
        validation_alias=AliasChoices("default_host", "default-host"),
        serialization_alias="default_host",
    )
    exposed_volume_info: CommaSeparatedStrList = Field(
        default_factory=lambda: CommaSeparatedStrList("percentage"),
        description="""
        Controls what volume information is exposed to users.
        Options include "percentage" for disk usage percentage.
        """,
        examples=["percentage", "percentage,bytes"],
        validation_alias=AliasChoices("exposed_volume_info", "exposed-volume-info"),
        serialization_alias="exposed_volume_info",
    )
    proxies: dict[str, VolumeProxyConfig] = Field(
        default_factory=dict,
        description="""
        Mapping of volume proxy configurations.
        Each key is a proxy name used in volume host references.
        """,
        examples=[
            {
                "local": {
                    "client_api": "http://localhost:6021",
                    "manager_api": "http://localhost:6022",
                    "secret": "some-secret",
                    "ssl_verify": True,
                }
            }
        ],
    )


# TODO: Make this more precise type
class ResourceSlotsConfig(BaseConfigSchema):
    model_config = ConfigDict(
        extra="allow",
    )


class OTELConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="""
        Whether to enable OpenTelemetry for tracing or logging.
        When enabled, traces or log will be collected and sent to the configured OTLP endpoint.
        """,
        examples=[True, False],
    )
    log_level: str = Field(
        default="INFO",
        description="""
        Log level for OpenTelemetry.
        Controls the verbosity of logs generated by OpenTelemetry.
        Common levels include 'debug', 'info', 'warn', 'error'.
        """,
        examples=["INFO", "DEBUG", "WARN", "ERROR", "TRACE"],
        alias="log-level",
    )
    endpoint: str = Field(
        default="http://localhost:4317",
        description="""
        OTLP endpoint for sending traces.
        Should include the host and port of the OTLP receiver.
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


class ReservoirObjectStorageConfig(BaseConfigSchema):
    storage_type: Literal["object_storage"] = Field(
        default="object_storage",
        description="""
        Type of the storage configuration.
        This is used to identify the specific storage type.
        """,
        alias="type",
    )
    bucket_name: str = Field(
        default="OBJECT_STORAGE_BUCKET_NAME",
        description="""
        Name of the bucket to use for the reservoir.
        """,
        examples=["minio-bucket"],
        validation_alias=AliasChoices("bucket-name", "bucket_name"),
        serialization_alias="bucket-name",
    )


StorageSpecificConfig = Union[ReservoirObjectStorageConfig]


class ReservoirConfig(BaseConfigSchema):
    enable_approve_process: bool = Field(
        default=False,
        description="""
        Whether to enable the approval process for artifact uploads.
        When enabled, artifacts require approval before being available.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("enable-approve-process", "enable_approve_process"),
        serialization_alias="enable-approve-process",
    )
    is_delegation_leaf: bool = Field(
        default=False,
        description="""
        Whether this reservoir is a leaf in a delegation hierarchy.
        If true, it cannot delegate to other reservoirs.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("is-delegation-leaf", "is_delegation_leaf"),
        serialization_alias="is-delegation-leaf",
    )
    storage_name: str = Field(
        default="RESERVOIR_STORAGE_NAME",
        description="""
        Name of the reservoir storage configuration.
        Used to identify this storage in the system.
        """,
        examples=["minio-storage", "gitlfs-storage", "vfs-storage"],
        validation_alias=AliasChoices("storage-name", "storage_name"),
        serialization_alias="storage-name",
    )
    config: StorageSpecificConfig = Field(
        default_factory=ReservoirObjectStorageConfig,
        discriminator="storage_type",
        description="""
        Configuration for the storage.
        """,
    )


class ModelRegistryConfig(BaseConfigSchema):
    model_registry: str = Field(
        default="MODEL_REGISTRY_NAME",
        description="""
        Name of the Model registry configuration.
        Used to identify this registry in the system.
        """,
        examples=["model-registry"],
        validation_alias=AliasChoices("model-registry", "model_registry"),
        serialization_alias="model-registry",
    )


class ManagerUnifiedConfig(BaseConfigSchema):
    # From legacy local config
    db: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="""
        Database configuration settings.
        Defines how the manager connects to its PostgreSQL database.
        Contains connection details, credentials, and pool settings.
        """,
    )
    etcd: EtcdConfig = Field(
        default_factory=EtcdConfig,
        description="""
        Etcd configuration settings.
        Used for distributed coordination between manager instances.
        Contains connection details and authentication information.
        """,
    )
    manager: ManagerConfig = Field(
        default_factory=ManagerConfig,
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
        validation_alias=AliasChoices("docker_registry", "docker-registry"),
        serialization_alias="docker-registry",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="""
        Logging system configuration.
        Controls how logs are formatted, filtered, and stored.
        Detailed configuration is handled in ai.backend.logging.
        """,
    )
    pyroscope: PyroscopeConfig = Field(
        default_factory=PyroscopeConfig,
        description="""
        Pyroscope profiling configuration.
        Controls integration with the Pyroscope performance profiling tool.
        Used for monitoring and analyzing application performance.
        """,
    )
    debug: DebugConfig = Field(
        default_factory=DebugConfig,
        description="""
        Debugging options configuration.
        Controls various debugging features and tools.
        Should typically be disabled in production environments.
        """,
    )
    reporter: ReporterConfig = Field(
        default_factory=ReporterConfig,
        description="""
        Reporter configuration.
        Controls how notifications and logs are reported.
        Includes settings for Audit Logs, and Action Monitors, and SMTP reporters.
        Each reporter can be configured with its own settings.
        """,
    )

    # From legacy shared config
    system: SystemConfig = Field(
        default_factory=SystemConfig,
        description="""
        System-wide settings.
        Controls general behavior of the Backend.AI system.
        """,
    )
    api: APIConfig = Field(
        default_factory=APIConfig,
        description="""
        API server configuration.
        Controls how the API behaves, including security and limits.
        """,
    )
    redis: RedisConfig = Field(
        default_factory=RedisConfig,
        description="""
        Redis database configuration.
        Used for distributed caching and messaging between managers.
        """,
    )
    idle: IdleCheckerConfig = Field(
        default_factory=IdleCheckerConfig,
        description="""
        Idle session checker configuration.
        """,
    )
    docker: DockerConfig = Field(
        default_factory=DockerConfig,
        description="""
        Docker container settings.
        Controls how Docker images are managed and used.
        """,
    )
    plugins: PluginsConfig = Field(
        default_factory=PluginsConfig,
        description="""
        Plugin system configuration.
        Controls behavior of various Backend.AI plugins.
        """,
    )
    network: NetworkConfig = Field(
        default_factory=NetworkConfig,
        description="""
        Network configuration settings.
        Controls networking between containers and agents.
        """,
    )
    watcher: WatcherConfig = Field(
        default_factory=WatcherConfig,
        description="""
        Watcher service configuration.
        Controls the component that monitors compute sessions.
        """,
    )
    auth: AuthConfig = Field(
        default_factory=AuthConfig,
        description="""
        Authentication settings.
        Controls password policies and other security measures.
        """,
    )
    session: SessionConfig = Field(
        default_factory=SessionConfig,
        description="""
        Compute session configuration.
        Controls behavior and limits of compute sessions.
        """,
    )
    metric: MetricConfig = Field(
        default_factory=MetricConfig,
        description="""
        Metric collection settings.
        Controls how metrics are collected and reported.
        """,
    )
    volumes: VolumesConfig = Field(
        default_factory=VolumesConfig,
        description="""
        Volume management settings.
        Controls how volumes are managed and accessed.
        """,
    )
    resource_slots: ResourceSlotsConfig = Field(
        default_factory=ResourceSlotsConfig,
        description="""
        Resource slots configuration.
        Controls how resource slots are allocated and managed.
        """,
    )
    otel: OTELConfig = Field(
        default_factory=OTELConfig,
        description="""
        OpenTelemetry configuration.
        Controls how tracing and logging are handled with OpenTelemetry.
        """,
    )
    service_discovery: ServiceDiscoveryConfig = Field(
        default_factory=ServiceDiscoveryConfig,
        description="""
        Service discovery configuration.
        Controls how services are discovered and connected within the Backend.AI system.
        """,
    )
    artifact_registry: ModelRegistryConfig = Field(
        default_factory=ModelRegistryConfig,
        description="""
        Default artifact registry config.
        """,
        validation_alias=AliasChoices("artifact_registry", "artifact-registry"),
        serialization_alias="artifact-registry",
    )
    reservoir: ReservoirConfig = Field(
        default_factory=ReservoirConfig,
        description="""
        Reservoir configuration.
        """,
    )

    # TODO: Remove me after changing the method of loading the license server address in the plugins
    model_config = ConfigDict(
        extra="allow",
    )

    def __repr__(self):
        return pformat(self.model_dump())
