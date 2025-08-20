from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, field_serializer, field_validator

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import RedisHelperConfig as RedisHelperConfigDict
from ai.backend.common.types import RedisProfileTarget, ValkeyProfileTarget, ValkeyTarget
from ai.backend.common.types import RedisTarget as _RedisTarget


class RedisHelperConfig(BaseModel):
    socket_timeout: float = Field(
        default=5.0,
        description="""
        Timeout in seconds for Redis socket operations.
        Controls how long operations wait before timing out.
        Increase for slow or congested networks.
        """,
        examples=[5.0, 10.0],
        validation_alias=AliasChoices("socket_timeout", "socket-timeout"),
        serialization_alias="socket_timeout",
    )
    socket_connect_timeout: float = Field(
        default=2.0,
        description="""
        Timeout in seconds for establishing Redis connections.
        Controls how long connection attempts wait before failing.
        Shorter values fail faster but may be too aggressive for some networks.
        """,
        examples=[2.0, 5.0],
        validation_alias=AliasChoices("socket_connect_timeout", "socket-connect-timeout"),
        serialization_alias="socket_connect_timeout",
    )
    reconnect_poll_timeout: float = Field(
        default=0.3,
        description="""
        Time in seconds to wait between reconnection attempts.
        Controls the polling frequency when trying to reconnect to Redis.
        Lower values reconnect faster but may increase network load.
        """,
        examples=[0.3, 1.0],
        validation_alias=AliasChoices("reconnect_poll_timeout", "reconnect-poll-timeout"),
        serialization_alias="reconnect_poll_timeout",
    )

    def to_dict(self) -> RedisHelperConfigDict:
        return RedisHelperConfigDict(
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            reconnect_poll_timeout=self.reconnect_poll_timeout,
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
        validation_alias=AliasChoices("service_name", "service-name"),
        serialization_alias="service-name",
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
    request_timeout: Optional[int] = Field(
        default=None,
        description="""
        Timeout in milliseconds for Redis requests.
        Controls how long operations wait before timing out.
        If None, uses the default timeout configured in the Redis client.
        """,
        examples=[None, 1000],
        validation_alias=AliasChoices("request_timeout", "request-timeout"),
        serialization_alias="request-timeout",
    )
    redis_helper_config: RedisHelperConfig = Field(
        default_factory=RedisHelperConfig,
        description="""
        Configuration for the Redis helper library.
        Controls timeouts and reconnection behavior.
        Adjust based on network conditions and reliability requirements.
        """,
        validation_alias=AliasChoices("redis_helper_config", "redis-helper-config"),
        serialization_alias="redis-helper-config",
    )
    use_tls: bool = Field(
        default=False,
        description="""
        Whether to use TLS for Redis connections.""",
        validation_alias=AliasChoices("use_tls", "use-tls"),
    )
    tls_skip_verify: bool = Field(
        default=False,
        description="""
        Whether to skip TLS certificate verification.
        Set to True for self-signed certificates or development environments.
        """,
        validation_alias=AliasChoices("tls_skip_verify", "tls-skip-verify"),
    )

    @field_validator("sentinel", mode="before")
    @classmethod
    def _parse_sentinel(
        cls, v: Optional[str | list[HostPortPairModel]]
    ) -> Optional[list[HostPortPairModel]]:
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
    def _serialize_addr(self, addr: Optional[HostPortPairModel], _info) -> Optional[str]:
        return None if addr is None else f"{addr.host}:{addr.port}"

    @field_serializer("sentinel")
    def _serialize_sentinel(
        self, sentinel: Optional[list[HostPortPairModel]], _info
    ) -> Optional[str]:
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
        validation_alias=AliasChoices("override_configs", "override-configs"),
        serialization_alias="override-configs",
    )

    def to_redis_profile_target(self) -> RedisProfileTarget:
        """
        Convert this Redis configuration to a profile target dictionary.
        This is used for serialization in the Backend.AI profile system.
        """
        addr = self.addr.to_legacy() if self.addr else None
        sentinel_addrs = None
        if self.sentinel:
            sentinel_addrs = [hp.to_legacy() for hp in self.sentinel]

        override_targets: Optional[dict[str, _RedisTarget]] = None
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
        override_targets: Optional[dict[str, ValkeyTarget]] = None
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
