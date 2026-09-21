"""The deployment usage narrowing the runtime variant and deployment preset reads.

One test per connection: the read keeps the rows the named deployment's revisions point
at and leaves the rest out.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
)
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.scopes import (
    PublicDeploymentPresetTarget,
)
from ai.backend.manager.models.deployment_revision_preset.searchable_fields import (
    DeploymentPresetSearchableFields,
)
from ai.backend.manager.models.deployment_revision_preset.searchers import (
    DeploymentPresetSearcher,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.endpoint.searchable_fields import DeploymentSearchableFields
from ai.backend.manager.models.endpoint.searchers import DeploymentSearcher
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
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant.scopes import PublicRuntimeVariantTarget
from ai.backend.manager.models.runtime_variant.searchable_fields import (
    RuntimeVariantSearchableFields,
)
from ai.backend.manager.models.runtime_variant.searchers import RuntimeVariantSearcher
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass
class UsageFixture:
    used_variant_id: RuntimeVariantID
    unused_variant_id: RuntimeVariantID
    used_preset_id: DeploymentPresetID
    unused_preset_id: DeploymentPresetID
    deployment_id: DeploymentID


class TestDeploymentUsage:
    @pytest.fixture
    async def db_with_cleanup(
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
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def usage(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[UsageFixture, None]:
        """One deployment with a single revision naming one variant and one preset."""
        suffix = uuid.uuid4().hex[:8]
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{suffix}"
        resource_group_name = f"test-sgroup-{suffix}"
        user_policy_name = f"test-upolicy-{suffix}"
        project_policy_name = f"test-ppolicy-{suffix}"
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        deployment_id = DeploymentID(uuid.uuid4())

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    total_resource_slots=ResourceSlot(),
                )
            )
            db_sess.add(
                ResourceGroupRow(
                    name=resource_group_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    email=f"test-{suffix}@test.com",
                    username=f"testuser-{suffix}",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_id=domain_id,
                    domain_name=domain_name,
                    resource_policy=user_policy_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"project-{suffix}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_policy_name,
                )
            )
            registry_id = ContainerRegistryID(uuid.uuid4())
            db_sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url="http://test-registry.local",
                    registry_name=f"test-registry-{suffix}",
                    type=ContainerRegistryType.DOCKER,
                )
            )
            await db_sess.flush()

            image = ImageRow(
                name=f"test-image-{suffix}",
                project=None,
                image=f"test-image-{suffix}",
                tag="latest",
                registry=f"test-registry-{suffix}",
                registry_id=registry_id,
                architecture="x86_64",
                config_digest="sha256:" + "a" * 64,
                size_bytes=1024,
                type=ImageType.COMPUTE,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "1g"}},
            )
            image.id = ImageID(uuid.uuid4())
            db_sess.add(image)

            variants = [
                RuntimeVariantRow(id=RuntimeVariantID(uuid.uuid4()), name=f"variant-{label}")
                for label in ("used", "unused")
            ]
            db_sess.add_all(variants)
            await db_sess.flush()

            presets = [
                DeploymentRevisionPresetRow(
                    id=DeploymentPresetID(uuid.uuid4()),
                    runtime_variant=variants[0].id,
                    name=f"preset-{label}",
                    rank=rank,
                    image_id=image.id,
                )
                for rank, label in enumerate(("used", "unused"), start=1)
            ]
            db_sess.add_all(presets)
            db_sess.add(
                EndpointRow(
                    id=deployment_id,
                    name=f"endpoint-{suffix}",
                    created_user=user_id,
                    session_owner=user_id,
                    domain=domain_name,
                    project=project_id,
                    resource_group=resource_group_name,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                    replicas=1,
                )
            )
            await db_sess.flush()

            db_sess.add(
                DeploymentRevisionRow(
                    endpoint=deployment_id,
                    revision_number=1,
                    image=image.id,
                    model_mount_destination="/models",
                    resource_group=resource_group_name,
                    runtime_variant_id=variants[0].id,
                    revision_preset_id=presets[0].id,
                )
            )

        yield UsageFixture(
            used_variant_id=variants[0].id,
            unused_variant_id=variants[1].id,
            used_preset_id=presets[0].id,
            unused_preset_id=presets[1].id,
            deployment_id=deployment_id,
        )

    @pytest.fixture
    def variant_repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> OpsRepository[RuntimeVariantData]:
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    @pytest.fixture
    def preset_repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> OpsRepository[DeploymentRevisionPresetData]:
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    @pytest.fixture
    def deployment_repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> OpsRepository[ModelDeploymentData]:
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    async def test_variant_usage_keeps_the_variant_the_deployment_names(
        self,
        variant_repository: OpsRepository[RuntimeVariantData],
        usage: UsageFixture,
    ) -> None:
        result = await variant_repository.scoped_search(
            ScopedSearcher(
                scopes=[PublicRuntimeVariantTarget()],
                used_by=[
                    RuntimeVariantSearchableFields.linked.usage.deployments.used_by(
                        usage.deployment_id
                    )
                ],
                searcher=RuntimeVariantSearcher(pagination=OffsetPagination(limit=10)),
            )
        )

        assert [item.id for item in result.items] == [usage.used_variant_id]

    async def test_preset_usage_keeps_the_preset_the_deployment_names(
        self,
        preset_repository: OpsRepository[DeploymentRevisionPresetData],
        usage: UsageFixture,
    ) -> None:
        result = await preset_repository.scoped_search(
            ScopedSearcher(
                scopes=[PublicDeploymentPresetTarget()],
                used_by=[
                    DeploymentPresetSearchableFields.linked.usage.deployments.used_by(
                        usage.deployment_id
                    )
                ],
                searcher=DeploymentPresetSearcher(pagination=OffsetPagination(limit=10)),
            )
        )

        assert [item.id for item in result.items] == [usage.used_preset_id]

    async def test_deployment_uses_keeps_the_deployment_naming_the_variant(
        self,
        deployment_repository: OpsRepository[ModelDeploymentData],
        usage: UsageFixture,
    ) -> None:
        result = await deployment_repository.global_search(
            GlobalSearcher(
                used_by=[
                    DeploymentSearchableFields.linked.usage.runtime_variants.uses(
                        usage.used_variant_id
                    )
                ],
                searcher=DeploymentSearcher(pagination=OffsetPagination(limit=10)),
            )
        )

        assert [item.id for item in result.items] == [usage.deployment_id]

    async def test_deployment_uses_leaves_out_a_variant_no_revision_names(
        self,
        deployment_repository: OpsRepository[ModelDeploymentData],
        usage: UsageFixture,
    ) -> None:
        result = await deployment_repository.global_search(
            GlobalSearcher(
                used_by=[
                    DeploymentSearchableFields.linked.usage.runtime_variants.uses(
                        usage.unused_variant_id
                    )
                ],
                searcher=DeploymentSearcher(pagination=OffsetPagination(limit=10)),
            )
        )

        assert result.items == []

    async def test_deployment_uses_keeps_the_deployment_naming_the_preset(
        self,
        deployment_repository: OpsRepository[ModelDeploymentData],
        usage: UsageFixture,
    ) -> None:
        result = await deployment_repository.global_search(
            GlobalSearcher(
                used_by=[
                    DeploymentSearchableFields.linked.usage.deployment_presets.uses(
                        usage.used_preset_id
                    )
                ],
                searcher=DeploymentSearcher(pagination=OffsetPagination(limit=10)),
            )
        )

        assert [item.id for item in result.items] == [usage.deployment_id]
