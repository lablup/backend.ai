import asyncio
import json
import logging
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final, FrozenSet, Literal, Optional, cast

import aiofiles
import aiofiles.os

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.common.types import HardwareMetadata, QuotaConfig, QuotaScopeID
from ai.backend.logging import BraceStyleAdapter

from ..abc import CAP_FAST_FS_SIZE, CAP_FAST_SIZE, CAP_METRIC, CAP_QUOTA, CAP_VFOLDER
from ..exception import (
    ExternalError,
    InvalidQuotaConfig,
    QuotaScopeNotFoundError,
    StorageProxyError,
)
from ..types import CapacityUsage, FSPerfMetric, QuotaUsage
from ..vfs import BaseQuotaModel, BaseVolume
from .config import config_iv
from .exceptions import VASTInvalidParameterError, VASTNotFoundError, VASTUnknownError
from .vastdata_client import VASTAPIClient, VASTQuota, VASTQuotaID

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


VAST_QUOTA_ID_FILE_NAME: Final = ".vast-quota-id"


class VASTQuotaModel(BaseQuotaModel):
    def __init__(
        self,
        mount_path: Path,
        api_client: VASTAPIClient,
    ) -> None:
        super().__init__(mount_path)
        self.api_client = api_client

    async def _get_vast_quota_id(self, quota_scope_id: QuotaScopeID) -> VASTQuotaID | None:
        qs_path = self.mangle_qspath(quota_scope_id)

        def _read():
            try:
                with open(qs_path / VAST_QUOTA_ID_FILE_NAME, "r") as f:
                    return VASTQuotaID(f.read())
            except FileNotFoundError:
                return None

        return await asyncio.get_running_loop().run_in_executor(None, _read)

    async def _set_vast_quota_id(
        self, quota_scope_id: QuotaScopeID, vast_quota_id: VASTQuotaID
    ) -> None:
        qs_path = self.mangle_qspath(quota_scope_id)

        def _write():
            qs_path.mkdir(parents=True, exist_ok=True)
            with open(qs_path / VAST_QUOTA_ID_FILE_NAME, "w") as f:
                f.write(str(vast_quota_id))

        await asyncio.get_running_loop().run_in_executor(None, _write)

    async def _rm_vast_quota_id(self, quota_scope_id: QuotaScopeID) -> None:
        qs_path = self.mangle_qspath(quota_scope_id)

        try:
            await aiofiles.os.remove(qs_path / VAST_QUOTA_ID_FILE_NAME)
        except FileNotFoundError:
            log.warning(f"vast quota id file not found (qid: {quota_scope_id}). skip")

    async def _modify_quota_scope(
        self,
        vast_quota_id: VASTQuotaID,
        config: QuotaConfig,
    ) -> VASTQuota:
        try:
            return await self.api_client.modify_quota(
                vast_quota_id,
                soft_limit=config.limit_bytes,
                hard_limit=config.limit_bytes,
            )
        except VASTInvalidParameterError:
            raise InvalidQuotaConfig
        except VASTUnknownError as e:
            raise ExternalError(str(e))

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)

        async def _set_quota(_options: QuotaConfig) -> VASTQuota:
            try:
                quota = await self.api_client.set_quota(
                    qspath,
                    soft_limit=_options.limit_bytes,
                    hard_limit=_options.limit_bytes,
                )
            except VASTInvalidParameterError as e:
                # Check if quota has already been set to the quota scope path
                quota_name = str(qspath)
                quotas = await self.api_client.list_quotas(quota_name)
                existing_quota: Optional[VASTQuota] = None
                for q in quotas:
                    if q.name == quota_name:
                        existing_quota = q
                        break
                else:
                    log.error(
                        "Got invalid parameter error but no quota exists with given quota name"
                        f" ({quota_name}). Raise error (orig:{str(e)})"
                    )
                    raise InvalidQuotaConfig
                assert existing_quota is not None
                await self._set_vast_quota_id(quota_scope_id, existing_quota.id)
                await self.api_client.modify_quota(
                    existing_quota.id,
                    soft_limit=_options.limit_bytes,
                    hard_limit=_options.limit_bytes,
                )
                return existing_quota
            except VASTUnknownError as e:
                raise ExternalError(str(e))
            return quota

        try:
            await aiofiles.os.makedirs(qspath)
        except FileExistsError:
            if options is None:
                return
            vast_quota_id = await self._get_vast_quota_id(quota_scope_id)
            if vast_quota_id is not None:
                existing_quota = await self.api_client.get_quota(vast_quota_id)
                if existing_quota is not None:
                    quota = await self._modify_quota_scope(vast_quota_id, options)
                else:
                    quota = await _set_quota(options)
            else:
                quota = await _set_quota(options)
            await self._set_vast_quota_id(quota_scope_id, quota.id)
        else:
            if options is None:
                return
            quota = await _set_quota(options)
            await self._set_vast_quota_id(quota_scope_id, quota.id)

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        vast_quota_id = await self._get_vast_quota_id(quota_scope_id)
        if vast_quota_id is None:
            raise QuotaScopeNotFoundError
        await self._modify_quota_scope(vast_quota_id, config)

    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> Optional[QuotaUsage]:
        if (vast_quota_id := await self._get_vast_quota_id(quota_scope_id)) is None:
            return None
        if (quota := await self.api_client.get_quota(vast_quota_id)) is None:
            return None
        return QuotaUsage(
            used_bytes=quota.used_capacity,
            limit_bytes=quota.hard_limit,
        )

    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        vast_quota_id = await self._get_vast_quota_id(quota_scope_id)
        if vast_quota_id is None:
            raise QuotaScopeNotFoundError
        try:
            await self.api_client.remove_quota(vast_quota_id)
        except VASTNotFoundError:
            raise QuotaScopeNotFoundError
        await self._rm_vast_quota_id(quota_scope_id)

    async def delete_quota_scope(self, quota_scope_id: QuotaScopeID) -> None:
        await self.unset_quota(quota_scope_id)
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.rmdir(qspath)


class VASTVolume(BaseVolume):
    api_client: VASTAPIClient

    name = "vast"

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        options: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            local_config,
            mount_path,
            etcd=etcd,
            options=options,
            event_dispatcher=event_dispatcher,
            event_producer=event_producer,
        )
        self.config = cast(Mapping[str, Any], config_iv.check(self.config))
        ssl_verify = self.config.get("vast_verify_ssl", False)
        self.api_client = VASTAPIClient(
            self.config["vast_endpoint"],
            self.config["vast_username"],
            self.config["vast_password"],
            storage_base_dir=self.config["vast_storage_base_dir"],
            api_version=self.config["vast_api_version"],
            ssl=ssl_verify,
            force_login=self.config["vast_force_login"],
        )

    async def shutdown(self) -> None:
        self.api_client.cache.cluster_info = None

    async def create_quota_model(self) -> VASTQuotaModel:
        return VASTQuotaModel(self.mount_path, self.api_client)

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_METRIC, CAP_QUOTA, CAP_FAST_FS_SIZE, CAP_FAST_SIZE])

    async def get_hwinfo(self) -> HardwareMetadata:
        cluster_id: int = self.config["vast_cluster_id"]
        try:
            clsuter_info = await self.api_client.get_cluster_info(cluster_id)
        except VASTUnknownError:
            return {
                "status": "unavailable",
                "status_info": None,
                "metadata": {},
            }
        if clsuter_info is None:
            raise StorageProxyError(f"vast cluster not found. (id: {cluster_id})")
        healthy_status: Literal["healthy", "degraded", "unavailable"] = "unavailable"
        match clsuter_info.state.lower():
            case "online" | "healthy":
                healthy_status = "healthy"
            case "init":
                healthy_status = "degraded"
            case "unknown":
                healthy_status = "unavailable"
        quotas = await self.api_client.list_quotas()
        return {
            "status": healthy_status,
            "status_info": clsuter_info.state,
            "metadata": {
                "quota": json.dumps([asdict(q) for q in quotas]),
                "cluster_info": json.dumps(asdict(clsuter_info)),
            },
        }

    async def get_performance_metric(self) -> FSPerfMetric:
        cluster_id: int = self.config["vast_cluster_id"]
        try:
            clsuter_info = await self.api_client.get_cluster_info(cluster_id)
        except VASTUnknownError:
            return FSPerfMetric(
                iops_read=-1,
                iops_write=-1,
                io_bytes_read=-1,
                io_bytes_write=-1,
                io_usec_read=-1,
                io_usec_write=-1,
            )
        if clsuter_info is None:
            raise StorageProxyError(f"vast cluster not found. (id: {cluster_id})")
        return FSPerfMetric(
            iops_read=clsuter_info.rd_iops,
            iops_write=clsuter_info.wr_iops,
            io_usec_read=clsuter_info.rd_latency,
            io_usec_write=clsuter_info.wr_latency,
            io_bytes_read=clsuter_info.rd_bw,
            io_bytes_write=clsuter_info.wr_bw,
        )

    async def get_fs_usage(self) -> CapacityUsage:
        cluster_id: int = self.config["vast_cluster_id"]
        try:
            clsuter_info = await self.api_client.get_cluster_info(cluster_id)
        except VASTUnknownError:
            return CapacityUsage(
                used_bytes=-1,
                capacity_bytes=-1,
            )
        if clsuter_info is None:
            raise StorageProxyError(f"vast cluster not found. (id: {cluster_id})")
        return CapacityUsage(
            used_bytes=clsuter_info.physical_space_in_use,
            capacity_bytes=clsuter_info.physical_space,
        )
