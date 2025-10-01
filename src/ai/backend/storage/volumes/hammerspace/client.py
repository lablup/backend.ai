from __future__ import annotations

from pathlib import Path
from typing import Optional

import aiohttp

from ai.backend.common.clients.http_client import ClientKey, ClientPool, tcp_client_session_factory

from .schema import CreateShareParams, Objective, Share
from .types import ConnectionInfo

DOMAIN_FOR_SESSION = "hammerspace"

SINGLETON_OBJECTIVE_NAME = "single-volume-objective"


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

    async def _create_login_session(self) -> aiohttp.ClientSession:
        session = self._create_session(ClientKey(self._connection_info.address, DOMAIN_FOR_SESSION))
        async with session.post(
            f"{self._connection_info.address}/login",
            json={
                "username": self._connection_info.username,
                "password": self._connection_info.password,
            },
        ) as resp:
            resp.raise_for_status()
        return session

    async def create_share(
        self,
        params: CreateShareParams,
    ) -> Share:
        session = await self._create_login_session()
        async with session.post(
            f"{self._connection_info.address}/shares",
            params=params.query(),
            json=params.body(),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            share = Share.model_validate(data)
            return share

    async def create_share_with_objective(
        self,
        params: CreateShareParams,
        objective: Objective,
    ) -> Share:
        session = await self._create_login_session()
        async with session.post(
            f"{self._connection_info.address}/shares",
            params=params.query(),
            json={
                **params.body(),
                "objectives": {"uoid": {"uuid": objective.uoid.uuid, "objectType": "OBJECTIVE"}},
            },
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            share = Share.model_validate(data)
            return share

    async def get_singleton_objectives(self) -> Optional[Objective]:
        session = await self._create_login_session()
        query = {"spec": f"name=eq={SINGLETON_OBJECTIVE_NAME}"}
        async with session.get(f"{self._connection_info.address}/objectives", params=query) as resp:
            resp.raise_for_status()
            data = await resp.json()
            objectives = [Objective.model_validate(obj) for obj in data]
            for obj in objectives:
                if obj.name == SINGLETON_OBJECTIVE_NAME:
                    return obj
            return None

    async def create_singleton_objective(
        self,
        mount_path: Path,
    ) -> Objective:
        session = await self._create_login_session()
        body = {
            "name": SINGLETON_OBJECTIVE_NAME,
            "placementObjective": {
                "placeOnLocations": [
                    {
                        "placeOn": [str(mount_path)],
                    }
                ],
            },
        }
        async with session.post(
            f"{self._connection_info.address}/objectives",
            json=body,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            obj = Objective.model_validate(data)
            return obj

    async def set_objective_to_share(
        self,
        share_id: str,
        objective: Objective,
    ) -> None:
        session = await self._create_login_session()
        body = {
            "objective-identifier": objective.uoid.uuid,
        }
        async with session.put(
            f"{self._connection_info.address}/shares/{share_id}/objective-set",
            json=body,
        ) as resp:
            resp.raise_for_status()
