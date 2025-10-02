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
from ai.backend.common.events.event_types.volume.broadcast import DoVolumeMountEvent
from ai.backend.common.types import QuotaConfig, QuotaScopeID
from ai.backend.storage.watcher import WatcherClient

from ...types import (
    QuotaUsage,
)
from ..abc import (
    AbstractQuotaModel,
)
from ..vfs import BaseQuotaModel, BaseVolume
from .client import HammerspaceAPIClient
from .errors import (
    HammerspaceAuthenticationError,
    HammerspaceConfigError,
)
from .request import CreateShareParams, GetShareParams
from .schema.share import Share
from .types import APIConnectionInfo, SSLConfig


class HammerspaceQuotaModelCreator:
    _client: HammerspaceAPIClient

    def __init__(
        self,
        connection_info: APIConnectionInfo,
        event_producer: EventProducer,
        mount_source: str,
        mount_target_path: Path,
    ) -> None:
        self._client = HammerspaceAPIClient(connection_info)
        self._event_producer = event_producer
        self._mount_source = mount_source
        self._mount_target_path = mount_target_path

    async def create_quota_model(self) -> HammerspaceQuotaModel:
        try:
            await self._client.try_login()
        except HammerspaceAuthenticationError as e:
            raise HammerspaceConfigError(
                "Failed to authenticate to Hammerspace. "
                f"Please check your user account. (username: {self._client._connection_info.username})"
            ) from e
        return HammerspaceQuotaModel(
            self._client,
            self._event_producer,
            self._mount_source,
            self._mount_target_path,
        )


class HammerspaceQuotaModel(BaseQuotaModel):
    _client: HammerspaceAPIClient
    _event_producer: EventProducer

    def __init__(
        self,
        client: HammerspaceAPIClient,
        event_producer: EventProducer,
        mount_source: str,
        mount_target_path: Path,
    ) -> None:
        self._client = client
        self._event_producer = event_producer
        self._mount_source = mount_source
        self._mount_target_path = mount_target_path

    def _get_share_name(self, quota_scope_id: QuotaScopeID) -> str:
        return str(quota_scope_id)

    def _get_share_path(self, quota_scope_id: QuotaScopeID) -> Path:
        return Path("/", quota_scope_id.pathname)

    def _get_mount_source(self, share: Share) -> str:
        return f"{self._mount_source}:{share.path}"

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        name = self._get_share_name(quota_scope_id)
        path = self._get_share_path(quota_scope_id)
        share_size_limit = options.limit_bytes if options is not None else None

        share = await self._client.create_share(
            CreateShareParams(
                name=name,
                path=path,
                share_size_limit=share_size_limit,
                create_path=True,
                validate_only=False,
            )
        )
        await self._event_producer.broadcast_event(
            DoVolumeMountEvent(
                dir_name=str(self._mount_target_path / path),
                volume_backend_name="hammerspace",
                fs_location=self._get_mount_source(share),
                quota_scope_id=quota_scope_id,
                edit_fstab=True,
            ),
            None,
        )

    @override
    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> Optional[QuotaUsage]:
        name = self._get_share_name(quota_scope_id)
        share = await self._client.get_share(GetShareParams(name=name))
        if share is None:
            return None
        return QuotaUsage(
            used_bytes=share.space.used,
            limit_bytes=share.space.total,
        )

    @override
    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        # Hammerspace does not support updating shares.
        # TODO: Raise not implemented error and handle it in Manager
        pass

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

        mount_source = self.config.get("mount_source")
        if mount_source is None:
            raise HammerspaceConfigError("Hammerspace volume requires 'mount_source' in options")
        self._mount_source = mount_source

        ssl_enabled = self.config.get("ssl_enabled", False)
        raw_ssl_config = self.config.get("ssl_config", None)
        ssl_config: Optional[SSLConfig] = None
        if raw_ssl_config is not None:
            ssl_config = SSLConfig(
                cert_file=raw_ssl_config.get("cert_file"),
                key_file=raw_ssl_config.get("key_file"),
            )
        self._connection_info = APIConnectionInfo(
            address=address,
            username=username,
            password=password,
            ssl_enabled=ssl_enabled,
            ssl_config=ssl_config,
        )

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        creator = HammerspaceQuotaModelCreator(
            self._connection_info,
            self.event_producer,
            self._mount_source,
            self.mount_path,
        )
        quota_model = await creator.create_quota_model()
        return quota_model
