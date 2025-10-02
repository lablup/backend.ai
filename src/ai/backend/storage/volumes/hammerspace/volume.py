from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Mapping,
    Optional,
    override,
)
from uuid import UUID

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
from .client import HammerspaceAPIClient
from .errors import (
    HammerspaceConfigError,
    HammerspaceObjectiveNotFound,
)
from .request import CreateShareParams
from .schema.objective import Objective
from .types import ConnectionInfo, SSLConfig


class HammerspaceQuotaModelCreator:
    _client: HammerspaceAPIClient

    def __init__(self, objective_id: UUID, connection_info: ConnectionInfo) -> None:
        self._objective_id = objective_id
        self._client = HammerspaceAPIClient(connection_info)

    async def create_quota_model(self) -> HammerspaceQuotaModel:
        objective = await self._client.get_objective(self._objective_id)
        if objective is None:
            raise HammerspaceObjectiveNotFound(
                f"No Hammerspace Objective found with ID {self._objective_id}."
            )
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

        await self._client.create_share(
            CreateShareParams(
                name=name,
                path=str(qspath),
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
        if address is None:
            raise HammerspaceConfigError("Hammerspace volume requires 'address' in options")
        username = self.config.get("username")
        if username is None:
            raise HammerspaceConfigError("Hammerspace volume requires 'username' in options")
        password = self.config.get("password")
        if password is None:
            raise HammerspaceConfigError("Hammerspace volume requires 'password' in options")
        objective_id = self.config.get("objective_id")
        if objective_id is None:
            raise HammerspaceConfigError("Hammerspace volume requires 'objective_id' in options")
        self._objective_id = UUID(objective_id)

        ssl_enabled = self.config.get("ssl_enabled", False)
        raw_ssl_config = self.config.get("ssl_config", None)
        ssl_config: Optional[SSLConfig] = None
        if raw_ssl_config is not None:
            ssl_config = SSLConfig(
                cert_file=raw_ssl_config.get("cert_file"),
                key_file=raw_ssl_config.get("key_file"),
            )
        self._connection_info = ConnectionInfo(
            address=address,
            username=username,
            password=password,
            ssl_enabled=ssl_enabled,
            ssl_config=ssl_config,
        )

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        creator = HammerspaceQuotaModelCreator(self._objective_id, self._connection_info)
        quota_model = await creator.create_quota_model()
        return quota_model
