import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Optional, Self, cast
from uuid import UUID

from glide import Batch, ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    BackoffStrategy,
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.types import AgentId, KernelId, SessionId, ValkeyTarget

PENDING_QUEUE_EXPIRY_SEC = 600  # 10 minutes
ROUTE_HEALTH_TTL_SEC = 120  # 2 minutes
MAX_HEALTH_STALENESS_SEC = 300  # 5 minutes - threshold for health status staleness
KERNEL_HEALTH_TTL_SEC = 300  # 5 minutes - TTL for kernel health status
MAX_KERNEL_HEALTH_STALENESS_SEC = 120  # 2 minutes - threshold for kernel health staleness
AGENT_LAST_CHECK_TTL_SEC = 1200  # 20 minutes - TTL for agent last check timestamp
ORPHAN_KERNEL_THRESHOLD_SEC = 600  # 10 minutes - threshold for orphan kernel detection


class HealthCheckStatus(enum.StrEnum):
    """Status of an individual health check (readiness or liveness)."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STALE = "stale"


# Resilience instance for valkey_schedule layer
valkey_schedule_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_SCHEDULE)),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


@dataclass
class HealthStatus:
    """Health status data for a route."""

    readiness: HealthCheckStatus | None  # None if never checked
    liveness: HealthCheckStatus | None  # None if never checked
    last_check: int | None  # Unix timestamp of last check by manager, None if never checked
    created_at: int  # Unix timestamp when route was initialized

    def get_status(self) -> HealthCheckStatus | None:
        """
        Get the overall health status of the route.

        Returns:
            HealthCheckStatus based on readiness and liveness:
            - None: if readiness is not set
            - STALE: if either readiness or liveness is stale
            - HEALTHY: if readiness is healthy (TODO: and liveness when implemented)
            - UNHEALTHY: if readiness is unhealthy
        """
        # TODO: Use liveness too after applying liveness checks in agent
        return self.readiness


@dataclass
class KernelStatus:
    """Presence status for a kernel."""

    presence: HealthCheckStatus | None  # HEALTHY, UNHEALTHY, STALE, or None if never reported
    last_presence: int | None  # Unix timestamp when Agent last reported presence, None if never
    last_check: int | None  # Unix timestamp when Manager last checked, None if never
    created_at: int  # Unix timestamp when first created  # Unix timestamp when first created, None if not initialized


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

    def _get_kernel_presence_key(self, kernel_id: KernelId) -> str:
        """
        Generate the Redis key for kernel presence status.

        :param kernel_id: The kernel ID
        :return: The formatted key string
        """
        return f"kernel:presence:{kernel_id}"

    def _get_agent_last_check_key(self, agent_id: AgentId) -> str:
        """
        Generate the Redis key for agent last check timestamp.

        :param agent_id: The agent ID
        :return: The formatted key string
        """
        return f"agent:last_check:{agent_id}"

    async def _get_redis_time(self) -> int:
        """
        Get current Unix timestamp from Redis server using TIME command.
        This ensures consistent timestamps across distributed systems.

        :return: Current Unix timestamp in seconds
        """
        result = await self._client.client.time()
        seconds_bytes, _ = result
        return int(seconds_bytes)

    async def get_redis_time(self) -> int:
        """
        Get current Unix timestamp from Redis server using TIME command.
        This ensures consistent timestamps across distributed systems.

        :return: Current Unix timestamp in seconds
        """
        return await self._get_redis_time()

    async def _validate_health_status(
        self,
        status: str | None,
        timestamp_str: str | None,
        current_time: int | None = None,
        staleness_sec: int = MAX_HEALTH_STALENESS_SEC,
    ) -> HealthCheckStatus | None:
        """
        Validate health status by checking if it's healthy and timestamp is not stale.

        :param status: The status string ("1" for healthy, "0" for unhealthy), or None if missing
        :param timestamp_str: The timestamp string value from Redis, or None if missing
        :param current_time: Optional pre-fetched Redis time (fetches if None)
        :param staleness_sec: Staleness threshold in seconds
        :return: HealthCheckStatus indicating the status:
                 - None: if status or timestamp is missing
                 - HEALTHY: status is "1" and timestamp is fresh
                 - UNHEALTHY: status is "0" and timestamp is fresh
                 - STALE: timestamp is stale or invalid
        """
        # Return None if status or timestamp is missing
        if status is None or timestamp_str is None:
            return None
        try:
            timestamp = int(timestamp_str)
            if current_time is None:
                current_time = await self._get_redis_time()
            is_stale = (current_time - timestamp) > staleness_sec
            if is_stale:
                return HealthCheckStatus.STALE
            return HealthCheckStatus.HEALTHY if status == "1" else HealthCheckStatus.UNHEALTHY
        except (ValueError, TypeError):
            # If timestamp is invalid, return None (not enough info)
            return None

    @valkey_schedule_resilience.apply()
    async def mark_schedule_needed(self, schedule_type: str) -> None:
        """
        Mark that scheduling is needed for the given schedule type.
        Simply sets a flag that will be checked in the next scheduling loop.

        :param schedule_type: The type of scheduling to mark
        """
        key = self._get_schedule_key(schedule_type)
        await self._client.client.set(key, b"1")

    @valkey_schedule_resilience.apply()
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

    @valkey_schedule_resilience.apply()
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

    @valkey_schedule_resilience.apply()
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

    @valkey_schedule_resilience.apply()
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

    @valkey_schedule_resilience.apply()
    async def mark_deployment_needed(self, lifecycle_type: str) -> None:
        """
        Mark that a deployment lifecycle operation is needed.
        Simply sets a flag that will be checked in the next scheduling loop.

        :param lifecycle_type: The type of deployment lifecycle to mark
        """
        key = self._get_deployment_key(lifecycle_type)
        await self._client.client.set(key, b"1")

    @valkey_schedule_resilience.apply()
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

    @valkey_schedule_resilience.apply()
    async def mark_route_needed(self, lifecycle_type: str) -> None:
        """
        Mark that a route lifecycle operation is needed.
        Simply sets a flag that will be checked in the next scheduling loop.

        :param lifecycle_type: The type of route lifecycle to mark
        """
        key = self._get_route_key(lifecycle_type)
        await self._client.client.set(key, b"1")

    @valkey_schedule_resilience.apply()
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

    @valkey_schedule_resilience.apply()
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
        # Pass None for missing fields instead of defaults
        readiness = await self._validate_health_status(
            data.get("readiness"), data.get("last_readiness")
        )
        liveness = await self._validate_health_status(
            data.get("liveness"), data.get("last_liveness")
        )
        last_check = int(data["last_check"]) if "last_check" in data else None
        created_at = int(data.get("created_at", "0"))

        return HealthStatus(
            readiness=readiness,
            liveness=liveness,
            last_check=last_check,
            created_at=created_at,
        )

    @valkey_schedule_resilience.apply()
    async def initialize_routes_health_status_batch(self, route_ids: list[str]) -> None:
        """
        Batch initialize health status for multiple routes in Redis with TTL.
        This should only be called during initial route creation.
        Always initializes with readiness=False and liveness=False.

        :param route_ids: List of route IDs to initialize
        """
        if not route_ids:
            return

        current_time = str(await self._get_redis_time())
        batch = Batch(is_atomic=False)

        for route_id in route_ids:
            key = self._get_route_health_key(route_id)
            data: Mapping[str | bytes, str | bytes] = {
                "readiness": "0",
                "liveness": "0",
                "last_check": current_time,
                "created_at": current_time,
                # last_readiness and last_liveness are not set until first health check
            }
            batch.hset(key, data)
            batch.expire(key, ROUTE_HEALTH_TTL_SEC)

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_schedule_resilience.apply()
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
            "last_readiness": str(await self._get_redis_time()),
        }

        batch = Batch(is_atomic=False)
        batch.hset(key, data)
        batch.expire(key, ROUTE_HEALTH_TTL_SEC)
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_schedule_resilience.apply()
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
            "last_liveness": str(await self._get_redis_time()),
        }

        batch = Batch(is_atomic=False)
        batch.hset(key, data)
        batch.expire(key, ROUTE_HEALTH_TTL_SEC)
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_schedule_resilience.apply()
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

        current_time = str(await self._get_redis_time())
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
            # Validate health check statuses - pass None for missing fields
            readiness_status = await self._validate_health_status(
                data.get("readiness"), data.get("last_readiness")
            )
            liveness_status = await self._validate_health_status(
                data.get("liveness"), data.get("last_liveness")
            )
            health_statuses[route_id] = HealthStatus(
                readiness=readiness_status,
                liveness=liveness_status,
                last_check=int(data["last_check"]) if "last_check" in data else None,
                created_at=int(data.get("created_at", "0")),
            )

        return health_statuses

    @valkey_schedule_resilience.apply()
    async def update_routes_readiness_batch(self, route_readiness: Mapping[str, bool]) -> None:
        """
        Batch update readiness status for multiple routes in Redis.
        This should be called by app proxy after health checks.

        :param route_readiness: Mapping of route ID to readiness status
        """
        if not route_readiness:
            return

        current_time = str(await self._get_redis_time())
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

    @valkey_schedule_resilience.apply()
    async def close(self) -> None:
        """
        Close the ValkeyScheduleClient connection.
        """
        if self._closed:
            return
        self._closed = True
        await self._client.disconnect()

    async def ping(self) -> None:
        """Ping the Valkey server to check connection health."""
        await self._client.ping()

    # ==================== Kernel Presence Methods ====================

    @valkey_schedule_resilience.apply()
    async def initialize_kernel_presence_batch(self, kernel_ids: Sequence[KernelId]) -> None:
        """
        Batch initialize presence status for multiple kernels in Redis.

        :param kernel_ids: Sequence of kernel IDs to initialize
        """
        if not kernel_ids:
            return

        current_time = await self._get_redis_time()
        current_time_str = str(current_time)
        batch = Batch(is_atomic=False)
        for kernel_id in kernel_ids:
            key = self._get_kernel_presence_key(kernel_id)
            data: Mapping[str | bytes, str | bytes] = {
                "presence": "0",
                "last_presence": current_time_str,
                "last_check": current_time_str,
                "created_at": current_time_str,
            }
            batch.hset(key, data)
            batch.expire(key, KERNEL_HEALTH_TTL_SEC)

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_schedule_resilience.apply()
    async def update_kernel_presence_batch(
        self,
        kernel_presences: Mapping[KernelId, bool],
    ) -> None:
        """
        Batch update presence status for multiple kernels in Redis.
        This is the preferred method for Agent to report all kernel presences.

        :param kernel_presences: Mapping of kernel_id to presence status
        """
        if not kernel_presences:
            return

        current_time = await self._get_redis_time()
        current_time_str = str(current_time)
        batch = Batch(is_atomic=False)
        for kernel_id, presence in kernel_presences.items():
            key = self._get_kernel_presence_key(kernel_id)
            data: Mapping[str | bytes, str | bytes] = {
                "presence": "1" if presence else "0",
                "last_presence": current_time_str,
            }
            batch.hset(key, data)
            batch.expire(key, KERNEL_HEALTH_TTL_SEC)

        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_schedule_resilience.apply()
    async def delete_kernel_presence_batch(self, kernel_ids: Sequence[KernelId]) -> None:
        """
        Batch delete presence status for multiple kernels from Redis.

        :param kernel_ids: Sequence of kernel IDs to delete
        """
        if not kernel_ids:
            return

        keys: list[str | bytes] = [self._get_kernel_presence_key(kid) for kid in kernel_ids]
        await self._client.client.delete(keys)

    @valkey_schedule_resilience.apply()
    async def check_kernel_presence_status_batch(
        self,
        kernel_ids: Sequence[KernelId],
        agent_ids: set[AgentId] | None = None,
    ) -> dict[KernelId, KernelStatus | None]:
        """
        Batch check kernel presence status and update last_check timestamp.
        This should be called by Manager during periodic checks.

        All operations (hset, expire, hgetall) for all kernels are batched
        into a single request. Optionally updates agent last_check timestamps.

        :param kernel_ids: Sequence of kernel IDs to check
        :param agent_ids: Optional set of agent IDs to update last_check for
        :return: Mapping of kernel_id to status (None if not found)
        """
        if not kernel_ids:
            return {}

        current_time = await self._get_redis_time()
        current_time_str = str(current_time)
        batch = Batch(is_atomic=False)

        # Update kernel status first, then agent last_check
        # This ordering prevents timing issues where agent appears alive
        # but kernels haven't been checked yet
        for kernel_id in kernel_ids:
            key = self._get_kernel_presence_key(kernel_id)
            batch.hset(key, {"last_check": current_time_str})
            batch.expire(key, KERNEL_HEALTH_TTL_SEC)
            batch.hgetall(key)

        # Update agent last_check timestamps after kernel updates
        if agent_ids:
            for agent_id in agent_ids:
                agent_key = self._get_agent_last_check_key(agent_id)
                batch.set(
                    agent_key,
                    current_time_str,
                    expiry=ExpirySet(ExpiryType.SEC, AGENT_LAST_CHECK_TTL_SEC),
                )

        results = await self._client.client.exec(batch, raise_on_error=False)
        if results is None:
            return {kernel_id: None for kernel_id in kernel_ids}

        # Process results - every 3rd result is the hgetall response
        # Kernel results come first (3 ops each), then agent results (1 op each)
        result: dict[KernelId, KernelStatus | None] = {}
        for i, kernel_id in enumerate(kernel_ids):
            # Results are in groups of 3: hset result, expire result, hgetall result
            idx = i * 3 + 2
            hgetall_result = results[idx] if len(results) > idx else None

            if not hgetall_result:
                result[kernel_id] = None
                continue

            hash_data = cast(dict[bytes, bytes], hgetall_result)
            # Check for presence field - if missing, key was accidentally created by hset
            # and should be treated as not found
            if not hash_data or b"presence" not in hash_data:
                result[kernel_id] = None
                continue

            # Parse existing data
            data = {k.decode(): v.decode() for k, v in hash_data.items()}

            # Validate presence status with staleness check - pass None for missing fields
            presence = await self._validate_health_status(
                data.get("presence"),
                data.get("last_presence"),
                current_time,
                MAX_KERNEL_HEALTH_STALENESS_SEC,
            )
            result[kernel_id] = KernelStatus(
                presence=presence,
                last_presence=int(data["last_presence"]) if "last_presence" in data else None,
                last_check=current_time,
                created_at=int(data.get("created_at", "0")),
            )

        return result

    # ==================== Agent Last Check Methods ====================

    @valkey_schedule_resilience.apply()
    async def get_agent_last_check(self, agent_id: AgentId) -> int | None:
        """
        Get the last check timestamp for an agent.
        This is used by Agent to determine if Manager has checked it.

        :param agent_id: The agent ID
        :return: Unix timestamp of last check, or None if not found
        """
        key = self._get_agent_last_check_key(agent_id)
        result = await self._client.client.get(key)
        if result is None:
            return None
        return int(result)

    @valkey_schedule_resilience.apply()
    async def get_kernel_presence_batch(
        self, kernel_ids: Sequence[KernelId]
    ) -> dict[KernelId, KernelStatus | None]:
        """
        Get kernel presence status without updating last_check.
        This is for Agent to read status without modifying timestamps.

        :param kernel_ids: Sequence of kernel IDs to check
        :return: Mapping of kernel_id to status (None if not found)
        """
        if not kernel_ids:
            return {}

        current_time = await self._get_redis_time()
        batch = Batch(is_atomic=False)
        for kernel_id in kernel_ids:
            key = self._get_kernel_presence_key(kernel_id)
            batch.hgetall(key)

        results = await self._client.client.exec(batch, raise_on_error=False)
        if results is None:
            return {kernel_id: None for kernel_id in kernel_ids}

        result: dict[KernelId, KernelStatus | None] = {}
        for i, kernel_id in enumerate(kernel_ids):
            hgetall_result = results[i] if len(results) > i else None
            if not hgetall_result:
                result[kernel_id] = None
                continue

            hash_data = cast(dict[bytes, bytes], hgetall_result)
            if not hash_data or b"presence" not in hash_data:
                result[kernel_id] = None
                continue

            data = {k.decode(): v.decode() for k, v in hash_data.items()}
            # Pass None for missing fields
            presence = await self._validate_health_status(
                data.get("presence"),
                data.get("last_presence"),
                current_time,
                MAX_KERNEL_HEALTH_STALENESS_SEC,
            )
            result[kernel_id] = KernelStatus(
                presence=presence,
                last_presence=int(data["last_presence"]) if "last_presence" in data else None,
                last_check=int(data["last_check"]) if "last_check" in data else None,
                created_at=int(data.get("created_at", "0")),
            )
        return result
