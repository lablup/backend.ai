from __future__ import annotations

import logging
import uuid
from functools import partial
from typing import Optional

import aiohttp

from ai.backend.common.clients.http_client import ClientKey, ClientPool, tcp_client_session_factory
from ai.backend.logging import BraceStyleAdapter

from .errors import (
    HammerspaceAuthenticationError,
)
from .request import CreateShareParams
from .schema.objective import Objective
from .schema.share import Share
from .types import ConnectionInfo

DOMAIN_FOR_HTTP_SESSION = "hammerspace"

SINGLETON_OBJECTIVE_NAME = "bai-single-volume-objective"


log = BraceStyleAdapter(logging.getLogger(__name__))


class HammerspaceAPIClient:
    def __init__(
        self,
        connection_info: ConnectionInfo,
    ) -> None:
        custom_session_factory = partial(
            tcp_client_session_factory,
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            ssl=connection_info.ssl_enabled,
        )
        self._client_pool = ClientPool(custom_session_factory)
        self._connection_info = connection_info

    def _create_session(self, key: ClientKey) -> aiohttp.ClientSession:
        session = self._client_pool.load_client_session(key)
        return session

    async def _create_login_session(self) -> aiohttp.ClientSession:
        session = self._create_session(
            ClientKey(str(self._connection_info.address), DOMAIN_FOR_HTTP_SESSION)
        )
        async with session.post(
            self._connection_info.address / "login",
            data={
                "username": self._connection_info.username,
                "password": self._connection_info.password,
            },
            ssl=self._connection_info.ssl_enabled,
        ) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                if resp.status // 100 == 4:
                    err_msg = repr(e)
                    raise HammerspaceAuthenticationError(
                        "Hammerspace authentication failed. "
                        f"username: {self._connection_info.username}, err: {err_msg}"
                    ) from e
                raise
        return session

    async def create_share(
        self,
        params: CreateShareParams,
    ) -> Share:
        session = await self._create_login_session()
        async with session.post(
            self._connection_info.address / "shares",
            params=params.query(),
            json=params.body(),
            ssl=self._connection_info.ssl_enabled,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            share = Share.model_validate(data)
            return share

    async def get_objective(self, id: uuid.UUID) -> Optional[Objective]:
        session = await self._create_login_session()
        query = {"spec": f"uoid.uuid=eq={id}"}
        async with session.get(self._connection_info.address / "objectives", params=query) as resp:
            resp.raise_for_status()
            data = await resp.json()
            objectives = [Objective.model_validate(obj) for obj in data]
            for obj in objectives:
                if obj.uoid.uuid == id:
                    return obj
            return None
