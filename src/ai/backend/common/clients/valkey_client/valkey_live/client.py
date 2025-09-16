import json
import logging
from collections.abc import Mapping
from typing import (
    Any,
    Final,
    Optional,
    Self,
    cast,
)
from uuid import UUID

from glide import (
    Batch,
    ConditionalChange,
    ExpirySet,
    ExpiryType,
    InfBound,
    ScoreBoundary,
)

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_live client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_LIVE)

_DEFAULT_EXPIRATION = 3600  # 1 hour default expiration
_SESSION_REQUESTS_SUFFIX: Final[str] = "requests"
_SESSION_LAST_RESPONSE_SUFFIX: Final[str] = "last_response_time"
_AGENT_LAST_SEEN_HASH: Final[str] = "agent.last_seen"


class ValkeyLiveClient:
    """
    Client for interacting with Valkey for live status tracking and service discovery.
    This client provides domain-specific operations for scheduler and manager components.
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
        Create a ValkeyLiveClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The name of the client.
        :param pubsub_channels: Set of channels to subscribe to for pub/sub functionality.
        :return: An instance of ValkeyLiveClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_decorator()
    async def close(self) -> None:
        """
        Close the ValkeyLiveClient connection.
        """
        if self._closed:
            log.debug("ValkeyLiveClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch for pipeline operations (internal use only).

        :param is_atomic: Whether the batch should be atomic (transaction).
        :return: A Batch instance.
        """
        return Batch(is_atomic=is_atomic)

    async def _execute_batch(self, batch: Batch) -> Any:
        """
        Execute a batch of commands (internal use only).

        :param batch: The batch to execute.
        :return: List of command results.
        """
        return await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def get_live_data(self, key: str) -> Optional[bytes]:
        """Get live data value by key."""
        return await self._client.client.get(key)

    @valkey_decorator()
    async def get_multiple_live_data(self, keys: list[str]) -> list[Optional[bytes]]:
        """
        Get multiple live data keys in a single batch operation.

        :param keys: List of keys to get.
        :return: List of values corresponding to the keys.
        """
        if not keys:
            return []
        return await self._client.client.mget(cast(list[str | bytes], keys))

    @valkey_decorator()
    async def store_live_data(
        self,
        key: str,
        value: str | bytes,
        *,
        ex: Optional[int] = None,
        xx: Optional[bool] = None,
    ) -> None:
        """Store live data value for key with optional expiration."""
        expiry = ExpirySet(ExpiryType.SEC, _DEFAULT_EXPIRATION if ex is None else ex)
        conditional_set = ConditionalChange.ONLY_IF_EXISTS if xx else None
        await self._client.client.set(key, value, conditional_set=conditional_set, expiry=expiry)

    @valkey_decorator()
    async def store_multiple_live_data(
        self,
        data: Mapping[str, str | bytes],
        *,
        ex: Optional[int] = None,
        xx: Optional[bool] = None,
    ) -> None:
        """Store multiple live data values for key with optional expiration."""
        if not data:
            return
        batch = self._create_batch()
        expiry = ExpirySet(ExpiryType.SEC, _DEFAULT_EXPIRATION if ex is None else ex)
        conditional_set = ConditionalChange.ONLY_IF_EXISTS if xx else None
        # To set the conditional_set and expiry, we issue multiple SET commands instead of a single MSET.
        for key, value in data.items():
            batch.set(key, value, conditional_set=conditional_set, expiry=expiry)
        await self._execute_batch(batch)

    @valkey_decorator()
    async def delete_live_data(self, key: str) -> int:
        """Delete live data keys."""
        return await self._client.client.delete([key])

    @valkey_decorator()
    async def incr_live_data(
        self,
        key: str,
        *,
        ex: Optional[int] = None,
    ) -> int:
        """Increment a key in the live data."""
        expiration_sec = _DEFAULT_EXPIRATION if ex is None else ex
        batch = self._create_batch()
        batch.incr(key)
        batch.expire(key, expiration_sec)
        results = await self._execute_batch(batch)
        return results[0]

    @valkey_decorator()
    async def replace_schedule_data(self, key: str, values: Mapping[str, str]) -> None:
        """
        Replace schedule data for a key with new values.

        :param key: The key to replace data for.
        :param values: Mapping of field names to new values.
        """
        if not values:
            log.warning("No values provided to replace schedule data.")
            return

        # Use batch to set all fields atomically
        batch = self._create_batch()
        batch.delete([key])
        batch.hset(key, cast(Mapping[str | bytes, str | bytes], values))
        await self._execute_batch(batch)

    @valkey_decorator()
    async def get_server_time(self) -> float:
        """Get server time as timestamp."""
        result = await self._client.client.time()
        if len(result) != 2:
            raise ValueError(
                f"Unexpected result from time command: {result}. Expected a tuple of (seconds, microseconds)."
            )
        seconds_bytes, microseconds_bytes = result
        seconds = float(seconds_bytes)
        microseconds = float(microseconds_bytes)
        return seconds + (microseconds / 10**6)

    @valkey_decorator()
    async def count_active_connections(self, session_id: str) -> int:
        """Count active connections for a session."""
        return await self._client.client.zcount(
            self._active_app_connection_key(session_id),
            InfBound.NEG_INF,
            InfBound.POS_INF,
        )

    @valkey_decorator()
    async def add_scheduler_metadata(
        self,
        key: str,
        mapping: Mapping[str, str | bytes],
    ) -> int:
        """Store scheduler metadata in hash fields."""
        return await self._client.client.hset(key, cast(Mapping[str | bytes, str | bytes], mapping))

    @valkey_decorator()
    async def get_scheduler_metadata(self, name: str) -> Mapping[str, str]:
        """
        Get scheduler metadata from hash fields.

        :param name: The hash key name.
        :return: Dictionary of field names to values.
        """
        result = await self._client.client.hgetall(name)
        if result is None:
            return {}

        # Convert bytes keys and values to strings
        metadata: dict[str, str] = {}
        for key, value in result.items():
            str_key: str = key.decode("utf-8")
            str_value: str = value.decode("utf-8")
            metadata[str_key] = str_value

        return metadata

    @valkey_decorator()
    async def update_connection_tracker(
        self,
        session_id: str,
        service: str,
        stream_id: str,
    ) -> None:
        """
        Update connection tracker with current timestamp.

        :param session_id: The session ID to track connections for.
        :param service: The service name.
        :param stream_id: The stream ID.
        """
        current_time = await self.get_server_time()
        connection_id = self._active_app_connection_value(
            kernel_id=session_id,
            service=service,
            stream_id=stream_id,
        )
        tracker_key = self._active_app_connection_key(session_id)
        await self._client.client.zadd(tracker_key, {connection_id: current_time})

    @valkey_decorator()
    async def update_app_connection_tracker(
        self,
        kernel_id: str,
        service: str,
        stream_id: str,
    ) -> None:
        """
        Update app connection tracker for a specific kernel, service, and stream.

        :param kernel_id: The kernel ID.
        :param service: The service name.
        :param stream_id: The stream ID.
        """
        tracker_key = self._active_app_connection_key(kernel_id)  # TODO: Check if this is correct
        tracker_val = self._active_app_connection_value(
            kernel_id=kernel_id,
            service=service,
            stream_id=stream_id,
        )
        current_time = await self.get_server_time()
        await self._client.client.zadd(tracker_key, {tracker_val: current_time})

    @valkey_decorator()
    async def remove_connection_tracker(
        self,
        session_id: str,
        service: str,
        stream_id: str,
    ) -> int:
        """
        Remove connection from tracker.

        :param session_id: The session ID to remove connection from.
        :param service: The service name.
        :param stream_id: The stream ID.
        :return: Number of connections removed.
        """
        tracker_key = self._active_app_connection_key(session_id)
        connection_id = self._active_app_connection_value(
            kernel_id=session_id,
            service=service,
            stream_id=stream_id,
        )
        return await self._client.client.zrem(tracker_key, [connection_id])

    @valkey_decorator()
    async def remove_stale_connections(
        self,
        session_id: str,
        max_timestamp: float,
    ) -> int:
        """
        Remove connections from tracker by score range.

        :param session_id: The session ID to clean up connections for.
        :param max_timestamp: Maximum timestamp (inclusive).
        :return: Number of connections removed.
        """
        tracker_key = self._active_app_connection_key(session_id)
        return await self._client.client.zremrangebyscore(
            tracker_key, InfBound.NEG_INF, ScoreBoundary(max_timestamp)
        )

    @valkey_decorator()
    async def update_agent_last_seen(self, agent_id: str, timestamp: float) -> None:
        """
        Update agent's last seen timestamp for liveness tracking.

        :param agent_id: The agent ID to update.
        :param timestamp: The timestamp when the agent was last seen.
        """
        await self._client.client.hset(_AGENT_LAST_SEEN_HASH, {agent_id: str(timestamp)})

    @valkey_decorator()
    async def remove_agent_last_seen(self, agent_id: str) -> None:
        """
        Remove agent's last seen timestamp when agent is terminated.

        :param agent_id: The agent ID to remove.
        """
        await self._client.client.hdel(_AGENT_LAST_SEEN_HASH, [agent_id])

    def _get_session_requests_key(self, session_id: str) -> str:
        """
        Generate session requests key.

        :param session_id: The session ID.
        :return: The generated key.
        """
        return f"session.{session_id}.{_SESSION_REQUESTS_SUFFIX}"

    def _get_session_last_response_key(self, session_id: str) -> str:
        """
        Generate session last response time key.

        :param session_id: The session ID.
        :return: The generated key.
        """
        return f"session.{session_id}.{_SESSION_LAST_RESPONSE_SUFFIX}"

    @valkey_decorator()
    async def get_session_statistics_batch(
        self, session_ids: list[str]
    ) -> list[Optional[dict[str, int]]]:
        """
        Get session statistics (requests and last response time) for multiple sessions.

        :param session_ids: List of session IDs to get statistics for.
        :return: List of session statistics with requests and last_response_ms.
        """
        if not session_ids:
            return []

        # Build keys for all sessions
        keys = []
        for session_id in session_ids:
            keys.extend([
                self._get_session_requests_key(session_id),
                self._get_session_last_response_key(session_id),
            ])

        # Get all values in one batch
        results = await self.get_multiple_live_data(keys)

        # Process results in pairs (requests, last_response_time)
        stats: list[Optional[dict[str, int]]] = []
        for i in range(0, len(results), 2):
            requests_result = results[i]
            last_response_result = results[i + 1]

            if requests_result is not None and last_response_result is not None:
                try:
                    requests = int(requests_result.decode("utf-8"))
                    last_response_ms = int(last_response_result.decode("utf-8"))
                    stats.append({"requests": requests, "last_response_ms": last_response_ms})
                except (ValueError, UnicodeDecodeError):
                    stats.append({"requests": 0, "last_response_ms": 0})
            else:
                stats.append({"requests": 0, "last_response_ms": 0})

        return stats

    @valkey_decorator()
    async def scan_agent_last_seen(self) -> list[tuple[str, float]]:
        """
        Scan all agent last seen entries.

        :return: List of (agent_id, last_seen_timestamp) tuples.
        """
        results = []
        cursor = b"0"
        while True:
            scan_result = await self._client.client.hscan(_AGENT_LAST_SEEN_HASH, cursor)
            if len(scan_result) != 2:
                break
            cursor = cast(bytes, scan_result[0])
            fields = cast(list[bytes], scan_result[1])
            for i in range(0, len(fields), 2):
                if i + 1 >= len(fields):
                    continue
                try:
                    field_name = fields[i].decode("utf-8")
                    field_value = float(fields[i + 1].decode("utf-8"))
                    results.append((field_name, field_value))
                except (ValueError, UnicodeDecodeError):
                    continue
            if cursor == b"0":
                break

        return results

    @valkey_decorator()
    async def scan_keys(self, pattern: str) -> list[str]:
        """
        Scan keys matching pattern.

        :param pattern: The pattern to match keys against.
        :return: List of matching keys.
        """
        results = []
        cursor = b"0"
        while True:
            scan_result = await self._client.client.scan(cursor, match=pattern, count=100)
            if len(scan_result) != 2:
                break
            cursor = cast(bytes, scan_result[0])
            keys = cast(list[bytes], scan_result[1])

            for key in keys:
                results.append(key.decode("utf-8"))
            if cursor == b"0":
                break

        return results

    @valkey_decorator()
    async def hset_with_expiry(
        self, key: str, mapping: Mapping[str, str], expiry_seconds: int
    ) -> None:
        """
        Set hash fields with expiry.

        :param key: The hash key.
        :param mapping: Dictionary of field names to values.
        :param expiry_seconds: Expiry time in seconds.
        """

        # Use batch to set hash and expiry atomically
        batch = self._create_batch()
        batch.hset(key, cast(Mapping[str | bytes, str | bytes], mapping))
        batch.expire(key, expiry_seconds)
        await self._execute_batch(batch)

    @valkey_decorator()
    async def hgetall_str(self, key: str) -> dict[str, str]:
        """
        Get all hash fields as strings.

        :param key: The hash key.
        :return: Dictionary of field names to values.
        """
        result = await self._client.client.hgetall(key)
        if result is None:
            return {}

        # Convert bytes keys and values to strings
        str_result: dict[str, str] = {}
        for k, v in result.items():
            str_key: str = k.decode("utf-8")
            str_value: str = v.decode("utf-8")
            str_result[str_key] = str_value

        return str_result

    @valkey_decorator()
    async def update_appproxy_redis_info(
        self,
        endpoint_id: UUID,
        connection_info: dict[str, Any],
        health_check_config: Optional[ModelHealthCheck],
    ) -> None:
        pipe = self._create_batch()
        pipe.set(
            f"endpoint.{endpoint_id}.route_connection_info",
            json.dumps(connection_info),
            expiry=ExpirySet(ExpiryType.SEC, 3600),
        )
        pipe.set(
            f"endpoint.{endpoint_id}.health_check_enabled",
            "true" if health_check_config is not None else "false",
            expiry=ExpirySet(ExpiryType.SEC, 3600),
        )
        # TODO: Don't update health_check_config when route is updated.
        if health_check_config:
            pipe.set(
                f"endpoint.{endpoint_id}.health_check_config",
                health_check_config.model_dump_json(),
                expiry=ExpirySet(ExpiryType.SEC, 3600),
            )
        await self._client.client.exec(pipe, raise_on_error=True)

    @valkey_decorator()
    async def delete_key(self, key: str) -> int:
        """
        Delete a key.

        :param key: The key to delete.
        :return: Number of keys deleted.
        """
        return await self._client.client.delete([key])

    def _active_app_connection_key(self, session_id: str) -> str:
        """
        Generate the key for tracking active app connections for a session.
        :param session_id: The session ID.
        :return: The key for active app connections.
        """
        return f"session.{session_id}.active_app_connections"

    def _active_app_connection_value(
        self,
        kernel_id: str,
        service: str,
        stream_id: str,
    ) -> str:
        """
        Generate the value for tracking active app connections.

        :param kernel_id: The kernel ID.
        :param service: The service name.
        :param stream_id: The stream ID.
        :return: The value for active app connections.
        """
        return f"{kernel_id}:{service}:{stream_id}"
