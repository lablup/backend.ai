import json
import uuid
from dataclasses import dataclass
from typing import Any, Self, Sequence

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import ValkeyTarget

from ..service_discovery import (
    MODEL_SERVICE_GROUP,
    MODEL_SERVICE_ROUTE_TTL,
    ModelServiceMetadata,
    ServiceDiscovery,
    ServiceMetadata,
)

_DEFAULT_PREFIX = "service_discovery"
_DEFAULT_TTL = 60 * 3  # 3 minutes


@dataclass
class RedisServiceDiscoveryArgs:
    valkey_target: ValkeyTarget
    db_id: int = 0
    ttl: int = _DEFAULT_TTL  # 3 minutes
    prefix: str = _DEFAULT_PREFIX


class RedisServiceDiscovery(ServiceDiscovery):
    _valkey_client: ValkeyLiveClient
    _ttl: int
    _prefix: str

    def __init__(self, valkey_client: ValkeyLiveClient, args: RedisServiceDiscoveryArgs) -> None:
        self._valkey_target = args.valkey_target
        self._db_id = args.db_id
        self._ttl = args.ttl
        self._prefix = args.prefix
        self._valkey_client = valkey_client

    @classmethod
    async def create(cls, args: RedisServiceDiscoveryArgs) -> Self:
        valkey_client = await ValkeyLiveClient.create(
            args.valkey_target,
            db_id=args.db_id,
            human_readable_name="service_discovery",
        )
        return cls(valkey_client, args)

    async def close(self) -> None:
        """Close the ValkeyLiveClient connection."""
        await self._valkey_client.close()

    async def _hsetex(self, key: str, mapping: dict[str, Any]) -> None:
        """Set hash fields with expiry using ValkeyLiveClient."""
        # Convert values to JSON strings
        json_mapping = {k: dump_json_str(v) for k, v in mapping.items()}
        await self._valkey_client.hset_with_expiry(key, json_mapping, self._ttl)

    async def _scan_keys(self, pattern: str) -> list[str]:
        """Scan keys matching pattern using ValkeyLiveClient."""
        return await self._valkey_client.scan_keys(pattern)

    async def _hget_json(self, name: str) -> ServiceMetadata:
        """Get hash fields and parse JSON values using ValkeyLiveClient."""
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

    async def sync_model_service_routes(
        self,
        routes: Sequence[ModelServiceMetadata],
    ) -> None:
        """
        Synchronize model service routes for Prometheus service discovery.

        Writes all current routes to Redis with TTL. Routes not included in this sync
        will be explicitly removed.
        """
        # Get all existing model-services to clean up stale ones
        existing_route_ids = set()
        try:
            existing_routes = await self.get_service_group(MODEL_SERVICE_GROUP)
            existing_route_ids = {route.id for route in existing_routes}
        except ValueError:
            # No existing routes, which is fine
            pass

        # Batch write all current routes
        for route in routes:
            # Convert to ServiceMetadata for storage
            service_meta = route.to_service_metadata()
            service_meta.health_status.update_heartbeat()

            key = self._service_prefix(service_meta.service_group, service_meta.id)
            # Use model service route TTL instead of default TTL
            json_mapping = {k: dump_json_str(v) for k, v in service_meta.to_dict().items()}
            await self._valkey_client.hset_with_expiry(key, json_mapping, MODEL_SERVICE_ROUTE_TTL)

        # Remove routes that are no longer present
        current_route_ids = {route.route_id for route in routes}
        stale_route_ids = existing_route_ids - current_route_ids
        for stale_id in stale_route_ids:
            await self.unregister(MODEL_SERVICE_GROUP, stale_id)

    def _service_group_prefix(self, service_group: str) -> str:
        return f"{self._prefix}.{service_group}"

    def _service_prefix(self, service_group: str, service_id: uuid.UUID) -> str:
        return f"{self._service_group_prefix(service_group)}.{service_id}"
