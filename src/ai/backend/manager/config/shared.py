from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, IPvAnyNetwork

from .local import HostPortPair


class SystemConfig(BaseModel):
    timezone: str = Field(
        default="UTC",
        description="""
        Timezone setting for the manager.
        Uses pytz-compatible timezone names.
        Affects how the manager reports timestamps in logs and APIs.
        """,
        examples=["UTC"],
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
    )
    allow_graphql_schema_introspection: bool = Field(
        default=False,
        description="""
        Whether to allow GraphQL schema introspection.
        Useful for development and debugging, but should be disabled in production.
        When disabled, GraphQL tools like GraphiQL won't be able to explore the schema.
        """,
        examples=[True, False],
    )
    allow_openapi_schema_introspection: bool = Field(
        default=False,
        description="""
        Whether to allow OpenAPI schema introspection.
        Useful for development and debugging, but should be disabled in production.
        When disabled, Swagger UI and similar tools won't work.
        """,
        examples=[True, False],
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
    addr: Optional[HostPortPair] = Field(
        default=None,
        description="""
        Network address and port of the Redis server.
        Redis is used for distributed caching and messaging between managers.
        Set to None when using Sentinel for high availability.
        """,
        examples=[None, {"host": "127.0.0.1", "port": 6379}],
    )
    sentinel: Optional[List[HostPortPair]] = Field(
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
    )


class RedisConfig(SingleRedisConfig):
    override_configs: Optional[Dict[str, SingleRedisConfig]] = Field(
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
    )


class DockerImageAutoPullPolicy(enum.StrEnum):
    digest = "digest"
    tag = "tag"
    none = "none"


class DockerImageConfig(BaseModel):
    auto_pull: DockerImageAutoPullPolicy = Field(
        default="digest",
        description="""
        Policy for automatically pulling Docker images.
        'digest': Pull if image digest has changed (most secure)
        'tag': Pull if image tag has changed
        'none': Never pull automatically (manual control)
        """,
        examples=["digest", "tag", "none"],
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
    accelerator: dict[str, dict[str, Any]] = Field(
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
    )


class SubnetConfig(BaseModel):
    agent: IPvAnyNetwork = Field(
        default="0.0.0.0/0",
        description="""
        IP subnet for agent communications.
        Specifies which subnet is used for agent-to-agent and agent-to-manager traffic.
        Use 0.0.0.0/0 to allow all IPv4 addresses.
        """,
        examples=["0.0.0.0/0", "192.168.0.0/24"],
    )
    container: IPvAnyNetwork = Field(
        default="0.0.0.0/0",
        description="""
        IP subnet for containers.
        Specifies which subnet is used for container networks.
        Use 0.0.0.0/0 to allow all IPv4 addresses.
        """,
        examples=["0.0.0.0/0", "172.17.0.0/16"],
    )


class NetworkConfig(BaseModel):
    inter_container: InterContainerNetworkConfig = Field(
        default_factory=InterContainerNetworkConfig,
        description="""
        Settings for networks between containers.
        Controls how containers communicate with each other.
        """,
    )
    subnet: SubnetConfig = Field(
        default_factory=SubnetConfig,
        description="""
        Subnet configurations for the Backend.AI network.
        Defines IP ranges for agents and containers.
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
        default=10,
        description="""
        Timeout in seconds for file I/O operations in watcher.
        Controls how long the watcher waits for file operations to complete.
        Increase for handling large files or slow storage systems.
        """,
        examples=[60.0, 120.0],
    )


class AuthConfig(BaseModel):
    max_password_age: Optional[datetime] = Field(
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
    )


# TODO: Need to rethink if we need to separate shared manager configs
class SharedManagerConfig(BaseModel):
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
