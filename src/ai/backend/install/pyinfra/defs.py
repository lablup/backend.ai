from functools import reduce
from ipaddress import IPv4Address
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator


def _to_ipv4_or_none(value: str | IPv4Address | None) -> IPv4Address | None:
    """Convert an optional string to IPv4Address, passing through existing values.

    This keeps field validators concise across multiple models.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return IPv4Address(value)
    return value


class RedisClusterNodeConfig(BaseModel):
    service_ip: str | IPv4Address | None = Field(default=None)
    service_port: Annotated[int, Field(strict=True, gt=0, lt=65535)]
    node_number: Annotated[int, Field(strict=True, ge=1, le=3)]

    @field_validator("service_ip")
    def validate_ip(cls, v: Any) -> IPv4Address | None:
        return _to_ipv4_or_none(v)


class RedisClusterConfig(BaseModel):
    name: str | None = Field(default=None)
    password: str | None = Field(default=None)
    redis_nodes: list[RedisClusterNodeConfig] = Field(default_factory=list)
    pids_limit: Annotated[int, Field(strict=True, ge=100, le=3000)]

    @field_validator("name")
    def validate_name(cls, v: Any) -> str:
        if len(v) < 1 or not v:
            raise ValueError("Invalid name of redis cluster")
        return v

    @field_validator("password")
    def validate_password(cls, v: Any) -> str:
        if not v or len(v) < 32:
            raise ValueError("The length of Redis cluster password have to be over 32 characters ")
        # only alphabet and number is ok
        if not reduce(lambda a, b: a and b, (x.isalpha() or x.isdigit() for x in v)):
            raise ValueError("Only alphabet and number is acceptable")
        return v


class RedisClusterSentinelConfig(BaseModel):
    service_ip: str | IPv4Address | None = Field(default=None)
    service_port: Annotated[int, Field(strict=True, gt=0, lt=65535)]
    cluster: RedisClusterConfig

    @field_validator("service_ip")
    def validate_ip(cls, v: Any) -> IPv4Address | None:
        return _to_ipv4_or_none(v)


class RedisHaproxyConfig(BaseModel):
    service_ip: str | IPv4Address | None = Field(default=None)
    service_port: Annotated[int, Field(strict=True, gt=0, lt=65535)]
    stat_port: Annotated[int, Field(strict=True, gt=0, lt=65535)]
    cluster: RedisClusterConfig

    @field_validator("service_ip")
    def validate_ip(cls, v: Any) -> IPv4Address | None:
        return _to_ipv4_or_none(v)


class EtcdClusterNodeConfig(BaseModel):
    service_ip: str | IPv4Address | None = Field(default=None)
    service_port: Annotated[int, Field(strict=True, gt=0, lt=65535)]
    peer_port: Annotated[int, Field(strict=True, gt=0, lt=65535)]
    node_number: Annotated[int, Field(strict=True, ge=1, le=3)]

    @field_validator("service_ip")
    def validate_ip(cls, v: Any) -> IPv4Address | None:
        return _to_ipv4_or_none(v)


class EtcdClusterConfig(BaseModel):
    name: str | None = Field(default=None)
    etcd_nodes: list[EtcdClusterNodeConfig] = Field(default_factory=list)
    pids_limit: Annotated[int, Field(strict=True, ge=100, le=3000)]

    @field_validator("name")
    def validate_name(cls, v: Any) -> str:
        if len(v) < 1 or not v:
            raise ValueError("Invalid name of etcd cluster")
        return v


class EtcdGrpcConfig(BaseModel):
    service_ip: str | IPv4Address | None = Field(default=None)
    service_port: Annotated[int, Field(strict=True, gt=0, lt=65535)]
    container_img: str = "cr.backend.ai/halfstack/etcd-grpcproxy:v3.4.22"
    cluster: EtcdClusterConfig

    @field_validator("service_ip")
    def validate_ip(cls, v: Any) -> IPv4Address | None:
        return _to_ipv4_or_none(v)
