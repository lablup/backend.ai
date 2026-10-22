import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, Final, override

import aiofiles
import aiofiles.os

from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.clients.storage_backends.exascaler.client import EXAScalerClient
from ai.backend.common.data.storage.types import StorageBackendCapability, StorageBackendType
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import QuotaScopeID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.errors import (
    QuotaScopeAlreadyExists,
    QuotaScopeNotFoundError,
)
from ai.backend.storage.types import QuotaConfig, QuotaUsage
from ai.backend.storage.volumes.abc import AbstractQuotaModel
from ai.backend.storage.volumes.vfs import BaseQuotaModel, BaseVolume
from ai.backend.storage.watcher import WatcherClient

FIRST_PROJECT_ID: Final = 100
PROJECT_MAIN_ID_KEY: Final = "ddn/main-project-id"
PROJECT_ID_FILE_NAME: Final = "project_id"

log = StructuredLogger(logging.getLogger(__spec__.name))


class EXAScalerQuotaModel(BaseQuotaModel):
    _client: EXAScalerClient
    etcd: AsyncEtcd

    def __init__(self, mount_path: Path, client: EXAScalerClient, etcd: AsyncEtcd) -> None:
        super().__init__(mount_path)
        self._client = client
        self.etcd = etcd

    async def _read_project_id(self, pid_file_path: str | Path) -> int | None:
        def _read() -> int | None:
            try:
                with Path(pid_file_path).open() as f:
                    return int(f.read())
            except FileNotFoundError:
                return None

        return await run_in_executor_with_context(None, _read)

    async def _write_project_id(self, pid: int, pid_file_path: str | Path) -> None:
        def _write() -> None:
            with Path(pid_file_path).open("w") as f:
                f.write(str(pid))

        await run_in_executor_with_context(None, _write)

    async def _read_main_project_id(self) -> int:
        raw_val = await self.etcd.get(PROJECT_MAIN_ID_KEY)
        if raw_val is None:
            val = int(FIRST_PROJECT_ID)
        else:
            val = int(raw_val)
        await self.etcd.put(PROJECT_MAIN_ID_KEY, str(val + 1))
        return val

    async def _get_quota_by_project(self, pid: int, qspath: Path) -> QuotaUsage | None:
        quota = await self._client.get_quota_by_project(pid, qspath)
        if quota is None:
            return None
        return QuotaUsage(used_bytes=quota.used_bytes, limit_bytes=quota.limit_bytes)

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        pid_path = qspath / PROJECT_ID_FILE_NAME
        try:
            await aiofiles.os.makedirs(qspath)
        except FileExistsError:
            pass
        project_id = await self._read_project_id(pid_path)
        if project_id is None:
            main_pid = await self._read_main_project_id()
            project_id = main_pid + 1
            await self._write_project_id(project_id, pid_path)
        else:
            quota_usage = await self._get_quota_by_project(project_id, qspath)
            if quota_usage is not None:
                raise QuotaScopeAlreadyExists

        await self._client.set_project_id(project_id, qspath)

        if options is not None:
            await self._client.set_quota_by_project(project_id, qspath, options.limit_bytes)

    @override
    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> QuotaUsage | None:
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            return None
        pid_path = qspath / PROJECT_ID_FILE_NAME
        if (pid := await self._read_project_id(pid_path)) is None:
            return None
        return await self._get_quota_by_project(pid, qspath)

    @override
    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        pid_path = qspath / PROJECT_ID_FILE_NAME
        pid = await self._read_project_id(pid_path)
        if pid is None:
            raise QuotaScopeNotFoundError
        await self._client.set_quota_by_project(pid, qspath, config.limit_bytes)

    @override
    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        pid_path = qspath / PROJECT_ID_FILE_NAME
        pid = await self._read_project_id(pid_path)
        if pid is None:
            raise QuotaScopeNotFoundError
        await self._client.unset_quota_by_project(pid, qspath)

    @override
    async def delete_quota_scope(self, quota_scope_id: QuotaScopeID) -> None:
        await self.unset_quota(quota_scope_id)
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.rmdir(qspath)


class EXAScalerFSVolume(BaseVolume):
    name: ClassVar[StorageBackendType] = StorageBackendType("exascaler")
    _client: EXAScalerClient

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
        self._client = EXAScalerClient()

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        return EXAScalerQuotaModel(self.mount_path, self._client, self.etcd)

    @override
    async def get_capabilities(self) -> frozenset[StorageBackendCapability]:
        return frozenset([StorageBackendCapability.VFOLDER, StorageBackendCapability.QUOTA])
