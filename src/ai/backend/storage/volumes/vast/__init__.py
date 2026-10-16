import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, Final, Literal, cast, override

import aiofiles
import aiofiles.os

from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.clients.storage_backends.vast.client import (
    VASTAPIClient,
    VASTAPIClientArgs,
)
from ai.backend.common.clients.storage_backends.vast.exceptions import (
    VASTInvalidParameterError,
    VASTNotFoundError,
    VASTQuotaAlreadyExistsError,
    VASTUnknownError,
)
from ai.backend.common.data.storage.types import (
    StorageBackendCapability,
    StorageBackendType,
)
from ai.backend.common.dto.clients.storage_backends.vast.request import (
    VASTModifyQuotaRequest,
    VASTSetQuotaRequest,
)
from ai.backend.common.dto.clients.storage_backends.vast.response import (
    VASTClusterInfo,
    VASTQuota,
)
from ai.backend.common.dto.clients.storage_backends.vast.types import VASTQuotaID
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import HardwareMetadata, QuotaConfig, QuotaScopeID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.errors import (
    ExternalStorageServiceError,
    InvalidQuotaConfig,
    QuotaScopeAlreadyExists,
    QuotaScopeNotFoundError,
    StorageProxyError,
)
from ai.backend.storage.types import CapacityUsage, FSPerfMetric, QuotaUsage
from ai.backend.storage.volumes.vfs import BaseQuotaModel, BaseVolume
from ai.backend.storage.watcher import WatcherClient

from .config import config_iv

log = StructuredLogger(logging.getLogger(__spec__.name))

VAST_QUOTA_ID_FILE_NAME: Final = ".vast-quota-id"


class VASTQuotaModel(BaseQuotaModel):
    api_client: VASTAPIClient
    _storage_base_dir: Path

    def __init__(
        self,
        mount_path: Path,
        api_client: VASTAPIClient,
        storage_base_dir: Path,
    ) -> None:
        super().__init__(mount_path)
        self.api_client = api_client
        self._storage_base_dir = storage_base_dir

    async def _get_vast_quota_id(self, quota_scope_id: QuotaScopeID) -> VASTQuotaID | None:
        qs_path = self.mangle_qspath(quota_scope_id)

        def _read() -> VASTQuotaID | None:
            try:
                with (qs_path / VAST_QUOTA_ID_FILE_NAME).open() as f:
                    return VASTQuotaID(f.read())
            except FileNotFoundError:
                return None

        return await run_in_executor_with_context(None, _read)

    async def _set_vast_quota_id(
        self, quota_scope_id: QuotaScopeID, vast_quota_id: VASTQuotaID
    ) -> None:
        qs_path = self.mangle_qspath(quota_scope_id)

        def _write() -> None:
            qs_path.mkdir(parents=True, exist_ok=True)
            with (qs_path / VAST_QUOTA_ID_FILE_NAME).open("w") as f:
                f.write(str(vast_quota_id))

        await run_in_executor_with_context(None, _write)

    async def _rm_vast_quota_id(self, quota_scope_id: QuotaScopeID) -> None:
        qs_path = self.mangle_qspath(quota_scope_id)

        try:
            await aiofiles.os.remove(qs_path / VAST_QUOTA_ID_FILE_NAME)
        except FileNotFoundError:
            log.trace("VAST quota id file not found for quota scope {}, skipping", quota_scope_id)

    async def _modify_quota(self, vast_quota_id: VASTQuotaID, limit_bytes: int) -> VASTQuota:
        await self.api_client.login()
        return await self.api_client.modify_quota(
            vast_quota_id,
            VASTModifyQuotaRequest(soft_limit=limit_bytes, hard_limit=limit_bytes),
        )

    async def _modify_quota_scope(
        self,
        vast_quota_id: VASTQuotaID,
        config: QuotaConfig,
    ) -> VASTQuota:
        try:
            return await self._modify_quota(vast_quota_id, config.limit_bytes)
        except VASTInvalidParameterError as e:
            raise InvalidQuotaConfig from e
        except VASTUnknownError as e:
            raise ExternalStorageServiceError(
                f"VAST API unknown error during quota modification: {e}"
            ) from e

    async def _set_quota(self, qspath: Path, options: QuotaConfig) -> VASTQuota:
        quota_name = str(qspath)
        await self.api_client.login()
        try:
            return await self.api_client.set_quota(
                VASTSetQuotaRequest(
                    name=quota_name,
                    path=str(self._storage_base_dir / qspath.name),
                    create_dir=False,
                    soft_limit=options.limit_bytes,
                    hard_limit=options.limit_bytes,
                )
            )
        except VASTQuotaAlreadyExistsError as e:
            raise QuotaScopeAlreadyExists from e
        except VASTInvalidParameterError as e:
            quotas = await self.api_client.list_quotas(quota_name)
            for existing_quota in quotas:
                if existing_quota.name == quota_name:
                    break
            else:
                raise InvalidQuotaConfig(f"No existing quota found with name {quota_name}") from e
            await self._modify_quota(existing_quota.id, options.limit_bytes)
            return existing_quota
        except VASTUnknownError as e:
            raise ExternalStorageServiceError(
                f"VAST API unknown error during quota creation: {e}"
            ) from e

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        try:
            await aiofiles.os.makedirs(qspath)
        except FileExistsError:
            if options is None:
                return
            vast_quota_id = await self._get_vast_quota_id(quota_scope_id)
            if vast_quota_id is not None:
                await self.api_client.login()
                existing_quota = await self.api_client.get_quota(vast_quota_id)
                if existing_quota is not None:
                    quota = await self._modify_quota_scope(vast_quota_id, options)
                else:
                    quota = await self._set_quota(qspath, options)
            else:
                quota = await self._set_quota(qspath, options)
            await self._set_vast_quota_id(quota_scope_id, quota.id)
        else:
            if options is None:
                return
            quota = await self._set_quota(qspath, options)
            await self._set_vast_quota_id(quota_scope_id, quota.id)

    @override
    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        vast_quota_id = await self._get_vast_quota_id(quota_scope_id)
        if vast_quota_id is None:
            raise QuotaScopeNotFoundError
        await self._modify_quota_scope(vast_quota_id, config)

    @override
    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> QuotaUsage | None:
        if (vast_quota_id := await self._get_vast_quota_id(quota_scope_id)) is None:
            return None
        await self.api_client.login()
        if (quota := await self.api_client.get_quota(vast_quota_id)) is None:
            return None
        if quota.used_capacity < 0 or quota.hard_limit < 0:
            log.warning(
                "negative quota usage reported",
                used_bytes=quota.used_capacity,
                limit_bytes=quota.hard_limit,
                response_body=quota.model_dump_json(),
            )
        return QuotaUsage(
            used_bytes=quota.used_capacity,
            limit_bytes=quota.hard_limit,
        )

    @override
    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        vast_quota_id = await self._get_vast_quota_id(quota_scope_id)
        if vast_quota_id is None:
            raise QuotaScopeNotFoundError
        await self.api_client.login()
        try:
            await self.api_client.remove_quota(vast_quota_id)
        except VASTNotFoundError as e:
            raise QuotaScopeNotFoundError from e
        await self._rm_vast_quota_id(quota_scope_id)

    @override
    async def delete_quota_scope(self, quota_scope_id: QuotaScopeID) -> None:
        await self.unset_quota(quota_scope_id)
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.rmdir(qspath)


class VASTVolume(BaseVolume):
    name: ClassVar[StorageBackendType] = StorageBackendType("vast")
    api_client: VASTAPIClient
    _storage_base_dir: Path

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        watcher: WatcherClient | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(
            local_config,
            mount_path,
            etcd=etcd,
            options=options,
            event_dispatcher=event_dispatcher,
            event_producer=event_producer,
            watcher=watcher,
        )
        self.config = cast(Mapping[str, Any], config_iv.check(self.config))
        self.api_client = VASTAPIClient(
            VASTAPIClientArgs(
                endpoint=self.config["vast_endpoint"],
                username=self.config["vast_username"],
                password=self.config["vast_password"],
                api_version=self.config["vast_api_version"],
                cluster_info_cache_ttl=self.config["vast_cluster_info_cache_ttl"],
                ssl_context=self.config.get("vast_verify_ssl", False),
                force_login=self.config["vast_force_login"],
            )
        )
        self._storage_base_dir = Path(self.config["vast_storage_base_dir"])

    @override
    async def shutdown(self) -> None:
        await self.api_client.aclose()

    @override
    async def create_quota_model(self) -> VASTQuotaModel:
        return VASTQuotaModel(self.mount_path, self.api_client, self._storage_base_dir)

    @override
    async def get_capabilities(self) -> frozenset[StorageBackendCapability]:
        return frozenset([
            StorageBackendCapability.VFOLDER,
            StorageBackendCapability.METRIC,
            StorageBackendCapability.QUOTA,
            StorageBackendCapability.FAST_FS_SIZE,
            StorageBackendCapability.FAST_SIZE,
        ])

    async def _get_cluster_info(self) -> VASTClusterInfo | None:
        """Returns None when the VAST API reports an unknown error."""
        cluster_id: int = self.config["vast_cluster_id"]
        await self.api_client.login()
        try:
            cluster_info = await self.api_client.get_cluster_info(cluster_id)
        except VASTUnknownError:
            return None
        if cluster_info is None:
            raise StorageProxyError(f"vast cluster not found. (id: {cluster_id})")
        return cluster_info

    @override
    async def get_hwinfo(self) -> HardwareMetadata:
        cluster_info = await self._get_cluster_info()
        if cluster_info is None:
            return {
                "status": "unavailable",
                "status_info": None,
                "metadata": {},
            }
        healthy_status: Literal["healthy", "degraded", "unavailable"] = "unavailable"
        match cluster_info.state.lower():
            case "online" | "healthy":
                healthy_status = "healthy"
            case "init":
                healthy_status = "degraded"
            case "unknown":
                healthy_status = "unavailable"
        quotas = await self.api_client.list_quotas()
        return {
            "status": healthy_status,
            "status_info": cluster_info.state,
            "metadata": {
                "quota": dump_json_str([q.model_dump(mode="json") for q in quotas]),
                "cluster_info": dump_json_str(cluster_info.model_dump(mode="json")),
            },
        }

    @override
    async def get_performance_metric(self) -> FSPerfMetric:
        cluster_info = await self._get_cluster_info()
        if cluster_info is None:
            return FSPerfMetric(
                iops_read=-1,
                iops_write=-1,
                io_bytes_read=-1,
                io_bytes_write=-1,
                io_usec_read=-1,
                io_usec_write=-1,
            )
        return FSPerfMetric(
            iops_read=cluster_info.rd_iops,
            iops_write=cluster_info.wr_iops,
            io_usec_read=cluster_info.rd_latency,
            io_usec_write=cluster_info.wr_latency,
            io_bytes_read=cluster_info.rd_bw,
            io_bytes_write=cluster_info.wr_bw,
        )

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        cluster_info = await self._get_cluster_info()
        if cluster_info is None:
            return CapacityUsage(
                used_bytes=-1,
                capacity_bytes=-1,
            )
        return CapacityUsage(
            used_bytes=cluster_info.physical_space_in_use,
            capacity_bytes=cluster_info.physical_space,
        )
