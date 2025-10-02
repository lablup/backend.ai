from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Mapping,
    Optional,
    override,
)

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import QuotaScopeID
from ai.backend.storage.watcher import WatcherClient

from ...types import (
    QuotaConfig,
)
from ..abc import (
    AbstractQuotaModel,
)
from ..vfs import BaseQuotaModel, BaseVolume
from .client import CreateShareParams, HammerspaceAPIClient
from .errors import (
    HammerspaceConfigError,
    HammerspaceVolumeNotFound,
)
from .schema import Objective
from .types import ConnectionInfo


class HammerspaceQuotaModelCreator:
    _client: HammerspaceAPIClient

    def __init__(self, mount_path: Path, connection_info: ConnectionInfo) -> None:
        self._mount_path = mount_path
        self._client = HammerspaceAPIClient(connection_info)

        self._objective: Optional[Objective] = None

    async def create_quota_model(self) -> HammerspaceQuotaModel:
        objective = await self._client.get_singleton_objectives()
        if objective is None:
            volume = await self._client.get_storage_volume(self._mount_path)
            if volume is None:
                raise HammerspaceVolumeNotFound(
                    f"No storage volume found for mount path: {self._mount_path}, "
                    "please create storage volume with the name matching the mount path.",
                )
            objective = await self._client.create_singleton_objective(volume)
        return HammerspaceQuotaModel(
            objective,
            self._client,
        )


class HammerspaceQuotaModel(BaseQuotaModel):
    _client: HammerspaceAPIClient

    def __init__(
        self,
        objective: Objective,
        client: HammerspaceAPIClient,
    ) -> None:
        self._objective = objective
        self._client = client

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        name = str(quota_scope_id)
        qspath = self.mangle_qspath(quota_scope_id)

        share = await self._client.create_share(
            CreateShareParams(
                name=name,
                path=str(qspath),
                create_path=True,
                validate_only=False,
            )
        )
        await self._client.set_objective_to_share(
            objective=self._objective,
            share=share,
        )

    @override
    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        pass


class HammerspaceVolume(BaseVolume):
    name: ClassVar[str] = "hammerspace"

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        watcher: Optional[WatcherClient] = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.local_config = local_config
        self.mount_path = mount_path
        self.config = options or {}
        self.etcd = etcd
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.watcher = watcher

        address = self.config.get("address")
        if address is None:
            raise HammerspaceConfigError("Hammerspace volume requires 'address' in options")
        username = self.config.get("username")
        if username is None:
            raise HammerspaceConfigError("Hammerspace volume requires 'username' in options")
        password = self.config.get("password")
        if password is None:
            raise HammerspaceConfigError("Hammerspace volume requires 'password' in options")
        self._connection_info = ConnectionInfo(
            address=address,
            username=username,
            password=password,
        )

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        creator = HammerspaceQuotaModelCreator(self.mount_path, self._connection_info)
        quota_model = await creator.create_quota_model()
        return quota_model
