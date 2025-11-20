from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Optional

from aiohttp import web

from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.storage.services.artifacts.types import ImportStepContext

if TYPE_CHECKING:
    from .api.types import CORSOptions, WebMiddleware
    from .volumes.abc import AbstractVolume


class AbstractStoragePlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    def get_volume_class(
        self,
    ) -> type[AbstractVolume]:
        raise NotImplementedError


@dataclass
class VerifierPluginResult:
    scanned_count: int
    infected_count: int
    metadata: dict[str, Any]


class AbstractArtifactVerifierPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    async def verify(self, artifact_path: Path, context: ImportStepContext) -> VerifierPluginResult:
        raise NotImplementedError


class StoragePluginContext(BasePluginContext[AbstractStoragePlugin]):
    plugin_group = "backendai_storage_v10"

    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        allowlist: Optional[set[str]] = None,
        blocklist: Optional[set[str]] = None,
    ) -> Iterator[tuple[str, type[AbstractStoragePlugin]]]:
        scanned_plugins = [*super().discover_plugins(plugin_group, allowlist, blocklist)]
        yield from scanned_plugins


class StorageArtifactVerifierPluginContext(BasePluginContext[AbstractArtifactVerifierPlugin]):
    plugin_group = "backendai_storage_artifact_verifier_v1"

    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        allowlist: Optional[set[str]] = None,
        blocklist: Optional[set[str]] = None,
    ) -> Iterator[tuple[str, type[AbstractArtifactVerifierPlugin]]]:
        scanned_plugins = [*super().discover_plugins(plugin_group, allowlist, blocklist)]
        yield from scanned_plugins


class StorageManagerWebappPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, list[WebMiddleware]]:
        raise NotImplementedError


class StorageManagerWebappPluginContext(BasePluginContext[StorageManagerWebappPlugin]):
    plugin_group = "backendai_storage_manager_webapp_v10"


class StorageClientWebappPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, list[WebMiddleware]]:
        raise NotImplementedError


class StorageClientWebappPluginContext(BasePluginContext[StorageClientWebappPlugin]):
    plugin_group = "backendai_storage_client_webapp_v10"
