"""V2 REST API client registry.

Provides ``V2ClientRegistry`` which lazy-loads domain clients that target
the ``/v2/`` REST endpoints (as opposed to ``BackendAIClientRegistry`` which
targets the v1 REST endpoints under ``/admin/`` etc.).
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .auth import AuthStrategy
from .base_client import BackendAIAuthClient
from .config import ClientConfig

if TYPE_CHECKING:
    from .domains_v2.agent import V2AgentClient
    from .domains_v2.app_config import V2AppConfigClient
    from .domains_v2.artifact import V2ArtifactClient
    from .domains_v2.artifact_registry import V2ArtifactRegistryClient
    from .domains_v2.audit_log import V2AuditLogClient
    from .domains_v2.container_registry import V2ContainerRegistryClient
    from .domains_v2.deployment import V2DeploymentClient
    from .domains_v2.domain import V2DomainClient
    from .domains_v2.export import V2ExportClient
    from .domains_v2.fair_share import V2FairShareClient
    from .domains_v2.gql import V2GQLClient
    from .domains_v2.huggingface_registry import V2HuggingFaceRegistryClient
    from .domains_v2.image import V2ImageClient
    from .domains_v2.keypair import V2KeypairClient
    from .domains_v2.login_history import V2LoginHistoryClient
    from .domains_v2.login_session import V2LoginSessionClient
    from .domains_v2.notification import V2NotificationClient
    from .domains_v2.object_storage import V2ObjectStorageClient
    from .domains_v2.project import V2ProjectClient
    from .domains_v2.prometheus_query_preset import V2PrometheusQueryPresetClient
    from .domains_v2.rbac import V2RBACClient
    from .domains_v2.reservoir_registry import V2ReservoirRegistryClient
    from .domains_v2.resource_allocation import V2ResourceAllocationClient
    from .domains_v2.resource_group import V2ResourceGroupClient
    from .domains_v2.resource_policy import V2ResourcePolicyClient
    from .domains_v2.resource_preset import V2ResourcePresetClient
    from .domains_v2.resource_slot import V2ResourceSlotClient
    from .domains_v2.resource_usage import V2ResourceUsageClient
    from .domains_v2.runtime_variant import V2RuntimeVariantClient
    from .domains_v2.runtime_variant_preset import V2RuntimeVariantPresetClient
    from .domains_v2.scheduling_history import V2SchedulingHistoryClient
    from .domains_v2.service_catalog import V2ServiceCatalogClient
    from .domains_v2.session import V2SessionClient
    from .domains_v2.storage_namespace import V2StorageNamespaceClient
    from .domains_v2.user import V2UserClient
    from .domains_v2.vfolder import V2VFolderClient
    from .domains_v2.vfs_storage import V2VFSStorageClient


class V2ClientRegistry:
    """Registry of domain clients targeting ``/v2/`` REST endpoints."""

    _client: BackendAIAuthClient

    def __init__(self, client: BackendAIAuthClient) -> None:
        self._client = client

    @classmethod
    async def create(
        cls,
        config: ClientConfig,
        auth: AuthStrategy,
    ) -> V2ClientRegistry:
        client = await BackendAIAuthClient.create(config, auth)
        return cls(client)

    async def close(self) -> None:
        await self._client.close()

    # ------------------------------------------------------------------ domains

    @cached_property
    def agent(self) -> V2AgentClient:
        from .domains_v2.agent import V2AgentClient

        return V2AgentClient(self._client)

    @cached_property
    def app_config(self) -> V2AppConfigClient:
        from .domains_v2.app_config import V2AppConfigClient

        return V2AppConfigClient(self._client)

    @cached_property
    def artifact(self) -> V2ArtifactClient:
        from .domains_v2.artifact import V2ArtifactClient

        return V2ArtifactClient(self._client)

    @cached_property
    def artifact_registry(self) -> V2ArtifactRegistryClient:
        from .domains_v2.artifact_registry import V2ArtifactRegistryClient

        return V2ArtifactRegistryClient(self._client)

    @cached_property
    def audit_log(self) -> V2AuditLogClient:
        from .domains_v2.audit_log import V2AuditLogClient

        return V2AuditLogClient(self._client)

    @cached_property
    def container_registry(self) -> V2ContainerRegistryClient:
        from .domains_v2.container_registry import V2ContainerRegistryClient

        return V2ContainerRegistryClient(self._client)

    @cached_property
    def deployment(self) -> V2DeploymentClient:
        from .domains_v2.deployment import V2DeploymentClient

        return V2DeploymentClient(self._client)

    @cached_property
    def domain(self) -> V2DomainClient:
        from .domains_v2.domain import V2DomainClient

        return V2DomainClient(self._client)

    @cached_property
    def export(self) -> V2ExportClient:
        from .domains_v2.export import V2ExportClient

        return V2ExportClient(self._client)

    @cached_property
    def fair_share(self) -> V2FairShareClient:
        from .domains_v2.fair_share import V2FairShareClient

        return V2FairShareClient(self._client)

    @cached_property
    def gql(self) -> V2GQLClient:
        from .domains_v2.gql import V2GQLClient

        return V2GQLClient(self._client)

    @cached_property
    def huggingface_registry(self) -> V2HuggingFaceRegistryClient:
        from .domains_v2.huggingface_registry import V2HuggingFaceRegistryClient

        return V2HuggingFaceRegistryClient(self._client)

    @cached_property
    def image(self) -> V2ImageClient:
        from .domains_v2.image import V2ImageClient

        return V2ImageClient(self._client)

    @cached_property
    def keypair(self) -> V2KeypairClient:
        from .domains_v2.keypair import V2KeypairClient

        return V2KeypairClient(self._client)

    @cached_property
    def login_history(self) -> V2LoginHistoryClient:
        from .domains_v2.login_history import V2LoginHistoryClient

        return V2LoginHistoryClient(self._client)

    @cached_property
    def login_session(self) -> V2LoginSessionClient:
        from .domains_v2.login_session import V2LoginSessionClient

        return V2LoginSessionClient(self._client)

    @cached_property
    def notification(self) -> V2NotificationClient:
        from .domains_v2.notification import V2NotificationClient

        return V2NotificationClient(self._client)

    @cached_property
    def object_storage(self) -> V2ObjectStorageClient:
        from .domains_v2.object_storage import V2ObjectStorageClient

        return V2ObjectStorageClient(self._client)

    @cached_property
    def project(self) -> V2ProjectClient:
        from .domains_v2.project import V2ProjectClient

        return V2ProjectClient(self._client)

    @cached_property
    def prometheus_query_preset(self) -> V2PrometheusQueryPresetClient:
        from .domains_v2.prometheus_query_preset import V2PrometheusQueryPresetClient

        return V2PrometheusQueryPresetClient(self._client)

    @cached_property
    def rbac(self) -> V2RBACClient:
        from .domains_v2.rbac import V2RBACClient

        return V2RBACClient(self._client)

    @cached_property
    def reservoir_registry(self) -> V2ReservoirRegistryClient:
        from .domains_v2.reservoir_registry import V2ReservoirRegistryClient

        return V2ReservoirRegistryClient(self._client)

    @cached_property
    def resource_allocation(self) -> V2ResourceAllocationClient:
        from .domains_v2.resource_allocation import V2ResourceAllocationClient

        return V2ResourceAllocationClient(self._client)

    @cached_property
    def resource_policy(self) -> V2ResourcePolicyClient:
        from .domains_v2.resource_policy import V2ResourcePolicyClient

        return V2ResourcePolicyClient(self._client)

    @cached_property
    def resource_group(self) -> V2ResourceGroupClient:
        from .domains_v2.resource_group import V2ResourceGroupClient

        return V2ResourceGroupClient(self._client)

    @cached_property
    def resource_preset(self) -> V2ResourcePresetClient:
        from .domains_v2.resource_preset import V2ResourcePresetClient

        return V2ResourcePresetClient(self._client)

    @cached_property
    def resource_slot(self) -> V2ResourceSlotClient:
        from .domains_v2.resource_slot import V2ResourceSlotClient

        return V2ResourceSlotClient(self._client)

    @cached_property
    def runtime_variant(self) -> V2RuntimeVariantClient:
        from .domains_v2.runtime_variant import V2RuntimeVariantClient

        return V2RuntimeVariantClient(self._client)

    @cached_property
    def runtime_variant_preset(self) -> V2RuntimeVariantPresetClient:
        from .domains_v2.runtime_variant_preset import V2RuntimeVariantPresetClient

        return V2RuntimeVariantPresetClient(self._client)

    @cached_property
    def resource_usage(self) -> V2ResourceUsageClient:
        from .domains_v2.resource_usage import V2ResourceUsageClient

        return V2ResourceUsageClient(self._client)

    @cached_property
    def scheduling_history(self) -> V2SchedulingHistoryClient:
        from .domains_v2.scheduling_history import V2SchedulingHistoryClient

        return V2SchedulingHistoryClient(self._client)

    @cached_property
    def service_catalog(self) -> V2ServiceCatalogClient:
        from .domains_v2.service_catalog import V2ServiceCatalogClient

        return V2ServiceCatalogClient(self._client)

    @cached_property
    def session(self) -> V2SessionClient:
        from .domains_v2.session import V2SessionClient

        return V2SessionClient(self._client)

    @cached_property
    def storage_namespace(self) -> V2StorageNamespaceClient:
        from .domains_v2.storage_namespace import V2StorageNamespaceClient

        return V2StorageNamespaceClient(self._client)

    @cached_property
    def user(self) -> V2UserClient:
        from .domains_v2.user import V2UserClient

        return V2UserClient(self._client)

    @cached_property
    def vfolder(self) -> V2VFolderClient:
        from .domains_v2.vfolder import V2VFolderClient

        return V2VFolderClient(self._client)

    @cached_property
    def vfs_storage(self) -> V2VFSStorageClient:
        from .domains_v2.vfs_storage import V2VFSStorageClient

        return V2VFSStorageClient(self._client)
