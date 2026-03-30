from __future__ import annotations

import uuid
from functools import cached_property
from typing import TYPE_CHECKING

from strawberry.dataloader import DataLoader

from ai.backend.common.types import AgentId, ImageID, KernelId, SessionId
from ai.backend.manager.data.permission.id import ObjectId

if TYPE_CHECKING:
    from ai.backend.common.dto.manager.v2.rbac.response import EntityNode  # pants: no-infer-dep
    from ai.backend.manager.api.adapters.registry import Adapters  # pants: no-infer-dep
    from ai.backend.manager.api.gql.agent.types import AgentV2GQL  # pants: no-infer-dep
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
    from ai.backend.manager.api.gql.deployment.types.route import Route  # pants: no-infer-dep
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.huggingface_registry import (  # pants: no-infer-dep
        HuggingFaceRegistry,
    )
    from ai.backend.manager.api.gql.image.types import (  # pants: no-infer-dep
        ImageV2AliasGQL,
        ImageV2GQL,
    )
    from ai.backend.manager.api.gql.kernel.types import KernelV2GQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.notification.types import (  # pants: no-infer-dep
        NotificationChannel,
        NotificationRule,
    )
    from ai.backend.manager.api.gql.object_storage import ObjectStorage  # pants: no-infer-dep
    from ai.backend.manager.api.gql.project_v2.types.node import (  # pants: no-infer-dep
        ProjectV2GQL,
    )
    from ai.backend.manager.api.gql.rbac.types.entity import EntityRefGQL  # pants: no-infer-dep
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
    from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
        DeploymentHistory,
        RouteHistory,
        SessionSchedulingHistory,
    )
    from ai.backend.manager.api.gql.session.types import SessionV2GQL  # pants: no-infer-dep
    from ai.backend.manager.api.gql.storage_namespace import (  # pants: no-infer-dep
        StorageNamespace,
    )
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL  # pants: no-infer-dep
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
    def audit_log_loader(
        self,
    ) -> DataLoader[uuid.UUID, AuditLogV2GQL | None]:
        adapter = self._adapters.audit_log

        async def load_fn(ids: list[uuid.UUID]) -> list[AuditLogV2GQL | None]:
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

        async def load_fn(names: list[str]) -> list[ResourceGroupGQL | None]:
            from ai.backend.manager.api.gql.resource_group.types import (  # pants: no-infer-dep
                ResourceGroupGQL as RG,
            )

            dtos = await adapter.batch_load_by_names(names)
            return [RG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def notification_channel_loader(
        self,
    ) -> DataLoader[uuid.UUID, NotificationChannel | None]:
        adapter = self._adapters.notification

        async def load_fn(ids: list[uuid.UUID]) -> list[NotificationChannel | None]:
            from ai.backend.manager.api.gql.notification.types import (  # pants: no-infer-dep
                NotificationChannel as NC,
            )

            dtos = await adapter.batch_load_channels_by_ids(ids)
            return [NC.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def notification_rule_loader(
        self,
    ) -> DataLoader[uuid.UUID, NotificationRule | None]:
        adapter = self._adapters.notification

        async def load_fn(ids: list[uuid.UUID]) -> list[NotificationRule | None]:
            from ai.backend.manager.api.gql.notification.types import (  # pants: no-infer-dep
                NotificationRule as NR,
            )

            dtos = await adapter.batch_load_rules_by_ids(ids)
            return [NR.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def artifact_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, ArtifactRegistry | None]:
        adapter = self._adapters.artifact_registry

        async def load_fn(ids: list[uuid.UUID]) -> list[ArtifactRegistry | None]:
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
    ) -> DataLoader[uuid.UUID, ContainerRegistryGQL | None]:
        adapter = self._adapters.container_registry

        async def load_fn(ids: list[uuid.UUID]) -> list[ContainerRegistryGQL | None]:
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
    ) -> DataLoader[uuid.UUID, StorageNamespace | None]:
        adapter = self._adapters.storage_namespace

        async def load_fn(ids: list[uuid.UUID]) -> list[StorageNamespace | None]:
            from ai.backend.manager.api.gql.storage_namespace import (  # pants: no-infer-dep
                StorageNamespace as SN,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [SN.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def object_storage_loader(
        self,
    ) -> DataLoader[uuid.UUID, ObjectStorage | None]:
        adapter = self._adapters.object_storage

        async def load_fn(ids: list[uuid.UUID]) -> list[ObjectStorage | None]:
            from ai.backend.manager.api.gql.object_storage import (  # pants: no-infer-dep
                ObjectStorage as OS,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [OS.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def vfs_storage_loader(
        self,
    ) -> DataLoader[uuid.UUID, VFSStorage | None]:
        adapter = self._adapters.vfs_storage

        async def load_fn(ids: list[uuid.UUID]) -> list[VFSStorage | None]:
            from ai.backend.manager.api.gql.vfs_storage import (  # pants: no-infer-dep
                VFSStorage as VS,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [VS.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def artifact_revision_loader(
        self,
    ) -> DataLoader[uuid.UUID, ArtifactRevision | None]:
        adapter = self._adapters.artifact

        async def load_fn(ids: list[uuid.UUID]) -> list[ArtifactRevision | None]:
            from ai.backend.manager.api.gql.artifact.types import (  # pants: no-infer-dep
                ArtifactRevision as ARev,
            )

            dtos = await adapter.batch_load_revisions_by_ids(ids)
            return [ARev.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def route_loader(
        self,
    ) -> DataLoader[uuid.UUID, Route | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[uuid.UUID]) -> list[Route | None]:
            from ai.backend.manager.api.gql.deployment.types.route import (  # pants: no-infer-dep
                Route as R,
            )

            dtos = await adapter.batch_load_routes_by_ids(ids)
            return [R.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def deployment_loader(
        self,
    ) -> DataLoader[uuid.UUID, ModelDeployment | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[uuid.UUID]) -> list[ModelDeployment | None]:
            from ai.backend.manager.api.gql.deployment.types.deployment import (  # pants: no-infer-dep
                ModelDeployment as MD,
            )

            dtos = await adapter.batch_load_by_ids(ids)
            return [MD.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def revision_loader(
        self,
    ) -> DataLoader[uuid.UUID, ModelRevision | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[uuid.UUID]) -> list[ModelRevision | None]:
            from ai.backend.manager.api.gql.deployment.types.revision import (  # pants: no-infer-dep
                ModelRevision as MRev,
            )

            dtos = await adapter.batch_load_revisions_by_ids(ids)
            return [MRev.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def replica_loader(
        self,
    ) -> DataLoader[uuid.UUID, ModelReplica | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[uuid.UUID]) -> list[ModelReplica | None]:
            from ai.backend.manager.api.gql.deployment.types.replica import (  # pants: no-infer-dep
                ModelReplica as MRep,
            )

            dtos = await adapter.batch_load_replicas_by_ids(ids)
            return [MRep.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def container_count_loader(
        self,
    ) -> DataLoader[AgentId, int]:
        adapter = self._adapters.agent

        async def load_fn(agent_ids: list[AgentId]) -> list[int]:
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
    ) -> DataLoader[KernelId, KernelV2GQL | None]:
        adapter = self._adapters.session

        async def load_fn(kernel_ids: list[KernelId]) -> list[KernelV2GQL | None]:
            from ai.backend.manager.api.gql.kernel.types import (  # pants: no-infer-dep
                KernelV2GQL as KG,
            )

            dtos = await adapter.batch_load_kernels_by_ids(kernel_ids)
            return [KG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def session_loader(
        self,
    ) -> DataLoader[SessionId, SessionV2GQL | None]:
        adapter = self._adapters.session

        async def load_fn(session_ids: list[SessionId]) -> list[SessionV2GQL | None]:
            from ai.backend.manager.api.gql.session.types import (  # pants: no-infer-dep
                SessionV2GQL as SG,
            )

            dtos = await adapter.batch_load_by_ids(session_ids)
            return [SG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def image_alias_loader(
        self,
    ) -> DataLoader[uuid.UUID, ImageV2AliasGQL | None]:
        """Load a single alias by its own ID (ImageAliasRow.id)."""
        adapter = self._adapters.image

        async def load_fn(ids: list[uuid.UUID]) -> list[ImageV2AliasGQL | None]:
            from ai.backend.manager.api.gql.image.types import (  # pants: no-infer-dep
                ImageV2AliasGQL as IAG,
            )

            dtos = await adapter.batch_load_aliases_by_ids(ids)
            return [IAG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def user_loader(
        self,
    ) -> DataLoader[uuid.UUID, UserV2GQL | None]:
        adapter = self._adapters.user

        async def load_fn(ids: list[uuid.UUID]) -> list[UserV2GQL | None]:
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

        async def load_fn(names: list[str]) -> list[DomainV2GQL | None]:
            from ai.backend.manager.api.gql.domain_v2.types.node import (  # pants: no-infer-dep
                DomainV2GQL as D,
            )

            dtos = await adapter.batch_load_by_names(names)
            return [D.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def project_loader(
        self,
    ) -> DataLoader[uuid.UUID, ProjectV2GQL | None]:
        adapter = self._adapters.project

        async def load_fn(ids: list[uuid.UUID]) -> list[ProjectV2GQL | None]:
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

        async def load_fn(agent_ids: list[AgentId]) -> list[AgentV2GQL | None]:
            from ai.backend.manager.api.gql.agent.types import (  # pants: no-infer-dep
                AgentV2GQL as AG,
            )

            dtos = await adapter.batch_load_by_ids(agent_ids)
            return [AG.from_pydantic(dto) if dto is not None else None for dto in dtos]

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
    ) -> DataLoader[uuid.UUID, AccessToken | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[uuid.UUID]) -> list[AccessToken | None]:
            from ai.backend.manager.api.gql.deployment.types.access_token import (  # pants: no-infer-dep
                AccessToken as AT,
            )

            dtos = await adapter.batch_load_access_tokens_by_ids(ids)
            return [AT.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def deployment_policy_by_endpoint_loader(
        self,
    ) -> DataLoader[uuid.UUID, DeploymentPolicyGQL | None]:
        adapter = self._adapters.deployment

        async def load_fn(ids: list[uuid.UUID]) -> list[DeploymentPolicyGQL | None]:
            from ai.backend.manager.api.gql.deployment.types.policy import (  # pants: no-infer-dep
                DeploymentPolicyGQL as DP,
            )

            dtos = await adapter.batch_load_policies_by_endpoint_ids(ids)
            return [DP.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def session_history_loader(
        self,
    ) -> DataLoader[uuid.UUID, SessionSchedulingHistory | None]:
        adapter = self._adapters.scheduling_history

        async def load_fn(ids: list[uuid.UUID]) -> list[SessionSchedulingHistory | None]:
            from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
                SessionSchedulingHistory as SSH,
            )

            dtos = await adapter.batch_load_session_histories_by_ids(ids)
            return [SSH.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def deployment_history_loader(
        self,
    ) -> DataLoader[uuid.UUID, DeploymentHistory | None]:
        adapter = self._adapters.scheduling_history

        async def load_fn(ids: list[uuid.UUID]) -> list[DeploymentHistory | None]:
            from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
                DeploymentHistory as DH,
            )

            dtos = await adapter.batch_load_deployment_histories_by_ids(ids)
            return [DH.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def route_history_loader(
        self,
    ) -> DataLoader[uuid.UUID, RouteHistory | None]:
        adapter = self._adapters.scheduling_history

        async def load_fn(ids: list[uuid.UUID]) -> list[RouteHistory | None]:
            from ai.backend.manager.api.gql.scheduling_history.types import (  # pants: no-infer-dep
                RouteHistory as RH,
            )

            dtos = await adapter.batch_load_route_histories_by_ids(ids)
            return [RH.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def role_loader(
        self,
    ) -> DataLoader[uuid.UUID, RoleGQL | None]:
        adapter = self._adapters.rbac

        async def load_fn(ids: list[uuid.UUID]) -> list[RoleGQL | None]:
            from ai.backend.manager.api.gql.rbac.types.role import (  # pants: no-infer-dep
                RoleGQL as RG,
            )

            dtos = await adapter.batch_load_roles_by_ids(ids)
            return [RG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def permission_loader(
        self,
    ) -> DataLoader[uuid.UUID, PermissionGQL | None]:
        adapter = self._adapters.rbac

        async def load_fn(ids: list[uuid.UUID]) -> list[PermissionGQL | None]:
            from ai.backend.manager.api.gql.rbac.types.permission import (  # pants: no-infer-dep
                PermissionGQL as PG,
            )

            dtos = await adapter.batch_load_permissions_by_ids(ids)
            return [PG.from_pydantic(dto) if dto is not None else None for dto in dtos]

        return DataLoader(load_fn=load_fn)

    @cached_property
    def permissions_by_role_loader(
        self,
    ) -> DataLoader[uuid.UUID, list[PermissionGQL]]:
        adapter = self._adapters.rbac

        async def load_fn(role_ids: list[uuid.UUID]) -> list[list[PermissionGQL]]:
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
    ) -> DataLoader[tuple[uuid.UUID, uuid.UUID], RoleAssignmentGQL | None]:
        adapter = self._adapters.rbac

        async def load_fn(
            pairs: list[tuple[uuid.UUID, uuid.UUID]],
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
    ) -> DataLoader[uuid.UUID, list[RoleAssignmentGQL]]:
        adapter = self._adapters.rbac

        async def load_fn(user_ids: list[uuid.UUID]) -> list[list[RoleAssignmentGQL]]:
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
    ) -> DataLoader[uuid.UUID, list[RoleAssignmentGQL]]:
        adapter = self._adapters.rbac

        async def load_fn(role_ids: list[uuid.UUID]) -> list[list[RoleAssignmentGQL]]:
            from ai.backend.manager.api.gql.rbac.types.role import (  # pants: no-infer-dep
                RoleAssignmentGQL as RAG,
            )

            dtos = await adapter.batch_load_assignments_by_role_ids(role_ids)
            return [
                [RAG.from_pydantic(dto) for dto in role_assignments] for role_assignments in dtos
            ]

        return DataLoader(load_fn=load_fn)
