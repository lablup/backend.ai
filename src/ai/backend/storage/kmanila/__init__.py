import asyncio
import base64
import hashlib
import hmac
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Final, NewType, Required, TypedDict, cast

import aiohttp
import trafaret as t
from yarl import URL

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventProducer, VolumeCreated
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import QuotaScopeID

from ..abc import AbstractQuotaModel
from ..exception import (
    ExecutionError,
    ExternalError,
    QuotaScopeAlreadyExists,
    QuotaScopeNotFoundError,
)
from ..types import QuotaConfig, QuotaUsage
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


RequestHeader = TypedDict(
    "RequestHeader",
    {
        "Content-Type": Required[str],
        "X-Auth-Token": Required[str],
        "x_auth_client_id": Required[str],
        "x_auth_date": Required[str],
        "x_auth_signature": Required[str],
    },
)


class KManilaQuotaModel(BaseQuotaModel):
    def __init__(
        self,
        mount_path: Path,
        etcd: AsyncEtcd,
        api_base_url: URL,
        agent_addrs: list[str],
        *,
        fs_location_prefix: str,
        access_to: str,
        access_level: str,
        kmanila_requestor_id: str,
        kmanila_requestor_pwd: str,
        kmanila_client_id: str,
        kmanila_client_secret_key: str,
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
        self.fs_location_prefix = fs_location_prefix
        self.access_to = access_to
        self.access_level = access_level
        self.kmanila_requestor_id = kmanila_requestor_id
        self.kmanila_requestor_pwd = kmanila_requestor_pwd
        self.kmanila_client_id = kmanila_client_id
        self.kmanila_client_secret_key = kmanila_client_secret_key
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
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            async with sess.post(
                self.api_base_url / "d3/adm/keystone/v3/auth/tokens",
                headers=headers,
                json=request_body,
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

    async def get_user_volume_id(self, quota_scope_id: QuotaScopeID) -> VolumeId | None:
        user_vol = await self.etcd.get_prefix(
            f"{QUOTA_VOLUME_ID_MAP_KEY}/{quota_scope_id.scope_id}"
        )
        if not user_vol:
            return None
        return VolumeId(str(user_vol["volume_id"]))

    async def put_user_volume_id(self, quota_scope_id: QuotaScopeID, data: QuotaVolumeMap) -> None:
        await self.etcd.put_prefix(
            f"{QUOTA_VOLUME_ID_MAP_KEY}/{quota_scope_id.scope_id}", cast(dict, data)
        )

    async def delete_user_volume_info(self, quota_scope_id: QuotaScopeID) -> None:
        await self.etcd.delete_prefix(f"{QUOTA_VOLUME_ID_MAP_KEY}/{quota_scope_id.scope_id}")

    async def get_volume_id(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        auth_info: dict[str, Any],
        *,
        do_hard_check: bool = True,
    ) -> VolumeId | None:
        if (vol_id := await self.get_user_volume_id(quota_scope_id)) is None:
            return None
        if not do_hard_check:
            return VolumeId(vol_id)
        if (volume_info := await self.fetch_volume_info(session, vol_id, auth_info)) is not None:
            return VolumeId(volume_info["share"]["id"])
        return None

    async def fetch_volume_info(
        self,
        session: aiohttp.ClientSession,
        volume_id: VolumeId,
        auth_info: dict[str, Any],
    ) -> dict[str, Any] | None:
        project_id = auth_info["project_id"]
        auth_token = auth_info["auth_token"]
        subpath = f"/d3/adm/manila/v2/{project_id}/shares/{volume_id}"
        headers = self._build_header(auth_token, subpath, "GET")
        async with session.get(subpath, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status // 100 == 4:
                raise ValueError(
                    f"Cannot get data from API server. {resp.status = }, {resp.url = }"
                )
            elif resp.status // 100 == 5:
                # If there is no volume data with given volume id, the Kmanila server returns 500 status
                log.info(f"Volume info not found. (id: {volume_id})")
                return None
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
        auth_token = auth_info["auth_token"]
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
        subpath = f"/d3/adm/manila/v2/{project_id}/shares"
        headers = self._build_header(auth_token, subpath, "POST")
        async with session.post(url=subpath, headers=headers, json=request_body) as resp:
            if resp.status not in (200, 201, 204):
                raise ExternalError(
                    f"Got invalid status code when post data to API server. {resp.status = }"
                )
            body = await resp.json()
            volume_creation_info = body["share"]
            volume_id = VolumeId(volume_creation_info["id"])

        # Poll creation complete
        trial = 1
        while True:
            log.debug(f"Poll if the volume has been created, {trial = }")
            if (await self.fetch_volume_info(session, volume_id, auth_info)) is not None:
                await self.put_user_volume_id(
                    quota_scope_id, QuotaVolumeMap(volume_id=volume_id, volume_name=name)
                )
                return volume_id
            await asyncio.sleep(1)
            trial += 1
            if trial > self.max_poll_count:
                raise ExternalError(f"Poll trial exceeds the maximum trial count, {trial = }")

    async def list_volume_access_control(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        volume_id: str,
        auth_info: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        List all access controls of the given volume.
        """

        project_id = auth_info["project_id"]
        auth_token = auth_info["auth_token"]
        subpath = f"/d3/adm/manila/v2/{project_id}/shares/{volume_id}/action"
        headers = self._build_header(auth_token, subpath, "POST")

        async with session.post(
            url=subpath,
            headers=headers,
            json={
                "os-access_list": None,
            },
        ) as resp:
            if resp.status != 200:
                raise ExternalError(f"Unable to fetch access control data. {resp.status = }")
            result = await resp.json()
            access_list: list[dict[str, Any]] = result["access_list"]
            return access_list

    async def create_volume_access_control(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        volume_id: str,
        auth_info: dict[str, Any],
        *,
        access_level: str,
        access_to: str,
    ) -> None:
        """
        Create access controls of the given volume.
        """

        project_id = auth_info["project_id"]
        auth_token = auth_info["auth_token"]
        subpath = f"/d3/adm/manila/v2/{project_id}/shares/{volume_id}/action"
        headers = self._build_header(auth_token, subpath, "POST")
        request_data = {
            "os-allow_access": {
                "access_level": access_level,
                "access_type": "ip",
                "access_to": access_to,
            }
        }
        async with session.post(
            subpath,
            headers=headers,
            json=request_data,
        ) as resp:
            if resp.status != 200:
                raise ExternalError(f"Unable to create access control. {resp.status = }")

    async def _create_access_control(
        self,
        session: aiohttp.ClientSession,
        quota_scope_id: QuotaScopeID,
        volume_id: str,
        auth_info: dict[str, Any],
    ) -> bool:
        """
        Should create a new access control for all newly created volumes.

        If the access control of the volume exists, returns False.
        if the access control does not exists, create it and returns True.
        """

        # Check the access control already exists with the given volume id.
        access_list = await self.list_volume_access_control(
            session, quota_scope_id, volume_id, auth_info
        )
        log_items = [
            str({"access_level": item["access_level"], "access_to": item["access_to"]})
            for item in access_list
        ]
        log.debug(f"Found {len(access_list)} access control items. ({', '.join(log_items)})")
        if access_list:
            return False

        # Should wait before create access control
        # Otherwise, we get status code 500
        await asyncio.sleep(5)
        await self.create_volume_access_control(
            session,
            quota_scope_id,
            volume_id,
            auth_info,
            access_level=self.access_level,
            access_to=self.access_to,
        )
        return True

    def _build_header(self, auth_token: str, subpath: str, method: str) -> RequestHeader:
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        signature = bytes(self.kmanila_client_secret_key, "utf8")
        md = hmac.new(signature, bytes(f"{now}_{method}_{subpath}", "utf8"), hashlib.sha256)
        sign = base64.b64encode(md.digest()).decode("utf8")
        return {
            "Content-Type": "application/json",
            "X-Auth-Token": auth_token,
            "x_auth_client_id": self.kmanila_client_id,
            "x_auth_date": now,
            "x_auth_signature": sign,
        }

    # override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        _extra_args: dict[str, Any] = kmanila_request_params.check(extra_args)
        volume_name: str = _extra_args["volume_name"]
        event_producer: EventProducer = _extra_args["event_producer"]

        auth_info = await self._get_auth_info(quota_scope_id)

        async with aiohttp.ClientSession(base_url=self.api_base_url) as sess:
            volume_id = await self._create_volume(
                sess, quota_scope_id, options, auth_info, name=volume_name
            )
            is_newly_created = await self._create_access_control(
                sess, quota_scope_id, volume_id, auth_info
            )
            if not is_newly_created:
                raise QuotaScopeAlreadyExists

        await event_producer.produce_event(
            VolumeCreated(
                mount_path=str(self.mangle_qspath(quota_scope_id)),
                fs_location=f"{self.fs_location_prefix}:/share_{volume_id}",
                fs_type="nfs",
                edit_fstab=True,
            )
        )

    # override
    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> QuotaUsage | None:
        auth_info = await self._get_auth_info(quota_scope_id)

        async with aiohttp.ClientSession(base_url=self.api_base_url) as session:
            if (await self.get_volume_id(session, quota_scope_id, auth_info)) is None:
                raise QuotaScopeNotFoundError
            return QuotaUsage(-1, -1)

    # override
    async def get_external_volume_info(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> dict[str, Any] | None:
        auth_info = await self._get_auth_info(quota_scope_id)

        async with aiohttp.ClientSession(base_url=self.api_base_url) as session:
            if (volume_id := await self.get_volume_id(session, quota_scope_id, auth_info)) is None:
                raise QuotaScopeNotFoundError
            if (data := await self.fetch_volume_info(session, volume_id, auth_info)) is not None:
                return data["share"]
            raise ExternalError("Cannot get volume info from NAS server.")

    # override
    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig,
    ) -> None:
        auth_info = await self._get_auth_info(quota_scope_id)

        async with aiohttp.ClientSession(base_url=self.api_base_url) as session:
            if (volume_id := await self.get_volume_id(session, quota_scope_id, auth_info)) is None:
                raise QuotaScopeNotFoundError
            project_id = auth_info["project_id"]
            auth_token = auth_info["auth_token"]
            subpath = f"/d3/adm/manila/v2/{project_id}/shares/{volume_id}/action"
            headers = self._build_header(auth_token, subpath, "POST")
            rqst_body = {"os-extend": {"new_size": options.limit_bytes, "force": True}}
            async with session.post(
                url=subpath,
                headers=headers,
                json=rqst_body,
            ):
                pass

    # override
    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        auth_info = await self._get_auth_info(quota_scope_id)

        async with aiohttp.ClientSession(base_url=self.api_base_url) as session:
            if (volume_id := await self.get_volume_id(session, quota_scope_id, auth_info)) is None:
                raise QuotaScopeNotFoundError
            project_id = auth_info["project_id"]
            auth_token = auth_info["auth_token"]
            subpath = f"/d3/adm/manila/v2/{project_id}/shares/{volume_id}"
            headers = self._build_header(auth_token, subpath, "DELETE")
            async with session.delete(
                url=subpath,
                headers=headers,
            ) as resp:
                status_code = resp.status
                if status_code != 202:
                    raise ExecutionError(f"Cannot delete volume. {status_code = }, {volume_id = }")

        # Delete user volume map info saved in etcd
        await self.delete_user_volume_info(quota_scope_id)


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
            fs_location_prefix=self.config["fs_location_prefix"],
            access_to=self.config["access_to"],
            access_level=access_level,
            kmanila_requestor_id=self.config["user_id"],
            kmanila_requestor_pwd=self.config["user_password"],
            kmanila_client_id=self.config["client_id"],
            kmanila_client_secret_key=self.config["client_secret_key"],
            default_project_id=self.config.get("project_id"),
            default_network_id=self.config.get("network_id"),
            availability_zone=self.config["availability_zone"],
            share_type=self.config["share_type"],
            max_poll_count=max_poll_count,
        )
