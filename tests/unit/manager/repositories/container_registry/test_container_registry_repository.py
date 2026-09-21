from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.image import (
    ContainerRegistryNotFound,
)
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.container_registry.creators import (
    ContainerRegistryCreator,
    ContainerRegistryProjectCreator,
)
from ai.backend.manager.models.container_registry.purgers import (
    ContainerRegistryProjectPurger,
    ContainerRegistryPurger,
)
from ai.backend.manager.models.container_registry.searchable_fields import (
    ContainerRegistrySearchableFields,
)
from ai.backend.manager.models.container_registry.updaters import (
    ContainerRegistryGlobalUpdater,
    ContainerRegistryUpdater,
)
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.image.creators import ImageCreator
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import PermissionRow, RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.ops.v2.share.write import V2ShareWriteOps
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory, DomainFixtureData


@dataclass
class _RegistryWithImages:
    """Registry with associated image IDs."""

    registry: ContainerRegistryData
    image_ids: list[UUID]


@dataclass
class _TwoRegistries:
    """Two registries for comparison tests."""

    registry1: ContainerRegistryData
    registry2: ContainerRegistryData


@dataclass
class _TwoRegistriesWithImages:
    """Two registries each with one image."""

    registry1: ContainerRegistryData
    image1_id: UUID
    registry2: ContainerRegistryData
    image2_id: UUID


@dataclass
class _RegistryWithGroups:
    """Registry with associated group IDs."""

    registry: ContainerRegistryData
    group_ids: list[ProjectID]


class TestContainerRegistryRepository:
    """Integration tests for ContainerRegistryRepository using real database"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        global_entity_ids: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            global_entity_ids,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,  # UserRow relationship dependency
                UserRow,
                KeyPairRow,
                ProjectRow,
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
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
                PermissionRow,
                RolePresetRow,
                RolePermissionPresetRow,
                # The registry's owner virtual entity and the allowed-project edges
                VirtualEntityRow,
                ScopeBindingRow,
                EntityLabelRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                EntityMembershipFieldRow,
                EntityShareRow,
            ],
        ):
            yield global_entity_ids

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ContainerRegistryRepository:
        """Create ContainerRegistryRepository instance with real database"""
        return ContainerRegistryRepository(
            db=db_with_cleanup, ops_provider=ShareOpsProvider(db_with_cleanup)
        )

    @pytest.fixture
    def relation_repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> RbacRelationRepository:
        """The relation writes the registry's allowed projects go through."""
        return RbacRelationRepository(RelationOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def sample_domain(
        self,
        domain_factory: DomainFactory,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        """Pre-created domain for group tests."""
        return await domain_factory(db_with_cleanup)

    @pytest.fixture
    async def sample_groups(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_domain: DomainFixtureData
    ) -> list[ProjectID]:
        """Pre-created 2 groups with required policies. Depends on sample_domain.domain_name."""
        resource_policy_name = f"test-policy-{sample_domain.domain_name}"
        group_ids: list[ProjectID] = []

        async with db_with_cleanup.begin_session() as session:
            # Create resource policies
            user_policy = UserResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(user_policy)

            project_policy = ProjectResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_policy)

            # Create 2 groups
            for i in range(2):
                group = ProjectRow(
                    name=f"test-group-{i}-{sample_domain.domain_name}",
                    domain_name=sample_domain.domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=resource_policy_name,
                )
                session.add(group)
                await session.flush()
                session.add(VirtualEntityRow(entity_type=ProjectEntityType(), entity_id=group.id))
                group_ids.append(group.id)

            await session.commit()
        return group_ids

    @pytest.fixture
    async def test_registry(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ContainerRegistryData:
        """Fixture that provides a pre-created test registry. TRUNCATE CASCADE handles cleanup."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.commit()
            await session.refresh(registry)  # Ensure all attributes are loaded
            return ContainerRegistrySearchableFields.own.to_data(registry)

    @pytest.fixture
    async def test_registry_with_custom_props(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> ContainerRegistryData:
        """Fixture that provides a registry with custom properties for detailed testing."""
        registry_name = "test-registry"
        project = "test-project"

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
                username="test-user",
                password="test-pass",
                ssl_verify=False,
                is_global=False,
            )
            session.add(registry)
            await session.commit()
            await session.refresh(registry)  # Ensure all attributes are loaded
            return ContainerRegistrySearchableFields.own.to_data(registry)

    @pytest.fixture
    async def sample_registry(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> ContainerRegistryData:
        """Pre-created single registry for simple tests."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.commit()
            await session.refresh(registry)
            return ContainerRegistrySearchableFields.own.to_data(registry)

    async def test_get_by_registry_and_project_success(
        self, repository: ContainerRegistryRepository, sample_registry: ContainerRegistryData
    ) -> None:
        """Test successful registry retrieval by name and project"""
        # When
        result = await repository.get_by_registry_and_project(
            sample_registry.registry_name, sample_registry.project
        )

        # Then
        assert result is not None
        assert isinstance(result, ContainerRegistryData)
        assert result.registry_name == sample_registry.registry_name
        assert result.project == sample_registry.project
        assert result.id == sample_registry.id

    async def test_get_by_registry_and_project_not_found(
        self, repository: ContainerRegistryRepository
    ) -> None:
        """Test registry retrieval when registry doesn't exist"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_by_registry_and_project("non-existent", "project")

    @pytest.fixture
    async def two_registries_same_name(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> _TwoRegistries:
        """Pre-created two registries with the same name but different projects."""
        registry_name = "test-registry-" + str(uuid.uuid4())[:8] + ".example.com"

        async with db_with_cleanup.begin_session() as session:
            registry1 = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project="project-" + str(uuid.uuid4())[:8],
            )
            registry2 = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project="project-" + str(uuid.uuid4())[:8],
            )
            session.add_all([registry1, registry2])
            await session.commit()
            await session.refresh(registry1)
            await session.refresh(registry2)
            return _TwoRegistries(
                registry1=ContainerRegistrySearchableFields.own.to_data(registry1),
                registry2=ContainerRegistrySearchableFields.own.to_data(registry2),
            )

    async def test_get_by_registry_name(
        self,
        repository: ContainerRegistryRepository,
        two_registries_same_name: _TwoRegistries,
    ) -> None:
        """Test retrieving all registries with the same name"""
        # When
        results = await repository.get_by_registry_name(
            two_registries_same_name.registry1.registry_name
        )

        # Then
        assert len(results) == 2
        for result in results:
            assert result.registry_name == two_registries_same_name.registry1.registry_name

    @pytest.fixture
    async def two_registries_different_names(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> _TwoRegistries:
        """Pre-created two registries with different names."""
        async with db_with_cleanup.begin_session() as session:
            registry1_name = str(uuid.uuid4())[:8] + ".example.com"
            registry2_name = str(uuid.uuid4())[:8] + ".example.com"

            registry1 = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry1_name}",
                registry_name=registry1_name,
                type=ContainerRegistryType.HARBOR2,
                project="project-" + str(uuid.uuid4())[:8],
            )
            registry2 = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry2_name}",
                registry_name=registry2_name,
                type=ContainerRegistryType.HARBOR2,
                project="project-" + str(uuid.uuid4())[:8],
            )
            session.add_all([registry1, registry2])
            await session.commit()
            await session.refresh(registry1)
            await session.refresh(registry2)
            return _TwoRegistries(
                registry1=ContainerRegistrySearchableFields.own.to_data(registry1),
                registry2=ContainerRegistrySearchableFields.own.to_data(registry2),
            )

    async def test_get_all(
        self,
        repository: ContainerRegistryRepository,
        two_registries_different_names: _TwoRegistries,
    ) -> None:
        """Test retrieving all registries"""
        # When
        result = await repository.get_all()

        # Then
        assert len(result) == 2

    @pytest.fixture
    async def creator(self) -> ContainerRegistryCreator:
        """Fixture that provides a minimal creator spec for creating registries."""
        return ContainerRegistryCreator(
            url="https://minimal.example.com",
            type=ContainerRegistryType.HARBOR2,
            registry_name="minimal-registry",
            project="minimal-project",
        )

    async def test_create_registry_minimal(
        self,
        repository: ContainerRegistryRepository,
        creator: ContainerRegistryCreator,
    ) -> None:
        """Test creating registry with minimal required fields"""
        # When
        result = await repository.create_registry(creator)

        # Then - Verify result
        assert result is not None
        assert result.registry_name == creator.registry_name
        assert result.url == creator.url
        assert result.type == creator.type
        assert result.project == creator.project
        assert result.id is not None

    @pytest.fixture
    async def registry_creator_and_projects(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> tuple[ContainerRegistryCreator, list[str]]:
        """A creator for a registry, beside the projects to be allowed on it."""
        registry_name = "registry-with-groups-" + str(uuid.uuid4())[:8]
        project = "project-with-groups-" + str(uuid.uuid4())[:8]
        domain_name = f"test-domain-{registry_name}"
        resource_policy_name = f"test-policy-{registry_name}"

        # Pre-create domain, resource policy, and 2 groups to associate
        group_ids: list[str] = []
        async with db_with_cleanup.begin_session() as session:
            # Create domain
            domain_id = DomainID(uuid.uuid4())
            domain = DomainRow(
                id=domain_id,
                name=domain_name,
                total_resource_slots=ResourceSlot(),
            )
            session.add(domain)

            # Create project resource policy
            project_policy = ProjectResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_policy)

            await session.flush()

            # Create 2 groups
            for i in range(2):
                group = ProjectRow(
                    name=f"test-group-for-registry-{i}-{registry_name}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=resource_policy_name,
                )
                session.add(group)
                await session.flush()
                session.add(VirtualEntityRow(entity_type=ProjectEntityType(), entity_id=group.id))
                group_ids.append(str(group.id))
            await session.commit()

        creator = ContainerRegistryCreator(
            url=f"https://{registry_name}",
            type=ContainerRegistryType.HARBOR2,
            registry_name=registry_name,
            project=project,
        )
        return creator, group_ids

    async def test_create_registry_then_link_projects(
        self,
        repository: ContainerRegistryRepository,
        relation_repository: RbacRelationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_creator_and_projects: tuple[ContainerRegistryCreator, list[str]],
    ) -> None:
        """A registry created, then linked to the projects allowed on it."""
        # Given - Registry and groups
        creator, group_ids = registry_creator_and_projects
        # When
        result = await repository.create_registry(creator)
        for group_id in group_ids:
            await relation_repository.create(
                [(ProjectID(uuid.UUID(group_id)), ContainerRegistryID(result.id))],
                ContainerRegistryProjectCreator(),
            )

        # Then - Verify registry created
        assert result is not None
        assert result.registry_name == creator.registry_name

        # Then - Verify the association rows
        async with db_with_cleanup.begin_readonly_session() as session:
            associations = (
                (
                    await session.execute(
                        sa.select(AssociationContainerRegistriesGroupsRow).where(
                            AssociationContainerRegistriesGroupsRow.registry_id == result.id
                        )
                    )
                )
                .scalars()
                .all()
            )

            assert len(associations) == 2
            assert {str(a.group_id) for a in associations} == set(group_ids)

    @pytest.fixture
    async def sample_registry_with_images(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> _RegistryWithImages:
        """Pre-created registry with 2 images."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)

            image1 = ImageRow(
                name=f"{registry_name}/{project}/image-1:latest",
                registry=registry_name,
                registry_id=registry.id,
                project=project,
                image="image-1",
                tag="latest",
                architecture="x86_64",
                is_local=False,
                type=ImageType.COMPUTE,
                config_digest="sha256:test1",
                size_bytes=1024 * 1024,
                accelerators=None,
                resources={},
                labels={},
                status=ImageStatus.ALIVE,
            )
            image2 = ImageRow(
                name=f"{registry_name}/{project}/image-2:latest",
                registry=registry_name,
                registry_id=registry.id,
                project=project,
                image="image-2",
                tag="latest",
                architecture="x86_64",
                is_local=False,
                type=ImageType.COMPUTE,
                config_digest="sha256:test2",
                size_bytes=1024 * 1024,
                accelerators=None,
                resources={},
                labels={},
                status=ImageStatus.ALIVE,
            )
            session.add_all([image1, image2])
            await session.commit()
            await session.refresh(registry)
            return _RegistryWithImages(
                registry=ContainerRegistrySearchableFields.own.to_data(registry),
                image_ids=[image1.id, image2.id],
            )

    async def test_clear_images(
        self,
        repository: ContainerRegistryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_registry_with_images: _RegistryWithImages,
    ) -> None:
        """Test clearing images for a registry"""
        registry = sample_registry_with_images.registry
        image_ids = sample_registry_with_images.image_ids

        # When
        result = await repository.clear_images(registry.registry_name, registry.project)

        # Then
        assert result is not None
        assert result.registry_name == registry.registry_name

        # Verify images are marked as deleted
        async with db_with_cleanup.begin_readonly_session() as session:
            images = (
                (await session.execute(sa.select(ImageRow).where(ImageRow.id.in_(image_ids))))
                .scalars()
                .all()
            )
            assert all(img.status == ImageStatus.DELETED for img in images)

    async def test_clear_images_not_found(self, repository: ContainerRegistryRepository) -> None:
        """Test clearing images when registry not found"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.clear_images("non-existent", "project")

    @pytest.fixture
    async def two_registries_with_images(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> _TwoRegistriesWithImages:
        """Pre-created two registries (same name, different projects) each with one image."""
        registry_name = "test-registry-" + str(uuid.uuid4())[:8] + ".example.com"
        project1 = "project-" + str(uuid.uuid4())[:8]
        project2 = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry1 = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project1,
            )
            registry2 = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project2,
            )
            session.add_all([registry1, registry2])

            image1 = ImageRow(
                name=f"{registry_name}/{project1}/image-1:latest",
                registry=registry_name,
                registry_id=registry1.id,
                project=project1,
                image="image-1",
                tag="latest",
                architecture="x86_64",
                is_local=False,
                type=ImageType.COMPUTE,
                config_digest="sha256:test1",
                size_bytes=1024 * 1024,
                accelerators=None,
                resources={},
                labels={},
                status=ImageStatus.ALIVE,
            )
            image2 = ImageRow(
                name=f"{registry_name}/{project2}/image-2:latest",
                registry=registry_name,
                registry_id=registry2.id,
                project=project2,
                image="image-2",
                tag="latest",
                architecture="x86_64",
                is_local=False,
                type=ImageType.COMPUTE,
                config_digest="sha256:test2",
                size_bytes=1024 * 1024,
                accelerators=None,
                resources={},
                labels={},
                status=ImageStatus.ALIVE,
            )
            session.add_all([image1, image2])
            await session.commit()
            await session.refresh(registry1)
            await session.refresh(registry2)

            return _TwoRegistriesWithImages(
                registry1=ContainerRegistrySearchableFields.own.to_data(registry1),
                image1_id=image1.id,
                registry2=ContainerRegistrySearchableFields.own.to_data(registry2),
                image2_id=image2.id,
            )

    async def test_clear_images_with_project_filter(
        self,
        repository: ContainerRegistryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        two_registries_with_images: _TwoRegistriesWithImages,
    ) -> None:
        """Test clearing images with project filter doesn't affect other projects"""
        reg1 = two_registries_with_images.registry1
        img1_id = two_registries_with_images.image1_id
        img2_id = two_registries_with_images.image2_id

        # When - Clear images only for project1
        await repository.clear_images(reg1.registry_name, reg1.project)

        # Then - Verify only project1 images are deleted
        async with db_with_cleanup.begin_readonly_session() as session:
            img_p1 = await session.scalar(sa.select(ImageRow).where(ImageRow.id == img1_id))
            img_p2 = await session.scalar(sa.select(ImageRow).where(ImageRow.id == img2_id))

            assert img_p1 is not None
            assert img_p2 is not None
            assert img_p1.status == ImageStatus.DELETED
            assert img_p2.status == ImageStatus.ALIVE

    async def test_get_registry_row_for_scanner_success(
        self, repository: ContainerRegistryRepository, sample_registry: ContainerRegistryData
    ) -> None:
        """Test getting registry row for scanner"""
        # When
        result = await repository.get_registry_row_for_scanner(
            sample_registry.registry_name, sample_registry.project
        )

        # Then
        assert result is not None
        assert isinstance(result, ContainerRegistryRow)
        assert result.registry_name == sample_registry.registry_name
        assert result.project == sample_registry.project
        assert result.id == sample_registry.id

    async def test_get_registry_row_for_scanner_not_found(
        self, repository: ContainerRegistryRepository
    ) -> None:
        """Test getting registry row when not found"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_registry_row_for_scanner("non-existent", "project")

    @pytest.fixture
    async def registry_for_modification(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> ContainerRegistryData:
        """Pre-created registry with specific initial values for modification testing."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
                username="initial-user",
                password="initial-password",
                ssl_verify=False,
                extra={"initial_key": "initial_value"},
            )
            session.add(registry)
            await session.commit()
            await session.refresh(registry)
            return ContainerRegistrySearchableFields.own.to_data(registry)

    async def test_modify_registry_success(
        self,
        repository: ContainerRegistryRepository,
        registry_for_modification: ContainerRegistryData,
    ) -> None:
        """Test successful registry modification"""
        # Given - Values to update
        changed_username = "modified-user"
        changed_password = "modified-password"
        changed_extra = {"modified_key": "modified_value"}

        result = await repository.modify_registry(
            ContainerRegistryUpdater(
                registry_id=ContainerRegistryID(registry_for_modification.id),
                url=OptionalState.nop(),
                type=OptionalState.nop(),
                registry_name=OptionalState.nop(),
                project=TriState.nop(),
                username=TriState.update(changed_username),
                password=TriState.update(changed_password),
                ssl_verify=TriState.nop(),
                extra=TriState.update(changed_extra),
            )
        )

        # Then
        assert result is not None

        # Then - Verify unchanged fields remain the same
        assert result.id == registry_for_modification.id
        assert result.registry_name == registry_for_modification.registry_name
        assert result.project == registry_for_modification.project

        # Then - Verify updated fields are changed
        assert result.username == changed_username
        assert result.password == changed_password
        assert result.extra == changed_extra

    async def test_modify_registry_not_found(self, repository: ContainerRegistryRepository) -> None:
        """Test modifying a non-existent registry"""
        non_existent_id = UUID("00000000-0000-0000-0000-000000000000")

        # Then
        with pytest.raises(ContainerRegistryNotFound):
            await repository.modify_registry(
                ContainerRegistryUpdater(
                    registry_id=ContainerRegistryID(non_existent_id),
                    url=OptionalState.nop(),
                    type=OptionalState.nop(),
                    registry_name=OptionalState.nop(),
                    project=TriState.nop(),
                    username=TriState.update("new-user"),
                    password=TriState.nop(),
                    ssl_verify=TriState.nop(),
                    extra=TriState.nop(),
                )
            )

    @dataclass
    class _RegistryWithAvailableGroups:
        """Registry with available groups for adding."""

        registry: ContainerRegistryData
        group_ids: list[ProjectID]

    @pytest.fixture
    async def registry_and_groups_for_adding(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_groups: list[ProjectID]
    ) -> _RegistryWithAvailableGroups:
        """Pre-created registry and 2 groups to link it to."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.flush()
            session.add(
                VirtualEntityRow(entity_type=ContainerRegistryEntityType(), entity_id=registry.id)
            )
            await session.commit()
            await session.refresh(registry)
            return self._RegistryWithAvailableGroups(
                registry=ContainerRegistrySearchableFields.own.to_data(registry),
                group_ids=sample_groups,
            )

    async def test_link_projects_to_registry(
        self,
        relation_repository: RbacRelationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_and_groups_for_adding: _RegistryWithAvailableGroups,
    ) -> None:
        """Linking projects to an existing registry writes the association rows."""
        registry_id = ContainerRegistryID(registry_and_groups_for_adding.registry.id)
        for group_id in registry_and_groups_for_adding.group_ids:
            await relation_repository.create(
                [(group_id, registry_id)], ContainerRegistryProjectCreator()
            )

        # Then - Verify associations were created
        async with db_with_cleanup.begin_readonly_session() as session:
            associations = (
                (
                    await session.execute(
                        sa.select(AssociationContainerRegistriesGroupsRow).where(
                            AssociationContainerRegistriesGroupsRow.registry_id
                            == registry_and_groups_for_adding.registry.id
                        )
                    )
                )
                .scalars()
                .all()
            )

            assert len(associations) == 2
            assert {a.group_id for a in associations} == set(
                registry_and_groups_for_adding.group_ids
            )

    @pytest.fixture
    async def registry_with_associated_groups(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_domain: DomainFixtureData
    ) -> _RegistryWithGroups:
        """Pre-created registry with 3 groups already associated."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]
        resource_policy_name = f"test-policy-{sample_domain.domain_name}-3groups"
        group_ids: list[ProjectID] = []

        async with db_with_cleanup.begin_session() as session:
            # Create registry
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.flush()
            session.add(
                VirtualEntityRow(entity_type=ContainerRegistryEntityType(), entity_id=registry.id)
            )

            # Create resource policies
            user_policy = UserResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(user_policy)

            project_policy = ProjectResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_policy)

            # Create 3 groups and associate them
            for i in range(3):
                group = ProjectRow(
                    name=f"test-group-{i}-{sample_domain.domain_name}-assoc",
                    domain_name=sample_domain.domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=resource_policy_name,
                )
                session.add(group)
                await session.flush()
                session.add(VirtualEntityRow(entity_type=ProjectEntityType(), entity_id=group.id))
                group_ids.append(group.id)

                # Associate with registry
                assoc = AssociationContainerRegistriesGroupsRow()
                assoc.registry_id = registry.id
                assoc.group_id = group.id
                session.add(assoc)

            await session.commit()
            await session.refresh(registry)
            return _RegistryWithGroups(
                registry=ContainerRegistrySearchableFields.own.to_data(registry),
                group_ids=group_ids,
            )

    async def test_unlink_project_from_registry(
        self,
        relation_repository: RbacRelationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_with_associated_groups: _RegistryWithGroups,
    ) -> None:
        """Unlinking one project leaves the rest of the associations standing."""
        # Given - Registry already has 3 groups associated
        group_count = 3

        # When - Unlink one group
        unlinked = await relation_repository.purge(
            [
                (
                    registry_with_associated_groups.group_ids[0],
                    ContainerRegistryID(registry_with_associated_groups.registry.id),
                )
            ],
            ContainerRegistryProjectPurger(),
        )
        assert unlinked == [True]

        # Then - Verify one group was removed
        async with db_with_cleanup.begin_readonly_session() as session:
            associations = (
                (
                    await session.execute(
                        sa.select(AssociationContainerRegistriesGroupsRow).where(
                            AssociationContainerRegistriesGroupsRow.registry_id
                            == registry_with_associated_groups.registry.id
                        )
                    )
                )
                .scalars()
                .all()
            )

            assert len(associations) == group_count - 1
            assert {a.group_id for a in associations} == {
                registry_with_associated_groups.group_ids[1],
                registry_with_associated_groups.group_ids[2],
            }

    @dataclass
    class _RegistryWithPartialGroups:
        """Registry with 2 groups associated out of 4 available."""

        registry: ContainerRegistryData
        all_group_ids: list[ProjectID]
        initially_associated_group_ids: list[ProjectID]
        available_group_ids: list[ProjectID]

    @pytest.fixture
    async def registry_with_partial_groups(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_domain: DomainFixtureData
    ) -> _RegistryWithPartialGroups:
        """Pre-created registry with 2 out of 4 groups associated."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]
        resource_policy_name = f"test-policy-{sample_domain.domain_name}-4groups"
        group_ids: list[ProjectID] = []

        async with db_with_cleanup.begin_session() as session:
            # Create registry
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.flush()
            session.add(
                VirtualEntityRow(entity_type=ContainerRegistryEntityType(), entity_id=registry.id)
            )

            # Create resource policies
            user_policy = UserResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(user_policy)

            project_policy = ProjectResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_policy)

            # Create 4 groups
            for i in range(4):
                group = ProjectRow(
                    name=f"test-group-{i}-{sample_domain.domain_name}-partial",
                    domain_name=sample_domain.domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=resource_policy_name,
                )
                session.add(group)
                await session.flush()
                session.add(VirtualEntityRow(entity_type=ProjectEntityType(), entity_id=group.id))
                group_ids.append(group.id)

            # Associate first 2 groups with the registry
            for gid in group_ids[:2]:
                assoc = AssociationContainerRegistriesGroupsRow()
                assoc.registry_id = registry.id
                assoc.group_id = gid
                session.add(assoc)

            await session.commit()
            await session.refresh(registry)
            return self._RegistryWithPartialGroups(
                registry=ContainerRegistrySearchableFields.own.to_data(registry),
                all_group_ids=group_ids,
                initially_associated_group_ids=group_ids[:2],
                available_group_ids=group_ids[2:],
            )

    async def test_link_and_unlink_projects_in_one_pass(
        self,
        relation_repository: RbacRelationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_with_partial_groups: _RegistryWithPartialGroups,
    ) -> None:
        """Links and unlinks made one pair at a time leave the expected set."""
        # Given - Registry has groups 0 and 1 associated
        group_ids = registry_with_partial_groups.all_group_ids
        registry_id = ContainerRegistryID(registry_with_partial_groups.registry.id)

        # When - Remove group 0, add group 2, 3
        await relation_repository.purge(
            [(group_ids[0], registry_id)], ContainerRegistryProjectPurger()
        )
        for group_id in group_ids[2:]:
            await relation_repository.create(
                [(group_id, registry_id)], ContainerRegistryProjectCreator()
            )

        # Then - Verify group 0 removed, groups 2,3 added, group 1 remains
        async with db_with_cleanup.begin_readonly_session() as session:
            associations = (
                (
                    await session.execute(
                        sa.select(AssociationContainerRegistriesGroupsRow).where(
                            AssociationContainerRegistriesGroupsRow.registry_id
                            == registry_with_partial_groups.registry.id
                        )
                    )
                )
                .scalars()
                .all()
            )

            assert len(associations) == 3
            assert {a.group_id for a in associations} == {
                group_ids[1],
                group_ids[2],
                group_ids[3],
            }

    async def test_unlink_a_project_that_was_never_linked(
        self, relation_repository: RbacRelationRepository, sample_registry: ContainerRegistryData
    ) -> None:
        """Unlinking a pair that was never linked answers False and raises nothing.

        Turning that into an error is the adapter's, which counts what it unlinked
        across the projects one request named."""
        unlinked = await relation_repository.purge(
            [
                (
                    ProjectID(uuid.UUID("00000000-0000-0000-0000-000000000000")),
                    ContainerRegistryID(sample_registry.id),
                )
            ],
            ContainerRegistryProjectPurger(),
        )
        assert unlinked == [False]

    async def test_link_a_project_already_linked_is_skipped(
        self,
        relation_repository: RbacRelationRepository,
        registry_with_partial_groups: _RegistryWithPartialGroups,
    ) -> None:
        """A project already allowed is left as it stands, so one request may name it
        beside a new one and the answer says which of the two landed."""
        group_ids = registry_with_partial_groups.all_group_ids
        registry_id = ContainerRegistryID(registry_with_partial_groups.registry.id)
        written = await relation_repository.create(
            [(group_ids[0], registry_id), (group_ids[2], registry_id)],
            ContainerRegistryProjectCreator(),
        )
        assert written == [False, True]

    async def test_link_a_project_that_is_not_there(
        self,
        relation_repository: RbacRelationRepository,
        registry_with_partial_groups: _RegistryWithPartialGroups,
    ) -> None:
        """A project id naming no project is refused rather than left to the foreign
        key."""
        registry_id = ContainerRegistryID(registry_with_partial_groups.registry.id)
        with pytest.raises(ProjectNotFound):
            await relation_repository.create(
                [(ProjectID(uuid.uuid4()), registry_id)], ContainerRegistryProjectCreator()
            )

    async def test_set_global_keeps_project_relations(
        self,
        repository: ContainerRegistryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_with_associated_groups: _RegistryWithGroups,
    ) -> None:
        """Switching the registry into public does not touch its project relations."""
        registry_id = registry_with_associated_groups.registry.id

        result = await repository.set_global(
            ContainerRegistryGlobalUpdater(
                registry_id=ContainerRegistryID(registry_id),
                is_global=True,
            )
        )

        assert result is not None
        assert result.is_global is True
        async with db_with_cleanup.begin_readonly_session() as session:
            linked = (
                await session.scalars(
                    sa.select(AssociationContainerRegistriesGroupsRow.group_id).where(
                        AssociationContainerRegistriesGroupsRow.registry_id == registry_id
                    )
                )
            ).all()
            assert set(linked) == set(registry_with_associated_groups.group_ids)

    async def test_allowed_project_reads_the_registry_and_is_read_by_it(
        self,
        relation_repository: RbacRelationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_and_groups_for_adding: _RegistryWithAvailableGroups,
    ) -> None:
        """The relation: the project governs the registry under READ, and the registry
        holds the project under a READ share."""
        registry_id = ContainerRegistryID(registry_and_groups_for_adding.registry.id)
        project_id = registry_and_groups_for_adding.group_ids[0]
        await relation_repository.create(
            [(project_id, registry_id)], ContainerRegistryProjectCreator()
        )

        assert await self._govern_cap(db_with_cleanup, project_id, registry_id) == Permission.READ
        assert await self._share_cap(db_with_cleanup, registry_id, project_id) == Permission.READ

        await relation_repository.purge(
            [(project_id, registry_id)], ContainerRegistryProjectPurger()
        )

        assert await self._govern_cap(db_with_cleanup, project_id, registry_id) is None
        assert await self._share_cap(db_with_cleanup, registry_id, project_id) is None

    def _node(self, entity: EntityIdentifier) -> sa.ScalarSelect[Any]:
        return (
            sa.select(VirtualEntityRow.id)
            .where(
                VirtualEntityRow.entity_type == entity.entity_type(),
                VirtualEntityRow.entity_id == entity,
            )
            .scalar_subquery()
        )

    async def _govern_cap(
        self, db: ExtendedAsyncSAEngine, scope: EntityIdentifier, entity: EntityIdentifier
    ) -> Permission | None:
        """The cap the scope governs the entity under; ``None`` when it does not."""
        async with db.begin_readonly_session() as session:
            return await session.scalar(
                sa.select(ScopeBindingRow.permission_cap).where(
                    ScopeBindingRow.virtual_entity_id == self._node(entity),
                    ScopeBindingRow.scope_entity_id == self._node(scope),
                )
            )

    async def _share_cap(
        self, db: ExtendedAsyncSAEngine, scope: EntityIdentifier, member: EntityIdentifier
    ) -> Permission | None:
        """The bits the scope holds the member under; ``None`` when it does not."""
        async with db.begin_readonly_session() as session:
            membership_id = await session.scalar(
                sa.select(EntityMembershipRow.id).where(
                    EntityMembershipRow.virtual_entity_id == self._node(scope),
                    EntityMembershipRow.member_entity_id == self._node(member),
                )
            )
            if membership_id is None:
                return None
            cap = Permission.NONE
            for bit in await session.scalars(
                sa.select(EntityMembershipCapRow.permission).where(
                    EntityMembershipCapRow.membership_id == membership_id
                )
            ):
                cap |= bit
            return cap

    async def test_delete_registry_takes_its_project_relations_with_it(
        self,
        repository: ContainerRegistryRepository,
        relation_repository: RbacRelationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_with_associated_groups: _RegistryWithGroups,
    ) -> None:
        """Deleting the registry takes the association rows and what each side read of
        the other: the foreign key removes the rows, and the registry's node going takes
        the edges naming it."""
        registry_id = ContainerRegistryID(registry_with_associated_groups.registry.id)
        project_id = registry_with_associated_groups.group_ids[0]
        await relation_repository.purge(
            [(project_id, registry_id)], ContainerRegistryProjectPurger()
        )
        await relation_repository.create(
            [(project_id, registry_id)], ContainerRegistryProjectCreator()
        )
        assert await self._govern_cap(db_with_cleanup, project_id, registry_id) == Permission.READ

        await repository.delete_registry(ContainerRegistryPurger(registry_id=registry_id))

        async with db_with_cleanup.begin_readonly_session() as session:
            left = await session.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationContainerRegistriesGroupsRow)
                .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
            )
            assert left == 0
        assert await self._govern_cap(db_with_cleanup, project_id, registry_id) is None
        assert await self._share_cap(db_with_cleanup, registry_id, project_id) is None

    async def test_delete_registry_success(
        self,
        repository: ContainerRegistryRepository,
        test_registry: ContainerRegistryData,
    ) -> None:
        """Test successful registry deletion"""
        # Given: A pre-created test registry
        registry_id = ContainerRegistryID(test_registry.id)
        registry_name = test_registry.registry_name

        # When: Delete the registry
        purger = ContainerRegistryPurger(registry_id=registry_id)
        result = await repository.delete_registry(purger)

        # Then: Returns deleted registry data
        assert result.id == registry_id
        assert result.registry_name == registry_name

        # And: Registry no longer exists
        with pytest.raises(ContainerRegistryNotFound):
            purger = ContainerRegistryPurger(registry_id=registry_id)
            await repository.delete_registry(purger)

    async def test_delete_registry_not_found(
        self,
        repository: ContainerRegistryRepository,
    ) -> None:
        """Test deletion of non-existent registry raises error"""
        # Given: Non-existent registry ID
        non_existent_id = ContainerRegistryID(uuid.uuid4())

        # When/Then: Raises ContainerRegistryNotFound
        with pytest.raises(ContainerRegistryNotFound):
            purger = ContainerRegistryPurger(registry_id=non_existent_id)
            await repository.delete_registry(purger)

    async def test_delete_registry_returns_data_before_deletion(
        self,
        repository: ContainerRegistryRepository,
        test_registry_with_custom_props: ContainerRegistryData,
    ) -> None:
        """Test that delete_registry returns complete data before deletion"""
        # Given: A registry with custom properties
        registry = test_registry_with_custom_props

        # When: Delete the registry
        purger = ContainerRegistryPurger(registry_id=ContainerRegistryID(registry.id))
        result = await repository.delete_registry(purger)

        # Then: Returns all registry data with correct properties
        assert result.id == registry.id
        assert result.registry_name == "test-registry"
        assert result.project == "test-project"
        assert result.username == "test-user"
        assert result.password == "test-pass"
        assert result.ssl_verify is False
        assert result.is_global is False


class TestContainerRegistryPublicMembership:
    """A global registry and the images it owns belong to the `public` scope, and a
    switch moves them in or out."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        global_entity_ids: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            global_entity_ids,
            [
                ImageRow,
                ContainerRegistryRow,
                VirtualEntityRow,
                ScopeBindingRow,
                EntityLabelRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                EntityMembershipFieldRow,
                EntityShareRow,
            ],
        ):
            yield global_entity_ids

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ContainerRegistryRepository:
        return ContainerRegistryRepository(
            db=db_with_cleanup, ops_provider=ShareOpsProvider(db_with_cleanup)
        )

    def _creator(self, *, is_global: bool | None) -> ContainerRegistryCreator:
        name = f"{uuid.uuid4().hex[:8]}.example.com"
        return ContainerRegistryCreator(
            url=f"https://{name}",
            type=ContainerRegistryType.HARBOR2,
            registry_name=name,
            project="stable",
            is_global=is_global,
        )

    async def _add_image(
        self, db: ExtendedAsyncSAEngine, registry: ContainerRegistryData, *, in_public: bool
    ) -> ImageID:
        """An image written the way the scan path writes one."""
        tag = uuid.uuid4().hex[:8]
        async with db.begin_session() as session:
            ops = V2ShareWriteOps(session)
            data = await ops.create_entity(
                ImageCreator(
                    name=f"{registry.registry_name}/stable/python:{tag}",
                    project="stable",
                    architecture="x86_64",
                    registry_id=ContainerRegistryID(registry.id),
                    registry=registry.registry_name,
                    image="python",
                    tag=tag,
                    config_digest=f"sha256:{uuid.uuid4().hex}",
                    size_bytes=1024,
                    type=ImageType.COMPUTE,
                    status=ImageStatus.ALIVE,
                    labels={},
                    registry_is_global=in_public,
                )
            )
        return ImageID(data.id)

    async def _in_public(self, db: ExtendedAsyncSAEngine, entity: EntityIdentifier) -> bool:
        """Whether `public` both owns and governs the entity."""
        public = global_entity_id(GlobalEntityName.PUBLIC)
        node = (
            sa.select(VirtualEntityRow.id)
            .where(
                VirtualEntityRow.entity_type == entity.entity_type(),
                VirtualEntityRow.entity_id == entity,
            )
            .scalar_subquery()
        )
        public_node = (
            sa.select(VirtualEntityRow.id)
            .where(
                VirtualEntityRow.entity_type == "global",
                VirtualEntityRow.entity_id == public,
            )
            .scalar_subquery()
        )
        async with db.begin_readonly_session() as session:
            owned = await session.scalar(
                sa.select(EntityMembershipRow.id).where(
                    EntityMembershipRow.virtual_entity_id == public_node,
                    EntityMembershipRow.member_entity_id == node,
                    EntityMembershipRow.capped.is_(False),
                )
            )
            governed = await session.scalar(
                sa.select(ScopeBindingRow.virtual_entity_id).where(
                    ScopeBindingRow.virtual_entity_id == node,
                    ScopeBindingRow.scope_entity_id == public_node,
                )
            )
        return owned is not None and governed is not None

    async def test_a_global_registry_is_created_in_public(
        self, repository: ContainerRegistryRepository, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        registry = await repository.create_registry(self._creator(is_global=True))

        assert await self._in_public(db_with_cleanup, ContainerRegistryID(registry.id))

    async def test_a_registry_created_without_the_column_is_global(
        self, repository: ContainerRegistryRepository, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        """The column defaults to true, so the row and its scopes have to agree."""
        registry = await repository.create_registry(self._creator(is_global=None))

        assert registry.is_global is True
        assert await self._in_public(db_with_cleanup, ContainerRegistryID(registry.id))

    async def test_a_project_registry_is_not_created_in_public(
        self, repository: ContainerRegistryRepository, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        registry = await repository.create_registry(self._creator(is_global=False))

        assert not await self._in_public(db_with_cleanup, ContainerRegistryID(registry.id))

    async def test_switching_it_on_takes_the_registry_and_its_images_in(
        self, repository: ContainerRegistryRepository, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        registry = await repository.create_registry(self._creator(is_global=False))
        image_ids = [
            await self._add_image(db_with_cleanup, registry, in_public=False) for _ in range(2)
        ]

        await repository.set_global(
            ContainerRegistryGlobalUpdater(
                registry_id=ContainerRegistryID(registry.id), is_global=True
            )
        )

        assert await self._in_public(db_with_cleanup, ContainerRegistryID(registry.id))
        for image_id in image_ids:
            assert await self._in_public(db_with_cleanup, image_id)

    async def test_switching_it_off_takes_the_registry_and_its_images_out(
        self, repository: ContainerRegistryRepository, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        registry = await repository.create_registry(self._creator(is_global=True))
        image_ids = [
            await self._add_image(db_with_cleanup, registry, in_public=True) for _ in range(2)
        ]

        await repository.set_global(
            ContainerRegistryGlobalUpdater(
                registry_id=ContainerRegistryID(registry.id), is_global=False
            )
        )

        assert not await self._in_public(db_with_cleanup, ContainerRegistryID(registry.id))
        for image_id in image_ids:
            assert not await self._in_public(db_with_cleanup, image_id)

    async def test_switching_it_on_twice_leaves_the_same_edges(
        self, repository: ContainerRegistryRepository, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        """A run that stopped part way is finished by repeating the call."""
        registry = await repository.create_registry(self._creator(is_global=False))
        image_id = await self._add_image(db_with_cleanup, registry, in_public=False)
        updater = ContainerRegistryGlobalUpdater(
            registry_id=ContainerRegistryID(registry.id), is_global=True
        )

        await repository.set_global(updater)
        await repository.set_global(updater)

        assert await self._in_public(db_with_cleanup, image_id)

    async def test_an_image_of_a_project_registry_stays_out_when_another_is_switched(
        self, repository: ContainerRegistryRepository, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        switched = await repository.create_registry(self._creator(is_global=False))
        other = await repository.create_registry(self._creator(is_global=False))
        untouched = await self._add_image(db_with_cleanup, other, in_public=False)

        await repository.set_global(
            ContainerRegistryGlobalUpdater(
                registry_id=ContainerRegistryID(switched.id), is_global=True
            )
        )

        assert not await self._in_public(db_with_cleanup, untouched)


class TestSearchContainerRegistries:
    """Integration tests for search_container_registries repository method."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        global_entity_ids: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            global_entity_ids,
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
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
            ],
        ):
            yield global_entity_ids

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ContainerRegistryRepository:
        return ContainerRegistryRepository(
            db=db_with_cleanup, ops_provider=ShareOpsProvider(db_with_cleanup)
        )

    @pytest.fixture
    async def sample_registries(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> list[ContainerRegistryData]:
        """Create 4 container registries with different types for testing."""
        registries: list[ContainerRegistryData] = []
        configs = [
            (ContainerRegistryType.DOCKER, "docker-reg", "project-a"),
            (ContainerRegistryType.DOCKER, "docker-reg-2", "project-b"),
            (ContainerRegistryType.HARBOR2, "harbor-reg", "harbor-project"),
            (ContainerRegistryType.GITHUB, "ghcr-reg", "ghcr-project"),
        ]
        async with db_with_cleanup.begin_session() as session:
            for reg_type, reg_name, project in configs:
                row = ContainerRegistryRow(
                    id=ContainerRegistryID(uuid.uuid4()),
                    url=f"https://{reg_name}.example.com",
                    registry_name=reg_name,
                    type=reg_type,
                    project=project,
                )
                session.add(row)
                await session.flush()
                registries.append(ContainerRegistrySearchableFields.own.to_data(row))
            await session.commit()
        return registries

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    # =========================================================================
    # Tests - Empty results
    # =========================================================================
