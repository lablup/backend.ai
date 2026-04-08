import logging
from typing import (
    Final,
    Self,
)

from glide import (
    ExpirySet,
    ExpiryType,
)

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

from .exceptions import InvalidSession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


_SESSION_KEY_EXPIRATION: Final[int] = 3600  # 1 hour


class ValkeyOpenIDClient:
    """
    Client for interacting with Valkey for statistics operations using GlideClient.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(
        self,
        client: AbstractValkeyClient,
    ) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str = "openid-client",
        pubsub_channels: set[str] | None = None,
    ) -> Self:
        """
        Create a ValkeyOpenIDClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name for the client.
        :param pubsub_channels: Set of channels to subscribe to for pub/sub functionality.
        :return: An instance of ValkeyStatClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            pubsub_channels=pubsub_channels,
        )
        await client.connect()
        return cls(
            client=client,
        )

    async def close(self) -> None:
        if self._closed:
            log.debug("ValkeyOpenIDClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    def _openid_key(self, session_key: str) -> str:
        return f"openid:session:{session_key}:code_verifier"

    async def set_openid_key(self, session_key: str, verifier: str) -> None:
        """
        Set OpenID verifier with expiration.

        :param key: The OpenID key.
        :param verifier: The verifier string.
        """
        key = self._openid_key(session_key)
        async with self._client.client() as conn:
            await conn.set(
                key,
                verifier,
                expiry=ExpirySet(ExpiryType.SEC, _SESSION_KEY_EXPIRATION),
            )

    async def get_openid_key(self, session_key: str) -> str:
        key = self._openid_key(session_key)
        async with self._client.client() as conn:
            result = await conn.get(key)
        if result is None:
            raise InvalidSession(reason=f"OpenID key not found for session {session_key}")
        return result.decode()
