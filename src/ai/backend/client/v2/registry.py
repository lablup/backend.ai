from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from ai.backend.client.config import get_config as get_v1_config

from .auth import AuthStrategy, HMACAuth
from .base_client import BackendAIAnonymousClient, BackendAIAuthClient
from .config import ClientConfig

if TYPE_CHECKING:
    from .domains.acl import ACLClient
    from .domains.agent import AgentClient
    from .domains.artifact import ArtifactClient
    from .domains.artifact_registry import ArtifactRegistryClient
    from .domains.auth import AuthClient
    from .domains.auto_scaling_rule import AutoScalingRuleClient
    from .domains.compute_session import ComputeSessionClient
    from .domains.config import ConfigClient
    from .domains.container_registry import ContainerRegistryClient
    from .domains.deployment import DeploymentClient
    from .domains.domain import DomainClient
    from .domains.error_log import ErrorLogClient
    from .domains.event_stream import EventStreamClient
    from .domains.export import ExportClient
    from .domains.fair_share import FairShareClient
    from .domains.group import GroupClient
    from .domains.image import ImageClient
    from .domains.infra import InfraClient
    from .domains.model_serving import ModelServingClient
    from .domains.notification import NotificationClient
    from .domains.object_storage import ObjectStorageClient
    from .domains.operations import OperationsClient
    from .domains.quota_scope import QuotaScopeClient
    from .domains.rbac import RBACClient
    from .domains.resource_policy import ResourcePolicyClient
    from .domains.scaling_group import ScalingGroupClient
    from .domains.scheduling_history import SchedulingHistoryClient
    from .domains.session import SessionClient
    from .domains.storage import StorageClient
    from .domains.streaming import StreamingClient
    from .domains.system import SystemClient
    from .domains.template import TemplateClient
    from .domains.user import UserClient
    from .domains.vfolder import VFolderClient


class BackendAIClientRegistry:
    _client: BackendAIAuthClient
    _anon_client: BackendAIAnonymousClient

    def __init__(
        self,
        client: BackendAIAuthClient,
        anon_client: BackendAIAnonymousClient,
    ) -> None:
        self._client = client
        self._anon_client = anon_client

    @classmethod
    async def create(
        cls,
        config: ClientConfig,
        auth: AuthStrategy,
    ) -> BackendAIClientRegistry:
        client = await BackendAIAuthClient.create(config, auth)
        anon_client = await BackendAIAnonymousClient.create(config)
        return cls(client, anon_client)

    @classmethod
    async def from_v1_config(cls) -> BackendAIClientRegistry:
        """Create a registry from the V1 SDK API configuration."""
        api_config = get_v1_config()
        v2_config = ClientConfig(
            endpoint=api_config.endpoint,
            skip_ssl_verification=api_config.skip_sslcert_validation,
            connection_timeout=api_config.connection_timeout,
            read_timeout=api_config.read_timeout,
        )
        auth = HMACAuth(api_config.access_key, api_config.secret_key)
        return await cls.create(v2_config, auth)

    async def close(self) -> None:
        await self._client.close()
        await self._anon_client.close()

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

        return AuthClient(self._client, self._anon_client)

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
    def quota_scope(self) -> QuotaScopeClient:
        from .domains.quota_scope import QuotaScopeClient

        return QuotaScopeClient(self._client)

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
    def domain(self) -> DomainClient:
        from .domains.domain import DomainClient

        return DomainClient(self._client)

    @cached_property
    def error_log(self) -> ErrorLogClient:
        from .domains.error_log import ErrorLogClient

        return ErrorLogClient(self._client)

    @cached_property
    def event_stream(self) -> EventStreamClient:
        from .domains.event_stream import EventStreamClient

        return EventStreamClient(self._client)

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
    def image(self) -> ImageClient:
        from .domains.image import ImageClient

        return ImageClient(self._client)

    @cached_property
    def storage(self) -> StorageClient:
        from .domains.storage import StorageClient

        return StorageClient(self._client)

    @cached_property
    def object_storage(self) -> ObjectStorageClient:
        from .domains.object_storage import ObjectStorageClient

        return ObjectStorageClient(self._client)

    @cached_property
    def scaling_group(self) -> ScalingGroupClient:
        from .domains.scaling_group import ScalingGroupClient

        return ScalingGroupClient(self._client)

    @cached_property
    def scheduling_history(self) -> SchedulingHistoryClient:
        from .domains.scheduling_history import SchedulingHistoryClient

        return SchedulingHistoryClient(self._client)

    @cached_property
    def artifact(self) -> ArtifactClient:
        from .domains.artifact import ArtifactClient

        return ArtifactClient(self._client)

    @cached_property
    def artifact_registry(self) -> ArtifactRegistryClient:
        from .domains.artifact_registry import ArtifactRegistryClient

        return ArtifactRegistryClient(self._client)

    @cached_property
    def acl(self) -> ACLClient:
        from .domains.acl import ACLClient

        return ACLClient(self._client)

    @cached_property
    def agent(self) -> AgentClient:
        from .domains.agent import AgentClient

        return AgentClient(self._client)

    @cached_property
    def user(self) -> UserClient:
        from .domains.user import UserClient

        return UserClient(self._client)

    @cached_property
    def compute_session(self) -> ComputeSessionClient:
        from .domains.compute_session import ComputeSessionClient

        return ComputeSessionClient(self._client)

    @cached_property
    def system(self) -> SystemClient:
        from .domains.system import SystemClient

        return SystemClient(self._client)

    @cached_property
    def auto_scaling_rule(self) -> AutoScalingRuleClient:
        from .domains.auto_scaling_rule import AutoScalingRuleClient

        return AutoScalingRuleClient(self._client)
