from __future__ import annotations

from functools import cached_property
from typing import Any, Self

from .auth import AuthStrategy
from .base_client import BackendAIClient
from .config import ClientConfig
from .domains.auth import AuthClient
from .domains.config import ConfigClient
from .domains.container_registry import ContainerRegistryClient
from .domains.infra import InfraClient
from .domains.model_serving import ModelServingClient
from .domains.operations import OperationsClient
from .domains.session import SessionClient
from .domains.storage import StorageClient
from .domains.streaming import StreamingClient
from .domains.template import TemplateClient
from .domains.vfolder import VFolderClient


class BackendAIClientRegistry:
    _client: BackendAIClient

    def __init__(self, config: ClientConfig, auth: AuthStrategy) -> None:
        self._client = BackendAIClient(config, auth)

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._client.__aexit__(*exc_info)

    @cached_property
    def session(self) -> SessionClient:
        return SessionClient(self._client)

    @cached_property
    def vfolder(self) -> VFolderClient:
        return VFolderClient(self._client)

    @cached_property
    def model_serving(self) -> ModelServingClient:
        return ModelServingClient(self._client)

    @cached_property
    def auth(self) -> AuthClient:
        return AuthClient(self._client)

    @cached_property
    def streaming(self) -> StreamingClient:
        return StreamingClient(self._client)

    @cached_property
    def config(self) -> ConfigClient:
        return ConfigClient(self._client)

    @cached_property
    def infra(self) -> InfraClient:
        return InfraClient(self._client)

    @cached_property
    def template(self) -> TemplateClient:
        return TemplateClient(self._client)

    @cached_property
    def operations(self) -> OperationsClient:
        return OperationsClient(self._client)

    @cached_property
    def container_registry(self) -> ContainerRegistryClient:
        return ContainerRegistryClient(self._client)

    @cached_property
    def storage(self) -> StorageClient:
        return StorageClient(self._client)
