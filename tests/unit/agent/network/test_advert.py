from typing import cast
from unittest.mock import AsyncMock, call

from ai.backend.agent.network.advert import publish_backend
from ai.backend.common.etcd import AbstractKVStore, ConfigScopes


class TestPublishBackend:
    async def test_the_boot_id_goes_first_then_the_backend(self) -> None:
        # With the backend first, a same-runtime restart briefly re-admits the old advert.
        etcd = AsyncMock()

        await publish_backend(cast(AbstractKVStore, etcd), "i-abc123", "docker", "boot-1")

        assert etcd.put.await_args_list == [
            call("network/agent/i-abc123/boot", "boot-1", scope=ConfigScopes.GLOBAL),
            call("network/agent/i-abc123/backend", "docker", scope=ConfigScopes.GLOBAL),
        ]
