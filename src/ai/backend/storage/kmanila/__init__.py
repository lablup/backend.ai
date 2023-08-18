import asyncio
import logging
from pathlib import Path
from typing import Any, Final, NewType, TypedDict, cast

import aiohttp
import trafaret as t
from yarl import URL

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import QuotaScopeID

from ..abc import AbstractQuotaModel
from ..exception import ExecutionError, ExternalError
from ..types import QuotaConfig
from ..vfs import BaseQuotaModel, BaseVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


DEFAULT_MAX_POLL_COUNT: Final = 20
DEFAULT_VOLUME_SIZE: Final = 1000
QUOTA_VOLUME_ID_MAP_KEY: Final = "kmanila/volumes"


kmanila_request_params = t.Dict(
    {
        t.Key("volume_name"): t.String(),
    }
).allow_extra("*")

VolumeId = NewType("VolumeId", str)


class QuotaVolumeMap(TypedDict):
    volume_id: str
    volume_name: str


class KManilaQuotaModel(BaseQuotaModel):
    def __init__(
        self,
        mount_path: Path,
        etcd: AsyncEtcd,
        api_base_url: URL,
        agent_addrs: list[str],
        *,
        access_to: str,
        access_level: str,
        kmanila_requestor_id: str,
        kmanila_requestor_pwd: str,
        default_project_id: str | None,
        default_network_id: str | None,
        availability_zone: str,
        share_type: str,
        max_poll_count: int,
    ) -> None:
        super().__init__(mount_path)
        self.etcd = etcd
        self.api_base_url = api_base_url
        self.agent_addrs = agent_addrs
        self.access_to = access_to
        self.access_level = access_level
        self.kmanila_requestor_id = kmanila_requestor_id
        self.kmanila_requestor_pwd = kmanila_requestor_pwd
        self.default_project_id = default_project_id
        self.default_network_id = default_network_id
        self.availability_zone = availability_zone
        self.share_type = share_type
        self.max_poll_count = max_poll_count

    async def _get_auth_info(self, user_id: QuotaScopeID) -> dict[str, Any]:
        async with aiohttp.ClientSession() as sess:
            rqst_id = self.kmanila_requestor_id
            rqst_pwd = self.kmanila_requestor_pwd
            request_body = {
                "auth": {
                    "identity": {
                        "methods": ["password"],
                        "password": {
                            "user": {
                                "domain": {"id": "default"},
                                "name": rqst_id,
                                "password": rqst_pwd,
                            }
                        },
                    },
                    "scope": {
                        "project": {
                            "domain": {"id": "default"},
                            "name": rqst_id,
                        }
                    },
                }
            }
            headers = {"Accept": "application/json"}
            async with sess.post(
                self.api_base_url / "d3/identity/auth/tokens", headers=headers, json=request_body
            ) as resp:
                token = resp.headers.get("X-Subject-Token")
                if token is None:
                    status_code = resp.status
                    raise ExecutionError(f"Token not found. {status_code = }, {rqst_id = }")
                if self.default_project_id is None:
                    data: dict[str, Any] = await resp.json()
                    project_id = data["token"]["project"]["id"]
                else:
                    project_id = self.default_project_id
                return {"project_id": project_id, "auth_token": token}

    async def get_user_volume_id(self, quota_scope_id: QuotaScopeID) -> str | None:
        user_vol = await self.etcd.get_prefix(
            f"{QUOTA_VOLUME_ID_MAP_KEY}/{quota_scope_id.scope_id}"
        )
        if not user_vol:
            return None
        return str(user_vol["volume_id"])

    async def put_user_volume_id(self, quota_scope_id: QuotaScopeID, data: QuotaVolumeMap) -> None:
        await self.etcd.put_prefix(
            f"{QUOTA_VOLUME_ID_MAP_KEY}/{quota_scope_id.scope_id}", cast(dict, data)
        )

    async def get_volume_id(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        auth_info: dict[str, Any],
        *,
        do_hard_check: bool = True,
    ) -> VolumeId | None:
        if (vol_id := await self.get_user_volume_id(quota_scope_id)) is not None:
            if not do_hard_check:
                return VolumeId(vol_id)
        project_id = auth_info["project_id"]
        async with session.get(f"/d3/adm/manila/v2/{project_id}/shares/{vol_id}") as resp:
            if resp.status == 200:
                volume_info = (await resp.json())["share"]
                return VolumeId(volume_info["id"])
            elif resp.status // 100 == 5:
                raise ExternalError("Cannot get data from API server")
        return None

    async def _create_volume(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None,
        auth_info: dict[str, Any],
        *,
        name: str,
    ) -> VolumeId:
        if (volume_id := await self.get_volume_id(session, quota_scope_id, auth_info)) is not None:
            return volume_id
        project_id = auth_info["project_id"]
        request_body = {
            "share": {
                "share_proto": "nfs",
                "share_network_id": self.default_network_id,
                "name": name,
                "is_public": False,
                "size": options.limit_bytes if options is not None else DEFAULT_VOLUME_SIZE,
                "availability_zone": self.availability_zone,
                "share_type": self.share_type,
            }
        }
        async with session.post(
            url=f"/d3/adm/manila/v2/{project_id}/shares", json=request_body
        ) as resp:
            if resp.status not in (200, 201, 204):
                raise ExternalError(
                    f"Got invalid status code when post data to API server. {resp.status = }"
                )

        # Poll creation complete
        trial = 1
        while True:
            log.debug(f"Poll if the volume has been created, {trial = }")
            if (
                volume_id := await self.get_volume_id(session, quota_scope_id, project_id)
            ) is not None:
                await self.put_user_volume_id(
                    quota_scope_id, QuotaVolumeMap(volume_id=volume_id, volume_name=name)
                )
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
        """
        Should create a new access control for all newly created volumes.
        """

        project_id = auth_info["project_id"]
        async with session.post(
            url=f"/d3/adm/manila/v2/{project_id}/shares/{volume_id}/action",
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
            f"/d3/adm/manila/v2/{project_id}/shares/{volume_id}/action",
            json=request_data,
        ) as resp:
            return True

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        volume_info: dict[str, str] = kmanila_request_params.check(extra_args)
        volume_name = volume_info["volume_name"]

        auth_info = await self._get_auth_info(quota_scope_id)
        headers = {
            "X-Auth-Token": auth_info["auth_token"],
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(base_url=self.api_base_url, headers=headers) as sess:
            volume_id = await self._create_volume(
                sess, quota_scope_id, options, auth_info, name=volume_name
            )
            await self._create_access_control(sess, quota_scope_id, volume_id, auth_info)


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
            self.etcd,
            URL(self.config["api_base_url"]),
            self.config["agent_addrs"],
            access_to=self.config["access_to"],
            access_level=access_level,
            kmanila_requestor_id=self.config["user_id"],
            kmanila_requestor_pwd=self.config["user_password"],
            default_project_id=self.config.get("project_id"),
            default_network_id=self.config.get("network_id"),
            availability_zone=self.config["availability_zone"],
            share_type=self.config["share_type"],
            max_poll_count=max_poll_count,
        )
