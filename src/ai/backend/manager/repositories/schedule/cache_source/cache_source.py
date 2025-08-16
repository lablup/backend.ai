"""Cache source for schedule repository operations."""

import logging
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import AccessKey
from ai.backend.logging.utils import BraceStyleAdapter

from .types import CacheConcurrencyData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScheduleCacheSource:
    """
    Cache source for schedule-related operations.
    Handles all Redis/Valkey cache operations for scheduling.
    """

    _valkey_stat: ValkeyStatClient

    def __init__(self, valkey_stat: ValkeyStatClient):
        self._valkey_stat = valkey_stat

    async def get_concurrency_snapshot(self, access_keys: set[AccessKey]) -> CacheConcurrencyData:
        """
        Get current concurrency data from cache for the given access keys.
        Returns concurrency counts for regular and SFTP sessions.
        """
        if not access_keys:
            return CacheConcurrencyData(
                sessions_by_keypair={},
                sftp_sessions_by_keypair={},
            )

        # Prepare all keys for batch retrieval
        access_key_list = list(access_keys)
        regular_keys = [f"keypair.concurrency_used.{ak}" for ak in access_key_list]
        sftp_keys = [f"keypair.sftp_concurrency_used.{ak}" for ak in access_key_list]
        all_keys = regular_keys + sftp_keys

        # Batch get all values
        results = await self._get_multiple_keys(all_keys)

        # Process results
        sessions_by_keypair: dict[AccessKey, int] = {}
        sftp_sessions_by_keypair: dict[AccessKey, int] = {}

        for i, ak in enumerate(access_key_list):
            # Regular concurrency
            regular_result = results[i] if i < len(results) else None
            sessions_by_keypair[ak] = int(regular_result.decode()) if regular_result else 0

            # SFTP concurrency
            sftp_idx = len(access_key_list) + i
            sftp_result = results[sftp_idx] if sftp_idx < len(results) else None
            sftp_sessions_by_keypair[ak] = int(sftp_result.decode()) if sftp_result else 0

        return CacheConcurrencyData(
            sessions_by_keypair=sessions_by_keypair,
            sftp_sessions_by_keypair=sftp_sessions_by_keypair,
        )

    async def _get_multiple_keys(self, keys: list[str]) -> list[Optional[bytes]]:
        """
        Get multiple keys from cache in a single operation.

        :param keys: List of cache keys to retrieve
        :return: List of values (bytes or None if key doesn't exist)
        """
        return await self._valkey_stat._get_multiple_keys(keys)
