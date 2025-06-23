import json
import uuid
from dataclasses import dataclass
from typing import Any, Sequence

from redis.asyncio.client import Pipeline, Redis

from ai.backend.common import redis_helper
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import RedisConnectionInfo

from ..service_discovery import ServiceDiscovery, ServiceMetadata

_DEFAULT_PREFIX = "service_discovery"
_DEFAULT_TTL = 60 * 3  # 3 minutes


@dataclass
class RedisServiceDiscoveryArgs:
    redis: RedisConnectionInfo
    ttl: int = _DEFAULT_TTL  # 3 minutes
    prefix: str = _DEFAULT_PREFIX


class RedisServiceDiscovery(ServiceDiscovery):
    _redis: RedisConnectionInfo
    _ttl: int
    _prefix: str

    def __init__(self, args: RedisServiceDiscoveryArgs) -> None:
        self._redis = args.redis
        self._ttl = args.ttl
        self._prefix = args.prefix

    async def _hsetex(self, key: str, mapping: dict[str, Any]) -> None:
        # TODO: Use actual `hsetex` after upgrading to redis-py 8.0
        async def _pipe_builder(r: Redis) -> Pipeline:
            pipe = r.pipeline()
            await pipe.hset(key, mapping={k: dump_json_str(v) for k, v in mapping.items()})
            await pipe.expire(key, self._ttl)
            await pipe.execute()
            return pipe

        await redis_helper.execute(self._redis, _pipe_builder)

    async def _scan_keys(self, pattern: str) -> list[str]:
        async def _run(r: Redis) -> list[str]:
            return [key.decode() async for key in r.scan_iter(match=pattern, count=100)]

        return await redis_helper.execute(self._redis, _run)

    async def _hget_json(self, name: str) -> ServiceMetadata:
        raw_hash: dict[bytes, bytes] = await redis_helper.execute(
            self._redis, lambda r: r.hgetall(name)
        )
        if not raw_hash:
            raise ValueError(f"Service key {name} not found.")

        result: dict[str, Any] = {}
        for raw_key, raw_value in raw_hash.items():
            key = raw_key.decode()
            value = json.loads(raw_value)
            result[key] = value

        return ServiceMetadata.from_dict(result)

    async def register(self, service_meta: ServiceMetadata) -> None:
        key = self._service_prefix(service_meta.service_group, service_meta.id)
        await self._hsetex(key, service_meta.to_dict())

    async def unregister(self, service_group: str, service_id: uuid.UUID) -> None:
        key = self._service_prefix(service_group, service_id)
        await redis_helper.execute(
            self._redis,
            lambda r: r.delete(key),
            service_name=self._redis.service_name,
        )

    async def heartbeat(self, service_meta: ServiceMetadata) -> None:
        service_meta.health_status.update_heartbeat()
        key = self._service_prefix(service_meta.service_group, service_meta.id)
        await self._hsetex(key, service_meta.to_dict())

    async def discover(self) -> Sequence[ServiceMetadata]:
        pattern = f"{self._prefix}.*.*"
        keys = await self._scan_keys(pattern)
        if not keys:
            raise ValueError("No service groups found.")
        return [await self._hget_json(key) for key in keys]

    async def get_service_group(self, service_group: str) -> Sequence[ServiceMetadata]:
        pattern = f"{self._service_group_prefix(service_group)}.*"
        keys = await self._scan_keys(pattern)
        if not keys:
            raise ValueError(f"No services found in group {service_group}.")
        return [await self._hget_json(key) for key in keys]

    async def get_service(self, service_group: str, service_id: uuid.UUID) -> ServiceMetadata:
        key = self._service_prefix(service_group, service_id)
        return await self._hget_json(key)

    def _service_group_prefix(self, service_group: str) -> str:
        return f"{self._prefix}.{service_group}"

    def _service_prefix(self, service_group: str, service_id: uuid.UUID) -> str:
        return f"{self._service_group_prefix(service_group)}.{service_id}"
