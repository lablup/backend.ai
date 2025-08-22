"""Cache source for schedule repository operations."""

import logging
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import AccessKey
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScheduleCacheSource:
    """
    Cache source for schedule-related operations.
    Handles all Redis/Valkey cache operations for scheduling.
    """

    _valkey_stat: ValkeyStatClient

    def __init__(self, valkey_stat: ValkeyStatClient):
        self._valkey_stat = valkey_stat

    async def get_keypair_concurrency(
        self, access_key: AccessKey, is_sftp: bool = False
    ) -> Optional[int]:
        """
        Get single keypair concurrency value from cache.

        :param access_key: The access key to query
        :param is_sftp: Whether to get SFTP concurrency (True) or regular concurrency (False)
        :return: Concurrency count if cached, None if not in cache
        """
        # Use the extended public method that supports both regular and SFTP concurrency
        # This now returns None for cache miss, distinguishing from actual 0 value
        return await self._valkey_stat.get_keypair_concurrency_used(
            str(access_key), is_private=is_sftp
        )

    async def set_keypair_concurrencies(
        self,
        access_key: AccessKey,
        regular_concurrency: int,
        sftp_concurrency: int,
    ) -> None:
        """
        Set both regular and SFTP concurrency values in cache in a batch.

        :param access_key: The access key to set
        :param regular_concurrency: The regular concurrency count to cache
        :param sftp_concurrency: The SFTP concurrency count to cache
        """
        # Use batch operation from ValkeyStatClient to set both values at once
        # This reduces network round trips to Redis/Valkey
        await self._valkey_stat.set_keypair_concurrencies(
            access_key=str(access_key),
            regular_concurrency=regular_concurrency,
            sftp_concurrency=sftp_concurrency,
        )

    async def invalidate_keypair_concurrencies(self, access_keys: list[AccessKey]) -> None:
        """
        Invalidate cache for multiple access keys by deleting their entries.
        Removes both regular and SFTP concurrency values.

        :param access_keys: List of access keys to invalidate cache for
        """
        if not access_keys:
            return

        # Convert AccessKey objects to strings and delete
        await self._valkey_stat.delete_keypair_concurrencies([str(ak) for ak in access_keys])
