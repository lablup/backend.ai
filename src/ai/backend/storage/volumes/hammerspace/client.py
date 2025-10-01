from __future__ import annotations

from dataclasses import dataclass

import aiohttp

from ai.backend.common.clients.http_client import ClientKey, ClientPool, tcp_client_session_factory

from .types import ConnectionInfo

DOMAIN_FOR_SESSION = "hammerspace"


@dataclass
class CreateShareParams:
    name: str
    path: str
    create_path: bool = True
    validate_only: bool = False

    def query(self) -> dict[str, str]:
        return {
            "create-path": "true" if self.create_path else "false",
            "validate-only": "true" if self.validate_only else "false",
        }

    def body(self) -> dict[str, str]:
        return {
            "name": self.name,
            "path": self.path,
        }


class HammerspaceAPIClient:
    def __init__(
        self,
        connection_info: ConnectionInfo,
    ) -> None:
        self._client_pool = ClientPool(tcp_client_session_factory)
        self._connection_info = connection_info

    def _create_session(self, key: ClientKey) -> aiohttp.ClientSession:
        session = self._client_pool.load_client_session(key)
        return session

    async def create_share(
        self,
        params: CreateShareParams,
    ) -> None:
        session = self._create_session(ClientKey(self._connection_info.address, DOMAIN_FOR_SESSION))
        async with session.post(
            f"{self._connection_info.address}/shares",
            params=params.query(),
            json=params.body(),
        ) as resp:
            resp.raise_for_status()
