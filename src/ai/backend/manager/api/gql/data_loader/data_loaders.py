from __future__ import annotations

import uuid
from functools import cached_property
from typing import TYPE_CHECKING

from strawberry.dataloader import DataLoader

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.data.entity.app_config_allow_list import (
    AppConfigAllowListEntityType,
    AppConfigAllowListID,
)
from ai.backend.common.data.entity.app_config_definition import (
    AppConfigDefinitionEntityType,
    AppConfigDefinitionID,
)
from ai.backend.common.data.entity.app_config_fragment import (
    AppConfigFragmentEntityType,
    AppConfigFragmentID,
)
from ai.backend.common.data.entity.artifact_registry import (
    ArtifactRegistryEntityType,
    ArtifactRegistryID,
)
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.deployment import DeploymentEntityType, DeploymentID
from ai.backend.common.data.entity.deployment_history import DeploymentHistoryID
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType, IdleCheckerID
from ai.backend.common.data.entity.image import ImageEntityType, ImageID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.notification import (
    NotificationChannelEntityType,
    NotificationChannelID,
    NotificationRuleEntityType,
    NotificationRuleID,
)
from ai.backend.common.data.entity.object_storage import ObjectStorageEntityType, ObjectStorageID
from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType, ResourceGroupID
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.route_history import RouteHistoryID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType, RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import (
    RuntimeVariantPresetEntityType,
    RuntimeVariantPresetID,
)
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.common.data.entity.storage_namespace import (
    StorageNamespaceEntityType,
    StorageNamespaceID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.entity.vfs_storage import VFSStorageEntityType, VFSStorageID
from ai.backend.common.types import AgentId
from ai.backend.manager.data.permission.id import ObjectId

if TYPE_CHECKING:
    from ai.backend.common.dto.manager.v2.rbac.response import EntityNode  # pants: no-infer-dep
    from ai.backend.manager.api.adapters.registry import Adapters  # pants: no-infer-dep
    from ai.backend.manager.api.gql.agent.types import AgentV2GQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.app_config_allow_list.types import (  # pants: no-infer-dep
        AppConfigAllowListGQL,
    )
    from ai.backend.manager.api.gql.app_config_definition.types import (  # pants: no-infer-dep
        AppConfigDefinitionGQL,
    )
    from ai.backend.manager.api.gql.app_config_fragment.types import (  # pants: no-infer-dep
        AppConfigFragmentGQL,
    )
    from ai.backend.manager.api.gql.artifact.types import (  # pants: no-infer-dep
        ArtifactRevision,
    )
    from ai.backend.manager.api.gql.artifact_registry import ArtifactRegistry  # pants: no-infer-dep
    from ai.backend.manager.api.gql.audit_log.types.node import (  # pants: no-infer-dep
        AuditLogV2GQL,
    )
    from ai.backend.manager.api.gql.container_registry.types import (  # pants: no-infer-dep
        ContainerRegistryGQL,
    )
    from ai.backend.manager.api.gql.deployment.types.access_token import (  # pants: no-infer-dep
        AccessToken,
    )
    from ai.backend.manager.api.gql.deployment.types.auto_scaling import (  # pants: no-infer-dep
        AutoScalingRule,
    )
    from ai.backend.manager.api.gql.deployment.types.deployment import (  # pants: no-infer-dep
        ModelDeployment,
    )
    from ai.backend.manager.api.gql.deployment.types.policy import (  # pants: no-infer-dep
        DeploymentPolicyGQL,
    )
    from ai.backend.manager.api.gql.deployment.types.replica import (  # pants: no-infer-dep
        ModelReplica,
    )
    from ai.backend.manager.api.gql.deployment.types.revision import (  # pants: no-infer-dep
        ModelRevision,
    )
    from ai.backend.manager.api.gql.deployment.types.revision_preset import (  # pants: no-infer-dep
        DeploymentRevisionPresetGQL,
    )
    from ai.backend.manager.api.gql.deployment.types.route import Route  # pants: no-infer-dep
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.huggingface_registry import (  # pants: no-infer-dep
        HuggingFaceRegistry,
    )
    from ai.backend.manager.api.gql.idle_checker.types import IdleCheckerGQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.image.types import (  # pants: no-infer-dep
        ImageV2AliasGQL,
        ImageV2GQL,
    )
    from ai.backend.manager.api.gql.kernel.types import (  # pants: no-infer-dep
        KernelV2GQL,
        ResourceAllocationGQL,
    )
    from ai.backend.manager.api.gql.notification.types import (  # pants: no-infer-dep
        NotificationChannel,
        NotificationRule,
    )
    from ai.backend.manager.api.gql.object_storage import ObjectStorage  # pants: no-infer-dep
    from ai.backend.manager.api.gql.project_v2.types.node import (  # pants: no-infer-dep
        ProjectV2GQL,
    )
    from ai.backend.manager.api.gql.prometheus_query_preset.types.category import (  # pants: no-infer-dep
        CategoryGQL,
    )
    from ai.backend.manager.api.gql.prometheus_query_preset.types.node import (  # pants: no-infer-dep
        QueryDefinitionGQL,
    )
    from ai.backend.manager.api.gql.rbac.types.entity import EntityRefGQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.rbac.types.entity_node import (  # pants: no-infer-dep
        EntityNode as EntityNodeGQL,
    )
    from ai.backend.manager.api.gql.rbac.types.permission import (  # pants: no-infer-dep
        PermissionGQL,
    )
    from ai.backend.manager.api.gql.rbac.types.role import (  # pants: no-infer-dep
        RoleAssignmentGQL,
        RoleGQL,
    )
    from ai.backend.manager.api.gql.reservoir_registry import (  # pants: no-infer-dep
        ReservoirRegistry,
    )
    from ai.backend.manager.api.gql.resource_group.types import (  # pants: no-infer-dep
        ResourceGroupGQL,
    )
    from ai.backend.manager.api.gql.runtime_variant.types import (  # pants: no-infer-dep
        RuntimeVariantGQL,
    )
    from ai.backend.manager.api.gql.runtime_variant_preset.types import (  # pants: no-infer-dep
        RuntimeVariantPresetGQL,
    )
    from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
        DeploymentHistory,
        KernelSchedulingHistoryGQL,
        RouteHistory,
        SessionSchedulingHistory,
    )
    from ai.backend.manager.api.gql.session.types import SessionV2GQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.storage_namespace import (  # pants: no-infer-dep
        StorageNamespace,
    )
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.vfolder_v2.types.node import (  # pants: no-infer-dep
        VFolderGQL,
    )
    from ai.backend.manager.api.gql.vfs_storage import VFSStorage  # pants: no-infer-dep


class DataLoaders:
    """
    Manages domain-specific DataLoader instances for GraphQL resolvers.

    This class is the central registry for all DataLoaders used in the GraphQL API.
    Each domain (notification, model_deployment, model_replica, etc.) will have
    its own loader instances initialized here.
    """

    _adapters: Adapters

    def __init__(self, adapters: Adapters) -> None:
        self._adapters = adapters

    @cached_property
    def app_config_allow_list_loader(
        self,
    ) -> DataLoader[AppConfigAllowListID, AppConfigAllowListGQL | None]:
        adapter = self._adapters.app_config_allow_list

        async def load_fn(
            ids: list[AppConfigAllowListID],
        ) -> list[AppConfigAllowListGQL | Exception | None]:
            from ai.backend.manager.api.gql.app_config_allow_list.types import (  # pants: no-infer-dep
                AppConfigAllowListGQL as ACL,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else ACL.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def app_config_definition_loader(
        self,
    ) -> DataLoader[AppConfigDefinitionID, AppConfigDefinitionGQL | None]:
        adapter = self._adapters.app_config_definition

        async def load_fn(
            ids: list[AppConfigDefinitionID],
        ) -> list[AppConfigDefinitionGQL | Exception | None]:
            from ai.backend.manager.api.gql.app_config_definition.types import (  # pants: no-infer-dep
                AppConfigDefinitionGQL as ACD,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else ACD.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def app_config_fragment_loader(
        self,
    ) -> DataLoader[AppConfigFragmentID, AppConfigFragmentGQL | None]:
        adapter = self._adapters.app_config_fragment

        async def load_fn(
            ids: list[AppConfigFragmentID],
        ) -> list[AppConfigFragmentGQL | Exception | None]:
            from ai.backend.manager.api.gql.app_config_fragment.types import (  # pants: no-infer-dep
                AppConfigFragmentGQL as ACF,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else ACF.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def idle_checker_loader(
        self,
    ) -> DataLoader[IdleCheckerID, IdleCheckerGQL | None]:
        adapter = self._adapters.idle_checker

        async def load_fn(ids: list[IdleCheckerID]) -> list[IdleCheckerGQL | None]:
            from ai.backend.manager.api.gql.idle_checker.types import (  # pants: no-infer-dep
                IdleCheckerGQL as IC,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [IC.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def audit_log_loader(
        self,
    ) -> DataLoader[AuditLogID, AuditLogV2GQL | None]:
        adapter = self._adapters.audit_log

        async def load_fn(ids: list[AuditLogID]) -> list[AuditLogV2GQL | None]:
            from ai.backend.manager.api.gql.audit_log.types.node import (  # pants: no-infer-dep
                AuditLogV2GQL as AL,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [AL.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def resource_group_loader(
        self,
    ) -> DataLoader[str, ResourceGroupGQL | None]:
        adapter = self._adapters.resource_group

        async def load_fn(names: list[str]) -> list[ResourceGroupGQL | Exception | None]:
            from ai.backend.manager.api.gql.resource_group.types import (  # pants: no-infer-dep
                ResourceGroupGQL as RG,
            )

            dtos = await adapter.batch_load_by_names(names)
            return [
                dto if dto is None or isinstance(dto, Exception) else RG.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def resource_group_by_id_loader(
        self,
    ) -> DataLoader[ResourceGroupID, ResourceGroupGQL | None]:
        adapter = self._adapters.resource_group

        async def load_fn(ids: list[ResourceGroupID]) -> list[ResourceGroupGQL | Exception | None]:
            from ai.backend.manager.api.gql.resource_group.types import (  # pants: no-infer-dep
                ResourceGroupGQL as RG,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else RG.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def vfolder_loader(
        self,
    ) -> DataLoader[VFolderUUID, VFolderGQL | None]:
        adapter = self._adapters.vfolder

        async def load_fn(ids: list[VFolderUUID]) -> list[VFolderGQL | None]:
            from ai.backend.manager.api.gql.vfolder_v2.types.node import (  # pants: no-infer-dep
                VFolderGQL as VF,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [VF.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def notification_channel_loader(
        self,
    ) -> DataLoader[NotificationChannelID, NotificationChannel | None]:
        adapter = self._adapters.notification

        async def load_fn(
            ids: list[NotificationChannelID],
        ) -> list[NotificationChannel | Exception | None]:
            from ai.backend.manager.api.gql.notification.types import (  # pants: no-infer-dep
                NotificationChannel as NC,
            )

            dtos = await adapter.batch_load_channels_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else NC.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def notification_rule_loader(
        self,
    ) -> DataLoader[NotificationRuleID, NotificationRule | None]:
        adapter = self._adapters.notification

        async def load_fn(
            ids: list[NotificationRuleID],
        ) -> list[NotificationRule | Exception | None]:
            from ai.backend.manager.api.gql.notification.types import (  # pants: no-infer-dep
                NotificationRule as NR,
            )

            dtos = await adapter.batch_load_rules_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else NR.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def artifact_registry_loader(
        self,
    ) -> DataLoader[ArtifactRegistryID, ArtifactRegistry | None]:
        adapter = self._adapters.artifact_registry

        async def load_fn(ids: list[ArtifactRegistryID]) -> list[ArtifactRegistry | None]:
            from strawberry import ID  # pants: no-infer-dep

            from ai.backend.manager.api.gql.artifact_registry import (  # pants: no-infer-dep
                ArtifactRegistry as AR,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                AR(
                    id=ID(str(dto.id)),
                    registry_id=ID(str(dto.registry_id)),
                    name=dto.name,
                    type=dto.type,
                )
                if dto is not None
                else None
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def container_registry_loader(
        self,
    ) -> DataLoader[ContainerRegistryID, ContainerRegistryGQL | None]:
        adapter = self._adapters.container_registry

        async def load_fn(ids: list[ContainerRegistryID]) -> list[ContainerRegistryGQL | None]:
            from ai.backend.manager.api.gql.container_registry.types import (  # pants: no-infer-dep
                ContainerRegistryGQL as CR,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [CR.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def huggingface_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, HuggingFaceRegistry | None]:
        adapter = self._adapters.huggingface_registry

        async def load_fn(ids: list[uuid.UUID]) -> list[HuggingFaceRegistry | None]:
            from ai.backend.manager.api.gql.huggingface_registry import (  # pants: no-infer-dep
                HuggingFaceRegistry as HF,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [HF.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def reservoir_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, ReservoirRegistry | None]:
        adapter = self._adapters.reservoir_registry

        async def load_fn(ids: list[uuid.UUID]) -> list[ReservoirRegistry | None]:
            from ai.backend.manager.api.gql.reservoir_registry import (  # pants: no-infer-dep
                ReservoirRegistry as RR,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [RR.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def storage_namespace_loader(
        self,
    ) -> DataLoader[StorageNamespaceID, StorageNamespace | None]:
        adapter = self._adapters.storage_namespace

        async def load_fn(
            ids: list[StorageNamespaceID],
        ) -> list[StorageNamespace | Exception | None]:
            from ai.backend.manager.api.gql.storage_namespace import (  # pants: no-infer-dep
                StorageNamespace as SN,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else SN.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def object_storage_loader(
        self,
    ) -> DataLoader[ObjectStorageID, ObjectStorage | None]:
        adapter = self._adapters.object_storage

        async def load_fn(ids: list[ObjectStorageID]) -> list[ObjectStorage | Exception | None]:
            from ai.backend.manager.api.gql.object_storage import (  # pants: no-infer-dep
                ObjectStorage as OS,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else OS.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def vfs_storage_loader(
        self,
    ) -> DataLoader[VFSStorageID, VFSStorage | None]:
        adapter = self._adapters.vfs_storage

        async def load_fn(ids: list[VFSStorageID]) -> list[VFSStorage | None]:
            from ai.backend.manager.api.gql.vfs_storage import (  # pants: no-infer-dep
                VFSStorage as VS,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [VS.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def artifact_revision_loader(
        self,
    ) -> DataLoader[ArtifactRevisionID, ArtifactRevision | None]:
        adapter = self._adapters.artifact

        async def load_fn(
            ids: list[ArtifactRevisionID],
        ) -> list[ArtifactRevision | Exception | None]:
            from ai.backend.manager.api.gql.artifact.types import (  # pants: no-infer-dep
                ArtifactRevision as ARev,
            )

            dtos = await adapter.batch_load_revisions_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else ARev.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def route_loader(
        self,
    ) -> DataLoader[uuid.UUID, Route | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[uuid.UUID]) -> list[Route | Exception | None]:
            from ai.backend.manager.api.gql.deployment.types.route import (  # pants: no-infer-dep
                Route as R,
            )

            dtos = await adapter.batch_load_routes_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else R.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def deployment_loader(
        self,
    ) -> DataLoader[DeploymentID, ModelDeployment | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[DeploymentID]) -> list[ModelDeployment | None]:
            from ai.backend.manager.api.gql.deployment.types.deployment import (  # pants: no-infer-dep
                ModelDeployment as MD,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [MD.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def revision_loader(
        self,
    ) -> DataLoader[DeploymentRevisionID, ModelRevision | None]:
        adapter = self._adapters.deployment

        async def load_fn(
            ids: list[DeploymentRevisionID],
        ) -> list[ModelRevision | Exception | None]:
            from ai.backend.manager.api.gql.deployment.types.revision import (  # pants: no-infer-dep
                ModelRevision as MRev,
            )

            dtos = await adapter.batch_load_revisions_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else MRev.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def revision_preset_loader(
        self,
    ) -> DataLoader[DeploymentPresetID, DeploymentRevisionPresetGQL | None]:
        adapter = self._adapters.deployment_revision_preset

        async def load_fn(
            ids: list[DeploymentPresetID],
        ) -> list[DeploymentRevisionPresetGQL | None]:
            from ai.backend.common.dto.manager.query import UUIDFilter
            from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (  # pants: no-infer-dep
                DeploymentRevisionPresetFilter,
                SearchDeploymentRevisionPresetsInput,
            )
            from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (  # pants: no-infer-dep
                DeploymentRevisionPresetNode,
            )
            from ai.backend.manager.api.gql.deployment.types.revision_preset import (  # pants: no-infer-dep
                DeploymentRevisionPresetGQL as DRP,
            )

            payload = await adapter.search(
                SearchDeploymentRevisionPresetsInput(
                    filter=DeploymentRevisionPresetFilter(id=UUIDFilter(in_=list(ids))),
                    limit=len(ids),
                )
            )
            node_map: dict[DeploymentPresetID, DeploymentRevisionPresetNode] = {
                DeploymentPresetID(item.id): item for item in payload.items
            }
            return [DRP.from_pydantic(node) if (node := node_map.get(pid)) else None for pid in ids]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def replica_loader(
        self,
    ) -> DataLoader[ReplicaID, ModelReplica | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[ReplicaID]) -> list[ModelReplica | Exception | None]:
            from ai.backend.manager.api.gql.deployment.types.replica import (  # pants: no-infer-dep
                ModelReplica as MRep,
            )

            dtos = await adapter.batch_load_replicas_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else MRep.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def container_count_loader(
        self,
    ) -> DataLoader[AgentId, int]:
        adapter = self._adapters.agent

        async def load_fn(agent_ids: list[AgentId]) -> list[int | Exception]:
            return await adapter.batch_load_container_counts(agent_ids)

        return DataLoader(load_fn=load_fn)

    @cached_property
    def image_loader(
        self,
    ) -> DataLoader[ImageID, ImageV2GQL | None]:
        adapter = self._adapters.image

        async def load_fn(image_ids: list[ImageID]) -> list[ImageV2GQL | None]:
            from ai.backend.manager.api.gql.image.types import (  # pants: no-infer-dep
                ImageV2GQL as IG,
            )

            dtos = await adapter.batch_load_by_ids(image_ids)
            return [IG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def kernel_loader(
        self,
    ) -> DataLoader[KernelID, KernelV2GQL | None]:
        adapter = self._adapters.session

        async def load_fn(kernel_ids: list[KernelID]) -> list[KernelV2GQL | None]:
            from ai.backend.manager.api.gql.kernel.types import (  # pants: no-infer-dep
                KernelV2GQL as KG,
            )

            dtos = await adapter.batch_load_kernels_by_ids(kernel_ids)
            return [KG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def session_loader(
        self,
    ) -> DataLoader[SessionID, SessionV2GQL | None]:
        adapter = self._adapters.session

        async def load_fn(session_ids: list[SessionID]) -> list[SessionV2GQL | None]:
            from ai.backend.manager.api.gql.session.types import (  # pants: no-infer-dep
                SessionV2GQL as SG,
            )

            dtos = await adapter.batch_load_by_ids(session_ids)
            return [SG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def session_resource_allocation_loader(
        self,
    ) -> DataLoader[SessionID, ResourceAllocationGQL]:
        adapter = self._adapters.session

        async def load_fn(session_ids: list[SessionID]) -> list[ResourceAllocationGQL]:
            from ai.backend.manager.api.gql.kernel.types import (  # pants: no-infer-dep
                ResourceAllocationGQL as RA,
            )

            dtos = await adapter.batch_resource_allocation_by_session(session_ids)
            return [RA.from_pydantic(dto) for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def kernel_resource_allocation_loader(
        self,
    ) -> DataLoader[KernelID, ResourceAllocationGQL]:
        adapter = self._adapters.session

        async def load_fn(kernel_ids: list[KernelID]) -> list[ResourceAllocationGQL]:
            from ai.backend.manager.api.gql.kernel.types import (  # pants: no-infer-dep
                ResourceAllocationGQL as RA,
            )

            dtos = await adapter.batch_resource_allocation_by_kernel(kernel_ids)
            return [RA.from_pydantic(dto) for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def image_alias_loader(
        self,
    ) -> DataLoader[ImageAliasID, ImageV2AliasGQL | None]:
        """Load a single alias by its own ID (ImageAliasRow.id)."""
        adapter = self._adapters.image

        async def load_fn(ids: list[ImageAliasID]) -> list[ImageV2AliasGQL | None]:
            from ai.backend.manager.api.gql.image.types import (  # pants: no-infer-dep
                ImageV2AliasGQL as IAG,
            )

            dtos = await adapter.batch_load_aliases_by_ids(ids)
            return [IAG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def user_loader(
        self,
    ) -> DataLoader[UserID, UserV2GQL | None]:
        adapter = self._adapters.user

        async def load_fn(ids: list[UserID]) -> list[UserV2GQL | None]:
            from ai.backend.manager.api.gql.user.types.node import (  # pants: no-infer-dep
                UserV2GQL as U,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [U.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def domain_loader(
        self,
    ) -> DataLoader[str, DomainV2GQL | None]:
        adapter = self._adapters.domain

        async def load_fn(names: list[str]) -> list[DomainV2GQL | Exception | None]:
            from ai.backend.manager.api.gql.domain_v2.types.node import (  # pants: no-infer-dep
                DomainV2GQL as D,
            )

            dtos = await adapter.batch_load_by_names(names)
            return [
                dto if dto is None or isinstance(dto, Exception) else D.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def domain_by_id_loader(
        self,
    ) -> DataLoader[DomainID, DomainV2GQL | None]:
        adapter = self._adapters.domain

        async def load_fn(ids: list[DomainID]) -> list[DomainV2GQL | Exception | None]:
            from ai.backend.manager.api.gql.domain_v2.types.node import (  # pants: no-infer-dep
                DomainV2GQL as D,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else D.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def project_loader(
        self,
    ) -> DataLoader[ProjectID, ProjectV2GQL | None]:
        adapter = self._adapters.project

        async def load_fn(ids: list[ProjectID]) -> list[ProjectV2GQL | None]:
            from ai.backend.manager.api.gql.project_v2.types.node import (  # pants: no-infer-dep
                ProjectV2GQL as PG,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [PG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def agent_loader(
        self,
    ) -> DataLoader[AgentId, AgentV2GQL | None]:
        adapter = self._adapters.agent

        async def load_fn(agent_ids: list[AgentId]) -> list[AgentV2GQL | Exception | None]:
            from ai.backend.manager.api.gql.agent.types import (  # pants: no-infer-dep
                AgentV2GQL as AG,
            )

            dtos = await adapter.batch_load_by_ids(agent_ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else AG.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def agent_by_uuid_loader(
        self,
    ) -> DataLoader[AgentUUID, AgentV2GQL | None]:
        adapter = self._adapters.agent

        async def load_fn(agent_uuids: list[AgentUUID]) -> list[AgentV2GQL | Exception | None]:
            from ai.backend.manager.api.gql.agent.types import (  # pants: no-infer-dep
                AgentV2GQL as AG,
            )

            dtos = await adapter.batch_load_by_uuids(agent_uuids)
            return [
                dto if dto is None or isinstance(dto, Exception) else AG.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def auto_scaling_rule_loader(
        self,
    ) -> DataLoader[uuid.UUID, AutoScalingRule | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[uuid.UUID]) -> list[AutoScalingRule | None]:
            from ai.backend.manager.api.gql.deployment.types.auto_scaling import (  # pants: no-infer-dep
                AutoScalingRule as ASR,
            )

            dtos = await adapter.batch_load_auto_scaling_rules_by_ids(ids)
            return [ASR.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def access_token_loader(
        self,
    ) -> DataLoader[DeploymentTokenID, AccessToken | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[DeploymentTokenID]) -> list[AccessToken | Exception | None]:
            from ai.backend.manager.api.gql.deployment.types.access_token import (  # pants: no-infer-dep
                AccessToken as AT,
            )

            dtos = await adapter.batch_load_access_tokens_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else AT.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def deployment_policy_by_endpoint_loader(
        self,
    ) -> DataLoader[DeploymentID, DeploymentPolicyGQL | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[DeploymentID]) -> list[DeploymentPolicyGQL | None]:
            from ai.backend.manager.api.gql.deployment.types.policy import (  # pants: no-infer-dep
                DeploymentPolicyGQL as DP,
            )

            dtos = await adapter.batch_load_policies_by_endpoint_ids(ids)
            return [DP.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def session_history_loader(
        self,
    ) -> DataLoader[SessionSchedulingHistoryID, SessionSchedulingHistory | None]:
        adapter = self._adapters.scheduling_history

        async def load_fn(
            ids: list[SessionSchedulingHistoryID],
        ) -> list[SessionSchedulingHistory | Exception | None]:
            from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
                SessionSchedulingHistory as SSH,
            )

            dtos = await adapter.batch_load_session_histories_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else SSH.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def kernel_history_loader(
        self,
    ) -> DataLoader[KernelSchedulingHistoryID, KernelSchedulingHistoryGQL | None]:
        adapter = self._adapters.scheduling_history

        async def load_fn(
            ids: list[KernelSchedulingHistoryID],
        ) -> list[KernelSchedulingHistoryGQL | Exception | None]:
            from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
                KernelSchedulingHistoryGQL as KSH,
            )

            dtos = await adapter.batch_load_kernel_histories_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else KSH.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def deployment_history_loader(
        self,
    ) -> DataLoader[DeploymentHistoryID, DeploymentHistory | None]:
        adapter = self._adapters.scheduling_history

        async def load_fn(
            ids: list[DeploymentHistoryID],
        ) -> list[DeploymentHistory | Exception | None]:
            from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
                DeploymentHistory as DH,
            )

            dtos = await adapter.batch_load_deployment_histories_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else DH.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def route_history_loader(
        self,
    ) -> DataLoader[RouteHistoryID, RouteHistory | None]:
        adapter = self._adapters.scheduling_history

        async def load_fn(ids: list[RouteHistoryID]) -> list[RouteHistory | Exception | None]:
            from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
                RouteHistory as RH,
            )

            dtos = await adapter.batch_load_route_histories_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else RH.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def role_loader(
        self,
    ) -> DataLoader[RoleID, RoleGQL | None]:
        adapter = self._adapters.rbac

        async def load_fn(ids: list[RoleID]) -> list[RoleGQL | None]:
            from ai.backend.manager.api.gql.rbac.types.role import (  # pants: no-infer-dep
                RoleGQL as RG,
            )

            dtos = await adapter.batch_load_roles_by_ids(ids)
            return [RG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def permission_loader(
        self,
    ) -> DataLoader[PermissionID, PermissionGQL | None]:
        adapter = self._adapters.rbac

        async def load_fn(ids: list[PermissionID]) -> list[PermissionGQL | None]:
            from ai.backend.manager.api.gql.rbac.types.permission import (  # pants: no-infer-dep
                PermissionGQL as PG,
            )

            dtos = await adapter.batch_load_permissions_by_ids(ids)
            return [PG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def permissions_by_role_loader(
        self,
    ) -> DataLoader[RoleID, list[PermissionGQL]]:
        adapter = self._adapters.rbac

        async def load_fn(role_ids: list[RoleID]) -> list[list[PermissionGQL]]:
            from ai.backend.manager.api.gql.rbac.types.permission import (  # pants: no-infer-dep
                PermissionGQL as PG,
            )

            dtos = await adapter.batch_load_permissions_by_role_ids(role_ids)
            return [[PG.from_pydantic(dto) for dto in role_perms] for role_perms in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def role_assignment_loader(
        self,
    ) -> DataLoader[uuid.UUID, RoleAssignmentGQL | None]:
        adapter = self._adapters.rbac

        async def load_fn(ids: list[uuid.UUID]) -> list[RoleAssignmentGQL | None]:
            from ai.backend.manager.api.gql.rbac.types.role import (  # pants: no-infer-dep
                RoleAssignmentGQL as RAG,
            )

            dtos = await adapter.batch_load_role_assignments_by_ids(ids)
            return [RAG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def role_assignment_by_role_and_user_loader(
        self,
    ) -> DataLoader[tuple[RoleID, UserID], RoleAssignmentGQL | None]:
        adapter = self._adapters.rbac

        async def load_fn(
            pairs: list[tuple[RoleID, UserID]],
        ) -> list[RoleAssignmentGQL | None]:
            from ai.backend.manager.api.gql.rbac.types.role import (  # pants: no-infer-dep
                RoleAssignmentGQL as RAG,
            )

            dtos = await adapter.batch_load_role_assignments_by_role_and_user_ids(pairs)
            return [RAG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def role_assignments_by_user_loader(
        self,
    ) -> DataLoader[UserID, list[RoleAssignmentGQL]]:
        adapter = self._adapters.rbac

        async def load_fn(user_ids: list[UserID]) -> list[list[RoleAssignmentGQL]]:
            from ai.backend.manager.api.gql.rbac.types.role import (  # pants: no-infer-dep
                RoleAssignmentGQL as RAG,
            )

            dtos = await adapter.batch_load_role_assignments_by_user_ids(user_ids)
            return [
                [RAG.from_pydantic(dto) for dto in user_assignments] for user_assignments in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def entity_loader(
        self,
    ) -> DataLoader[ObjectId, EntityNode | None]:
        adapter = self._adapters.rbac

        async def load_fn(object_ids: list[ObjectId]) -> list[EntityNode | None]:
            return await adapter.batch_load_entities_by_type_and_ids(object_ids)

        return DataLoader(load_fn=load_fn)

    @cached_property
    def element_association_loader(
        self,
    ) -> DataLoader[uuid.UUID, EntityRefGQL | None]:
        adapter = self._adapters.rbac

        async def load_fn(ids: list[uuid.UUID]) -> list[EntityRefGQL | None]:
            from ai.backend.manager.api.gql.rbac.types.entity import (  # pants: no-infer-dep
                EntityRefGQL as ERG,
            )

            dtos = await adapter.batch_load_element_associations_by_ids(ids)
            return [ERG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def assignments_by_role_loader(
        self,
    ) -> DataLoader[RoleID, list[RoleAssignmentGQL]]:
        adapter = self._adapters.rbac

        async def load_fn(role_ids: list[RoleID]) -> list[list[RoleAssignmentGQL]]:
            from ai.backend.manager.api.gql.rbac.types.role import (  # pants: no-infer-dep
                RoleAssignmentGQL as RAG,
            )

            dtos = await adapter.batch_load_assignments_by_role_ids(role_ids)
            return [
                [RAG.from_pydantic(dto) for dto in role_assignments] for role_assignments in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def runtime_variant_loader(
        self,
    ) -> DataLoader[RuntimeVariantID, RuntimeVariantGQL | None]:
        adapter = self._adapters.runtime_variant

        async def load_fn(
            ids: list[RuntimeVariantID],
        ) -> list[RuntimeVariantGQL | Exception | None]:
            from ai.backend.manager.api.gql.runtime_variant.types import (  # pants: no-infer-dep
                RuntimeVariantGQL as RV,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else RV.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def runtime_variant_preset_loader(
        self,
    ) -> DataLoader[RuntimeVariantPresetID, RuntimeVariantPresetGQL | None]:
        adapter = self._adapters.runtime_variant_preset

        async def load_fn(
            ids: list[RuntimeVariantPresetID],
        ) -> list[RuntimeVariantPresetGQL | None]:
            from ai.backend.manager.api.gql.runtime_variant_preset.types import (  # pants: no-infer-dep
                RuntimeVariantPresetGQL as RVP,
            )

            nodes = await adapter.batch_load_by_ids(ids)
            return [RVP.from_pydantic(node) if node is not None else None for node in nodes]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def query_definition_loader(
        self,
    ) -> DataLoader[PrometheusQueryPresetID, QueryDefinitionGQL | None]:
        adapter = self._adapters.prometheus_query_preset

        async def load_fn(ids: list[PrometheusQueryPresetID]) -> list[QueryDefinitionGQL | None]:
            from ai.backend.manager.api.gql.prometheus_query_preset.types.node import (  # pants: no-infer-dep
                QueryDefinitionGQL as QD,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [QD.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def category_loader(
        self,
    ) -> DataLoader[PrometheusQueryPresetCategoryID, CategoryGQL | None]:
        adapter = self._adapters.prometheus_query_preset_category

        async def load_fn(
            ids: list[PrometheusQueryPresetCategoryID],
        ) -> list[CategoryGQL | Exception | None]:
            from ai.backend.manager.api.gql.prometheus_query_preset.types.category import (  # pants: no-infer-dep
                CategoryGQL as CG,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [
                dto if dto is None or isinstance(dto, Exception) else CG.from_pydantic(dto)
                for dto in dtos
            ]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def entity_node_loader(self) -> DataLoader[EntityIdentifier, EntityNodeGQL | None]:
        """Resolves an entity from its id alone.

        An :class:`EntityIdentifier` carries the kind it is an id of, so every read
        holding one resolves it here rather than choosing a loader itself. A kind with
        no loader answers ``None``.
        """

        async def load_fn(
            ids: list[EntityIdentifier],
        ) -> list[EntityNodeGQL | Exception | None]:
            return [await self._entity_node(entity_id) for entity_id in ids]

        return DataLoader(load_fn=load_fn)

    async def _entity_node(self, entity_id: EntityIdentifier) -> EntityNodeGQL | None:
        match entity_id.entity_type():
            case AgentEntityType():
                return await self.agent_by_uuid_loader.load(AgentUUID(entity_id))
            case AppConfigAllowListEntityType():
                return await self.app_config_allow_list_loader.load(AppConfigAllowListID(entity_id))
            case AppConfigDefinitionEntityType():
                return await self.app_config_definition_loader.load(
                    AppConfigDefinitionID(entity_id)
                )
            case AppConfigFragmentEntityType():
                return await self.app_config_fragment_loader.load(AppConfigFragmentID(entity_id))
            case ArtifactRegistryEntityType():
                return await self.artifact_registry_loader.load(ArtifactRegistryID(entity_id))
            case ContainerRegistryEntityType():
                return await self.container_registry_loader.load(ContainerRegistryID(entity_id))
            case DeploymentEntityType():
                return await self.deployment_loader.load(DeploymentID(entity_id))
            case DomainEntityType():
                return await self.domain_by_id_loader.load(DomainID(entity_id))
            case IdleCheckerEntityType():
                return await self.idle_checker_loader.load(IdleCheckerID(entity_id))
            case ImageEntityType():
                return await self.image_loader.load(ImageID(entity_id))
            case NotificationChannelEntityType():
                return await self.notification_channel_loader.load(NotificationChannelID(entity_id))
            case NotificationRuleEntityType():
                return await self.notification_rule_loader.load(NotificationRuleID(entity_id))
            case ObjectStorageEntityType():
                return await self.object_storage_loader.load(ObjectStorageID(entity_id))
            case ProjectEntityType():
                return await self.project_loader.load(ProjectID(entity_id))
            case ResourceGroupEntityType():
                return await self.resource_group_by_id_loader.load(ResourceGroupID(entity_id))
            case RoleEntityType():
                return await self.role_loader.load(RoleID(entity_id))
            case RuntimeVariantEntityType():
                return await self.runtime_variant_loader.load(RuntimeVariantID(entity_id))
            case RuntimeVariantPresetEntityType():
                return await self.runtime_variant_preset_loader.load(
                    RuntimeVariantPresetID(entity_id)
                )
            case SessionEntityType():
                return await self.session_loader.load(SessionID(entity_id))
            case StorageNamespaceEntityType():
                return await self.storage_namespace_loader.load(StorageNamespaceID(entity_id))
            case UserEntityType():
                return await self.user_loader.load(UserID(entity_id))
            case VFolderEntityType():
                return await self.vfolder_loader.load(VFolderUUID(entity_id))
            case VFSStorageEntityType():
                return await self.vfs_storage_loader.load(VFSStorageID(entity_id))
            case _:
                return None
