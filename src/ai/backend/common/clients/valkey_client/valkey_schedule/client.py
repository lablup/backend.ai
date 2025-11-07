from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from time import time
from typing import Optional, Self, cast
from uuid import UUID

from glide import Batch, ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import SessionId, ValkeyTarget

PENDING_QUEUE_EXPIRY_SEC = 600  # 10 minutes
ROUTE_HEALTH_TTL_SEC = 120  # 2 minutes
MAX_HEALTH_STALENESS_SEC = 300  # 5 minutes - threshold for health status staleness


# Layer-specific decorator for valkey_schedule client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_SCHEDULE)


@dataclass
class HealthStatus:
    """Health status data for a route."""

    readiness: bool
    liveness: bool
    last_check: int  # Unix timestamp of last check by manager

    def is_alive(self) -> bool:
        """Check if the route is considered alive (both readiness and liveness are true)."""
        # TODO: Use liveness too after applying liveness checks in agent
        return self.readiness


class ValkeyScheduleClient:
    """
    Client for managing scheduling marks in Valkey.
    Provides simple flag-based coordination between scheduling loops.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
    ) -> Self:
        """
        Create a ValkeyScheduleClient instance.

        :param valkey_target: The target Valkey server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The name of the client.
        :return: An instance of ValkeyScheduleClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    def _get_schedule_key(self, schedule_type: str) -> str:
        """
        Generate the Redis key for the given schedule type.

        :param schedule_type: The type of scheduling
        :return: The formatted key string
        """
        return f"schedule:{schedule_type}"

    def _get_deployment_key(self, lifecycle_type: str) -> str:
        """
        Generate the Redis key for the given deployment lifecycle type.

        :param lifecycle_type: The type of deployment lifecycle
        :return: The formatted key string
        """
        return f"deployment:{lifecycle_type}"

    def _get_route_key(self, lifecycle_type: str) -> str:
        """
        Generate the Redis key for the given route lifecycle type.

        :param lifecycle_type: The type of route lifecycle
        :return: The formatted key string
        """
        return f"route:{lifecycle_type}"

    def _get_route_health_key(self, route_id: str) -> str:
        """
        Generate the Redis key for route health status.

        :param route_id: The route ID
        :return: The formatted key string
        """
        return f"route:health:{route_id}"

    def _is_health_status_valid(self, status: str, timestamp_str: str) -> bool:
        """
        Check if health status is healthy and timestamp is not stale.

        :param status: The status string ("1" for healthy, "0" for unhealthy)
        :param timestamp_str: The timestamp string value from Redis
        :return: True if status is healthy and timestamp is not stale, False otherwise
        """
        if status != "1":
            return False
        try:
            timestamp = int(timestamp_str)
            current_time = int(time())
            return (current_time - timestamp) <= MAX_HEALTH_STALENESS_SEC
        except (ValueError, TypeError):
            return False

    @valkey_decorator()
    async def mark_schedule_needed(self, schedule_type: str) -> None:
        """
        Mark that scheduling is needed for the given schedule type.
        Simply sets a flag that will be checked in the next scheduling loop.

        :param schedule_type: The type of scheduling to mark
        """
        key = self._get_schedule_key(schedule_type)
        await self._client.client.set(key, b"1")

    @valkey_decorator()
    async def load_and_delete_schedule_mark(self, schedule_type: str) -> bool:
        """
        Check if a scheduling mark exists and atomically delete it.
        This ensures that only one scheduler processes the mark.

        :param schedule_type: The type of scheduling to check
        :return: True if a mark existed (and was deleted), False otherwise
        """
        key = self._get_schedule_key(schedule_type)
        # Use Batch for atomic GET and DELETE
        batch = Batch(is_atomic=True)
        batch.get(key)
        batch.delete([key])
        results = await self._client.client.exec(batch, raise_on_error=True)

        # Check if results exist and the first element (GET result) is not None
        if results and len(results) > 0:
            return results[0] is not None
        return False

    def _pending_queue_key(self, resource_group_id: str) -> str:
        return f"pending_queue:{resource_group_id}"

    def _queue_position_key(self, session_id: SessionId) -> str:
        return f"queue_position:{session_id}"

    @valkey_decorator()
    async def set_pending_queue(
        self, resource_group_id: str, session_ids: Sequence[SessionId]
    ) -> None:
        """
        Set up the pending queue for a specific resource group and store the position of sessions in the pending queue.
        """
        batch = Batch(is_atomic=False)
        key = self._pending_queue_key(resource_group_id)
        value = dump_json_str([str(sid) for sid in session_ids])
        batch.set(key, value, expiry=ExpirySet(ExpiryType.SEC, PENDING_QUEUE_EXPIRY_SEC))

        for position, session_id in enumerate(session_ids):
            pos_key = self._queue_position_key(session_id)
            batch.set(
                pos_key, str(position), expiry=ExpirySet(ExpiryType.SEC, PENDING_QUEUE_EXPIRY_SEC)
            )
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def get_pending_queue(self, resource_group_id: str) -> list[SessionId]:
        """
        Get the pending queue for a specific resource group.
        """
        key = self._pending_queue_key(resource_group_id)
        result = await self._client.client.get(key)
        if result is None:
            return []
        raw_session_ids = load_json(result)
        return [SessionId(UUID(sid)) for sid in raw_session_ids]

    @valkey_decorator()
    async def get_queue_positions(self, session_ids: Sequence[SessionId]) -> list[Optional[int]]:
        """
        Get the positions of multiple sessions in their pending queue.
        """
        if not session_ids:
            return []
        batch = Batch(is_atomic=False)
        for session_id in session_ids:
            key = self._queue_position_key(session_id)
            batch.get(key)
        batch_result = await self._client.client.exec(batch, raise_on_error=True)
        if batch_result is None:
            return [None for _ in session_ids]

        result: list[Optional[int]] = []
        for pos in batch_result:
            if pos is None:
                result.append(None)
            else:
                try:
                    result.append(int(pos))  # type: ignore[arg-type]
                except ValueError:
                    result.append(None)
        return result

    @valkey_decorator()
    async def mark_deployment_needed(self, lifecycle_type: str) -> None:
        """
        Mark that a deployment lifecycle operation is needed.
        Simply sets a flag that will be checked in the next scheduling loop.

        :param lifecycle_type: The type of deployment lifecycle to mark
        """
        key = self._get_deployment_key(lifecycle_type)
        await self._client.client.set(key, b"1")

    @valkey_decorator()
    async def load_and_delete_deployment_mark(self, lifecycle_type: str) -> bool:
        """
        Check if a deployment lifecycle mark exists and atomically delete it.
        This ensures that only one scheduler processes the mark.

        :param lifecycle_type: The type of deployment lifecycle to check
        :return: True if a mark existed (and was deleted), False otherwise
        """
        key = self._get_deployment_key(lifecycle_type)
        # Use Batch for atomic GET and DELETE
        batch = Batch(is_atomic=True)
        batch.get(key)
        batch.delete([key])
        results = await self._client.client.exec(batch, raise_on_error=True)

        # Check if results exist and the first element (GET result) is not None
        if results and len(results) > 0:
            return results[0] is not None
        return False

    @valkey_decorator()
    async def mark_route_needed(self, lifecycle_type: str) -> None:
        """
        Mark that a route lifecycle operation is needed.
        Simply sets a flag that will be checked in the next scheduling loop.

        :param lifecycle_type: The type of route lifecycle to mark
        """
        key = self._get_route_key(lifecycle_type)
        await self._client.client.set(key, b"1")

    @valkey_decorator()
    async def load_and_delete_route_mark(self, lifecycle_type: str) -> bool:
        """
        Check if a route lifecycle mark exists and atomically delete it.
        This ensures that only one scheduler processes the mark.

        :param lifecycle_type: The type of route lifecycle to check
        :return: True if a mark existed (and was deleted), False otherwise
        """
        key = self._get_route_key(lifecycle_type)
        # Use Batch for atomic GET and DELETE
        batch = Batch(is_atomic=True)
        batch.get(key)
        batch.delete([key])
        results = await self._client.client.exec(batch, raise_on_error=True)

        # Check if results exist and the first element (GET result) is not None
        if results and len(results) > 0:
            return results[0] is not None
        return False

    @valkey_decorator()
    async def get_route_health_status(self, route_id: str) -> Optional[HealthStatus]:
        """
        Get health status for a route from Redis.

        :param route_id: The route ID to check
        :return: HealthStatus object or None if not found
        """
        key = self._get_route_health_key(route_id)
        result = await self._client.client.hgetall(key)
        if not result:
            return None

        # Convert bytes to strings and parse
        data = {k.decode(): v.decode() for k, v in result.items()}

        # Parse boolean values using validation helper (checks both status and staleness)
        readiness = self._is_health_status_valid(
            data.get("readiness", "0"), data.get("last_readiness", "0")
        )
        liveness = self._is_health_status_valid(
            data.get("liveness", "0"), data.get("last_liveness", "0")
        )
        last_check = int(data["last_check"]) if "last_check" in data else 0

        return HealthStatus(readiness=readiness, liveness=liveness, last_check=last_check)

    @valkey_decorator()
    async def initialize_routes_health_status_batch(self, route_ids: list[str]) -> None:
        """
        Batch initialize health status for multiple routes in Redis with TTL.
        This should only be called during initial route creation.
        Always initializes with readiness=False and liveness=False.

        :param route_ids: List of route IDs to initialize
        """
        if not route_ids:
            return

        current_time = str(int(time()))
        batch = Batch(is_atomic=False)

        for route_id in route_ids:
            key = self._get_route_health_key(route_id)
            data: Mapping[str | bytes, str | bytes] = {
                "readiness": "0",
                "liveness": "0",
                "last_check": current_time,
                # last_readiness and last_liveness are not set until first health check
            }
            batch.hset(key, data)
            batch.expire(key, ROUTE_HEALTH_TTL_SEC)

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def update_route_readiness(self, route_id: str, readiness: bool) -> None:
        """
        Update readiness status for a route in Redis.
        This should be called by app proxy after health check.

        :param route_id: The route ID to update
        :param readiness: Whether the route is ready
        """
        key = self._get_route_health_key(route_id)
        data: Mapping[str | bytes, str | bytes] = {
            "readiness": "1" if readiness else "0",
            "last_readiness": str(int(time())),
        }

        batch = Batch(is_atomic=False)
        batch.hset(key, data)
        batch.expire(key, ROUTE_HEALTH_TTL_SEC)
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def update_route_liveness(self, route_id: str, liveness: bool) -> None:
        """
        Update liveness status for a route in Redis.
        This should be called by agent after liveness check.

        :param route_id: The route ID to update
        :param liveness: Whether the route is alive
        """
        key = self._get_route_health_key(route_id)
        data: Mapping[str | bytes, str | bytes] = {
            "liveness": "1" if liveness else "0",
            "last_liveness": str(int(time())),
        }

        batch = Batch(is_atomic=False)
        batch.hset(key, data)
        batch.expire(key, ROUTE_HEALTH_TTL_SEC)
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def check_route_health_status(
        self, route_ids: list[str]
    ) -> Mapping[str, Optional[HealthStatus]]:
        """
        Check health status for multiple routes and update last_check timestamp.
        This is used by the manager to track when it last checked each route.

        :param route_ids: List of route IDs to check
        :return: Mapping of route ID to HealthStatus object or None if not found
        """
        if not route_ids:
            return {}

        current_time = str(int(time()))
        batch = Batch(is_atomic=False)

        # Single batch: update last_check, refresh TTL, and get all data
        for route_id in route_ids:
            key = self._get_route_health_key(route_id)
            batch.hset(key, {"last_check": current_time})
            batch.expire(key, ROUTE_HEALTH_TTL_SEC)
            batch.hgetall(key)

        results = await self._client.client.exec(batch, raise_on_error=False)
        if results is None:
            return {route_id: None for route_id in route_ids}

        # Process results - every 3rd result is the hgetall response
        health_statuses: dict[str, Optional[HealthStatus]] = {}
        for i, route_id in enumerate(route_ids):
            # Results are in groups of 3: hset result, expire result, hgetall result
            hgetall_result = results[i * 3 + 2] if len(results) > i * 3 + 2 else None

            if not hgetall_result:
                health_statuses[route_id] = None
                continue

            result = cast(dict[bytes, bytes], hgetall_result)
            if not result:
                health_statuses[route_id] = None
                continue

            # Parse existing data
            data = {k.decode(): v.decode() for k, v in result.items()}
            # Parse boolean values using validation helper (checks both status and staleness)
            health_statuses[route_id] = HealthStatus(
                readiness=self._is_health_status_valid(
                    data.get("readiness", "0"), data.get("last_readiness", "0")
                ),
                liveness=self._is_health_status_valid(
                    data.get("liveness", "0"), data.get("last_liveness", "0")
                ),
                last_check=int(data["last_check"]) if "last_check" in data else 0,
            )

        return health_statuses

    @valkey_decorator()
    async def update_routes_readiness_batch(self, route_readiness: Mapping[str, bool]) -> None:
        """
        Batch update readiness status for multiple routes in Redis.
        This should be called by app proxy after health checks.

        :param route_readiness: Mapping of route ID to readiness status
        """
        if not route_readiness:
            return

        current_time = str(int(time()))
        batch = Batch(is_atomic=False)
        for route_id, readiness in route_readiness.items():
            key = self._get_route_health_key(route_id)
            data: Mapping[str | bytes, str | bytes] = {
                "readiness": "1" if readiness else "0",
                "last_readiness": current_time,
            }
            batch.hset(key, data)
            batch.expire(key, ROUTE_HEALTH_TTL_SEC)

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def close(self) -> None:
        """
        Close the ValkeyScheduleClient connection.
        """
        if self._closed:
            return
        self._closed = True
        await self._client.disconnect()
