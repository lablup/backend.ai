from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.exception import ContainerRegistryGroupsAlreadyAssociated
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.errors.image import (
    ContainerRegistryGroupsAssociationNotFound,
    ContainerRegistryNotFound,
)
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.updaters import (
    ContainerRegistryUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables


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
    group_ids: list[UUID]


class TestContainerRegistryRepository:
    """Integration tests for ContainerRegistryRepository using real database"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                GroupRow,
                ContainerRegistryRow,
                ImageRow,
                AssociationContainerRegistriesGroupsRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ContainerRegistryRepository:
        """Create ContainerRegistryRepository instance with real database"""
        return ContainerRegistryRepository(db=db_with_cleanup)

    @pytest.fixture
    def admin_repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AdminContainerRegistryRepository:
        """Create AdminContainerRegistryRepository instance with real database"""
        return AdminContainerRegistryRepository(db=db_with_cleanup)

    @pytest.fixture
    async def sample_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Pre-created domain for group tests. Returns domain name."""
        domain_name = "test-domain-" + str(uuid.uuid4())[:8]
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(name=domain_name, total_resource_slots={})
            session.add(domain)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def sample_groups(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_domain: str
    ) -> list[UUID]:
        """Pre-created 2 groups with required policies. Depends on sample_domain."""
        resource_policy_name = f"test-policy-{sample_domain}"
        group_ids: list[UUID] = []

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
                group = GroupRow(
                    name=f"test-group-{i}-{sample_domain}",
                    domain_name=sample_domain,
                    total_resource_slots={},
                    resource_policy=resource_policy_name,
                )
                session.add(group)
                await session.flush()
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
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.commit()
            await session.refresh(registry)  # Ensure all attributes are loaded
            registry_data = registry.to_dataclass()

        return registry_data

    @pytest.fixture
    async def test_registry_with_custom_props(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> ContainerRegistryData:
        """Fixture that provides a registry with custom properties for detailed testing."""
        registry_name = "test-registry"
        project = "test-project"

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
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
            registry_data = registry.to_dataclass()

        return registry_data

    @pytest.fixture
    async def sample_registry(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> ContainerRegistryData:
        """Pre-created single registry for simple tests."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.commit()
            await session.refresh(registry)
            return registry.to_dataclass()

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project="project-" + str(uuid.uuid4())[:8],
            )
            registry2 = ContainerRegistryRow(
                id=uuid.uuid4(),
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
                registry1=registry1.to_dataclass(),
                registry2=registry2.to_dataclass(),
            )

    @pytest.mark.asyncio
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
                id=uuid.uuid4(),
                url=f"https://{registry1_name}",
                registry_name=registry1_name,
                type=ContainerRegistryType.HARBOR2,
                project="project-" + str(uuid.uuid4())[:8],
            )
            registry2 = ContainerRegistryRow(
                id=uuid.uuid4(),
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
                registry1=registry1.to_dataclass(),
                registry2=registry2.to_dataclass(),
            )

    @pytest.mark.asyncio
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
    async def sample_registry_with_images(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> _RegistryWithImages:
        """Pre-created registry with 2 images."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
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
                registry=registry.to_dataclass(),
                image_ids=[image1.id, image2.id],
            )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project1,
            )
            registry2 = ContainerRegistryRow(
                id=uuid.uuid4(),
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
                registry1=registry1.to_dataclass(),
                image1_id=image1.id,
                registry2=registry2.to_dataclass(),
                image2_id=image2.id,
            )

    @pytest.mark.asyncio
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

            assert img_p1.status == ImageStatus.DELETED
            assert img_p2.status == ImageStatus.ALIVE

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
                id=uuid.uuid4(),
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
            return registry.to_dataclass()

    @pytest.mark.asyncio
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
            Updater(
                spec=ContainerRegistryUpdaterSpec(
                    url=OptionalState.nop(),
                    type=OptionalState.nop(),
                    registry_name=OptionalState.nop(),
                    project=TriState.nop(),
                    username=TriState.update(changed_username),
                    password=TriState.update(changed_password),
                    ssl_verify=TriState.nop(),
                    is_global=TriState.nop(),
                    extra=TriState.update(changed_extra),
                    allowed_groups=TriState.nop(),
                ),
                pk_value=registry_for_modification.id,
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

    @pytest.mark.asyncio
    async def test_modify_registry_not_found(self, repository: ContainerRegistryRepository) -> None:
        """Test modifying a non-existent registry"""
        non_existent_id = UUID("00000000-0000-0000-0000-000000000000")

        # Then
        with pytest.raises(ContainerRegistryNotFound):
            await repository.modify_registry(
                Updater(
                    spec=ContainerRegistryUpdaterSpec(
                        url=OptionalState.nop(),
                        type=OptionalState.nop(),
                        registry_name=OptionalState.nop(),
                        project=TriState.nop(),
                        username=TriState.update("new-user"),
                        password=TriState.nop(),
                        ssl_verify=TriState.nop(),
                        is_global=TriState.nop(),
                        extra=TriState.nop(),
                        allowed_groups=TriState.nop(),
                    ),
                    pk_value=non_existent_id,
                )
            )

    @dataclass
    class _RegistryWithAvailableGroups:
        """Registry with available groups for adding."""

        registry: ContainerRegistryData
        group_ids: list[UUID]

    @pytest.fixture
    async def registry_and_groups_for_adding(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_groups: list[UUID]
    ) -> _RegistryWithAvailableGroups:
        """Pre-created registry and 2 groups for testing adding allowed_groups."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.commit()
            await session.refresh(registry)
            return self._RegistryWithAvailableGroups(
                registry=registry.to_dataclass(),
                group_ids=sample_groups,
            )

    @pytest.mark.asyncio
    async def test_modify_registry_add_allowed_groups(
        self,
        repository: ContainerRegistryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_and_groups_for_adding: _RegistryWithAvailableGroups,
    ) -> None:
        """Test adding allowed_groups to an existing registry"""
        # When
        result = await repository.modify_registry(
            Updater(
                spec=ContainerRegistryUpdaterSpec(
                    url=OptionalState.nop(),
                    type=OptionalState.nop(),
                    registry_name=OptionalState.nop(),
                    project=TriState.nop(),
                    username=TriState.nop(),
                    password=TriState.nop(),
                    ssl_verify=TriState.update(True),
                    is_global=TriState.nop(),
                    extra=TriState.nop(),
                    allowed_groups=TriState.update(
                        AllowedGroupsModel(
                            add=[str(g) for g in registry_and_groups_for_adding.group_ids],
                            remove=[],
                        )
                    ),
                ),
                pk_value=registry_and_groups_for_adding.registry.id,
            )
        )

        # Then
        assert result is not None

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
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_domain: str
    ) -> _RegistryWithGroups:
        """Pre-created registry with 3 groups already associated."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]
        resource_policy_name = f"test-policy-{sample_domain}-3groups"
        group_ids: list[UUID] = []

        async with db_with_cleanup.begin_session() as session:
            # Create registry
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)

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
                group = GroupRow(
                    name=f"test-group-{i}-{sample_domain}-assoc",
                    domain_name=sample_domain,
                    total_resource_slots={},
                    resource_policy=resource_policy_name,
                )
                session.add(group)
                await session.flush()
                group_ids.append(group.id)

                # Associate with registry
                assoc = AssociationContainerRegistriesGroupsRow()
                assoc.registry_id = registry.id
                assoc.group_id = group.id
                session.add(assoc)

            await session.commit()
            await session.refresh(registry)
            return _RegistryWithGroups(registry=registry.to_dataclass(), group_ids=group_ids)

    @pytest.mark.asyncio
    async def test_modify_registry_remove_allowed_groups(
        self,
        repository: ContainerRegistryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_with_associated_groups: _RegistryWithGroups,
    ) -> None:
        """Test removing allowed_groups from an existing registry"""
        # Given - Registry already has 3 groups associated
        group_count = 3

        # When - Request to remove one group
        result = await repository.modify_registry(
            Updater(
                spec=ContainerRegistryUpdaterSpec(
                    url=OptionalState.nop(),
                    type=OptionalState.nop(),
                    registry_name=OptionalState.nop(),
                    project=TriState.nop(),
                    username=TriState.nop(),
                    password=TriState.nop(),
                    ssl_verify=TriState.update(True),
                    is_global=TriState.nop(),
                    extra=TriState.nop(),
                    allowed_groups=TriState.update(
                        AllowedGroupsModel(
                            add=[], remove=[str(registry_with_associated_groups.group_ids[0])]
                        )
                    ),
                ),
                pk_value=registry_with_associated_groups.registry.id,
            )
        )

        # Then
        assert result is not None

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
        all_group_ids: list[UUID]
        initially_associated_group_ids: list[UUID]
        available_group_ids: list[UUID]

    @pytest.fixture
    async def registry_with_partial_groups(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_domain: str
    ) -> _RegistryWithPartialGroups:
        """Pre-created registry with 2 out of 4 groups associated."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]
        resource_policy_name = f"test-policy-{sample_domain}-4groups"
        group_ids: list[UUID] = []

        async with db_with_cleanup.begin_session() as session:
            # Create registry
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)

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
                group = GroupRow(
                    name=f"test-group-{i}-{sample_domain}-partial",
                    domain_name=sample_domain,
                    total_resource_slots={},
                    resource_policy=resource_policy_name,
                )
                session.add(group)
                await session.flush()
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
                registry=registry.to_dataclass(),
                all_group_ids=group_ids,
                initially_associated_group_ids=group_ids[:2],
                available_group_ids=group_ids[2:],
            )

    @pytest.mark.asyncio
    async def test_modify_registry_add_and_remove_allowed_groups(
        self,
        repository: ContainerRegistryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_with_partial_groups: _RegistryWithPartialGroups,
    ) -> None:
        """Test adding and removing allowed_groups simultaneously"""
        # Given - Registry has groups 0 and 1 associated
        group_ids = registry_with_partial_groups.all_group_ids

        # When - Remove group 0, add group 2, 3
        result = await repository.modify_registry(
            Updater(
                spec=ContainerRegistryUpdaterSpec(
                    url=OptionalState.nop(),
                    type=OptionalState.nop(),
                    registry_name=OptionalState.nop(),
                    project=TriState.nop(),
                    username=TriState.nop(),
                    password=TriState.nop(),
                    ssl_verify=TriState.update(True),
                    is_global=TriState.nop(),
                    extra=TriState.nop(),
                    allowed_groups=TriState.update(
                        AllowedGroupsModel(
                            add=[str(group_ids[2]), str(group_ids[3])],
                            remove=[str(group_ids[0])],
                        )
                    ),
                ),
                pk_value=registry_with_partial_groups.registry.id,
            )
        )

        # Then
        assert result is not None

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

    @pytest.mark.asyncio
    async def test_modify_registry_remove_nonexistent_allowed_groups(
        self, repository: ContainerRegistryRepository, sample_registry: ContainerRegistryData
    ) -> None:
        """Test removing non-existent allowed_groups raises error"""
        # Given - An updater attempting to remove a non-existent group
        updater = Updater(
            spec=ContainerRegistryUpdaterSpec(
                url=OptionalState.nop(),
                type=OptionalState.nop(),
                registry_name=OptionalState.nop(),
                project=TriState.nop(),
                username=TriState.update("user"),
                password=TriState.nop(),
                ssl_verify=TriState.nop(),
                is_global=TriState.nop(),
                extra=TriState.nop(),
                allowed_groups=TriState.update(
                    AllowedGroupsModel(add=[], remove=["00000000-0000-0000-0000-000000000000"])
                ),
            ),
            pk_value=sample_registry.id,
        )

        # Then - Should raise error for non-existent group
        with pytest.raises(ContainerRegistryGroupsAssociationNotFound):
            await repository.modify_registry(updater)

    @pytest.fixture
    async def updater_spec_with_two_duplicate_two_new_allowed_groups(
        self, registry_with_partial_groups: _RegistryWithPartialGroups
    ) -> ContainerRegistryUpdaterSpec:
        """UpdaterSpec that attempts to add duplicate allowed_groups."""
        group_ids = registry_with_partial_groups.all_group_ids
        return ContainerRegistryUpdaterSpec(
            url=OptionalState.nop(),
            type=OptionalState.nop(),
            registry_name=OptionalState.nop(),
            project=TriState.nop(),
            username=TriState.nop(),
            password=TriState.nop(),
            ssl_verify=TriState.update(True),
            is_global=TriState.nop(),
            extra=TriState.nop(),
            allowed_groups=TriState.update(
                AllowedGroupsModel(
                    add=[
                        str(group_ids[0]),  # duplicate
                        str(group_ids[1]),  # duplicate
                        str(group_ids[2]),  # new
                        str(group_ids[3]),  # new
                    ],
                    remove=[],
                )
            ),
        )

    @pytest.mark.asyncio
    async def test_modify_registry_add_duplicate_allowed_groups(
        self,
        repository: ContainerRegistryRepository,
        registry_with_partial_groups: _RegistryWithPartialGroups,
        updater_spec_with_two_duplicate_two_new_allowed_groups: ContainerRegistryUpdaterSpec,
    ) -> None:
        """Test adding duplicate allowed_groups raises ContainerRegistryGroupsAlreadyAssociated error"""
        # When - Try to add 2 duplicate, 2 new groups
        # Then - Should raise error for duplicate groups
        with pytest.raises(ContainerRegistryGroupsAlreadyAssociated):
            await repository.modify_registry(
                Updater(
                    spec=updater_spec_with_two_duplicate_two_new_allowed_groups,
                    pk_value=registry_with_partial_groups.registry.id,
                )
            )

    @pytest.mark.asyncio
    async def test_delete_registry_success(
        self,
        repository: ContainerRegistryRepository,
        test_registry: ContainerRegistryData,
    ) -> None:
        """Test successful registry deletion"""
        # Given: A pre-created test registry
        registry_id = test_registry.id
        registry_name = test_registry.registry_name

        # When: Delete the registry
        purger = Purger(row_class=ContainerRegistryRow, pk_value=registry_id)
        result = await repository.delete_registry(purger)

        # Then: Returns deleted registry data
        assert result.id == registry_id
        assert result.registry_name == registry_name

        # And: Registry no longer exists
        with pytest.raises(ContainerRegistryNotFound):
            purger = Purger(row_class=ContainerRegistryRow, pk_value=registry_id)
            await repository.delete_registry(purger)

    @pytest.mark.asyncio
    async def test_delete_registry_not_found(
        self,
        repository: ContainerRegistryRepository,
    ) -> None:
        """Test deletion of non-existent registry raises error"""
        # Given: Non-existent registry ID
        non_existent_id = uuid.uuid4()

        # When/Then: Raises ContainerRegistryNotFound
        with pytest.raises(ContainerRegistryNotFound):
            purger = Purger(row_class=ContainerRegistryRow, pk_value=non_existent_id)
            await repository.delete_registry(purger)

    @pytest.mark.asyncio
    async def test_delete_registry_returns_data_before_deletion(
        self,
        repository: ContainerRegistryRepository,
        test_registry_with_custom_props: ContainerRegistryData,
    ) -> None:
        """Test that delete_registry returns complete data before deletion"""
        # Given: A registry with custom properties
        registry = test_registry_with_custom_props

        # When: Delete the registry
        purger = Purger(row_class=ContainerRegistryRow, pk_value=registry.id)
        result = await repository.delete_registry(purger)

        # Then: Returns all registry data with correct properties
        assert result.id == registry.id
        assert result.registry_name == "test-registry"
        assert result.project == "test-project"
        assert result.username == "test-user"
        assert result.password == "test-pass"
        assert result.ssl_verify is False
        assert result.is_global is False
