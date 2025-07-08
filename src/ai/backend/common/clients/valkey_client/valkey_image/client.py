import logging
from typing import ParamSpec, Self, TypeVar

from glide import Batch

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
    valkey_decorator,
)
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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
        redis_target: RedisTarget,
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
            target=redis_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    async def close(self) -> None:
        """
        Close the ValkeyImageClient connection.
        """
        if self._closed:
            log.warning("ValkeyImageClient is already closed.")
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
        while True:
            result = await self._client.client.scan(cursor)
            if isinstance(result, list) and len(result) >= 2:
                new_cursor = result[0]
                keys = result[1]
                if keys:
                    tx = self._create_batch()
                    for key in keys:
                        key_str = key.decode() if isinstance(key, bytes) else str(key)
                        tx.srem(key_str, [agent_id])
                    await self._client.client.exec(tx, raise_on_error=True)
                cursor = new_cursor if isinstance(new_cursor, bytes) else b"0"
            else:
                break
            if cursor == b"0":
                break

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
        return {member.decode() if isinstance(member, bytes) else str(member) for member in result}

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
        if results:
            for result in results:
                if result is None:
                    final_results.append(set())
                elif hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
                    final_results.append({
                        member.decode() if isinstance(member, bytes) else str(member)
                        for member in result
                    })
                else:
                    final_results.append(set())
        return final_results

    @valkey_decorator()
    async def get_agent_count_for_image(
        self,
        image_canonical: str,
    ) -> int:
        """
        Get the count of agents that have a specific image.

        :param image_canonical: The image canonical name.
        :return: Number of agents.
        """
        return await self._client.client.scard(image_canonical)

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
        if results:
            return [
                int(result) if result is not None and isinstance(result, (int, str)) else 0
                for result in results
            ]
        return []

    @valkey_decorator()
    async def get_all_image_names(self) -> list[str]:
        """
        Get all image canonical names.

        :return: List of image canonical names.
        """
        all_keys = []
        cursor = b"0"
        while True:
            result = await self._client.client.scan(cursor)
            if isinstance(result, list) and len(result) >= 2:
                new_cursor = result[0]
                keys = result[1]
                if keys:
                    all_keys.extend([
                        key.decode() if isinstance(key, bytes) else str(key) for key in keys
                    ])
                cursor = new_cursor if isinstance(new_cursor, bytes) else b"0"
            else:
                break
            if cursor == b"0":
                break
        return all_keys

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        return Batch(is_atomic=is_atomic)
