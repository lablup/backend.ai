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
from .types import ConnectionInfo


class HammerspaceQuotaModel(BaseQuotaModel):
    _client: HammerspaceAPIClient

    def __init__(self, mount_path: Path, connection_info: ConnectionInfo) -> None:
        self._mount_path = mount_path
        self._client = HammerspaceAPIClient(connection_info)

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        name = str(quota_scope_id)
        path = self._mount_path / name
        await self._client.create_share(
            CreateShareParams(
                name=name,
                path=str(path),
                create_path=True,
                validate_only=False,
            )
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
        if not address:
            raise ValueError("Hammerspace volume requires 'address' in options")
        self._connection_info = ConnectionInfo(
            address=address,
        )

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        return HammerspaceQuotaModel(self.mount_path, self._connection_info)
