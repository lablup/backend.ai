from typing import Self

from glide import Batch

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget

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
