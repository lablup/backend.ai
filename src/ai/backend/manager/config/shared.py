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
         + "timeout"
           - threshold: "10m"
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
import sys
import urllib
from collections.abc import Mapping
from contextvars import ContextVar
from datetime import datetime, timezone
from ipaddress import IPv4Network
from pprint import pformat
from typing import Any, Final, List, Optional, Sequence, TypeAlias

import aiotools
import click
import yarl
from pydantic import BaseModel, ConfigDict, Field, IPvAnyNetwork, field_serializer

from ai.backend.common import config
from ai.backend.common.defs import DEFAULT_FILE_IO_TIMEOUT
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.identity import get_instance_id
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.typed_validators import (
    TimeDuration,
    TimeZone,
    _TimeDurationPydanticAnnotation,
)
from ai.backend.common.types import (
    HostPortPair,
    SlotName,
    SlotTypes,
    current_resource_slots,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.defs import DEFAULT_METRIC_RANGE_VECTOR_TIMEWINDOW, INTRINSIC_SLOTS
from ai.backend.manager.errors.exceptions import ServerMisconfiguredError

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8

NestedStrKeyedDict: TypeAlias = "dict[str, Any | NestedStrKeyedDict]"

current_vfolder_types: ContextVar[List[str]] = ContextVar("current_vfolder_types")


class SystemConfig(BaseModel):
    timezone: TimeZone = Field(
        default_factory=lambda: timezone.utc,
        description="""
        Timezone setting for the manager.
        Uses pytz-compatible timezone names.
        """,
        examples=["UTC"],
    )


class ResourcesConfig(BaseModel):
    group_resource_visibility: bool = Field(
        default=False,
        description="""
        Whether to return group resource status in check-presets.
        If true, group resources are visible to all users in the group.
        """,
        examples=[True, False],
    )


class APIConfig(BaseModel):
    allow_origins: str = Field(
        default="*",
        description="""
        CORS allow-origins setting.
        Use '*' to allow all origins, or specify comma-separated domain patterns.
        Important for browser-based clients connecting to the API.
        """,
        examples=["*", "https://example.com"],
        alias="allow-origins",
    )
    allow_graphql_schema_introspection: bool = Field(
        default=False,
        description="""
        Whether to allow GraphQL schema introspection.
        Useful for development and debugging, but should be disabled in production.
        When disabled, GraphQL tools like GraphiQL won't be able to explore the schema.
        """,
        examples=[True, False],
        alias="allow-graphql-schema-introspection",
    )
    allow_openapi_schema_introspection: bool = Field(
        default=False,
        description="""
        Whether to allow OpenAPI schema introspection.
        Useful for development and debugging, but should be disabled in production.
        When disabled, Swagger UI and similar tools won't work.
        """,
        examples=[True, False],
        alias="allow-openapi-schema-introspection",
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
        alias="max-gql-query-depth",
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
        alias="max-gql-connection-page-size",
    )
    resources: Optional[ResourcesConfig] = Field(
        default=None,
        description="""
        Resource visibility settings.
        Controls how resources are shared and visible between users and groups.
        """,
        examples=[None, {"group_resource_visibility": True}],
    )


class RedisHelperConfig(BaseModel):
    socket_timeout: float = Field(
        default=5.0,
        description="""
        Timeout in seconds for Redis socket operations.
        Controls how long operations wait before timing out.
        Increase for slow or congested networks.
        """,
        examples=[5.0, 10.0],
    )
    socket_connect_timeout: float = Field(
        default=2.0,
        description="""
        Timeout in seconds for establishing Redis connections.
        Controls how long connection attempts wait before failing.
        Shorter values fail faster but may be too aggressive for some networks.
        """,
        examples=[2.0, 5.0],
    )
    reconnect_poll_timeout: float = Field(
        default=0.3,
        description="""
        Time in seconds to wait between reconnection attempts.
        Controls the polling frequency when trying to reconnect to Redis.
        Lower values reconnect faster but may increase network load.
        """,
        examples=[0.3, 1.0],
    )


class SingleRedisConfig(BaseModel):
    addr: Optional[HostPortPairModel] = Field(
        default=None,
        description="""
        Network address and port of the Redis server.
        Redis is used for distributed caching and messaging between managers.
        Set to None when using Sentinel for high availability.
        """,
        examples=[None, {"host": "127.0.0.1", "port": 6379}],
    )
    sentinel: Optional[list[HostPortPairModel]] = Field(
        default=None,
        description="""
        List of Redis Sentinel addresses for high availability.
        If provided, the manager will use Redis Sentinel for automatic failover.
        When using Sentinel, the addr field is ignored and service_name is required.
        """,
        examples=[
            None,
            [{"host": "redis-sentinel", "port": 26379}, {"host": "redis-sentinel", "port": 26380}],
        ],
    )
    service_name: Optional[str] = Field(
        default=None,
        description="""
        Service name for Redis Sentinel.
        Required when using Redis Sentinel for high availability.
        Identifies which service to monitor for failover.
        """,
        examples=[None, "mymaster", "backend-ai"],
        alias="service-name",
    )
    password: Optional[str] = Field(
        default=None,
        description="""
        Password for authenticating with Redis.
        Set to None if Redis doesn't require authentication.
        Should be kept secret in production environments.
        """,
        examples=[None, "REDIS_PASSWORD"],
    )
    redis_helper_config: RedisHelperConfig = Field(
        default_factory=RedisHelperConfig,
        description="""
        Configuration for the Redis helper library.
        Controls timeouts and reconnection behavior.
        Adjust based on network conditions and reliability requirements.
        """,
        alias="redis-helper-config",
    )

    @field_serializer("addr")
    def _serialize_addr(self, addr: Optional[HostPortPairModel], _info) -> Optional[str]:
        return None if addr is None else f"{addr.host}:{addr.port}"

    @field_serializer("sentinel")
    def _serialize_sentinel(
        self, sentinel: Optional[list[HostPortPairModel]], _info
    ) -> Optional[str]:
        if sentinel is None:
            return None
        return ",".join(f"{hp.host}:{hp.port}" for hp in sentinel)


class RedisConfig(SingleRedisConfig):
    override_configs: Optional[dict[str, SingleRedisConfig]] = Field(
        default=None,
        description="""
        Optional override configurations for specific Redis contexts.
        Allows different Redis settings for different services within Backend.AI.
        Each key represents a context name, and the value is a complete Redis configuration.
        """,
        examples=[
            None,
            {
                "live": {
                    "addr": {"host": "127.0.0.1", "port": 6379},
                    "password": "different-password",
                    "redis_helper_config": {"socket_timeout": 10.0},
                }
            },
        ],
        alias="override-configs",
    )


class DockerImageAutoPullPolicy(enum.StrEnum):
    digest = "digest"
    tag = "tag"
    none = "none"


class DockerImageConfig(BaseModel):
    auto_pull: DockerImageAutoPullPolicy = Field(
        default=DockerImageAutoPullPolicy.digest,
        description="""
        Policy for automatically pulling Docker images.
        'digest': Pull if image digest has changed (most secure)
        'tag': Pull if image tag has changed
        'none': Never pull automatically (manual control)
        """,
        examples=[item.value for item in DockerImageAutoPullPolicy],
    )


class DockerConfig(BaseModel):
    image: DockerImageConfig = Field(
        default_factory=DockerImageConfig,
        description="""
        Docker image management settings.
        Controls how the manager handles Docker images.
        """,
    )


class PluginsConfig(BaseModel):
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
        alias="agent-selector",
    )
    network: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="""
        Network plugin configurations.
        """,
        examples=[{"overlay": {"mtu": 1500}}],
    )


class InterContainerNetworkConfig(BaseModel):
    default_driver: Optional[str] = Field(
        default="overlay",
        description="""
        Default network driver for inter-container communication.
        'overlay' is typically used for multi-host networking.
        Container communication performance depends on this setting.
        """,
        examples=["overlay", None],
        alias="default-driver",
    )
    # TODO: Write description
    enabled: bool = Field(
        default=False,
        description="""
        """,
        examples=[True, False],
    )
    # TODO: Write description
    plugin: Optional[str] = Field(
        default=None,
        description="""
        """,
    )
    enabled: bool = Field(
        default=False,
        description="""
        """,
        examples=[True, False],
    )
    plugin: Optional[str] = Field(
        default=None,
        description="""
        """,
    )


class SubnetNetworkConfig(BaseModel):
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


class RpcConfig(BaseModel):
    keepalive_timeout: float = Field(
        default=60.0,
        # TODO: Write description
        description="""
        """,
        examples=[60.0, 120.0],
        alias="keepalive-timeout",
    )


class NetworkConfig(BaseModel):
    inter_container: InterContainerNetworkConfig = Field(
        default_factory=InterContainerNetworkConfig,
        description="""
        Settings for networks between containers.
        Controls how containers communicate with each other.
        """,
        alias="inter-container",
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


class WatcherConfig(BaseModel):
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
        alias="file-io-timeout",
    )


class AuthConfig(BaseModel):
    max_password_age: Optional[TimeDuration] = Field(
        default=None,
        description="""
        Maximum password age before requiring a change.
        Format is a duration string like "90d" for 90 days.
        Set to None to disable password expiration.
        """,
        examples=[None, "90d", "180d"],
    )


class HangToleranceThresholdConfig(BaseModel):
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


class HangToleranceConfig(BaseModel):
    threshold: HangToleranceThresholdConfig = Field(
        default_factory=HangToleranceThresholdConfig,
        description="""
        Threshold settings for detecting hung sessions.
        Defines timeouts for different session states.
        """,
    )


class SessionConfig(BaseModel):
    hang_tolerance: HangToleranceConfig = Field(
        default_factory=HangToleranceConfig,
        description="""
        Configuration for detecting and handling hung sessions.
        Controls how the system detects and recovers from session failures.
        """,
        alias="hang-tolerance",
    )


class MetricConfig(BaseModel):
    address: HostPortPairModel = Field(
        default=HostPortPairModel(host="127.0.0.1", port=9090),
        description="""
        Address for the metric collection service.
        """,
        examples=[None, {"host": "127.0.0.1", "port": 9090}],
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
    def _serialize_addr(self, addr: Optional[HostPortPairModel], _info: Any) -> Optional[str]:
        return None if addr is None else f"{addr.host}:{addr.port}"


class IdleCheckerConfig(BaseModel):
    enabled: str = Field(
        default="timeout,utilization",
        description="""
        Enabled idle checkers.
        Comma-separated list of checker names.
        """,
        examples=["timeout", "utilization"],
    )
    app_streaming_packet_timeout: TimeDuration = Field(
        default=_TimeDurationPydanticAnnotation.time_duration_validator("5m"),
        description="""
        Timeout for app-streaming TCP connections.
        Controls how long the system waits before considering a connection idle.
        """,
        examples=["5m", "10m"],
    )
    checkers: dict[str, Any] = Field(
        default_factory=dict,
        description="""
        Idle checkers configurations.
        """,
        examples=[
            {
                "timeout": {
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


class VolumesConfig(BaseModel):
    types: dict[str, Any] = Field(
        default_factory=dict,
        description="""
        """,
        examples=[{"user": {}, "group": {}}],
        alias="_types",
    )
    default_host: Optional[str] = Field(
        default=None,
        description="""
        """,
        examples=[None, "localhost:6021"],
    )
    proxies: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="""
        """,
        examples=[
            {
                "local": {
                    "client_api": "http://localhost:6021",
                    "manager_api": "http://localhost:6022",
                    "secret": "xxxxxx...",
                    "ssl_verify": True,
                    "sftp_scaling_groups": "group-1,group-2,...",
                },
                "mynas1": {
                    "client_api": "https://proxy1.example.com:6021",
                    "manager_api": "https://proxy1.example.com:6022",
                    "secret": "xxxxxx...",
                    "ssl_verify": True,
                    "sftp_scaling_groups": "group-3,group-4,...",
                },
            }
        ],
    )
    exposed_volume_info: Optional[str] = Field(
        default=None,
        description="""
        """,
        examples=[None, "percentage"],
    )


# TODO: Make this more precise type
class ResourceSlotsConfig(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )


# TODO: Need to rethink if we need to separate shared manager configs
class ManagerSharedConfigDataModel(BaseModel):
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
    auth: Optional[AuthConfig] = Field(
        default=None,
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
        Controls how resources are allocated and managed.
        """,
    )


class ManagerSharedConfig:
    data: ManagerSharedConfigDataModel

    def __init__(
        self,
        etcd_addr: HostPortPair,
        etcd_user: Optional[str],
        etcd_password: Optional[str],
        namespace: str,
    ) -> None:
        super().__init__()
        credentials = None
        if etcd_user:
            assert etcd_user is not None
            assert etcd_password is not None
            credentials = {
                "user": etcd_user,
                "password": etcd_password,
            }
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
            # TODO: provide a way to specify other scope prefixes
        }
        self.etcd = AsyncEtcd(etcd_addr, namespace, scope_prefix_map, credentials=credentials)

    async def close(self) -> None:
        await self.etcd.close()

    async def reload(self) -> None:
        raw_cfg = await self.etcd.get_prefix("config")

        try:
            self.data = ManagerSharedConfigDataModel.model_validate(raw_cfg)
        except config.ConfigurationError as e:
            print("Validation of shared etcd configuration has failed:", file=sys.stderr)
            print(pformat(e.invalid_data), file=sys.stderr)
            raise click.Abort()

    def __hash__(self) -> int:
        # When used as a key in dicts, we don't care our contents.
        # Just treat it like an opaque object.
        return hash(id(self))

    @classmethod
    def flatten(cls, key_prefix: str, inner_dict: NestedStrKeyedDict) -> dict[str, str]:
        flattend_dict: dict[str, str] = {}
        for k, v in inner_dict.items():
            if k == "":
                flattened_key = key_prefix
            else:
                flattened_key = key_prefix + "/" + urllib.parse.quote(k, safe="")
            match v:
                case Mapping():
                    flattend_dict.update(cls.flatten(flattened_key, v))  # type: ignore
                case str():
                    flattend_dict[flattened_key] = v
                case int() | float() | yarl.URL():
                    flattend_dict[flattened_key] = str(v)
                case _:
                    raise ValueError(
                        f"The value {v!r} must be serialized before storing to the etcd"
                    )
        return flattend_dict

    async def get_raw(self, key: str, allow_null: bool = True) -> Optional[str]:
        value = await self.etcd.get(key)
        if not allow_null and value is None:
            raise ServerMisconfiguredError("A required etcd config is missing.", key)
        return value

    async def register_myself(self) -> None:
        instance_id = await get_instance_id()
        manager_info = {
            f"nodes/manager/{instance_id}": "up",
        }
        await self.etcd.put_dict(manager_info)

    async def deregister_myself(self) -> None:
        instance_id = await get_instance_id()
        await self.etcd.delete_prefix(f"nodes/manager/{instance_id}")

    async def update_resource_slots(
        self,
        slot_key_and_units: Mapping[SlotName, SlotTypes],
    ) -> None:
        updates = {}
        known_slots = await self.get_resource_slots()
        for k, v in slot_key_and_units.items():
            if k not in known_slots or v != known_slots[k]:
                updates[f"config/resource_slots/{k}"] = v.value
        if updates:
            await self.etcd.put_dict(updates)

    async def update_manager_status(self, status) -> None:
        await self.etcd.put("manager/status", status.value)
        self.get_manager_status.cache_clear()

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def _get_resource_slots(self):
        raw_data = await self.etcd.get_prefix_dict("config/resource_slots")
        return {SlotName(k): SlotTypes(v) for k, v in raw_data.items()}

    async def get_resource_slots(self) -> Mapping[SlotName, SlotTypes]:
        """
        Returns the system-wide known resource slots and their units.
        """
        try:
            ret = current_resource_slots.get()
        except LookupError:
            configured_slots = await self._get_resource_slots()
            ret = {**INTRINSIC_SLOTS, **configured_slots}
            current_resource_slots.set(ret)
        return ret

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def _get_vfolder_types(self):
        return await self.etcd.get_prefix("volumes/_types")

    async def get_vfolder_types(self) -> Sequence[str]:
        """
        Returns the vfolder types currently set. One of "user" and/or "group".
        If none is specified, "user" type is implicitly assumed.
        """
        try:
            ret = current_vfolder_types.get()
        except LookupError:
            vf_types = await self._get_vfolder_types()
            ret = list(vf_types.keys())
            current_vfolder_types.set(ret)
        return ret

    @aiotools.lru_cache(maxsize=1, expire_after=5.0)
    async def get_manager_nodes_info(self):
        return await self.etcd.get_prefix_dict("nodes/manager")

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def get_manager_status(self) -> ManagerStatus:
        status = await self.etcd.get("manager/status")
        if status is None:
            return ManagerStatus.TERMINATED
        return ManagerStatus(status)

    async def watch_manager_status(self):
        async with aiotools.aclosing(self.etcd.watch("manager/status")) as agen:
            async for ev in agen:
                yield ev

    # TODO: refactor using contextvars in Python 3.7 so that the result is cached
    #       in a per-request basis.
    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def get_allowed_origins(self):
        return await self.etcd.get("config/api/allow-origins")

    def get_redis_url(self, db: int = 0) -> yarl.URL:
        """
        Returns a complete URL composed from the given Redis config.
        """
        if not self.data.redis.addr:
            raise ValueError("Redis config is not set.")

        url = yarl.URL("redis://host").with_host(str(self.data.redis.addr.host)).with_port(
            self.data.redis.addr.port
        ).with_password(self.data.redis.password) / str(db)
        return url
