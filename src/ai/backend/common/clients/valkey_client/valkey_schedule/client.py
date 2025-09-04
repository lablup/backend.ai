from collections.abc import Sequence
from typing import Optional, Self
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


# Layer-specific decorator for valkey_schedule client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_SCHEDULE)


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
        if not session_ids:
            return
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
    async def close(self) -> None:
        """
        Close the ValkeyScheduleClient connection.
        """
        if self._closed:
            return
        self._closed = True
        await self._client.disconnect()
