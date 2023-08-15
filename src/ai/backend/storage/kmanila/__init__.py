import asyncio
import logging
from pathlib import Path
from typing import Any, Final

import aiohttp
import trafaret as t
from yarl import URL

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import QuotaScopeID

from ..abc import AbstractQuotaModel
from ..exception import ExecutionError, ExternalError
from ..types import Optional, QuotaConfig
from ..vfs import BaseQuotaModel, BaseVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


DEFAULT_MAX_POLL_COUNT: Final = 20
DEFAULT_VOLUME_SIZE: Final = 1000
DEFAULT_VOLUME_NAME: Final = "defualt"


kmanila_request_params = t.Dict(
    {
        t.Key("user_id", default=None): t.Null | t.String(),
        t.Key("password", default=None): t.Null | t.String(),
        t.Key("volume_name", default=None): t.Null | t.String(),
    }
).allow_extra("*")


class KManilaQuotaModel(BaseQuotaModel):
    def __init__(
        self,
        mount_path: Path,
        api_base_url: URL,
        agent_addrs: list[str],
        *,
        access_to: str,
        access_level: str,
        default_user_id: str,
        default_user_password: str,
        default_project_id: Optional[str],
        default_netword_id: Optional[str],
        max_poll_count: int,
    ) -> None:
        super().__init__(mount_path)
        self.api_base_url = api_base_url
        self.agent_addrs = agent_addrs
        self.access_to = access_to
        self.access_level = access_level
        self.default_user_id = default_user_id
        self.default_user_password = default_user_password
        self.default_project_id = default_project_id
        self.default_netword_id = default_netword_id
        self.max_poll_count = max_poll_count

    async def _get_auth_info(self, user_info: dict[str, Any]) -> dict[str, Any]:
        async with aiohttp.ClientSession() as sess:
            user_id = user_info["user_id"]
            password = user_info["password"]
            request_body = {
                "auth": {
                    "identity": {
                        "methods": ["password"],
                        "password": {
                            "user": {
                                "domain": {"id": "default"},
                                "name": user_info["user_id"],
                                "password": password,
                            }
                        },
                    },
                    "scope": {
                        "project": {
                            "domain": {"id": "default"},
                            "name": user_info["user_id"],
                        }
                    },
                }
            }
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            async with sess.post(
                self.api_base_url / "identity/auth/tokens", headers=headers, json=request_body
            ) as resp:
                token = resp.headers.get("X-Subject-Token")
                if token is None:
                    status_code = resp.status
                    log.exception(f"Token not found. (code: {status_code}, user: {user_id})")
                    raise ExecutionError(f"Token not found. {status_code = }, {user_id = }")
                if self.default_project_id is None:
                    data: dict[str, Any] = await resp.json()
                    project_id = data["token"]["project"]["id"]
                else:
                    project_id = self.default_project_id
                return {"project_id": project_id, "auth_token": token}

    async def created_volume_id(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        auth_info: dict[str, Any],
    ) -> Optional[str]:
        project_id = auth_info["project_id"]
        async with session.get(f"nas/{project_id}/shares/detail") as resp:
            if resp.status == 200:
                volume_list = (await resp.json())["shares"]
                for vol in volume_list:
                    return vol["id"]
                return None
            else:
                raise ExternalError("Cannot get data from API server")

    async def _create_volume(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig],
        auth_info: dict[str, Any],
        *,
        name: str,
    ) -> str:
        if (
            volume_id := await self.created_volume_id(session, quota_scope_id, auth_info)
        ) is not None:
            return volume_id
        project_id = auth_info["project_id"]
        request_body = {
            "share": {
                "share_proto": "nfs",
                "share_network_id": self.default_netword_id,
                "name": name,
                "is_public": False,
                "size": options.limit_bytes if options is not None else DEFAULT_VOLUME_SIZE,
                "availability_zone": "DX-DCN-CJ",
                "share_type": "SSD",
            }
        }
        async with session.post(url=f"nas/{project_id}/shares", json=request_body) as resp:
            if resp.status not in (200, 201, 204):
                raise ExternalError(
                    f"Got invalid status code when post data to API server. {resp.status = }"
                )
            await asyncio.sleep(0)

        # Poll creation complete
        trial = 1
        while True:
            log.debug(f"Poll if the volume has been created, {trial = }")
            if (
                volume_id := await self.created_volume_id(session, quota_scope_id, project_id)
            ) is not None:
                return volume_id
            await asyncio.sleep(1)
            trial += 1
            if trial > self.max_poll_count:
                raise ExternalError(f"Poll trial exceeds the maximum trial count, {trial = }")

    async def _create_access_control(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        volume_id: str,
        auth_info: dict[str, Any],
    ) -> bool:
        project_id = auth_info["project_id"]
        async with session.post(
            url=f"nas/{project_id}/shares/{volume_id}/action",
            json={
                "os-access_list": None,
            },
        ) as resp:
            result = await resp.json()
            access_list: list[dict[str, Any]] = result["access_list"]
            log_items = [
                str({"access_level": item["access_level"], "access_to": item["access_to"]})
                for item in access_list
            ]
            log.debug(f"Found {len(access_list)} access control items. ({', '.join(log_items)})")
            if access_list:
                return False

        request_data = {
            "os-allow_access": {
                "access_level": self.access_level,
                "access_type": "ip",
                "access_to": self.access_to,
            }
        }
        async with session.post(
            f"nas/{project_id}/shares/{volume_id}/action",
            json=request_data,
        ) as resp:
            return True

    async def _mount_volumes_to_agents(self) -> None:
        # Do mount request to GPU nodes through ssh
        def _build_ssh_cmd(agent_addr: str) -> list[str]:
            return ["ssh", agent_addr]

        for agent_addr in self.agent_addrs:
            cmds = _build_ssh_cmd(agent_addr)
            await asyncio.create_subprocess_exec(*cmds)

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        if extra_args is not None:
            kmanila_request_params.check(extra_args)
        else:
            extra_args = {}
        user_info = {
            "user_id": extra_args.get("user_id") or self.default_user_id,
            "password": extra_args.get("password") or self.default_user_password,
        }
        volume_name = extra_args.get("volume_name") or DEFAULT_VOLUME_NAME

        auth_info = await self._get_auth_info(user_info)
        headers = {
            "X-Auth-Token": auth_info["auth_token"],
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(base_url=self.api_base_url, headers=headers) as sess:
            volume_id = await self._create_volume(
                sess, quota_scope_id, options, auth_info, name=volume_name
            )
            is_newly_created = await self._create_access_control(
                sess, quota_scope_id, volume_id, auth_info
            )
            if is_newly_created:
                await self._mount_volumes_to_agents()


class KManilaFSVolume(BaseVolume):
    async def create_quota_model(self) -> AbstractQuotaModel:
        access_level = self.config.get("access_level", "rw")
        max_poll_count = (
            int(self.config.get("max_poll_count"))  # type: ignore[arg-type]
            if self.config.get("max_poll_count")
            else DEFAULT_MAX_POLL_COUNT
        )
        return KManilaQuotaModel(
            self.mount_path,
            URL(self.config["api_base_url"]),
            self.config["agent_addrs"],
            access_to=self.config["access_to"],
            access_level=access_level,
            default_user_id=self.config["user_id"],
            default_user_password=self.config["user_password"],
            default_project_id=self.config.get("project_id"),
            default_netword_id=self.config.get("netword_id"),
            max_poll_count=max_poll_count,
        )
