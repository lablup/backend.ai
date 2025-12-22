from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Optional
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
    def repository(self, database_engine: ExtendedAsyncSAEngine) -> ContainerRegistryRepository:
        """Create ContainerRegistryRepository instance with real database"""
        return ContainerRegistryRepository(db=database_engine)

    @pytest.fixture
    def admin_repository(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AdminContainerRegistryRepository:
        """Create AdminContainerRegistryRepository instance with real database"""
        return AdminContainerRegistryRepository(db=database_engine)

    @pytest.fixture
    async def test_registry_factory(self, database_engine: ExtendedAsyncSAEngine):
        """Factory fixture for creating test registries with automatic cleanup."""
        created_registries: list[tuple[str, str]] = []

        @asynccontextmanager
        async def _create_registry(
            registry_name: Optional[str] = None,
            project: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            ssl_verify: bool = True,
            is_global: bool = True,
            extra: Optional[dict[str, str]] = None,
        ) -> AsyncGenerator[ContainerRegistryData, None]:
            """Create a test container registry with random names and ensure cleanup."""
            if registry_name is None:
                registry_name = str(uuid.uuid4())[:8] + ".example.com"
            if project is None:
                project = "project-" + str(uuid.uuid4())[:8]

            async with database_engine.begin_session() as session:
                registry = ContainerRegistryRow(
                    id=uuid.uuid4(),
                    url=f"https://{registry_name}",
                    registry_name=registry_name,
                    type=ContainerRegistryType.HARBOR2,
                    project=project,
                    username=username,
                    password=password,
                    ssl_verify=ssl_verify,
                    is_global=is_global,
                    extra=extra,
                )
                session.add(registry)
                await session.flush()

                registry_data = registry.to_dataclass()
                created_registries.append((registry_name, project))

            try:
                yield registry_data
            finally:
                pass  # Cleanup handled in teardown

        yield _create_registry

        # Cleanup all created registries
        async with database_engine.begin_session() as session:
            for registry_name, project in created_registries:
                await session.execute(
                    sa.delete(ImageRow).where(
                        (ImageRow.registry == registry_name)
                        & (ImageRow.project == project if project else sa.true())
                    )
                )
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(
                        (ContainerRegistryRow.registry_name == registry_name)
                        & (ContainerRegistryRow.project == project if project else sa.true())
                    )
                )

    @pytest.fixture
    async def test_image_factory(self, database_engine: ExtendedAsyncSAEngine):
        """Factory fixture for creating test images with automatic cleanup."""
        created_image_ids: list[UUID] = []

        async def _create_image(
            registry_id: UUID,
            registry_name: str,
            project: Optional[str] = None,
            image_name: Optional[str] = None,
            status: ImageStatus = ImageStatus.ALIVE,
        ) -> UUID:
            """Create a test image for the registry with random names."""
            if project is None:
                project = "project-" + str(uuid.uuid4())[:8]
            if image_name is None:
                image_name = "image-" + str(uuid.uuid4())[:8]

            async with database_engine.begin_session() as session:
                image = ImageRow(
                    name=f"{registry_name}/{project or 'library'}/{image_name}:latest",
                    registry=registry_name,
                    registry_id=registry_id,
                    project=project,
                    image=image_name,
                    tag="latest",
                    architecture="x86_64",
                    is_local=False,
                    type=ImageType.COMPUTE,
                    config_digest="sha256:test",
                    size_bytes=1024 * 1024,  # 1MB
                    accelerators=None,
                    resources={},
                    labels={},
                    status=status,
                )
                session.add(image)
                await session.flush()
                created_image_ids.append(image.id)

            return image.id

        yield _create_image

        # Cleanup all created images
        async with database_engine.begin_session() as session:
            if created_image_ids:
                await session.execute(sa.delete(ImageRow).where(ImageRow.id.in_(created_image_ids)))

    @pytest.fixture
    async def test_groups_factory(self, database_engine: ExtendedAsyncSAEngine):
        """Factory fixture for creating test groups with automatic cleanup."""
        created_resources: list[tuple[str, list[UUID]]] = []

        @asynccontextmanager
        async def _create_groups(
            domain_name: Optional[str] = None, group_count: int = 2
        ) -> AsyncGenerator[list[UUID], None]:
            """Create test groups for allowed_groups testing."""
            if domain_name is None:
                domain_name = "test-domain-" + str(uuid.uuid4())[:8]

            resource_policy_name = f"test-policy-{domain_name}"
            group_ids: list[UUID] = []

            async with database_engine.begin_session() as session:
                # Create domain
                domain = DomainRow(name=domain_name, total_resource_slots={})
                session.add(domain)

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

                # Create groups
                for i in range(group_count):
                    group = GroupRow(
                        name=f"test-group-{i}-{domain_name}",
                        domain_name=domain_name,
                        total_resource_slots={},
                        resource_policy=resource_policy_name,
                    )
                    session.add(group)
                    await session.flush()
                    group_ids.append(group.id)

            created_resources.append((domain_name, group_ids))

            try:
                yield group_ids
            finally:
                pass  # Cleanup handled in teardown

        yield _create_groups

        # Cleanup all created resources
        for domain_name, group_ids in created_resources:
            resource_policy_name = f"test-policy-{domain_name}"
            async with database_engine.begin_session() as session:
                await session.execute(sa.delete(GroupRow).where(GroupRow.id.in_(group_ids)))
                await session.execute(
                    sa.delete(ProjectResourcePolicyRow).where(
                        ProjectResourcePolicyRow.name == resource_policy_name
                    )
                )
                await session.execute(
                    sa.delete(UserResourcePolicyRow).where(
                        UserResourcePolicyRow.name == resource_policy_name
                    )
                )
                await session.execute(sa.delete(DomainRow).where(DomainRow.name == domain_name))

    @pytest.fixture
    async def test_registry(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ContainerRegistryData, None]:
        """Fixture that provides a pre-created test registry with cleanup."""
        registry_name = str(uuid.uuid4())[:8] + ".example.com"
        project = "project-" + str(uuid.uuid4())[:8]

        async with database_engine.begin_session() as session:
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
            )
            session.add(registry)
            await session.flush()
            await session.refresh(registry)  # Ensure all attributes are loaded
            registry_data = registry.to_dataclass()

        try:
            yield registry_data
        finally:
            # Cleanup: attempt to delete registry if it still exists
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(
                        ContainerRegistryRow.id == registry_data.id
                    )
                )

    @pytest.fixture
    async def test_registry_with_custom_props(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ContainerRegistryData, None]:
        """Fixture that provides a registry with custom properties for detailed testing."""
        registry_name = "test-registry"
        project = "test-project"

        async with database_engine.begin_session() as session:
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
            await session.flush()
            await session.refresh(registry)  # Ensure all attributes are loaded
            registry_data = registry.to_dataclass()

        try:
            yield registry_data
        finally:
            # Cleanup: attempt to delete registry if it still exists
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(
                        ContainerRegistryRow.id == registry_data.id
                    )
                )

    @pytest.fixture
    async def sample_registry(
        self, test_registry_factory
    ) -> AsyncGenerator[ContainerRegistryData, None]:
        """Pre-created single registry for simple tests."""
        async with test_registry_factory() as registry:
            yield registry

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
        self, test_registry_factory
    ) -> AsyncGenerator[_TwoRegistries, None]:
        """Pre-created two registries with the same name but different projects."""
        registry_name = "test-registry-" + str(uuid.uuid4())[:8] + ".example.com"
        async with test_registry_factory(registry_name=registry_name) as registry1:
            async with test_registry_factory(registry_name=registry_name) as registry2:
                yield _TwoRegistries(registry1=registry1, registry2=registry2)

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
        self, test_registry_factory
    ) -> AsyncGenerator[_TwoRegistries, None]:
        """Pre-created two registries with different names."""
        async with test_registry_factory() as registry1:
            async with test_registry_factory() as registry2:
                yield _TwoRegistries(registry1=registry1, registry2=registry2)

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
        self, test_registry_factory, test_image_factory
    ) -> AsyncGenerator[_RegistryWithImages, None]:
        """Pre-created registry with 2 images."""
        async with test_registry_factory() as registry:
            image_id1 = await test_image_factory(
                registry_id=registry.id,
                registry_name=registry.registry_name,
                project=registry.project,
            )
            image_id2 = await test_image_factory(
                registry_id=registry.id,
                registry_name=registry.registry_name,
                project=registry.project,
            )
            yield _RegistryWithImages(registry=registry, image_ids=[image_id1, image_id2])

    @pytest.mark.asyncio
    async def test_clear_images(
        self,
        repository: ContainerRegistryRepository,
        database_engine: ExtendedAsyncSAEngine,
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
        async with database_engine.begin_readonly_session() as session:
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
        self, test_registry_factory, test_image_factory
    ) -> AsyncGenerator[_TwoRegistriesWithImages, None]:
        """Pre-created two registries (same name, different projects) each with one image."""
        registry_name = "test-registry-" + str(uuid.uuid4())[:8] + ".example.com"
        async with test_registry_factory(registry_name=registry_name) as registry1:
            async with test_registry_factory(registry_name=registry_name) as registry2:
                image_id1 = await test_image_factory(
                    registry_id=registry1.id,
                    registry_name=registry1.registry_name,
                    project=registry1.project,
                )
                image_id2 = await test_image_factory(
                    registry_id=registry2.id,
                    registry_name=registry2.registry_name,
                    project=registry2.project,
                )
                yield _TwoRegistriesWithImages(
                    registry1=registry1,
                    image1_id=image_id1,
                    registry2=registry2,
                    image2_id=image_id2,
                )

    @pytest.mark.asyncio
    async def test_clear_images_with_project_filter(
        self,
        repository: ContainerRegistryRepository,
        database_engine: ExtendedAsyncSAEngine,
        two_registries_with_images: _TwoRegistriesWithImages,
    ) -> None:
        """Test clearing images with project filter doesn't affect other projects"""
        reg1 = two_registries_with_images.registry1
        img1_id = two_registries_with_images.image1_id
        img2_id = two_registries_with_images.image2_id

        # When - Clear images only for project1
        await repository.clear_images(reg1.registry_name, reg1.project)

        # Then - Verify only project1 images are deleted
        async with database_engine.begin_readonly_session() as session:
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
        self, test_registry_factory
    ) -> AsyncGenerator[ContainerRegistryData, None]:
        """Pre-created registry with specific initial values for modification testing."""
        async with test_registry_factory(
            username="initial-user",
            password="initial-password",
            ssl_verify=False,
            extra={"initial_key": "initial_value"},
        ) as registry:
            yield registry

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
        self, test_registry_factory, test_groups_factory, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[_RegistryWithAvailableGroups, None]:
        """Pre-created registry and groups for testing adding allowed_groups."""
        async with test_registry_factory() as registry:
            async with test_groups_factory(group_count=2) as group_ids:
                yield self._RegistryWithAvailableGroups(registry=registry, group_ids=group_ids)
                # Cleanup associations
                async with database_engine.begin_session() as session:
                    await session.execute(
                        sa.delete(AssociationContainerRegistriesGroupsRow).where(
                            AssociationContainerRegistriesGroupsRow.group_id.in_(group_ids)
                        )
                    )

    @pytest.mark.asyncio
    async def test_modify_registry_add_allowed_groups(
        self,
        repository: ContainerRegistryRepository,
        database_engine: ExtendedAsyncSAEngine,
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
        async with database_engine.begin_readonly_session() as session:
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
        self, test_registry_factory, test_groups_factory, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[_RegistryWithGroups, None]:
        """Pre-created registry with 3 groups already associated."""
        async with test_registry_factory() as registry:
            async with test_groups_factory(group_count=3) as group_ids:
                # Associate all groups with the registry
                async with database_engine.begin_session() as session:
                    for gid in group_ids:
                        assoc = AssociationContainerRegistriesGroupsRow()
                        assoc.registry_id = registry.id
                        assoc.group_id = gid
                        session.add(assoc)

                yield _RegistryWithGroups(registry=registry, group_ids=group_ids)

    @pytest.mark.asyncio
    async def test_modify_registry_remove_allowed_groups(
        self,
        repository: ContainerRegistryRepository,
        database_engine: ExtendedAsyncSAEngine,
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
        async with database_engine.begin_readonly_session() as session:
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
        self, test_registry_factory, test_groups_factory, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[_RegistryWithPartialGroups, None]:
        """Pre-created registry with 2 out of 4 groups associated."""
        async with test_registry_factory() as registry:
            async with test_groups_factory(group_count=4) as group_ids:
                # Associate first 2 groups with the registry
                async with database_engine.begin_session() as session:
                    for gid in group_ids[:2]:
                        assoc = AssociationContainerRegistriesGroupsRow()
                        assoc.registry_id = registry.id
                        assoc.group_id = gid
                        session.add(assoc)

                yield self._RegistryWithPartialGroups(
                    registry=registry,
                    all_group_ids=group_ids,
                    initially_associated_group_ids=group_ids[:2],
                    available_group_ids=group_ids[2:],
                )

    @pytest.mark.asyncio
    async def test_modify_registry_add_and_remove_allowed_groups(
        self,
        repository: ContainerRegistryRepository,
        database_engine: ExtendedAsyncSAEngine,
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
        async with database_engine.begin_readonly_session() as session:
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
        database_engine: ExtendedAsyncSAEngine,
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
