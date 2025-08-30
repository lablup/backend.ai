import logging
from typing import ParamSpec, Self, TypeVar, cast

from glide import Batch

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_image client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_IMAGE)

P = ParamSpec("P")
R = TypeVar("R")


class ValkeyImageClient:
    """
    Client for managing agent-image mappings using Valkey sets.
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
        Create a ValkeyImageClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The name of the client.
        :return: An instance of ValkeyImageClient.
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
        Close the ValkeyImageClient connection.
        """
        if self._closed:
            log.debug("ValkeyImageClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    @valkey_decorator()
    async def add_agent_to_images(
        self,
        agent_id: str,
        image_canonicals: list[str],
    ) -> None:
        """
        Add an agent to multiple image sets.

        :param agent_id: The agent ID to add.
        :param image_canonicals: List of image canonical names.
        """
        if not image_canonicals:
            return

        tx = self._create_batch()
        for image_canonical in image_canonicals:
            tx.sadd(image_canonical, [agent_id])
        await self._client.client.exec(tx, raise_on_error=True)

    @valkey_decorator()
    async def remove_agent_from_images(
        self,
        agent_id: str,
        image_canonicals: list[str],
    ) -> None:
        """
        Remove an agent from multiple image sets.

        :param agent_id: The agent ID to remove.
        :param image_canonicals: List of image canonical names.
        """
        if not image_canonicals:
            return

        tx = self._create_batch()
        for image_canonical in image_canonicals:
            tx.srem(image_canonical, [agent_id])
        await self._client.client.exec(tx, raise_on_error=True)

    @valkey_decorator()
    async def remove_agent_from_all_images(
        self,
        agent_id: str,
    ) -> None:
        """
        Remove an agent from all image sets.

        :param agent_id: The agent ID to remove.
        """
        cursor = b"0"
        keys_to_remove: list[bytes] = []
        while True:
            result = await self._client.client.scan(cursor)
            if len(result) != 2:
                raise ValueError(
                    f"Unexpected result from scan: {result}. Expected a tuple of (cursor, keys)."
                )
            cursor = cast(bytes, result[0])
            keys = cast(list[bytes], result[1])
            keys_to_remove.extend(keys)
            if cursor == b"0":
                break
        if keys_to_remove:
            tx = self._create_batch()
            for key in keys_to_remove:
                tx.srem(key, [agent_id])
            await self._client.client.exec(tx, raise_on_error=True)

    @valkey_decorator()
    async def get_agents_for_image(
        self,
        image_canonical: str,
    ) -> set[str]:
        """
        Get all agents that have a specific image.

        :param image_canonical: The image canonical name.
        :return: Set of agent IDs.
        """
        result = await self._client.client.smembers(image_canonical)
        return {member.decode() for member in result}

    @valkey_decorator()
    async def get_agents_for_images(
        self,
        image_canonicals: list[str],
    ) -> list[set[str]]:
        """
        Get all agents for multiple images.

        :param image_canonicals: List of image canonical names.
        :return: List of agent ID sets, one for each image.
        """
        if not image_canonicals:
            return []

        tx = self._create_batch()
        for image_canonical in image_canonicals:
            tx.smembers(image_canonical)

        results = await self._client.client.exec(tx, raise_on_error=True)
        final_results: list[set[str]] = []
        if not results:
            return final_results
        for result in results:
            result = cast(set[bytes], result)
            final_results.append({member.decode() for member in result})
        return final_results

    @valkey_decorator()
    async def get_agent_counts_for_images(
        self,
        image_canonicals: list[str],
    ) -> list[int]:
        """
        Get the count of agents for multiple images.

        :param image_canonicals: List of image canonical names.
        :return: List of agent counts, one for each image.
        """
        if not image_canonicals:
            return []

        tx = self._create_batch()
        for image_canonical in image_canonicals:
            tx.scard(image_canonical)

        results = await self._client.client.exec(tx, raise_on_error=True)
        if not results:
            return []
        return [cast(int, result) for result in results]

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        return Batch(is_atomic=is_atomic)
