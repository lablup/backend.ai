from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .auth import AuthStrategy
from .base_client import BackendAIClient
from .config import ClientConfig

if TYPE_CHECKING:
    from .domains.agent import AgentClient
    from .domains.artifact import ArtifactClient
    from .domains.auth import AuthClient
    from .domains.compute_session import ComputeSessionClient
    from .domains.config import ConfigClient
    from .domains.container_registry import ContainerRegistryClient
    from .domains.deployment import DeploymentClient
    from .domains.export import ExportClient
    from .domains.fair_share import FairShareClient
    from .domains.group import GroupClient
    from .domains.infra import InfraClient
    from .domains.model_serving import ModelServingClient
    from .domains.notification import NotificationClient
    from .domains.operations import OperationsClient
    from .domains.rbac import RBACClient
    from .domains.resource_policy import ResourcePolicyClient
    from .domains.scheduling_history import SchedulingHistoryClient
    from .domains.session import SessionClient
    from .domains.storage import StorageClient
    from .domains.streaming import StreamingClient
    from .domains.template import TemplateClient
    from .domains.vfolder import VFolderClient


class BackendAIClientRegistry:
    _client: BackendAIClient

    def __init__(self, client: BackendAIClient) -> None:
        self._client = client

    @classmethod
    async def create(
        cls,
        config: ClientConfig,
        auth: AuthStrategy,
    ) -> BackendAIClientRegistry:
        client = await BackendAIClient.create(config, auth)
        return cls(client)

    async def close(self) -> None:
        await self._client.close()

    @cached_property
    def session(self) -> SessionClient:
        from .domains.session import SessionClient

        return SessionClient(self._client)

    @cached_property
    def vfolder(self) -> VFolderClient:
        from .domains.vfolder import VFolderClient

        return VFolderClient(self._client)

    @cached_property
    def model_serving(self) -> ModelServingClient:
        from .domains.model_serving import ModelServingClient

        return ModelServingClient(self._client)

    @cached_property
    def auth(self) -> AuthClient:
        from .domains.auth import AuthClient

        return AuthClient(self._client)

    @cached_property
    def streaming(self) -> StreamingClient:
        from .domains.streaming import StreamingClient

        return StreamingClient(self._client)

    @cached_property
    def config(self) -> ConfigClient:
        from .domains.config import ConfigClient

        return ConfigClient(self._client)

    @cached_property
    def infra(self) -> InfraClient:
        from .domains.infra import InfraClient

        return InfraClient(self._client)

    @cached_property
    def template(self) -> TemplateClient:
        from .domains.template import TemplateClient

        return TemplateClient(self._client)

    @cached_property
    def operations(self) -> OperationsClient:
        from .domains.operations import OperationsClient

        return OperationsClient(self._client)

    @cached_property
    def fair_share(self) -> FairShareClient:
        from .domains.fair_share import FairShareClient

        return FairShareClient(self._client)

    @cached_property
    def rbac(self) -> RBACClient:
        from .domains.rbac import RBACClient

        return RBACClient(self._client)

    @cached_property
    def resource_policy(self) -> ResourcePolicyClient:
        from .domains.resource_policy import ResourcePolicyClient

        return ResourcePolicyClient(self._client)

    @cached_property
    def container_registry(self) -> ContainerRegistryClient:
        from .domains.container_registry import ContainerRegistryClient

        return ContainerRegistryClient(self._client)

    @cached_property
    def deployment(self) -> DeploymentClient:
        from .domains.deployment import DeploymentClient

        return DeploymentClient(self._client)

    @cached_property
    def export(self) -> ExportClient:
        from .domains.export import ExportClient

        return ExportClient(self._client)

    @cached_property
    def notification(self) -> NotificationClient:
        from .domains.notification import NotificationClient

        return NotificationClient(self._client)

    @cached_property
    def group(self) -> GroupClient:
        from .domains.group import GroupClient

        return GroupClient(self._client)

    @cached_property
    def storage(self) -> StorageClient:
        from .domains.storage import StorageClient

        return StorageClient(self._client)

    @cached_property
    def scheduling_history(self) -> SchedulingHistoryClient:
        from .domains.scheduling_history import SchedulingHistoryClient

        return SchedulingHistoryClient(self._client)

    @cached_property
    def artifact(self) -> ArtifactClient:
        from .domains.artifact import ArtifactClient

        return ArtifactClient(self._client)

    @cached_property
    def agent(self) -> AgentClient:
        from .domains.agent import AgentClient

        return AgentClient(self._client)

    @cached_property
    def compute_session(self) -> ComputeSessionClient:
        from .domains.compute_session import ComputeSessionClient

        return ComputeSessionClient(self._client)
