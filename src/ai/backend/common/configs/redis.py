from __future__ import annotations

from typing import Annotated, Any

from pydantic import AliasChoices, BaseModel, Field, field_serializer, field_validator

from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import RedisHelperConfig as RedisHelperConfigDict
from ai.backend.common.types import RedisProfileTarget, ValkeyProfileTarget, ValkeyTarget
from ai.backend.common.types import RedisTarget as _RedisTarget


class RedisHelperConfig(BaseModel):
    socket_timeout: Annotated[
        float,
        Field(
            default=5.0,
            validation_alias=AliasChoices("socket_timeout", "socket-timeout"),
            serialization_alias="socket_timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for Redis socket operations. "
                "Controls how long operations wait before timing out. "
                "Increase for slow or congested networks."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="5.0", prod="10.0"),
        ),
    ]
    socket_connect_timeout: Annotated[
        float,
        Field(
            default=2.0,
            validation_alias=AliasChoices("socket_connect_timeout", "socket-connect-timeout"),
            serialization_alias="socket_connect_timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for establishing Redis connections. "
                "Controls how long connection attempts wait before failing. "
                "Shorter values fail faster but may be too aggressive for some networks."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="2.0", prod="5.0"),
        ),
    ]
    reconnect_poll_timeout: Annotated[
        float,
        Field(
            default=0.3,
            validation_alias=AliasChoices("reconnect_poll_timeout", "reconnect-poll-timeout"),
            serialization_alias="reconnect_poll_timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Time in seconds to wait between reconnection attempts. "
                "Controls the polling frequency when trying to reconnect to Redis. "
                "Lower values reconnect faster but may increase network load."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="0.3", prod="1.0"),
        ),
    ]
    connection_ready_timeout: Annotated[
        float,
        Field(
            default=20.0,
            validation_alias=AliasChoices("connection_ready_timeout", "connection-ready-timeout"),
            serialization_alias="connection_ready_timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds to wait for a connection from the blocking connection pool. "
                "Used by BlockingConnectionPool for distributed locking scenarios. "
                "If no connection is available within this time, a timeout error is raised."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="20.0", prod="30.0"),
        ),
    ]

    def to_dict(self) -> RedisHelperConfigDict:
        return RedisHelperConfigDict(
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            reconnect_poll_timeout=self.reconnect_poll_timeout,
            connection_ready_timeout=self.connection_ready_timeout,
        )


class SingleRedisConfig(BaseModel):
    addr: Annotated[
        HostPortPairModel | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Network address and port of the Redis server. "
                "Redis is used for distributed caching and messaging between managers. "
                "Set to None when using Sentinel for high availability."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="127.0.0.1:6379", prod="redis-server:6379"),
        ),
    ]
    sentinel: Annotated[
        list[HostPortPairModel] | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "List of Redis Sentinel addresses for high availability. "
                "If provided, the manager will use Redis Sentinel for automatic failover. "
                "When using Sentinel, the addr field is ignored and service_name is required."
            ),
            added_version="25.13.0",
            composite=CompositeType.LIST,
            example=ConfigExample(
                local="",
                prod="redis-sentinel:26379",
            ),
        ),
    ]
    service_name: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("service_name", "service-name"),
            serialization_alias="service-name",
        ),
        BackendAIConfigMeta(
            description=(
                "Service name for Redis Sentinel. "
                "Required when using Redis Sentinel for high availability. "
                "Identifies which service to monitor for failover."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="mymaster", prod="backend-ai"),
        ),
    ]
    password: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Password for authenticating with Redis. "
                "Set to None if Redis doesn't require authentication. "
                "Should be kept secret in production environments."
            ),
            added_version="25.13.0",
            secret=True,
            example=ConfigExample(local="", prod="REDIS_PASSWORD"),
        ),
    ]
    request_timeout: Annotated[
        int | None,
        Field(
            default=None,
            validation_alias=AliasChoices("request_timeout", "request-timeout"),
            serialization_alias="request-timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in milliseconds for Redis requests. "
                "Controls how long operations wait before timing out. "
                "If None, uses the default timeout configured in the Redis client."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="1000", prod="5000"),
        ),
    ]
    redis_helper_config: Annotated[
        RedisHelperConfig,
        Field(
            default_factory=RedisHelperConfig,
            validation_alias=AliasChoices("redis_helper_config", "redis-helper-config"),
            serialization_alias="redis-helper-config",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for the Redis helper library. "
                "Controls timeouts and reconnection behavior. "
                "Adjust based on network conditions and reliability requirements."
            ),
            added_version="25.13.0",
            composite=CompositeType.FIELD,
        ),
    ]
    use_tls: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("use_tls", "use-tls"),
        ),
        BackendAIConfigMeta(
            description="Whether to use TLS for Redis connections.",
            added_version="25.13.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    tls_skip_verify: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("tls_skip_verify", "tls-skip-verify"),
        ),
        BackendAIConfigMeta(
            description=(
                "Whether to skip TLS certificate verification. "
                "Set to True for self-signed certificates or development environments."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]

    @field_validator("sentinel", mode="before")
    @classmethod
    def _parse_sentinel(
        cls, v: str | list[HostPortPairModel] | None
    ) -> list[HostPortPairModel] | None:
        if v is None or isinstance(v, list):
            return v
        if isinstance(v, str):
            entries: list[HostPortPairModel] = []
            for part in v.split(","):
                host, port = part.strip().split(":")
                entries.append(HostPortPairModel(host=host, port=int(port)))
            return entries
        raise TypeError("sentinel must be list or 'host:port,host:port' string")

    @field_serializer("addr")
    def _serialize_addr(self, addr: HostPortPairModel | None, _info: Any) -> str | None:
        return None if addr is None else f"{addr.host}:{addr.port}"

    @field_serializer("sentinel")
    def _serialize_sentinel(
        self, sentinel: list[HostPortPairModel] | None, _info: Any
    ) -> str | None:
        if sentinel is None:
            return None
        return ",".join(f"{hp.host}:{hp.port}" for hp in sentinel)

    def to_redis_target(self) -> _RedisTarget:
        """
        Convert this Redis configuration to a Redis target.
        This is used for serialization in the Backend.AI profile system.
        """
        addr = self.addr.to_legacy() if self.addr else None
        sentinel_addrs = None
        if self.sentinel:
            sentinel_addrs = [hp.to_legacy() for hp in self.sentinel]

        return _RedisTarget(
            addr=addr,
            sentinel=sentinel_addrs,
            service_name=self.service_name,
            password=self.password,
            redis_helper_config=self.redis_helper_config.to_dict(),
        )

    def to_valkey_target(self) -> ValkeyTarget:
        """
        Convert this Redis configuration to a Valkey target.
        This is used for serialization in the Backend.AI profile system.
        """
        addr = self.addr.address if self.addr else None
        sentinel_addrs = None
        if self.sentinel:
            sentinel_addrs = [hp.address for hp in self.sentinel]

        return ValkeyTarget(
            addr=addr,
            sentinel=sentinel_addrs,
            service_name=self.service_name,
            password=self.password,
            request_timeout=self.request_timeout,
        )


class RedisConfig(SingleRedisConfig):
    override_configs: Annotated[
        dict[str, SingleRedisConfig] | None,
        Field(
            default=None,
            validation_alias=AliasChoices("override_configs", "override-configs"),
            serialization_alias="override-configs",
        ),
        BackendAIConfigMeta(
            description=(
                "Optional override configurations for specific Redis contexts. "
                "Allows different Redis settings for different services within Backend.AI. "
                "Each key represents a context name, and the value is a complete Redis configuration."
            ),
            added_version="25.13.0",
            composite=CompositeType.FIELD,
        ),
    ]

    def to_redis_profile_target(self) -> RedisProfileTarget:
        """
        Convert this Redis configuration to a profile target dictionary.
        This is used for serialization in the Backend.AI profile system.
        """
        addr = self.addr.to_legacy() if self.addr else None
        sentinel_addrs = None
        if self.sentinel:
            sentinel_addrs = [hp.to_legacy() for hp in self.sentinel]

        override_targets: dict[str, _RedisTarget] | None = None
        if self.override_configs:
            override_targets = {k: v.to_redis_target() for k, v in self.override_configs.items()}

        return RedisProfileTarget(
            addr=addr,
            sentinel=sentinel_addrs,
            service_name=self.service_name,
            password=self.password,
            redis_helper_config=self.redis_helper_config.to_dict(),
            override_targets=override_targets,
        )

    def to_valkey_profile_target(self) -> ValkeyProfileTarget:
        """
        Convert this Valkey configuration to a profile target dictionary.
        This is used for serialization in the Backend.AI profile system.
        """
        addr = self.addr.address if self.addr else None
        sentinel_addrs = None
        if self.sentinel:
            sentinel_addrs = [hp.address for hp in self.sentinel]
        override_targets: dict[str, ValkeyTarget] | None = None
        if self.override_configs:
            override_targets = {k: v.to_valkey_target() for k, v in self.override_configs.items()}

        return ValkeyProfileTarget(
            addr=addr,
            sentinel=sentinel_addrs,
            service_name=self.service_name,
            password=self.password,
            override_targets=override_targets,
            request_timeout=self.request_timeout,
        )
