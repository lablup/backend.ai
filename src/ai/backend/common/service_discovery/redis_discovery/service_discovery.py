import json
import uuid
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import RedisTarget

from ..service_discovery import ServiceDiscovery, ServiceMetadata

_DEFAULT_PREFIX = "service_discovery"
_DEFAULT_TTL = 60 * 3  # 3 minutes


@dataclass
class RedisServiceDiscoveryArgs:
    redis_target: RedisTarget
    db_id: int = 0
    ttl: int = _DEFAULT_TTL  # 3 minutes
    prefix: str = _DEFAULT_PREFIX


class RedisServiceDiscovery(ServiceDiscovery):
    _valkey_client: Optional[ValkeyLiveClient]
    _ttl: int
    _prefix: str

    def __init__(self, args: RedisServiceDiscoveryArgs) -> None:
        self._redis_target = args.redis_target
        self._db_id = args.db_id
        self._ttl = args.ttl
        self._prefix = args.prefix
        self._valkey_client = None  # Will be initialized in connect()

    async def connect(self) -> None:
        """Initialize the ValkeyLiveClient connection."""
        if self._valkey_client is None:
            self._valkey_client = await ValkeyLiveClient.create(
                self._redis_target,
                db_id=self._db_id,
                human_readable_name="service_discovery",
            )

    async def close(self) -> None:
        """Close the ValkeyLiveClient connection."""
        if self._valkey_client is not None:
            await self._valkey_client.close()
            self._valkey_client = None

    async def _hsetex(self, key: str, mapping: dict[str, Any]) -> None:
        """Set hash fields with expiry using ValkeyLiveClient."""
        if self._valkey_client is None:
            raise RuntimeError("ValkeyLiveClient not initialized. Call connect() first.")

        # Convert values to JSON strings
        json_mapping = {k: dump_json_str(v) for k, v in mapping.items()}
        await self._valkey_client.hset_with_expiry(key, json_mapping, self._ttl)

    async def _scan_keys(self, pattern: str) -> list[str]:
        """Scan keys matching pattern using ValkeyLiveClient."""
        if self._valkey_client is None:
            raise RuntimeError("ValkeyLiveClient not initialized. Call connect() first.")

        return await self._valkey_client.scan_keys(pattern)

    async def _hget_json(self, name: str) -> ServiceMetadata:
        """Get hash fields and parse JSON values using ValkeyLiveClient."""
        if self._valkey_client is None:
            raise RuntimeError("ValkeyLiveClient not initialized. Call connect() first.")

        raw_hash = await self._valkey_client.hgetall_str(name)
        if not raw_hash:
            raise ValueError(f"Service key {name} not found.")

        result: dict[str, Any] = {}
        for key, value in raw_hash.items():
            result[key] = json.loads(value)

        return ServiceMetadata.from_dict(result)

    async def register(self, service_meta: ServiceMetadata) -> None:
        key = self._service_prefix(service_meta.service_group, service_meta.id)
        await self._hsetex(key, service_meta.to_dict())

    async def unregister(self, service_group: str, service_id: uuid.UUID) -> None:
        """Unregister a service using ValkeyLiveClient."""
        if self._valkey_client is None:
            raise RuntimeError("ValkeyLiveClient not initialized. Call connect() first.")

        key = self._service_prefix(service_group, service_id)
        await self._valkey_client.delete_key(key)

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
