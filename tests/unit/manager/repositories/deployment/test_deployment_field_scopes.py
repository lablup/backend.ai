"""The operation scopes that confine a deployment's field-row searches to one deployment.

Each of the three field kinds is seeded under two deployments, so a scope that returns
the named deployment's rows and nothing else is what these assert.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import ClusterMode, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import (
    ModelDeploymentAccessTokenData,
    ModelReplicaData,
    ModelRevisionData,
)
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.scopes import (
    DeploymentRevisionOperationScope,
)
from ai.backend.manager.models.deployment_revision.searchers import ModelRevisionSearcher
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow, EndpointTokenRow
from ai.backend.manager.models.endpoint.scopes import DeploymentAccessTokenOperationScope
from ai.backend.manager.models.endpoint.searchers import DeploymentAccessTokenSearcher
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.scopes import DeploymentReplicaOperationScope
from ai.backend.manager.models.routing.searchers import ModelReplicaSearcher
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass
class _Seeded:
    """One row of each field kind under each of two deployments."""

    named: DeploymentID
    other: DeploymentID
    named_revision: DeploymentRevisionID
    other_revision: DeploymentRevisionID
    named_replica: ReplicaID
    other_replica: ReplicaID
    named_token: DeploymentTokenID
    other_token: DeploymentTokenID


class TestDeploymentFieldScopes:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                EndpointTokenRow,
                ResourceSlotTypeRow,
                DeploymentRevisionResourceSlotRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def seeded(self, database: ExtendedAsyncSAEngine) -> _Seeded:
        suffix = uuid.uuid4().hex[:8]
        domain_name = f"scope-domain-{suffix}"
        domain_id = DomainID(uuid.uuid4())
        group_name = f"scope-group-{suffix}"
        user_policy = f"scope-upolicy-{suffix}"
        project_policy = f"scope-ppolicy-{suffix}"
        user_id = UserID(uuid.uuid4())
        project_id = ProjectID(uuid.uuid4())
        registry_id = uuid.uuid4()
        image_id = ImageID(uuid.uuid4())
        runtime_variant_id = uuid.uuid4()
        named = DeploymentID(uuid.uuid4())
        other = DeploymentID(uuid.uuid4())
        revision_ids = {
            named: DeploymentRevisionID(uuid.uuid4()),
            other: DeploymentRevisionID(uuid.uuid4()),
        }
        replica_ids = {
            named: ReplicaID(uuid.uuid4()),
            other: ReplicaID(uuid.uuid4()),
        }
        token_ids = {
            named: DeploymentTokenID(uuid.uuid4()),
            other: DeploymentTokenID(uuid.uuid4()),
        }

        async with database.begin_session() as db_sess:
            db_sess.add(
                DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot())
            )
            db_sess.add(
                ResourceGroupRow(
                    name=group_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    email=f"scope-{suffix}@test.com",
                    username=f"scope-{suffix}",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_id=domain_id,
                    domain_name=domain_name,
                    resource_policy=user_policy,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"scope-project-{suffix}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_policy,
                )
            )
            db_sess.add(
                ContainerRegistryRow(
                    id=ContainerRegistryID(registry_id),
                    url="http://scope-registry.local",
                    registry_name=f"scope-registry-{suffix}",
                    type=ContainerRegistryType.DOCKER,
                )
            )
            db_sess.add(
                RuntimeVariantRow(
                    id=runtime_variant_id,
                    name=f"scope-variant-{suffix}",
                    description="scope test variant",
                    default_model_definition=DefaultModelDefinition(),
                )
            )
            await db_sess.flush()

            image = ImageRow(
                name=f"scope-image-{suffix}",
                project=None,
                image=f"scope-image-{suffix}",
                tag="latest",
                registry=f"scope-registry-{suffix}",
                registry_id=registry_id,
                architecture="x86_64",
                config_digest="sha256:" + "c" * 64,
                size_bytes=1024,
                type=ImageType.COMPUTE,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "1g"}},
            )
            image.id = image_id
            db_sess.add(image)
            await db_sess.flush()

            for index, deployment_id in enumerate((named, other)):
                db_sess.add(
                    EndpointRow(
                        id=deployment_id,
                        name=f"scope-endpoint-{index}-{suffix}",
                        created_user=user_id,
                        session_owner=user_id,
                        domain=domain_name,
                        project=project_id,
                        resource_group=group_name,
                        lifecycle_stage=EndpointLifecycle.CREATED,
                        replicas=1,
                    )
                )
            await db_sess.flush()

            for deployment_id in (named, other):
                db_sess.add(
                    DeploymentRevisionRow(
                        id=revision_ids[deployment_id],
                        endpoint=deployment_id,
                        revision_number=1,
                        image=image_id,
                        model=None,
                        model_mount_destination="/models",
                        vfolder_subpath=None,
                        resource_group=group_name,
                        resource_opts={},
                        cluster_mode=ClusterMode.SINGLE_NODE.name,
                        cluster_size=1,
                        runtime_variant_id=runtime_variant_id,
                        environ={},
                        extra_mounts=[],
                    )
                )
                db_sess.add(
                    RoutingRow(
                        id=replica_ids[deployment_id],
                        endpoint=deployment_id,
                        session=None,
                        session_owner=user_id,
                        domain=domain_name,
                        project=project_id,
                        traffic_ratio=1.0,
                        revision=revision_ids[deployment_id],
                    )
                )
                db_sess.add(
                    EndpointTokenRow(
                        id=token_ids[deployment_id],
                        token=f"token-{deployment_id}-{suffix}",
                        endpoint=deployment_id,
                        domain=domain_name,
                        project=project_id,
                        session_owner=user_id,
                    )
                )
            await db_sess.flush()

        return _Seeded(
            named=named,
            other=other,
            named_revision=revision_ids[named],
            other_revision=revision_ids[other],
            named_replica=replica_ids[named],
            other_replica=replica_ids[other],
            named_token=token_ids[named],
            other_token=token_ids[other],
        )

    @pytest.fixture
    def revisions(self, database: ExtendedAsyncSAEngine) -> OpsRepository[ModelRevisionData]:
        return OpsRepository[ModelRevisionData](V2DBOpsProvider(database))

    @pytest.fixture
    def replicas(self, database: ExtendedAsyncSAEngine) -> OpsRepository[ModelReplicaData]:
        return OpsRepository[ModelReplicaData](V2DBOpsProvider(database))

    @pytest.fixture
    def tokens(
        self, database: ExtendedAsyncSAEngine
    ) -> OpsRepository[ModelDeploymentAccessTokenData]:
        return OpsRepository[ModelDeploymentAccessTokenData](V2DBOpsProvider(database))

    async def test_revision_scope_returns_only_the_named_deployments_rows(
        self, revisions: OpsRepository[ModelRevisionData], seeded: _Seeded
    ) -> None:
        result = await revisions.search_in_scopes(
            [DeploymentRevisionOperationScope(deployment_id=seeded.named)],
            ModelRevisionSearcher(pagination=OffsetPagination(limit=10, offset=0)),
        )

        assert [item.id for item in result.items] == [seeded.named_revision]
        assert result.total_count == 1

    async def test_replica_scope_returns_only_the_named_deployments_rows(
        self, replicas: OpsRepository[ModelReplicaData], seeded: _Seeded
    ) -> None:
        result = await replicas.search_in_scopes(
            [DeploymentReplicaOperationScope(deployment_id=seeded.named)],
            ModelReplicaSearcher(pagination=OffsetPagination(limit=10, offset=0)),
        )

        assert [item.id for item in result.items] == [seeded.named_replica]
        assert result.total_count == 1

    async def test_access_token_scope_returns_only_the_named_deployments_rows(
        self, tokens: OpsRepository[ModelDeploymentAccessTokenData], seeded: _Seeded
    ) -> None:
        result = await tokens.search_in_scopes(
            [DeploymentAccessTokenOperationScope(deployment_id=seeded.named)],
            DeploymentAccessTokenSearcher(pagination=OffsetPagination(limit=10, offset=0)),
        )

        assert [item.id for item in result.items] == [seeded.named_token]
        assert result.total_count == 1

    async def test_naming_both_deployments_returns_both_deployments_rows(
        self, revisions: OpsRepository[ModelRevisionData], seeded: _Seeded
    ) -> None:
        # The scopes combine with OR, so a caller reaching for two owners sees both.
        result = await revisions.search_in_scopes(
            [
                DeploymentRevisionOperationScope(deployment_id=seeded.named),
                DeploymentRevisionOperationScope(deployment_id=seeded.other),
            ],
            ModelRevisionSearcher(pagination=OffsetPagination(limit=10, offset=0)),
        )

        assert {item.id for item in result.items} == {
            seeded.named_revision,
            seeded.other_revision,
        }
