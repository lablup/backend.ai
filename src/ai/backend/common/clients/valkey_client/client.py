from typing import final

from glide import (
    Batch,
    GlideClient,
)


class ValkeyClient:
    _client: GlideClient
    _is_cluster_mode: bool

    def __init__(self, client: GlideClient, is_cluster_mode: bool) -> None:
        self._client = client
        self._is_cluster_mode = is_cluster_mode

    @final
    async def ping(self) -> None:
        """
        Ping the Valkey server to check connectivity.
        """
        await self._client.ping()

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        return Batch(is_atomic=is_atomic)
