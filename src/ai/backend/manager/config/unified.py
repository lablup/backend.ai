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
     + jwt
       - secret-key: "..."                     # JWT signing secret key (min 32 chars)
       - algorithm: "HS256"                    # JWT signing algorithm (HS256, HS384, HS512)
       - token-expiration-seconds: 900         # JWT token TTL in seconds (default: 15min)
       - issuer: "backend.ai"                  # JWT issuer identifier (shared by manager & webserver)
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
from datetime import UTC, datetime
from ipaddress import IPv4Network
from pathlib import Path
from pprint import pformat
from typing import Annotated, Any, Literal

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
from ai.backend.common.configs.client import HttpTimeoutConfig
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.configs.jwt import SharedJWTConfig
from ai.backend.common.configs.otel import OTELConfig
from ai.backend.common.configs.pyroscope import PyroscopeConfig
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.configs.service_discovery import ServiceDiscoveryConfig
from ai.backend.common.data.storage.types import ArtifactStorageImportStep, NamedStorageTarget
from ai.backend.common.defs import DEFAULT_FILE_IO_TIMEOUT
from ai.backend.common.lock import EtcdLock, FileLock, RedisLock
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
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
try:
    _file_perm = (Path(__file__).parent.parent / "server.py").stat()
except FileNotFoundError:
    # Fallback for test environments where server.py is not present
    _file_perm = type("_FallbackPerm", (), {"st_uid": os.getuid(), "st_gid": os.getgid()})()


class DatabaseType(enum.StrEnum):
    postgresql = "postgresql"


class DatabaseConfig(BaseConfigSchema):
    type: Annotated[
        Literal["postgresql"],
        Field(default="postgresql"),
        BackendAIConfigMeta(
            description=(
                "Type of the database system to use. Currently, only PostgreSQL is supported "
                "as the main database backend for Backend.AI. PostgreSQL provides the ACID "
                "compliance and advanced features required for reliable session and resource management."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="postgresql", prod="postgresql"),
        ),
    ]
    addr: Annotated[
        HostPortPair,
        Field(default=HostPortPair(host="127.0.0.1", port=5432)),
        BackendAIConfigMeta(
            description=(
                "Network address and port of the PostgreSQL database server. "
                "Default is the standard PostgreSQL port (5432) on localhost. "
                "In production, point this to your database server or cluster endpoint."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="127.0.0.1:5432", prod="db.example.com:5432"),
        ),
    ]
    name: Annotated[
        str,
        Field(default="DB_NAME", min_length=2, max_length=64),
        BackendAIConfigMeta(
            description=(
                "Name of the PostgreSQL database to use for Backend.AI. "
                "This database must exist and be accessible by the configured user. "
                "The database should be created before starting the manager. "
                "Length must be between 2 and 64 characters due to PostgreSQL naming constraints."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="backend", prod="backend"),
        ),
    ]
    user: Annotated[
        str,
        Field(default="DB_USER"),
        BackendAIConfigMeta(
            description=(
                "Username for authenticating with the PostgreSQL database. "
                "This user must have sufficient privileges for all database operations "
                "including creating/dropping tables, indexes, and running migrations."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="postgres", prod="backend_user"),
        ),
    ]
    password: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Password for authenticating with the PostgreSQL database. "
                "Can be a direct password string or an environment variable reference. "
                "For security, using environment variables is strongly recommended in production."
            ),
            added_version="25.8.0",
            secret=True,
            example=ConfigExample(local="develove", prod="DB_PASSWORD"),
        ),
    ]
    pool_size: Annotated[
        int,
        Field(
            default=8,
            ge=1,
            validation_alias=AliasChoices("pool-size", "pool_size"),
            serialization_alias="pool-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Size of the SQLAlchemy database connection pool. "
                "Determines how many concurrent database connections to maintain. "
                "Should be tuned based on expected load, number of worker processes, "
                "and database server capacity. Higher values improve concurrency but consume more resources."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="8", prod="16"),
        ),
    ]
    pool_recycle: Annotated[
        float,
        Field(
            default=-1,
            ge=-1,
            validation_alias=AliasChoices("pool-recycle", "pool_recycle"),
            serialization_alias="pool-recycle",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum lifetime of a connection in seconds before it's recycled. "
                "Set to -1 to disable connection recycling. "
                "Useful for handling database connections closed by the server after inactivity "
                "or by network equipment with idle timeouts."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="-1", prod="3600"),
        ),
    ]
    pool_pre_ping: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("pool-pre-ping", "pool_pre_ping"),
            serialization_alias="pool-pre-ping",
        ),
        BackendAIConfigMeta(
            description=(
                "Whether to test connections with a lightweight ping before using them. "
                "Helps detect stale or disconnected connections before they cause application errors. "
                "Adds a small overhead per connection checkout but improves reliability. "
                "Recommended for production environments with network instability."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    max_overflow: Annotated[
        int,
        Field(
            default=64,
            ge=-1,
            validation_alias=AliasChoices("max-overflow", "max_overflow"),
            serialization_alias="max-overflow",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of additional connections to create beyond the pool_size. "
                "Set to -1 for unlimited overflow connections. "
                "These temporary connections are created when pool_size is insufficient "
                "and are closed when returned to the pool."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="64", prod="128"),
        ),
    ]
    lock_conn_timeout: Annotated[
        float,
        Field(
            default=0,
            ge=0,
            validation_alias=AliasChoices("lock-conn-timeout", "lock_conn_timeout"),
            serialization_alias="lock-conn-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for acquiring a connection from the pool. "
                "0 means wait indefinitely. "
                "If connections cannot be acquired within this time, an exception is raised. "
                "Set a reasonable value in production to prevent indefinite blocking."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="0", prod="30"),
        ),
    ]


class EventLoopType(enum.StrEnum):
    ASYNCIO = "asyncio"
    UVLOOP = "uvloop"


class DistributedLockType(enum.StrEnum):
    filelock = "filelock"
    pg_advisory = "pg_advisory"
    redlock = "redlock"
    etcd = "etcd"
    etcetra = "etcetra"


class AuthConfig(BaseConfigSchema):
    max_password_age: Annotated[
        TimeDuration | None,
        Field(
            default=None,
            validation_alias=AliasChoices("max_password_age", "max-password-age"),
            serialization_alias="max_password_age",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum password age before requiring users to change their password. "
                "Format is a duration string like '90d' for 90 days, '6m' for 6 months. "
                "Set to None to disable password expiration. "
                "Recommended for compliance with security policies."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="", prod="90d"),
        ),
    ]
    password_hash_algorithm: Annotated[
        PasswordHashAlgorithm,
        Field(
            default=PasswordHashAlgorithm.PBKDF2_SHA256,
            validation_alias=AliasChoices("password-hash-algorithm", "password_hash_algorithm"),
            serialization_alias="password-hash-algorithm",
        ),
        BackendAIConfigMeta(
            description=(
                "The password hashing algorithm to use for new passwords. "
                "Supported algorithms: bcrypt, sha256, sha3_256, pbkdf2_sha256, pbkdf2_sha3_256. "
                "PBKDF2_SHA256 is recommended for most deployments. "
                "Existing passwords with different algorithms will be gradually migrated on login."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="pbkdf2_sha256", prod="pbkdf2_sha256"),
        ),
    ]
    password_hash_rounds: Annotated[
        int,
        Field(
            default=600_000,
            ge=1,
            le=2_000_000,
            validation_alias=AliasChoices("password-hash-rounds", "password_hash_rounds"),
            serialization_alias="password-hash-rounds",
        ),
        BackendAIConfigMeta(
            description=(
                "The number of iterations for the password hashing algorithm. "
                "Higher values are more secure but slower. "
                "For bcrypt: valid range is 4-31 (auto-capped). "
                "For PBKDF2: recommended 100,000+ (default 600,000). "
                "The value is automatically adjusted to fit algorithm constraints."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="600000", prod="600000"),
        ),
    ]
    password_hash_salt_size: Annotated[
        int,
        Field(
            default=32,
            ge=16,
            le=256,
            validation_alias=AliasChoices("password-hash-salt-size", "password_hash_salt_size"),
            serialization_alias="password-hash-salt-size",
        ),
        BackendAIConfigMeta(
            description=(
                "The size of the salt in bytes for password hashing. "
                "Larger salts provide better protection against rainbow table attacks. "
                "Minimum: 16 bytes (128 bits), Default: 32 bytes (256 bits), Maximum: 256 bytes. "
                "Note: bcrypt manages its own salt internally, so this setting doesn't apply to bcrypt."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="32", prod="32"),
        ),
    ]


class ManagerConfig(BaseConfigSchema):
    ipc_base_path: Annotated[
        AutoDirectoryPath,
        Field(
            default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
            validation_alias=AliasChoices("ipc-base-path", "ipc_base_path"),
            serialization_alias="ipc-base-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Base directory path for inter-process communication files. "
                "Used for Unix domain sockets and other IPC mechanisms. "
                "This directory must be writable by the manager process. "
                "In production, consider using /var/run/backend.ai/ipc for better security."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="/tmp/backend.ai/ipc", prod="/var/run/backend.ai/ipc"),
        ),
    ]
    num_proc: Annotated[
        int,
        Field(
            default=_max_num_proc,
            ge=1,
            le=os.cpu_count(),
            validation_alias=AliasChoices("num-proc", "num_proc"),
            serialization_alias="num-proc",
        ),
        BackendAIConfigMeta(
            description=(
                "Number of worker processes to spawn for the manager. "
                "Defaults to the number of CPU cores available. "
                "For optimal performance, set this to match your CPU core count. "
                "Higher values improve request concurrency but consume more memory."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="4", prod="8"),
        ),
    ]
    id: Annotated[
        str,
        Field(default_factory=lambda: f"i-{socket.gethostname()}"),
        BackendAIConfigMeta(
            description=(
                "Unique identifier for this manager instance. "
                "Used to distinguish between multiple manager instances in a cluster. "
                "By default, uses the hostname with an 'i-' prefix. "
                "Must be unique across all managers in the same Backend.AI cluster."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="i-local-manager", prod="i-manager-01"),
        ),
    ]
    user: Annotated[
        UserID | None,
        Field(default=UserID(_file_perm.st_uid)),
        BackendAIConfigMeta(
            description=(
                "User ID (UID) under which the manager process runs. "
                "If not specified, defaults to the UID of the server.py file. "
                "Important for proper file permissions when creating files and sockets. "
                "Should match the user that owns the Backend.AI installation."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="1000", prod="1000"),
        ),
    ]
    group: Annotated[
        GroupID | None,
        Field(default=GroupID(_file_perm.st_gid)),
        BackendAIConfigMeta(
            description=(
                "Group ID (GID) under which the manager process runs. "
                "If not specified, defaults to the GID of the server.py file. "
                "Important for proper file permissions when creating files and sockets. "
                "Should match the group that owns the Backend.AI installation."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="1000", prod="1000"),
        ),
    ]
    service_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="0.0.0.0", port=8080),
            validation_alias=AliasChoices("service-addr", "service_addr"),
            serialization_alias="service-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Network address and port where the manager API service will listen. "
                "Default is all interfaces (0.0.0.0) on port 8080. "
                "For private deployments behind a load balancer, consider using 127.0.0.1. "
                "This is the main entry point for client API requests."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="0.0.0.0:8080", prod="0.0.0.0:8080"),
        ),
    ]
    announce_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="127.0.0.1", port=5432),
            alias="announce-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Address and port to announce to other Backend.AI components for service discovery. "
                "This should be the externally reachable address of this manager instance. "
                "Other components use this address to connect to the manager."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="127.0.0.1:8080", prod="manager.example.com:8080"),
        ),
    ]
    announce_internal_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="host.docker.internal", port=18080),
            alias="announce-internal-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Address and port to announce for internal API requests between Backend.AI components. "
                "Used for service discovery of internal endpoints. "
                "Should be accessible from containers and other internal services."
            ),
            added_version="25.8.0",
            example=ConfigExample(
                local="host.docker.internal:18080", prod="manager-internal:18080"
            ),
        ),
    ]
    internal_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="0.0.0.0", port=18080),
            validation_alias=AliasChoices("internal-addr", "internal_addr"),
            serialization_alias="internal-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Network address and port to accept internal API requests from other Backend.AI components. "
                "Internal APIs are used for inter-service communication and are not exposed to clients. "
                "Should be bound to an internal network interface in production."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="0.0.0.0:18080", prod="0.0.0.0:18080"),
        ),
    ]
    rpc_auth_manager_keypair: Annotated[
        Path,
        Field(
            default=Path("fixtures/manager/manager.key_secret"),
            validation_alias=AliasChoices("rpc-auth-manager-keypair", "rpc_auth_manager_keypair"),
            serialization_alias="rpc-auth-manager-keypair",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to the keypair file used for RPC authentication between manager components. "
                "This file contains cryptographic key pairs for secure inter-service communication. "
                "In production, should be stored in a secure location with restricted permissions (0600)."
            ),
            added_version="25.8.0",
            secret=True,
            example=ConfigExample(
                local="fixtures/manager/manager.key_secret",
                prod="/etc/backend.ai/keys/manager.key_secret",
            ),
        ),
    ]
    heartbeat_timeout: Annotated[
        float,
        Field(
            default=40.0,
            ge=1.0,
            validation_alias=AliasChoices("heartbeat-timeout", "heartbeat_timeout"),
            serialization_alias="heartbeat-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for agent heartbeat checks. "
                "If an agent doesn't respond within this time, it's considered offline. "
                "Should be set higher than the agent's heartbeat interval (default 10s). "
                "Increase in environments with high network latency."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="40.0", prod="60.0"),
        ),
    ]
    # TODO: Don't use this. Change to use KMS.
    secret: Annotated[
        str,
        Field(default_factory=lambda: secrets.token_urlsafe(16)),
        BackendAIConfigMeta(
            description=(
                "Secret key for manager authentication and signing operations. "
                "Used for securing API tokens and inter-service communication. "
                "Should be a strong random string in production environments. "
                "If not provided, one is auto-generated (not recommended for clustered deployments)."
            ),
            added_version="25.8.0",
            secret=True,
            example=ConfigExample(local="XXXXXXXXXXXXXX", prod="<generate-secure-random-string>"),
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
                "Whether to enable SSL/TLS for secure API communication. "
                "Strongly recommended for production deployments exposed to public networks. "
                "Requires valid certificate (ssl_cert) and private key (ssl_privkey) when enabled."
            ),
            added_version="25.8.0",
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
                "Path to the SSL/TLS certificate file in PEM format. "
                "Required when ssl_enabled is true. "
                "Can be a self-signed certificate for development or a CA-issued certificate for production."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="", prod="/etc/backend.ai/ssl/manager.crt"),
        ),
    ]
    ssl_privkey: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("ssl-privkey", "ssl_privkey"),
            serialization_alias="ssl-privkey",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to the SSL/TLS private key file in PEM format. "
                "Required when ssl_enabled is true. "
                "The key file should have restricted permissions (0600) for security."
            ),
            added_version="25.8.0",
            secret=True,
            example=ConfigExample(local="", prod="/etc/backend.ai/ssl/manager.key"),
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
                "Event loop implementation to use for async operations. "
                "'asyncio' is the Python standard library implementation (default). "
                "'uvloop' is a faster alternative based on libuv but may have compatibility issues. "
                "Use uvloop for better performance in high-throughput scenarios."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="asyncio", prod="asyncio"),
        ),
    ]
    distributed_lock: Annotated[
        DistributedLockType,
        Field(
            default=DistributedLockType.pg_advisory,
            validation_alias=AliasChoices("distributed-lock", "distributed_lock"),
            serialization_alias="distributed-lock",
        ),
        BackendAIConfigMeta(
            description=(
                "Distributed lock mechanism to coordinate multiple manager instances. "
                "Options: filelock (single-node), pg_advisory (PostgreSQL, default), "
                "redlock (Redis), etcd (etcd v2), etcetra (etcd v3). "
                "Choose based on your infrastructure and cluster size."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="pg_advisory", prod="pg_advisory"),
        ),
    ]
    pg_advisory_config: Annotated[
        Mapping[str, Any],
        Field(
            default=PgAdvisoryLock.default_config,
            validation_alias=AliasChoices("pg-advisory-config", "pg_advisory_config"),
            serialization_alias="pg-advisory-config",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for PostgreSQL advisory locks. "
                "Used when distributed_lock is set to pg_advisory. "
                "Usually the defaults work well for most deployments."
            ),
            added_version="25.8.0",
        ),
    ]
    filelock_config: Annotated[
        Mapping[str, Any],
        Field(
            default=FileLock.default_config,
            validation_alias=AliasChoices("filelock-config", "filelock_config"),
            serialization_alias="filelock-config",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for file-based locks. "
                "Used when distributed_lock is set to filelock. "
                "Only suitable for single-node deployments."
            ),
            added_version="25.8.0",
        ),
    ]
    redlock_config: Annotated[
        Mapping[str, Any],
        Field(
            default=RedisLock.default_config,
            validation_alias=AliasChoices("redlock-config", "redlock_config"),
            serialization_alias="redlock-config",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for Redis-based distributed locking (Redlock algorithm). "
                "Used when distributed_lock is set to redlock. "
                "Recommended for large clusters with Redis infrastructure."
            ),
            added_version="25.8.0",
        ),
    ]
    etcdlock_config: Annotated[
        Mapping[str, Any],
        Field(
            default=EtcdLock.default_config,
            validation_alias=AliasChoices("etcdlock-config", "etcdlock_config"),
            serialization_alias="etcdlock-config",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for etcd-based distributed locking. "
                "Used when distributed_lock is set to etcd or etcetra. "
                "Recommended for clusters already using etcd for coordination."
            ),
            added_version="25.8.0",
        ),
    ]
    session_schedule_lock_lifetime: Annotated[
        float,
        Field(
            default=30,
            validation_alias=AliasChoices(
                "session-schedule-lock-lifetime", "session_schedule_lock_lifetime"
            ),
            serialization_alias="session_schedule_lock_lifetime",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum lifetime in seconds for session scheduling locks. "
                "If scheduling takes longer than this, locks are automatically released. "
                "Prevents deadlocks in case a manager fails during scheduling. "
                "Increase if scheduling large sessions takes longer than 30 seconds."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="30", prod="60"),
        ),
    ]
    session_check_precondition_lock_lifetime: Annotated[
        float,
        Field(
            default=30,
            validation_alias=AliasChoices(
                "session-check-precondition-lock-lifetime",
                "session_check_precondition_lock_lifetime",
            ),
            serialization_alias="session_check_precondition_lock_lifetime",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum lifetime in seconds for session precondition check locks. "
                "Controls how long the manager can hold a lock while checking session creation conditions. "
                "Should be balanced to prevent both deadlocks and race conditions."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="30", prod="60"),
        ),
    ]
    session_start_lock_lifetime: Annotated[
        float,
        Field(
            default=30,
            validation_alias=AliasChoices(
                "session-start-lock-lifetime", "session_start_lock_lifetime"
            ),
            serialization_alias="session_start_lock_lifetime",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum lifetime in seconds for session start locks. "
                "Controls how long the manager can hold a lock while starting a session. "
                "Longer values are safer but may block other managers longer on failure."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="30", prod="60"),
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
                "Path to the file where the manager process ID will be written. "
                "Useful for service management, monitoring, and graceful shutdown scripts. "
                "Set to /dev/null by default to disable this feature."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="/dev/null", prod="/var/run/backend.ai/manager.pid"),
        ),
    ]
    allowed_plugins: Annotated[
        set[str] | None,
        Field(
            default=None,
            validation_alias=AliasChoices("allowed-plugins", "allowed_plugins"),
            serialization_alias="allowed-plugins",
        ),
        BackendAIConfigMeta(
            description=(
                "Explicit list of plugins to load (whitelist). "
                "If specified, only these plugins will be loaded even if others are installed. "
                "Useful for controlling exactly which plugins are active in production. "
                "Leave as None to load all available plugins except disabled_plugins."
            ),
            added_version="25.8.0",
            example=ConfigExample(
                local='["example.plugin.what.you.want"]',
                prod='["example.plugin.what.you.want"]',
            ),
        ),
    ]
    disabled_plugins: Annotated[
        set[str] | None,
        Field(
            default=None,
            validation_alias=AliasChoices("disabled-plugins", "disabled_plugins"),
            serialization_alias="disabled-plugins",
        ),
        BackendAIConfigMeta(
            description=(
                "List of plugins to explicitly disable (blacklist). "
                "These plugins won't be loaded even if they're installed. "
                "Useful for disabling problematic or unwanted plugins without uninstalling."
            ),
            added_version="25.8.0",
            example=ConfigExample(
                local='["example.plugin.what.you.want"]',
                prod='["example.plugin.what.you.want"]',
            ),
        ),
    ]
    hide_agents: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("hide-agents", "hide_agents"),
            serialization_alias="hide-agents",
        ),
        BackendAIConfigMeta(
            description=(
                "Whether to hide detailed agent information in API responses. "
                "When enabled, agent details are obscured in user-facing APIs. "
                "Recommended for multi-tenant environments to improve security and privacy."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    agent_selection_resource_priority: Annotated[
        list[str],
        Field(
            default=["cuda", "rocm", "tpu", "cpu", "mem"],
            validation_alias=AliasChoices(
                "agent-selection-resource-priority", "agent_selection_resource_priority"
            ),
            serialization_alias="agent-selection-resource-priority",
        ),
        BackendAIConfigMeta(
            description=(
                "Priority order for resources when selecting agents for compute sessions. "
                "Determines which resources are considered more important during scheduling. "
                "Default prioritizes GPU resources (CUDA, ROCm, TPU) over CPU and memory. "
                "Customize based on your workload patterns."
            ),
            added_version="25.8.0",
            example=ConfigExample(
                local='["cuda", "rocm", "tpu", "cpu", "mem"]',
                prod='["cuda", "rocm", "tpu", "cpu", "mem"]',
            ),
        ),
    ]
    importer_image: Annotated[
        str,
        Field(
            default="lablup/importer:manylinux2010",
            validation_alias=AliasChoices("importer-image", "importer_image"),
            serialization_alias="importer-image",
        ),
        BackendAIConfigMeta(
            description=(
                "Container image used for the legacy importer service. "
                "This feature is deprecated and may be removed in future versions. "
                "The importer handles tasks like installing additional packages."
            ),
            added_version="25.8.0",
            deprecated_version="25.10.0",
            deprecation_hint="This feature is deprecated and will be removed in a future version.",
            example=ConfigExample(
                local="lablup/importer:manylinux2010", prod="lablup/importer:manylinux2010"
            ),
        ),
    ]
    max_wsmsg_size: Annotated[
        int,
        Field(
            default=16 * (2**20),  # default: 16 MiB
            validation_alias=AliasChoices("max-wsmsg-size", "max_wsmsg_size"),
            serialization_alias="max-wsmsg-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum WebSocket message size in bytes. "
                "Controls the largest message that can be sent over WebSocket connections. "
                "Default is 16 MiB (16777216 bytes), sufficient for most use cases. "
                "Increase for applications that transfer larger data chunks."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="16777216", prod="33554432"),
        ),
    ]
    aiomonitor_port: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            le=65535,
            validation_alias=AliasChoices("aiomonitor-port", "aiomonitor_port"),
            serialization_alias="aiomonitor-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Deprecated: Port for the aiomonitor terminal UI. "
                "Use aiomonitor_termui_port instead."
            ),
            added_version="25.8.0",
            deprecated_version="25.10.0",
            deprecation_hint="Use aiomonitor_termui_port instead.",
        ),
    ]
    aiomonitor_termui_port: Annotated[
        int,
        Field(
            default=38100,
            ge=1,
            le=65535,
            validation_alias=AliasChoices("aiomonitor-termui-port", "aiomonitor_termui_port"),
            serialization_alias="aiomonitor-termui-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port for the aiomonitor terminal UI debugging console. "
                "Allows connecting via telnet to inspect running async tasks and debug issues. "
                "Should be accessible only from trusted networks for security."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="38100", prod="38100"),
        ),
    ]
    aiomonitor_webui_port: Annotated[
        int,
        Field(
            default=39100,
            ge=1,
            le=65535,
            validation_alias=AliasChoices("aiomonitor-webui-port", "aiomonitor_webui_port"),
            serialization_alias="aiomonitor-webui-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port for the aiomonitor web-based monitoring interface. "
                "Provides a browser-based UI for monitoring async tasks and manager health. "
                "Should be accessible only from trusted networks for security."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="39100", prod="39100"),
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
                "Whether to use the experimental Redis-based event dispatcher. "
                "May provide better performance for event handling in large clusters. "
                "Not recommended for production use unless specifically tested and needed."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    status_update_interval: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            validation_alias=AliasChoices("status-update-interval", "status_update_interval"),
            serialization_alias="status-update-interval",
        ),
        BackendAIConfigMeta(
            description=(
                "Interval in seconds between manager status updates to the cluster. "
                "Controls how frequently the manager broadcasts its health status. "
                "Smaller values provide more real-time information but increase network overhead."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="60.0", prod="30.0"),
        ),
    ]
    status_lifetime: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            validation_alias=AliasChoices("status-lifetime", "status_lifetime"),
            serialization_alias="status-lifetime",
        ),
        BackendAIConfigMeta(
            description=(
                "How long in seconds status information is considered valid. "
                "Status records older than this will be ignored or refreshed. "
                "Should be greater than status_update_interval to avoid gaps."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="120", prod="90"),
        ),
    ]
    public_metrics_port: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            le=65535,
            validation_alias=AliasChoices("public-metrics-port", "public_metrics_port"),
            serialization_alias="public-metrics-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Port for exposing public metrics in Prometheus format. "
                "If specified, metrics endpoint will be available at this port. "
                "Leave as None to disable public metrics exposure."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="", prod="9090"),
        ),
    ]

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
    ssl_verify: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("ssl-verify", "ssl_verify"),
            serialization_alias="ssl-verify",
        ),
        BackendAIConfigMeta(
            description=(
                "Whether to verify SSL certificates when connecting to Docker registries. "
                "Disabling this is not recommended except for testing with self-signed certificates. "
                "In production, always use verified SSL certificates."
            ),
            added_version="25.8.0",
            deprecated_version="25.10.0",
            deprecation_hint="This configuration is deprecated and may be removed in a future version.",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]


class SMTPReporterConfig(BaseConfigSchema):
    name: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Name of the SMTP reporter for identification. "
                "Used to reference this reporter from action monitors and other configurations."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="smtp", prod="smtp"),
        ),
    ]
    host: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "SMTP server hostname or IP address. "
                "This is the mail server that will relay your notification emails."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="localhost", prod="smtp.gmail.com"),
        ),
    ]
    port: Annotated[
        int,
        Field(ge=1, le=65535),
        BackendAIConfigMeta(
            description=(
                "SMTP server port number. "
                "Common ports: 25 (unencrypted), 465 (SSL/TLS), 587 (STARTTLS). "
                "Use 465 or 587 for secure email transmission."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="25", prod="587"),
        ),
    ]
    username: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Username for authenticating with the SMTP server. "
                "Usually an email address or account name depending on the mail provider."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="user@localhost", prod="user@example.com"),
        ),
    ]
    password: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Password for SMTP server authentication. "
                "For Gmail, use an app-specific password instead of your account password."
            ),
            added_version="25.8.0",
            secret=True,
        ),
    ]
    sender: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Email address that will appear as the sender ('From' field). "
                "Must be authorized to send from the configured SMTP server."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="noreply@localhost", prod="noreply@example.com"),
        ),
    ]
    recipients: Annotated[
        list[str],
        Field(),
        BackendAIConfigMeta(
            description=(
                "List of email addresses to receive notification emails. "
                "All recipients will receive the same notification content."
            ),
            added_version="25.8.0",
            example=ConfigExample(
                local='["admin@localhost"]',
                prod='["ops-team@example.com"]',
            ),
        ),
    ]
    use_tls: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("use-tls", "use_tls"),
            serialization_alias="use-tls",
        ),
        BackendAIConfigMeta(
            description=(
                "Whether to use TLS encryption for SMTP communication. "
                "Strongly recommended for production to protect credentials and email content."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    max_workers: Annotated[
        int,
        Field(
            default=5,
            ge=1,
            validation_alias=AliasChoices("max-workers", "max_workers"),
            serialization_alias="max-workers",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of concurrent worker threads for sending emails. "
                "Higher values improve throughput but consume more resources. "
                "Adjust based on your SMTP server's rate limits."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="5", prod="10"),
        ),
    ]
    template: Annotated[
        str,
        Field(default=_default_smtp_template),
        BackendAIConfigMeta(
            description=(
                "Jinja2 template for the email body. "
                "Available placeholders: action_type, entity_id, status, description, "
                "created_at, ended_at, duration. Customize to match your notification needs."
            ),
            added_version="25.8.0",
        ),
    ]
    trigger_policy: Annotated[
        Literal["ALL", "ON_ERROR"],
        Field(
            default="ALL",
            validation_alias=AliasChoices("trigger-policy", "trigger_policy"),
            serialization_alias="trigger-policy",
        ),
        BackendAIConfigMeta(
            description=(
                "Policy for when to send email notifications. "
                "ALL: Send for all events regardless of status. "
                "ON_ERROR: Send only when errors occur. "
                "Use ON_ERROR to reduce notification volume in production."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="ALL", prod="ON_ERROR"),
        ),
    ]


class ActionMonitorsConfig(BaseConfigSchema):
    subscribed_actions: Annotated[
        list[str],
        Field(
            default=[],
            validation_alias=AliasChoices("subscribed-actions", "subscribed_actions"),
            serialization_alias="subscribed-actions",
        ),
        BackendAIConfigMeta(
            description=(
                "List of action types to monitor for notifications. "
                "Actions are specified as 'category:action' format. "
                "Examples: 'session:create_from_params', 'session:create_cluster'. "
                "Empty list means no actions are monitored."
            ),
            added_version="25.8.0",
        ),
    ]
    reporter: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Name of the reporter to use for sending notifications. "
                "Must match a configured reporter name (e.g., 'smtp', 'audit_log')."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="smtp", prod="smtp"),
        ),
    ]


class ReporterConfig(BaseConfigSchema):
    smtp: Annotated[
        list[SMTPReporterConfig],
        Field(default=[]),
        BackendAIConfigMeta(
            description=(
                "List of SMTP reporter configurations for email notifications. "
                "Each SMTP reporter can be configured with different SMTP servers, "
                "templates, and trigger policies. Multiple reporters enable routing "
                "different notification types to different email destinations."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    action_monitors: Annotated[
        list[ActionMonitorsConfig],
        Field(
            default=[],
            validation_alias=AliasChoices("action-monitors", "action_monitors"),
            serialization_alias="action-monitors",
        ),
        BackendAIConfigMeta(
            description=(
                "List of action monitor configurations. "
                "Action monitors subscribe to specific Backend.AI events and route them "
                "to configured reporters. Enables customizable alerting based on system events."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


class DebugConfig(BaseConfigSchema):
    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Master switch for debug mode in the manager. "
                "When enabled, activates various debugging features and verbose logging. "
                "Should always be disabled in production for security and performance reasons."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    asyncio: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable Python asyncio debug mode. "
                "Helps detect issues like coroutines never awaited or excessive event loop delays. "
                "Adds significant overhead; use only during development and debugging."
            ),
            added_version="25.8.0",
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
                "Enable enhanced task information in aiomonitor. "
                "Provides more detailed information about running asyncio tasks. "
                "Useful for debugging complex async issues but adds monitoring overhead."
            ),
            added_version="25.8.0",
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
                "Log all internal system events passing through the event bus. "
                "Very verbose output useful for debugging event flow issues. "
                "Not recommended for production due to high log volume."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    log_scheduler_ticks: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("log-scheduler-ticks", "log_scheduler_ticks"),
            serialization_alias="log-scheduler-ticks",
        ),
        BackendAIConfigMeta(
            description=(
                "Log detailed information about scheduler tick operations. "
                "Helps diagnose scheduling issues and timing problems. "
                "Generates many log entries; use sparingly even in development."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    periodic_sync_stats: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("periodic-sync-stats", "periodic_sync_stats"),
            serialization_alias="periodic-sync-stats",
        ),
        BackendAIConfigMeta(
            description=(
                "Periodically collect and log system statistics. "
                "Helpful for monitoring system behavior and performance trends over time. "
                "Can be enabled in production for diagnostics when needed."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]


class SystemConfig(BaseConfigSchema):
    timezone: Annotated[
        TimeZone,
        Field(default_factory=lambda: UTC),
        BackendAIConfigMeta(
            description=(
                "Default timezone for the manager and all time-related operations. "
                "Uses pytz-compatible timezone names (e.g., 'UTC', 'Asia/Seoul', 'America/New_York'). "
                "Affects timestamps displayed in logs, APIs, and scheduled operations."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="UTC", prod="UTC"),
        ),
    ]


class ResourcesConfig(BaseConfigSchema):
    group_resource_visibility: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Whether to expose group resource usage statistics in check-presets API. "
                "When true, users can see aggregate resource usage for their groups. "
                "Useful for group-level resource monitoring and planning."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]


class APIConfig(BaseConfigSchema):
    allow_origins: Annotated[
        str,
        Field(
            default="*",
            validation_alias=AliasChoices("allow_origins", "allow-origins"),
            serialization_alias="allow-origins",
        ),
        BackendAIConfigMeta(
            description=(
                "CORS (Cross-Origin Resource Sharing) allow-origins header value. "
                "Use '*' to allow all origins (not recommended for production). "
                "Specify comma-separated domain patterns for production security."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="*", prod="https://console.example.com"),
        ),
    ]
    allow_graphql_schema_introspection: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "allow_graphql_schema_introspection", "allow-graphql-schema-introspection"
            ),
            serialization_alias="allow-graphql-schema-introspection",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow GraphQL schema introspection queries. "
                "Enables development tools like GraphiQL to explore the API schema. "
                "Should be disabled in production to prevent information leakage."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    allow_openapi_schema_introspection: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "allow_openapi_schema_introspection", "allow-openapi-schema-introspection"
            ),
            serialization_alias="allow-openapi-schema-introspection",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow OpenAPI schema introspection endpoints. "
                "Enables Swagger UI and similar API documentation tools. "
                "Should be disabled in production to prevent information leakage."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    max_gql_query_depth: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            validation_alias=AliasChoices("max_gql_query_depth", "max-gql-query-depth"),
            serialization_alias="max-gql-query-depth",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum allowed depth for GraphQL queries. "
                "Limits query complexity to prevent denial-of-service attacks. "
                "Set to None to disable depth limiting (not recommended for production)."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="", prod="10"),
        ),
    ]
    max_gql_connection_page_size: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            validation_alias=AliasChoices(
                "max_gql_connection_page_size", "max-gql-connection-page-size"
            ),
            serialization_alias="max-gql-connection-page-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum page size for GraphQL connection (pagination) queries. "
                "Limits the number of items returned in a single request. "
                "Set to None to use the default pagination limits."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="", prod="100"),
        ),
    ]
    resources: Annotated[
        ResourcesConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Resource visibility and sharing settings for the API. "
                "Controls how resource information is exposed to different user roles."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


class DockerImageAutoPullPolicy(enum.StrEnum):
    digest = "digest"
    tag = "tag"
    none = "none"


class DockerImageConfig(BaseConfigSchema):
    auto_pull: Annotated[
        DockerImageAutoPullPolicy,
        Field(
            default=DockerImageAutoPullPolicy.digest,
            validation_alias=AliasChoices("auto_pull", "auto-pull"),
            serialization_alias="auto_pull",
        ),
        BackendAIConfigMeta(
            description=(
                "Policy for automatically pulling Docker images before session creation. "
                "'digest': Pull when image digest changes (most secure, ensures exact version). "
                "'tag': Pull when image tag changes (faster, but may get unexpected updates). "
                "'none': Never auto-pull (requires manual image management)."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="digest", prod="digest"),
        ),
    ]


class DockerConfig(BaseConfigSchema):
    image: Annotated[
        DockerImageConfig,
        Field(default_factory=DockerImageConfig),
        BackendAIConfigMeta(
            description=(
                "Docker image management configuration. "
                "Controls image pulling policies and registry interactions."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


class PluginsConfig(BaseConfigSchema):
    accelerator: Annotated[
        dict[str, Any],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description=(
                "Accelerator plugin configurations for GPU, TPU, and other devices. "
                "Keys are accelerator types (e.g., 'cuda', 'rocm', 'tpu'). "
                "Values contain plugin-specific settings like allocation modes and memory management."
            ),
            added_version="25.8.0",
        ),
    ]
    scheduler: Annotated[
        dict[str, dict[str, Any]],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description=(
                "Scheduler plugin configurations for session scheduling strategies. "
                "Keys are scheduler names (e.g., 'fifo', 'lifo', 'drf'). "
                "Values contain scheduler-specific settings like retry counts and priorities."
            ),
            added_version="25.8.0",
        ),
    ]
    agent_selector: Annotated[
        dict[str, dict[str, Any]],
        Field(
            default_factory=dict,
            validation_alias=AliasChoices("agent_selector", "agent-selector"),
            serialization_alias="agent-selector",
        ),
        BackendAIConfigMeta(
            description=(
                "Agent selector plugin configurations for agent selection strategies. "
                "Controls how agents are chosen for session placement. "
                "Can implement load-based, resource-based, or custom selection algorithms."
            ),
            added_version="25.8.0",
        ),
    ]
    network: Annotated[
        dict[str, dict[str, Any]],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description=(
                "Network plugin configurations for container networking. "
                "Keys are network driver names (e.g., 'overlay'). "
                "Values contain settings like MTU, subnet ranges, and encryption options."
            ),
            added_version="25.8.0",
        ),
    ]


class InterContainerNetworkConfig(BaseConfigSchema):
    default_driver: Annotated[
        str | None,
        Field(
            default="overlay",
            validation_alias=AliasChoices("default_driver", "default-driver"),
            serialization_alias="default-driver",
        ),
        BackendAIConfigMeta(
            description=(
                "Default network driver for inter-container communication in cluster sessions. "
                "'overlay' enables multi-host container networking for distributed workloads. "
                "Container communication performance depends on this setting."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="overlay", prod="overlay"),
        ),
    ]
    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Whether to enable inter-container networking for cluster sessions. "
                "When enabled, containers in the same session can communicate directly. "
                "Required for distributed computing frameworks like Horovod or PyTorch distributed."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    plugin: Annotated[
        Any | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Network plugin configuration for inter-container communication. "
                "Allows custom network plugin settings for advanced networking scenarios."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="{}", prod="{}"),
        ),
    ]


class SubnetNetworkConfig(BaseConfigSchema):
    agent: Annotated[
        IPvAnyNetwork,
        Field(default=IPv4Network("0.0.0.0/0")),
        BackendAIConfigMeta(
            description=(
                "IP subnet for agent communications. "
                "Specifies which network range is allowed for agent-to-agent and agent-to-manager traffic. "
                "Use '0.0.0.0/0' to allow all IPv4 addresses, or specify a restricted range for security."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="0.0.0.0/0", prod="10.0.0.0/8"),
        ),
    ]
    container: Annotated[
        IPvAnyNetwork,
        Field(default=IPv4Network("0.0.0.0/0")),
        BackendAIConfigMeta(
            description=(
                "IP subnet for container networks. "
                "Specifies which network range is allocated to containers. "
                "Use '0.0.0.0/0' to allow all IPv4 addresses, or '172.17.0.0/16' for Docker default."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="0.0.0.0/0", prod="172.17.0.0/16"),
        ),
    ]


class RpcConfig(BaseConfigSchema):
    keepalive_timeout: Annotated[
        float,
        Field(
            default=60.0,
            validation_alias=AliasChoices("keepalive_timeout", "keepalive-timeout"),
            serialization_alias="keepalive-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for RPC connection keepalive between manager and agents. "
                "If no activity occurs within this time, the connection is considered stale. "
                "Increase in environments with intermittent network connectivity."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="60.0", prod="120.0"),
        ),
    ]


class NetworkConfig(BaseConfigSchema):
    inter_container: Annotated[
        InterContainerNetworkConfig,
        Field(
            default_factory=InterContainerNetworkConfig,
            validation_alias=AliasChoices("inter_container", "inter-container"),
            serialization_alias="inter-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for networks between containers. "
                "Controls how containers in cluster sessions communicate with each other. "
                "Important for distributed computing workloads."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    subnet: Annotated[
        SubnetNetworkConfig,
        Field(default_factory=SubnetNetworkConfig),
        BackendAIConfigMeta(
            description=(
                "Subnet configurations for Backend.AI network segmentation. "
                "Defines IP address ranges for agents and containers."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    rpc: Annotated[
        RpcConfig,
        Field(default_factory=RpcConfig),
        BackendAIConfigMeta(
            description=(
                "RPC (Remote Procedure Call) network settings for internal service communication. "
                "Controls timeouts and keepalive settings for manager-agent communication."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


class WatcherConfig(BaseConfigSchema):
    token: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Authentication token for the watcher service. "
                "Used to secure communication between manager and the agent watcher component. "
                "Should be a secure random string in production environments."
            ),
            added_version="25.8.0",
            secret=True,
            example=ConfigExample(local="", prod="WATCHER_TOKEN"),
        ),
    ]
    file_io_timeout: Annotated[
        float,
        Field(
            default=DEFAULT_FILE_IO_TIMEOUT,
            validation_alias=AliasChoices("file_io_timeout", "file-io-timeout"),
            serialization_alias="file-io-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for file I/O operations performed by the watcher. "
                "Controls how long the watcher waits for file operations to complete. "
                "Increase for handling large files or when using slow storage systems."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="60.0", prod="120.0"),
        ),
    ]


class HangToleranceThresholdConfig(BaseConfigSchema):
    PREPARING: Annotated[
        datetime | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Maximum time a session can stay in PREPARING state before considered hung. "
                "Format is a duration string like '10m' for 10 minutes or '1h' for 1 hour. "
                "When exceeded, the system will attempt recovery actions for the session."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="10m", prod="30m"),
        ),
    ]
    TERMINATING: Annotated[
        datetime | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Maximum time a session can stay in TERMINATING state before considered hung. "
                "Format is a duration string like '10m' for 10 minutes or '1h' for 1 hour. "
                "When exceeded, the system will force-terminate the session."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="10m", prod="30m"),
        ),
    ]


class HangToleranceConfig(BaseConfigSchema):
    threshold: Annotated[
        HangToleranceThresholdConfig,
        Field(default_factory=HangToleranceThresholdConfig),
        BackendAIConfigMeta(
            description=(
                "Threshold settings for detecting hung sessions in various states. "
                "Defines maximum times sessions can remain in transitional states "
                "before the system considers them hung and takes recovery action."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


class SessionConfig(BaseConfigSchema):
    hang_tolerance: Annotated[
        HangToleranceConfig,
        Field(
            default_factory=HangToleranceConfig,
            validation_alias=AliasChoices("hang_tolerance", "hang-tolerance"),
            serialization_alias="hang-tolerance",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for detecting and handling hung sessions. "
                "Controls how the system identifies sessions stuck in transitional states "
                "and what recovery actions to take. Essential for maintaining system health."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


class MetricConfig(BaseConfigSchema):
    address: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="127.0.0.1", port=9090),
            alias="addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Address for the Prometheus metric server used for collecting session statistics. "
                "Backend.AI queries this Prometheus instance to retrieve resource usage metrics for "
                "compute sessions. The metrics are used for monitoring dashboards, idle session "
                "detection, and resource optimization. Ensure the Prometheus server is accessible "
                "from the manager and configured to scrape agent metrics."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="127.0.0.1:9090", prod="prometheus.backend.svc:9090"),
        ),
    ]
    timewindow: Annotated[
        str,
        Field(default=DEFAULT_METRIC_RANGE_VECTOR_TIMEWINDOW),
        BackendAIConfigMeta(
            description=(
                "Time window for metric range vector queries in PromQL format. "
                "This parameter controls the lookback period when querying Prometheus for "
                "resource usage statistics. For example, '1h' means metrics are averaged over "
                "the past 1 hour. Shorter windows provide more responsive metrics but may be "
                "noisier; longer windows smooth out spikes but delay detection of changes."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="1m", prod="1h"),
        ),
    ]

    @field_serializer("address")
    def _serialize_addr(self, addr: HostPortPair | None, _info: Any) -> str | None:
        return None if addr is None else f"{addr.host}:{addr.port}"


class IdleCheckerConfig(BaseConfigSchema):
    enabled: Annotated[
        str,
        Field(default=""),
        BackendAIConfigMeta(
            description=(
                "Comma-separated list of enabled idle checker names. Idle checkers automatically "
                "terminate sessions that have been idle for too long, helping to free up resources. "
                "Available checkers include 'network_timeout' (monitors network activity), "
                "'utilization' (monitors CPU/GPU/memory usage), and 'session_lifetime' (enforces "
                "maximum session duration). Leave empty to disable idle checking entirely."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="", prod="network_timeout,utilization"),
        ),
    ]
    app_streaming_packet_timeout: Annotated[
        TimeDuration,
        Field(
            default=_TimeDurationPydanticAnnotation.time_duration_validator("5m"),
            validation_alias=AliasChoices(
                "app_streaming_packet_timeout", "app-streaming-packet-timeout"
            ),
            serialization_alias="app_streaming_packet_timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout duration for app-streaming TCP packet activity. When a session runs "
                "an interactive application (web apps, IDEs), this timeout determines how long "
                "to wait for network packets before considering the connection stale. This helps "
                "detect disconnected or abandoned interactive sessions. Format is a duration "
                "string like '5m' for 5 minutes."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="5m", prod="10m"),
        ),
    ]
    checkers: Annotated[
        dict[str, Any],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description=(
                "Detailed configuration for each idle checker. Each key is a checker name (matching "
                "those in 'enabled'), and the value is checker-specific configuration. For "
                "'network_timeout', set 'threshold' for the idle duration. For 'utilization', "
                "configure 'resource-thresholds' with CPU/memory/GPU utilization percentages, "
                "'thresholds-check-operator' (and/or), 'time-window' for averaging period, and "
                "'initial-grace-period' to skip checking after session start."
            ),
            added_version="25.8.0",
        ),
    ]


class VolumeTypeConfig(BaseConfigSchema):
    user: Annotated[
        dict[str, Any] | str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for user-owned virtual folders. When this field is set (even as an "
                "empty dict), users can create personal virtual folders to store and manage their "
                "data. User folders are private by default and only accessible by the owner. "
                "Set to None to disable user-level virtual folder creation entirely."
            ),
            added_version="25.8.0",
        ),
    ]
    group: Annotated[
        dict[str, Any] | str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for group-owned virtual folders. When this field is set (even as an "
                "empty dict), users can create shared virtual folders at the group level. Group "
                "folders allow collaboration by sharing data among team members within the same "
                "group. Access permissions are managed at the group level. Set to None to disable "
                "group-level virtual folder creation."
            ),
            added_version="25.8.0",
        ),
    ]


# Same as aiohttp default timeout settings
_DEFAULT_TIMEOUT = HttpTimeoutConfig()  # type: ignore[call-arg]


class StorageProxyClientTimeoutConfig(BaseConfigSchema):
    """
    Per-method timeout configuration for StorageProxyManagerFacingClient.
    Each field corresponds to a method in the client class.
    If not specified, the default timeout (total=300s, sock_connect=30s) is used.
    """

    # Volume operations
    get_volumes: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("get-volumes", "get_volumes"),
            serialization_alias="get-volumes",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for the get_volumes storage proxy operation. This operation lists all "
                "available storage volumes from the proxy. Default timeout is sufficient for most "
                "deployments, but may need adjustment for proxies with many volumes."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # Folder operations
    create_folder: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("create-folder", "create_folder"),
            serialization_alias="create-folder",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for folder creation on the storage proxy. Creating folders is typically "
                "fast but may take longer on network-attached storage or when quotas need setup."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    delete_folder: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("delete-folder", "delete_folder"),
            serialization_alias="delete-folder",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for folder deletion operations. Deleting folders with many files may take "
                "significant time. Consider increasing this timeout for storage backends with "
                "slow deletion performance."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    clone_folder: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("clone-folder", "clone_folder"),
            serialization_alias="clone-folder",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for folder cloning operations. Cloning copies an entire folder structure "
                "and may take considerable time depending on the data size and storage performance."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    get_mount_path: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("get-mount-path", "get_mount_path"),
            serialization_alias="get-mount-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving the mount path of a virtual folder. This is a lightweight "
                "operation that returns the filesystem path used by agents to mount the folder."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # Volume info operations
    get_volume_hwinfo: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("get-volume-hwinfo", "get_volume_hwinfo"),
            serialization_alias="get-volume-hwinfo",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving volume hardware information. This operation queries the "
                "underlying storage system for capacity and capability information."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    get_volume_performance_metric: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices(
                "get-volume-performance-metric", "get_volume_performance_metric"
            ),
            serialization_alias="get-volume-performance-metric",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving volume performance metrics. This operation queries I/O "
                "statistics from the storage system for monitoring purposes."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    get_fs_usage: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("get-fs-usage", "get_fs_usage"),
            serialization_alias="get-fs-usage",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving filesystem usage statistics. Returns disk space usage "
                "information for capacity monitoring and alerting."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # Quota operations
    get_volume_quota: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("get-volume-quota", "get_volume_quota"),
            serialization_alias="get-volume-quota",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving volume-level quota settings. Queries the overall quota "
                "configuration for a storage volume."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    update_volume_quota: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("update-volume-quota", "update_volume_quota"),
            serialization_alias="update-volume-quota",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for updating volume-level quota settings. Modifies the overall quota "
                "configuration for a storage volume."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    get_quota_scope: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("get-quota-scope", "get_quota_scope"),
            serialization_alias="get-quota-scope",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving quota scope information. Quota scopes define quota limits "
                "at user or project level within a volume."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    update_quota_scope: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("update-quota-scope", "update_quota_scope"),
            serialization_alias="update-quota-scope",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for updating quota scope configuration. Updates quota limits for a "
                "specific user or project within a volume."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    delete_quota_scope_quota: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("delete-quota-scope-quota", "delete_quota_scope_quota"),
            serialization_alias="delete-quota-scope-quota",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for deleting quota scope quotas. Removes quota limits for a specific "
                "user or project within a volume."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # File operations
    mkdir: Annotated[
        HttpTimeoutConfig,
        Field(default_factory=lambda: _DEFAULT_TIMEOUT),
        BackendAIConfigMeta(
            description=(
                "Timeout for creating directories within a virtual folder. A lightweight operation "
                "that creates a new directory in the storage backend."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    rename_file: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("rename-file", "rename_file"),
            serialization_alias="rename-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for renaming files or directories. This is typically a fast metadata "
                "operation on most filesystems."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    delete_files: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("delete-files", "delete_files"),
            serialization_alias="delete-files",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for synchronous file deletion operations. Deletes files immediately and "
                "waits for completion."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    delete_files_async: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("delete-files-async", "delete_files_async"),
            serialization_alias="delete-files-async",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for asynchronous file deletion operations. Initiates deletion in the "
                "background without waiting for completion."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    move_file: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("move-file", "move_file"),
            serialization_alias="move-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for moving files between directories. May involve data copy if moving "
                "across different storage volumes."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    upload_file: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("upload-file", "upload_file"),
            serialization_alias="upload-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for file upload operations. Consider increasing for large file uploads "
                "or slow network connections."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    download_file: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("download-file", "download_file"),
            serialization_alias="download-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for file download operations. Consider increasing for large file downloads "
                "or slow network connections."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    download_archive_file: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("download-archive-file", "download_archive_file"),
            serialization_alias="download-archive-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for archive download session creation (token issuance). "
                "Does not affect the subsequent archive download streaming."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    list_files: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("list-files", "list_files"),
            serialization_alias="list-files",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for listing files in a directory. May need adjustment for directories "
                "with thousands of files."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    fetch_file: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("fetch-file", "fetch_file"),
            serialization_alias="fetch-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for fetching file contents or metadata. Used for reading file information "
                "without full download."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # Folder usage operations
    get_folder_usage: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("get-folder-usage", "get_folder_usage"),
            serialization_alias="get-folder-usage",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving folder disk usage. Calculates total size of a folder "
                "including all subfolders and files."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    get_used_bytes: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("get-used-bytes", "get_used_bytes"),
            serialization_alias="get-used-bytes",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving total bytes used by a folder. Returns the raw byte count "
                "consumed by the folder."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # HuggingFace operations
    scan_huggingface_models: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("scan-huggingface-models", "scan_huggingface_models"),
            serialization_alias="scan-huggingface-models",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for scanning HuggingFace model repositories. Searches for available "
                "models that can be imported from HuggingFace Hub."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    retrieve_huggingface_models: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices(
                "retrieve-huggingface-models", "retrieve_huggingface_models"
            ),
            serialization_alias="retrieve-huggingface-models",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving multiple HuggingFace model metadata. Gets detailed "
                "information about a batch of HuggingFace models."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    retrieve_huggingface_model: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices(
                "retrieve-huggingface-model", "retrieve_huggingface_model"
            ),
            serialization_alias="retrieve-huggingface-model",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving a single HuggingFace model's metadata. Gets detailed "
                "information about one specific HuggingFace model."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    import_huggingface_models: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("import-huggingface-models", "import_huggingface_models"),
            serialization_alias="import-huggingface-models",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for importing HuggingFace models to storage. Downloads model files from "
                "HuggingFace Hub. May need significant timeout for large models."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    get_huggingface_model_commit_hash: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices(
                "get-huggingface-model-commit-hash", "get_huggingface_model_commit_hash"
            ),
            serialization_alias="get-huggingface-model-commit-hash",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for retrieving HuggingFace model commit hash. Gets the specific version "
                "identifier for a model revision."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # Reservoir operations
    import_reservoir_models: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("import-reservoir-models", "import_reservoir_models"),
            serialization_alias="import-reservoir-models",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for importing models from reservoir storage. Handles model artifact "
                "imports from the Backend.AI reservoir system."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # S3 operations
    download_s3_file: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("download-s3-file", "download_s3_file"),
            serialization_alias="download-s3-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for downloading files from S3-compatible storage. Used for S3 backend "
                "storage operations."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    get_s3_presigned_download_url: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices(
                "get-s3-presigned-download-url", "get_s3_presigned_download_url"
            ),
            serialization_alias="get-s3-presigned-download-url",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for generating S3 presigned download URLs. Creates temporary authenticated "
                "URLs for direct S3 downloads."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    get_s3_presigned_upload_url: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices(
                "get-s3-presigned-upload-url", "get_s3_presigned_upload_url"
            ),
            serialization_alias="get-s3-presigned-upload-url",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for generating S3 presigned upload URLs. Creates temporary authenticated "
                "URLs for direct S3 uploads."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    delete_s3_object: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("delete-s3-object", "delete_s3_object"),
            serialization_alias="delete-s3-object",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for deleting objects from S3-compatible storage. Removes files stored "
                "in S3 backend storage."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # VFS operations
    download_vfs_file_streaming: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices(
                "download-vfs-file-streaming", "download_vfs_file_streaming"
            ),
            serialization_alias="download-vfs-file-streaming",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for streaming file downloads from VFS storage. Used for efficient "
                "large file transfers from virtual filesystem backends."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    list_vfs_files: Annotated[
        HttpTimeoutConfig,
        Field(
            default_factory=lambda: _DEFAULT_TIMEOUT,
            validation_alias=AliasChoices("list-vfs-files", "list_vfs_files"),
            serialization_alias="list-vfs-files",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for listing files in VFS storage. Enumerates files and directories "
                "in virtual filesystem backends."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


class VolumeProxyConfig(BaseConfigSchema):
    client_api: Annotated[
        str,
        Field(
            validation_alias=AliasChoices("client_api", "client-api"),
            serialization_alias="client_api",
        ),
        BackendAIConfigMeta(
            description=(
                "Client-facing API endpoint URL of the storage proxy. This URL is used by "
                "clients (users, compute sessions) to access virtual folder contents through "
                "direct file operations. Should include protocol, host, and port. Ensure "
                "this endpoint is accessible from client networks and compute nodes."
            ),
            added_version="25.8.0",
            example=ConfigExample(
                local="http://localhost:6021", prod="https://storage.example.com:6021"
            ),
        ),
    ]
    manager_api: Annotated[
        str,
        Field(
            validation_alias=AliasChoices("manager_api", "manager-api"),
            serialization_alias="manager_api",
        ),
        BackendAIConfigMeta(
            description=(
                "Manager-facing API endpoint URL of the storage proxy. This internal URL is used "
                "by the manager to perform administrative operations like creating/deleting folders, "
                "managing quotas, and checking storage status. Should only be accessible from "
                "the manager's network."
            ),
            added_version="25.8.0",
            example=ConfigExample(
                local="http://localhost:6022", prod="http://storage-internal:6022"
            ),
        ),
    ]
    secret: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Secret key for authenticating manager requests to the storage proxy's manager API. "
                "This secret must match the value configured on the storage proxy server. Used to "
                "verify that requests come from authorized manager instances. Keep this value "
                "secure and do not expose it to clients."
            ),
            added_version="25.8.0",
            secret=True,
            example=ConfigExample(local="changeme", prod="<generate-secure-random-string>"),
        ),
    ]
    ssl_verify: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("ssl_verify", "ssl-verify"),
            serialization_alias="ssl_verify",
        ),
        BackendAIConfigMeta(
            description=(
                "Whether to verify SSL/TLS certificates when connecting to the storage proxy. "
                "Should be True in production environments for security. Can be set to False "
                "during development or testing with self-signed certificates, but this reduces "
                "security and should never be done in production."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    sftp_scaling_groups: Annotated[
        CommaSeparatedStrList | None,
        Field(
            default=None,
            validation_alias=AliasChoices("sftp_scaling_groups", "sftp-scaling-groups"),
            serialization_alias="sftp_scaling_groups",
        ),
        BackendAIConfigMeta(
            description=(
                "Comma-separated list of scaling group names that are allowed to use this storage "
                "proxy for SFTP sessions. SFTP sessions provide interactive file transfer access "
                "to virtual folders. When set, only sessions in the specified scaling groups can "
                "create SFTP connections to this storage proxy. Leave None to allow all scaling groups."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="default", prod="sftp-group-1,sftp-group-2"),
        ),
    ]
    timeouts: Annotated[
        StorageProxyClientTimeoutConfig,
        Field(default_factory=StorageProxyClientTimeoutConfig),
        BackendAIConfigMeta(
            description=(
                "Per-operation timeout configuration for storage proxy client requests. Each "
                "storage proxy API method can have its own timeout values. Use this to adjust "
                "timeouts for specific operations that may take longer than the defaults, such "
                "as file uploads/downloads or model imports."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


class VolumesConfig(BaseConfigSchema):
    types: Annotated[
        VolumeTypeConfig,
        Field(
            default_factory=lambda: VolumeTypeConfig(user={}),
            alias="_types",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for enabled virtual folder types. Defines which types of virtual "
                "folders can be created in the system. Contains sub-configurations for user-level "
                "and group-level folders. At minimum, user folders are typically enabled to allow "
                "users to store their personal data and session outputs."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    default_host: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("default_host", "default-host"),
            serialization_alias="default_host",
        ),
        BackendAIConfigMeta(
            description=(
                "Default volume host to use when creating new virtual folders. The format is "
                "'proxy_name:volume_name' where proxy_name matches a key in the 'proxies' "
                "configuration. When users create folders without specifying a host, this default "
                "is used. If not set, users must explicitly specify the host for each folder."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="local:volume1", prod="nas-proxy:main-volume"),
        ),
    ]
    exposed_volume_info: Annotated[
        CommaSeparatedStrList,
        Field(
            default_factory=lambda: CommaSeparatedStrList("percentage"),
            validation_alias=AliasChoices("exposed_volume_info", "exposed-volume-info"),
            serialization_alias="exposed_volume_info",
        ),
        BackendAIConfigMeta(
            description=(
                "Comma-separated list of volume information to expose to users. Controls what "
                "storage metrics are visible in the user interface and API responses. Options "
                "include 'percentage' for disk usage percentage. Additional metrics may be "
                "available depending on the storage backend capabilities."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="percentage", prod="percentage"),
        ),
    ]
    proxies: Annotated[
        dict[str, VolumeProxyConfig],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description=(
                "Mapping of storage proxy configurations by proxy name. Each key is a unique "
                "proxy name used in volume host references (e.g., 'local:volume1' uses the "
                "'local' proxy). Each value is a VolumeProxyConfig defining the proxy's API "
                "endpoints, authentication, and settings. Multiple proxies can be configured "
                "for different storage backends or locations."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]


# TODO: Make this more precise type
class ResourceSlotsConfig(BaseConfigSchema):
    """
    Resource slots configuration. This config allows extra fields for custom resource slot definitions.
    Standard slots like 'cpu' and 'mem' are handled by agents, while accelerator plugins may
    define additional slots (e.g., 'cuda.shares', 'cuda.device', 'rocm.device').
    """

    model_config = ConfigDict(
        extra="allow",
    )


class ReservoirObjectStorageConfig(BaseConfigSchema):
    storage_type: Annotated[
        Literal["object_storage"],
        Field(default="object_storage", alias="type"),
        BackendAIConfigMeta(
            description=(
                "Type identifier for this storage configuration. Must be 'object_storage' for "
                "S3-compatible object storage backends. This discriminator field is used to "
                "determine the storage configuration type when parsing the reservoir config."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="object_storage", prod="object_storage"),
        ),
    ]
    bucket_name: Annotated[
        str,
        Field(
            default="OBJECT_STORAGE_BUCKET_NAME",
            validation_alias=AliasChoices("bucket-name", "bucket_name"),
            serialization_alias="bucket-name",
        ),
        BackendAIConfigMeta(
            description=(
                "Name of the S3 bucket to use for reservoir storage. This bucket must exist "
                "and be accessible using the credentials configured in the storage proxy. The "
                "reservoir stores model artifacts, checkpoints, and other binary assets in this "
                "bucket. Ensure proper bucket policies are configured for access control."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="backend-ai-reservoir", prod="prod-model-artifacts"),
        ),
    ]


class ReservoirVFSStorageConfig(BaseConfigSchema):
    storage_type: Annotated[
        Literal["vfs_storage"],
        Field(default="vfs_storage", alias="type"),
        BackendAIConfigMeta(
            description=(
                "Type identifier for this storage configuration. Must be 'vfs_storage' for "
                "virtual filesystem storage backends. This discriminator field is used to "
                "determine the storage configuration type when parsing the reservoir config."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="vfs_storage", prod="vfs_storage"),
        ),
    ]
    subpath: Annotated[
        str,
        Field(default=""),
        BackendAIConfigMeta(
            description=(
                "Subpath within the VFS storage volume for reservoir data. This path is appended "
                "to the storage backend's base path to create the full reservoir location. Use "
                "this to organize reservoir data within a larger storage volume. Leave empty to "
                "use the volume root."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="artifacts", prod="models/reservoir"),
        ),
    ]


StorageSpecificConfig = ReservoirObjectStorageConfig | ReservoirVFSStorageConfig


class ReservoirConfig(BaseConfigSchema):
    enable_approve_process: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("enable-approve-process", "enable_approve_process"),
            serialization_alias="enable-approve-process",
        ),
        BackendAIConfigMeta(
            description=(
                "Whether to enable the approval workflow for model artifact uploads. When enabled, "
                "uploaded model artifacts require explicit approval by an administrator before "
                "they become available for use. This provides an additional review step for "
                "security and quality control in production environments."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    use_delegation: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("use-delegation", "use_delegation"),
            serialization_alias="use-delegation",
        ),
        BackendAIConfigMeta(
            description=(
                "Whether this reservoir uses delegation to upstream reservoirs. In a hierarchical "
                "reservoir setup, leaf reservoirs (use_delegation=True) can delegate model requests "
                "to parent reservoirs. Set to False if this reservoir is standalone or is itself "
                "a delegation target."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    storage_name: Annotated[
        str,
        Field(
            validation_alias=AliasChoices("storage-name", "storage_name"),
            serialization_alias="storage-name",
        ),
        BackendAIConfigMeta(
            description=(
                "Name of the default storage backend for reservoir operations. This storage is "
                "used for steps not explicitly specified in storage_step_selection. The name "
                "must match a configured storage in the storage proxy. Examples include object "
                "storage backends like MinIO or VFS storage backends."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="local-minio", prod="prod-s3-storage"),
        ),
    ]
    config: Annotated[
        StorageSpecificConfig,
        Field(default_factory=ReservoirObjectStorageConfig, discriminator="storage_type"),
        BackendAIConfigMeta(
            description=(
                "Storage-specific configuration for the reservoir. The config type is determined "
                "by the 'storage_type' discriminator field. Use ReservoirObjectStorageConfig "
                "for S3-compatible storage or ReservoirVFSStorageConfig for virtual filesystem "
                "storage backends."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    storage_step_selection: Annotated[
        dict[ArtifactStorageImportStep, str],
        Field(
            default_factory=dict,
            validation_alias=AliasChoices("storage_step_selection", "storage-step-selection"),
            serialization_alias="storage-step-selection",
        ),
        BackendAIConfigMeta(
            description=(
                "Mapping of artifact import steps to storage backend names. Allows using different "
                "storage backends for different stages of the model import process. Keys are "
                "import steps like 'download' and 'archive'. Steps not specified here use the "
                "storage_name default. This enables optimizing storage for different workload types."
            ),
            added_version="25.8.0",
        ),
    ]

    def resolve_storage_step_selection(
        self,
    ) -> dict[ArtifactStorageImportStep, NamedStorageTarget]:
        """
        Resolves the actual `storage_step_selection` to be passed to the storage proxy based on `storage_step_selection` and `storage_name`
        """

        _REQUIRED_STEPS = {ArtifactStorageImportStep.DOWNLOAD, ArtifactStorageImportStep.ARCHIVE}

        resolved_selection: dict[ArtifactStorageImportStep, NamedStorageTarget] = {
            step: NamedStorageTarget(storage_name=name)
            for step, name in self.storage_step_selection.items()
        }
        for required_step in _REQUIRED_STEPS:
            if required_step not in resolved_selection:
                resolved_selection[required_step] = NamedStorageTarget(
                    storage_name=self.storage_name
                )

        return resolved_selection

    @property
    def archive_storage(self) -> str:
        """
        Resolve the storage backend for the `ARCHIVE` step.
        If not explicitly specified, falls back to `storage_name`.
        """
        return self.storage_step_selection.get(ArtifactStorageImportStep.ARCHIVE, self.storage_name)


class ArtifactRegistryConfig(BaseConfigSchema):
    model_registry: Annotated[
        str,
        Field(
            validation_alias=AliasChoices("model-registry", "model_registry"),
            serialization_alias="model-registry",
        ),
        BackendAIConfigMeta(
            description=(
                "Name identifier for the default model registry configuration. This name is used "
                "to reference the registry in API calls and configuration. The actual registry "
                "location and credentials are managed through the reservoir configuration. This "
                "setting establishes which model registry to use for artifact storage operations."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="local-registry", prod="prod-model-registry"),
        ),
    ]


class DeploymentConfig(BaseConfigSchema):
    enable_model_definition_override: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "enable-model-definition-override", "enable_model_definition_override"
            ),
            serialization_alias="enable-model-definition-override",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable custom model definition override from storage for non-CUSTOM runtime variants. "
                "When enabled, after generating the standard model definition programmatically, the "
                "system attempts to fetch a custom definition from storage if model_definition_path "
                "is specified in the model revision. The custom definition overrides the generated "
                "one if found; otherwise, the generated definition is used as fallback. This allows "
                "customizing model serving configurations while maintaining automatic defaults."
            ),
            added_version="25.8.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]


class ExportConfig(BaseConfigSchema):
    """Export-related configuration."""

    max_rows: Annotated[
        int,
        Field(
            default=100_000,
            ge=1000,
            le=1_000_000,
            validation_alias=AliasChoices("max-rows", "max_rows"),
            serialization_alias="max-rows",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of rows per export request. "
                "Limits the amount of data that can be exported in a single request "
                "to prevent memory exhaustion and timeout issues."
            ),
            added_version="26.1.0",
            example=ConfigExample(local="100000", prod="100000"),
        ),
    ]

    statement_timeout_sec: Annotated[
        int,
        Field(
            default=300,
            ge=60,
            le=3600,
            validation_alias=AliasChoices("statement-timeout-sec", "statement_timeout_sec"),
            serialization_alias="statement-timeout-sec",
        ),
        BackendAIConfigMeta(
            description=(
                "Database statement timeout in seconds for export queries. "
                "Long-running export queries will be cancelled after this duration."
            ),
            added_version="26.1.0",
            example=ConfigExample(local="300", prod="300"),
        ),
    ]

    max_concurrent_exports: Annotated[
        int,
        Field(
            default=10,
            ge=1,
            le=50,
            validation_alias=AliasChoices("max-concurrent-exports", "max_concurrent_exports"),
            serialization_alias="max-concurrent-exports",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of concurrent export requests allowed. "
                "Prevents system overload from too many simultaneous export operations."
            ),
            added_version="26.1.0",
            example=ConfigExample(local="10", prod="10"),
        ),
    ]


class ManagerUnifiedConfig(BaseConfigSchema):
    # From legacy local config
    db: Annotated[
        DatabaseConfig,
        Field(default_factory=DatabaseConfig),
        BackendAIConfigMeta(
            description=(
                "Database configuration for the Backend.AI manager. Defines how the manager "
                "connects to its PostgreSQL database including connection parameters, credentials, "
                "and connection pool settings. The database stores all persistent state including "
                "users, sessions, resources, and audit logs."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    etcd: Annotated[
        EtcdConfig,
        Field(default_factory=EtcdConfig),
        BackendAIConfigMeta(
            description=(
                "Etcd distributed key-value store configuration. Etcd is used for cluster "
                "coordination, service discovery, and shared configuration between manager "
                "instances. In multi-manager deployments, etcd ensures consistent state across "
                "all manager nodes."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    manager: Annotated[
        ManagerConfig,
        Field(default_factory=ManagerConfig),
        BackendAIConfigMeta(
            description=(
                "Core manager service configuration. Controls fundamental manager behavior "
                "including network binding, process management, scaling parameters, and internal "
                "service communication. This is the primary configuration block for the manager "
                "component itself."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    docker_registry: Annotated[
        DockerRegistryConfig,
        Field(
            default=DockerRegistryConfig.model_validate({"ssl-verify": True}),
            validation_alias=AliasChoices("docker_registry", "docker-registry"),
            serialization_alias="docker-registry",
        ),
        BackendAIConfigMeta(
            description=(
                "Deprecated Docker registry configuration. This legacy configuration controls "
                "basic Docker registry connection settings. For new deployments, use the "
                "container registry configuration through the API instead. This setting may "
                "be removed in future versions."
            ),
            added_version="25.8.0",
            deprecated_version="25.10.0",
            deprecation_hint="Use container registry configuration through the API instead.",
            composite=CompositeType.FIELD,
        ),
    ]
    logging: Annotated[
        LoggingConfig,
        Field(default_factory=LoggingConfig),
        BackendAIConfigMeta(
            description=(
                "Logging system configuration. Controls how the manager formats, filters, and "
                "outputs log messages. Supports multiple log handlers including console, file, "
                "and remote logging services. Detailed logging configuration helps with debugging "
                "and monitoring."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    pyroscope: Annotated[
        PyroscopeConfig,
        Field(default_factory=PyroscopeConfig),
        BackendAIConfigMeta(
            description=(
                "Pyroscope continuous profiling configuration. When enabled, sends profiling "
                "data to a Pyroscope server for performance analysis and optimization. Useful "
                "for identifying bottlenecks and understanding resource usage patterns in "
                "production deployments."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    debug: Annotated[
        DebugConfig,
        Field(default_factory=DebugConfig),
        BackendAIConfigMeta(
            description=(
                "Debugging options configuration. Controls various debugging features that aid "
                "in development and troubleshooting. Most debug options should be disabled in "
                "production environments as they may impact performance or expose sensitive "
                "information."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    reporter: Annotated[
        ReporterConfig,
        Field(default_factory=ReporterConfig),
        BackendAIConfigMeta(
            description=(
                "Reporter configuration for notifications and alerts. Controls how the manager "
                "reports events and sends notifications through various channels including "
                "audit logs, action monitors, and SMTP email reporters. Each reporter type "
                "can be independently configured."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # From legacy shared config
    system: Annotated[
        SystemConfig,
        Field(default_factory=SystemConfig),
        BackendAIConfigMeta(
            description=(
                "System-wide configuration settings. Controls general Backend.AI system behavior "
                "that affects all components. These settings typically apply globally across "
                "the entire installation."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    api: Annotated[
        APIConfig,
        Field(default_factory=APIConfig),
        BackendAIConfigMeta(
            description=(
                "API server configuration. Controls how the manager's REST and GraphQL APIs "
                "behave including rate limiting, request size limits, session management, and "
                "security settings. These settings affect how clients interact with Backend.AI."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    redis: Annotated[
        RedisConfig,
        Field(default_factory=RedisConfig),
        BackendAIConfigMeta(
            description=(
                "Redis configuration for caching and messaging. Redis is used for distributed "
                "caching, session state storage, real-time messaging between components, and "
                "background task queuing. Configure connection details and authentication here."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    idle: Annotated[
        IdleCheckerConfig,
        Field(default_factory=IdleCheckerConfig),
        BackendAIConfigMeta(
            description=(
                "Idle session checker configuration. Controls automatic termination of inactive "
                "sessions to free up resources. Multiple checker types can be enabled including "
                "network timeout, resource utilization, and session lifetime checkers."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    docker: Annotated[
        DockerConfig,
        Field(default_factory=DockerConfig),
        BackendAIConfigMeta(
            description=(
                "Docker container runtime settings. Controls how Docker images are managed "
                "and used for compute sessions. Includes image configuration and container "
                "runtime defaults."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    plugins: Annotated[
        PluginsConfig,
        Field(default_factory=PluginsConfig),
        BackendAIConfigMeta(
            description=(
                "Plugin system configuration. Controls behavior of Backend.AI plugins including "
                "scheduler plugins, hook plugins, and accelerator plugins. Plugins extend "
                "manager functionality for custom scheduling, event handling, and hardware support."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    network: Annotated[
        NetworkConfig,
        Field(default_factory=NetworkConfig),
        BackendAIConfigMeta(
            description=(
                "Network configuration for container networking. Controls how compute session "
                "containers connect to networks and communicate with each other. Supports various "
                "network modes including overlay networks for multi-host deployments."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    watcher: Annotated[
        WatcherConfig,
        Field(default_factory=WatcherConfig),
        BackendAIConfigMeta(
            description=(
                "Watcher service configuration. The watcher monitors compute sessions and agent "
                "health. Configure connection settings for communicating with watcher instances "
                "deployed alongside agents."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    auth: Annotated[
        AuthConfig,
        Field(default_factory=AuthConfig),
        BackendAIConfigMeta(
            description=(
                "Authentication and security settings. Controls password policies, login "
                "behavior, and other authentication-related configurations. Ensure strong "
                "password requirements in production environments."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    jwt: Annotated[
        SharedJWTConfig,
        Field(default_factory=SharedJWTConfig),
        BackendAIConfigMeta(
            description=(
                "JWT (JSON Web Token) authentication configuration. Controls JWT token signing "
                "and verification settings used for stateless authentication between components. "
                "Shared between manager and webserver for consistent token handling."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    session: Annotated[
        SessionConfig,
        Field(default_factory=SessionConfig),
        BackendAIConfigMeta(
            description=(
                "Compute session configuration. Controls behavior and resource limits for "
                "compute sessions including default settings, timeouts, and session lifecycle "
                "management parameters."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    metric: Annotated[
        MetricConfig,
        Field(default_factory=MetricConfig),
        BackendAIConfigMeta(
            description=(
                "Metric collection configuration. Controls how the manager collects and queries "
                "performance metrics from Prometheus for session monitoring, idle detection, "
                "and resource optimization."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    volumes: Annotated[
        VolumesConfig,
        Field(default_factory=VolumesConfig),
        BackendAIConfigMeta(
            description=(
                "Virtual folder and storage volume configuration. Controls how storage volumes "
                "are managed, which folder types are enabled, and configures connections to "
                "storage proxy services for file operations."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    resource_slots: Annotated[
        ResourceSlotsConfig,
        Field(default_factory=ResourceSlotsConfig),
        BackendAIConfigMeta(
            description=(
                "Resource slot configuration. Defines available resource types beyond standard "
                "CPU and memory. Accelerator plugins add custom resource slots here for GPUs "
                "and other specialized hardware."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    otel: Annotated[
        OTELConfig,
        Field(default_factory=OTELConfig),
        BackendAIConfigMeta(
            description=(
                "OpenTelemetry configuration for distributed tracing. When enabled, sends trace "
                "data to an OpenTelemetry collector for request tracking across Backend.AI "
                "components. Useful for debugging and performance analysis."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    service_discovery: Annotated[
        ServiceDiscoveryConfig,
        Field(default_factory=ServiceDiscoveryConfig),
        BackendAIConfigMeta(
            description=(
                "Service discovery configuration. Controls how Backend.AI components discover "
                "and connect to each other in dynamic environments. Supports multiple discovery "
                "mechanisms for different deployment scenarios."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    artifact_registry: Annotated[
        ArtifactRegistryConfig | None,
        Field(
            default=None,
            validation_alias=AliasChoices("artifact_registry", "artifact-registry"),
            serialization_alias="artifact-registry",
        ),
        BackendAIConfigMeta(
            description=(
                "Default artifact registry configuration. Specifies the default model registry "
                "for artifact operations. When configured, enables model artifact management "
                "features in Backend.AI."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    reservoir: Annotated[
        ReservoirConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Reservoir configuration for model artifact storage. The reservoir system "
                "manages binary artifacts like trained models and checkpoints. Configure "
                "storage backends and import workflows here."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    deployment: Annotated[
        DeploymentConfig,
        Field(default_factory=DeploymentConfig),
        BackendAIConfigMeta(
            description=(
                "Deployment and model serving configuration. Controls behavior of the model "
                "deployment features in Backend.AI including inference endpoint management "
                "and model definition handling."
            ),
            added_version="25.8.0",
            composite=CompositeType.FIELD,
        ),
    ]
    export: Annotated[
        ExportConfig,
        Field(default_factory=ExportConfig),
        BackendAIConfigMeta(
            description=(
                "Export API configuration. Controls CSV export functionality including "
                "row limits, timeouts, and concurrency limits. These settings prevent "
                "resource exhaustion from large export operations."
            ),
            added_version="26.1.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # TODO: Remove me after changing the method of loading the license server address in the plugins
    model_config = ConfigDict(
        extra="allow",
    )

    def __repr__(self) -> str:
        return pformat(self.model_dump())
