"""
Tests for ContainerRegistryRepository and AdminContainerRegistryRepository functionality.
Integration tests using real database operations.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryCreator,
    ContainerRegistryData,
    ContainerRegistryLocationInfo,
    ContainerRegistryModifier,
)
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
from ai.backend.manager.repositories.base import Querier
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.options import ContainerRegistryOrders
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.types import OptionalState, TriState


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

    @asynccontextmanager
    async def create_test_registry(
        self,
        database_engine: ExtendedAsyncSAEngine,
        registry_name: str = "test-registry.example.com",
        project: str = "test-project",
        username: Optional[str] = None,
        password: Optional[str] = None,
        ssl_verify: bool = True,
        is_global: bool = True,
        extra: Optional[dict[str, str]] = None,
    ) -> AsyncGenerator[ContainerRegistryData, None]:
        """Create a test container registry and ensure cleanup"""
        async with database_engine.begin_session() as session:
            registry = ContainerRegistryRow(
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

        try:
            yield registry_data
        finally:
            async with database_engine.begin_session() as session:
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

    @asynccontextmanager
    async def create_test_images_for_registry(
        self,
        database_engine: ExtendedAsyncSAEngine,
        registry_data: ContainerRegistryData,
        image_names: list[str],
    ) -> AsyncGenerator[list[UUID], None]:
        """Create multiple test images for a registry and return their IDs"""
        image_ids = []
        for image_name in image_names:
            image_id = await self.create_test_image(
                database_engine,
                registry_data.id,
                registry_data.registry_name,
                registry_data.project,
                image_name,
                ImageStatus.ALIVE,
            )
            image_ids.append(image_id)

        try:
            yield image_ids
        finally:
            # Cleanup is handled by create_test_registry
            pass

    @asynccontextmanager
    async def create_test_groups(
        self,
        database_engine: ExtendedAsyncSAEngine,
        domain_name: str = "test-domain",
        group_count: int = 2,
    ) -> AsyncGenerator[list[UUID], None]:
        """Create test groups for allowed_groups testing"""
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

        try:
            yield group_ids
        finally:
            # Cleanup
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

    async def create_test_image(
        self,
        database_engine: ExtendedAsyncSAEngine,
        registry_id: UUID,
        registry_name: str,
        project: Optional[str] = "library",
        image_name: str = "test-image",
        status: ImageStatus = ImageStatus.ALIVE,
    ) -> UUID:
        """Create a test image for the registry"""
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

        return image.id

    @pytest.mark.asyncio
    async def test_get_by_registry_and_project_success(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test successful registry retrieval by name and project"""
        project_name = "test-project"
        registry_name = "test-registry.example.com"
        async with self.create_test_registry(
            database_engine, registry_name, project_name
        ) as registry_data:
            # When
            result = await repository.get_by_registry_and_project(registry_name, project_name)

            # Then
            assert result is not None
            assert isinstance(result, ContainerRegistryData)
            assert result.registry_name == registry_name
            assert result.project == project_name
            assert result.id == registry_data.id

    @pytest.mark.asyncio
    async def test_get_by_registry_and_project_not_found(
        self, repository: ContainerRegistryRepository
    ) -> None:
        """Test registry retrieval when registry doesn't exist"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_by_registry_and_project("non-existent", "project")

    @pytest.mark.asyncio
    async def test_get_by_registry_name(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test retrieving all registries with the same name"""
        registry_name = "test-registry.example.com"
        project1_name = "project1"
        project2_name = "project2"

        async with (
            self.create_test_registry(database_engine, registry_name, project1_name),
            self.create_test_registry(database_engine, registry_name, project2_name),
        ):
            # When
            results = await repository.get_by_registry_name(registry_name)

            # Then
            assert len(results) >= 2
            for result in results:
                assert result.registry_name == registry_name

    @pytest.mark.asyncio
    async def test_get_all(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test retrieving all registries"""
        registry1_name = "test-registry1.example.com"
        registry2_name = "test-registry2.example.com"
        project1_name = "project1"
        project2_name = "project2"

        async with (
            self.create_test_registry(database_engine, registry1_name, project1_name),
            self.create_test_registry(database_engine, registry2_name, project2_name),
        ):
            # When
            result = await repository.get_all()

            # Then
            assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_clear_images(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test clearing images for a registry"""
        registry_name = "test-registry.example.com"
        project_name = "test-project"

        async with self.create_test_registry(
            database_engine, registry_name, project_name
        ) as registry_data:
            # Create test images
            image_id1 = await self.create_test_image(
                database_engine,
                registry_data.id,
                registry_name,
                project_name,
                "image1",
            )
            image_id2 = await self.create_test_image(
                database_engine,
                registry_data.id,
                registry_name,
                project_name,
                "image2",
            )

            # When
            result = await repository.clear_images(registry_name, project_name)

            # Then
            assert result is not None
            assert result.registry_name == registry_name

            # Verify images are marked as deleted
            async with database_engine.begin_readonly_session() as session:
                images = (
                    (
                        await session.execute(
                            sa.select(ImageRow).where(ImageRow.id.in_([image_id1, image_id2]))
                        )
                    )
                    .scalars()
                    .all()
                )
                assert all(img.status == ImageStatus.DELETED for img in images)

    @pytest.mark.asyncio
    async def test_clear_images_not_found(self, repository: ContainerRegistryRepository) -> None:
        """Test clearing images when registry not found"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.clear_images("non-existent", "project")

    @pytest.mark.asyncio
    async def test_clear_images_with_project_filter(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test clearing images with project filter doesn't affect other projects"""
        registry_name = "test-registry.example.com"
        project1_name = "project1"
        project2_name = "project2"

        async with (
            self.create_test_registry(
                database_engine, registry_name, project1_name
            ) as registry_data1,
            self.create_test_registry(
                database_engine, registry_name, project2_name
            ) as registry_data2,
        ):
            # Create images in different projects
            image_id_in_project1 = await self.create_test_image(
                database_engine,
                registry_data1.id,
                registry_name,
                project1_name,
                "image1",
            )
            image_id_in_project2 = await self.create_test_image(
                database_engine,
                registry_data2.id,
                registry_name,
                project2_name,
                "image2",
            )

            # When - Clear images only for project1
            await repository.clear_images(registry_name, project1_name)

            # Then - Verify only project1 images are deleted
            async with database_engine.begin_readonly_session() as session:
                img_p1 = await session.scalar(
                    sa.select(ImageRow).where(ImageRow.id == image_id_in_project1)
                )
                img_p2 = await session.scalar(
                    sa.select(ImageRow).where(ImageRow.id == image_id_in_project2)
                )

                assert img_p1.status == ImageStatus.DELETED
                assert img_p2.status == ImageStatus.ALIVE

    @pytest.mark.asyncio
    async def test_get_registry_row_for_scanner_success(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test getting registry row for scanner"""
        registry_name = "test-registry.example.com"
        project_name = "test-project"

        async with self.create_test_registry(
            database_engine, registry_name, project_name
        ) as registry_data:
            # When
            result = await repository.get_registry_row_for_scanner(registry_name, project_name)

            # Then
            assert result is not None
            assert isinstance(result, ContainerRegistryRow)
            assert result.registry_name == registry_name
            assert result.project == project_name
            assert result.id == registry_data.id

    @pytest.mark.asyncio
    async def test_get_registry_row_for_scanner_not_found(
        self, repository: ContainerRegistryRepository
    ) -> None:
        """Test getting registry row when not found"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_registry_row_for_scanner("non-existent", "project")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "creator",
        [
            ContainerRegistryCreator(
                url="https://new-registry.example.com",
                type=ContainerRegistryType.HARBOR2,
                registry_name="new-registry.example.com",
                project="new-project",
                username="test-user",
                password="test-password",
                ssl_verify=True,
                is_global=False,
                extra={"key": "value"},
                allowed_groups=None,
            )
        ],
    )
    async def test_create_registry_success(
        self,
        repository: ContainerRegistryRepository,
        creator: ContainerRegistryCreator,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test successful registry creation"""
        # When
        try:
            result = await repository.create_registry(creator)

            # Then
            assert result is not None
            assert result.url == creator.url
            assert result.registry_name == creator.registry_name
            assert result.project == creator.project
            assert result.type == creator.type
            assert result.username == creator.username
            assert result.password == creator.password
            assert result.ssl_verify == creator.ssl_verify
            assert result.is_global == creator.is_global
            assert result.extra == creator.extra

            # Verify it was actually created in the database
            verify_result = await repository.get_by_registry_and_project(
                creator.registry_name, creator.project
            )
            assert verify_result.id == result.id
        finally:
            # Cleanup
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(
                        (ContainerRegistryRow.registry_name == creator.registry_name)
                        & (ContainerRegistryRow.project == creator.project)
                    )
                )

    @pytest.mark.asyncio
    async def test_modify_registry_success(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test successful registry modification"""
        registry_name = "modify-registry.example.com"
        project_name = "modify-project"
        username = "initial-user"
        password = "initial-password"
        ssl_verify = False
        extra = {"initial_key": "initial_value"}

        changed_username = "modified-user"
        changed_password = "modified-password"
        changed_extra = {"modified_key": "modified_value"}

        async with self.create_test_registry(
            database_engine,
            registry_name=registry_name,
            project=project_name,
            username=username,
            password=password,
            ssl_verify=ssl_verify,
            extra=extra,
        ) as registry_data:
            # When - Modify only username and password, extra
            result = await repository.modify_registry(
                registry_data.id,
                ContainerRegistryModifier(
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
            )

            # Then
            assert result is not None

            # Then - Verify unchanged fields remain the same
            assert result.id == registry_data.id
            assert result.registry_name == registry_name
            assert result.project == project_name
            assert result.ssl_verify == ssl_verify

            # Then - Verify only username and password, extra are changed
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
                non_existent_id,
                modifier=ContainerRegistryModifier(
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
            )

    @pytest.mark.asyncio
    async def test_delete_registry_success(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test successful registry deletion"""
        registry_name = "delete-registry.example.com"
        project_name = "delete-project"

        async with self.create_test_registry(
            database_engine, registry_name, project_name
        ) as registry_data:
            # When
            result = await repository.delete_registry(registry_data.id)

            # Then
            assert result is not None
            assert result.id == registry_data.id
            assert result.registry_name == registry_name
            assert result.project == project_name

            # Verify it was actually deleted
            with pytest.raises(ContainerRegistryNotFound):
                await repository.get_by_registry_and_project(registry_name, project_name)

    @pytest.mark.asyncio
    async def test_delete_registry_not_found(self, repository: ContainerRegistryRepository) -> None:
        """Test deleting a non-existent registry"""
        non_existent_id = UUID("00000000-0000-0000-0000-000000000000")

        # Then
        with pytest.raises(ContainerRegistryNotFound):
            await repository.delete_registry(non_existent_id)

    @pytest.mark.asyncio
    async def test_delete_registry_with_images(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test deleting a registry that has associated images"""
        registry_name = "delete-with-images-registry.example.com"
        project_name = "delete-with-images-project"

        async with self.create_test_registry(
            database_engine, registry_name, project_name
        ) as registry_data:
            # Create test images
            await self.create_test_image(
                database_engine,
                registry_data.id,
                registry_name,
                project_name,
                "image1",
            )
            await self.create_test_image(
                database_engine,
                registry_data.id,
                registry_name,
                project_name,
                "image2",
            )

            # When - Delete the registry
            result = await repository.delete_registry(registry_data.id)

            # Then - Registry should be deleted
            assert result is not None
            assert result.id == registry_data.id

            # Verify registry is deleted
            with pytest.raises(ContainerRegistryNotFound):
                await repository.get_by_registry_and_project(registry_name, project_name)

    @pytest.mark.asyncio
    async def test_create_registry_with_allowed_groups(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test creating a registry with allowed_groups"""
        registry_name = "test-ag-create.example.com"
        project_name = "test-project"

        async with self.create_test_groups(
            database_engine=database_engine, domain_name="test-domain-create", group_count=2
        ) as group_ids:
            try:
                result = await repository.create_registry(
                    ContainerRegistryCreator(
                        url=f"https://{registry_name}",
                        type=ContainerRegistryType.HARBOR2,
                        registry_name=registry_name,
                        project=project_name,
                        username="test-user",
                        password="test-password",
                        ssl_verify=True,
                        is_global=False,
                        extra=None,
                        allowed_groups=AllowedGroupsModel(
                            add=[str(group_ids[0]), str(group_ids[1])], remove=[]
                        ),
                    )
                )

                assert result is not None
                assert result.registry_name == registry_name

                # Verify associations were created
                async with database_engine.begin_readonly_session() as session:
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
                    assert {a.group_id for a in associations} == set(group_ids)
            finally:
                # Cleanup
                async with database_engine.begin_session() as session:
                    await session.execute(
                        sa.delete(AssociationContainerRegistriesGroupsRow).where(
                            AssociationContainerRegistriesGroupsRow.group_id.in_(group_ids)
                        )
                    )
                    await session.execute(
                        sa.delete(ContainerRegistryRow).where(
                            (ContainerRegistryRow.registry_name == registry_name)
                            & (ContainerRegistryRow.project == project_name)
                        )
                    )

    @pytest.mark.asyncio
    async def test_modify_registry_add_allowed_groups(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test adding allowed_groups to an existing registry"""
        registry_name = "test-ag-add.example.com"
        project_name = "test-project"

        async with (
            self.create_test_registry(
                database_engine, registry_name, project_name
            ) as registry_data,
            self.create_test_groups(
                database_engine=database_engine, domain_name="test-domain-add", group_count=2
            ) as group_ids,
        ):
            result = await repository.modify_registry(
                registry_data.id,
                ContainerRegistryModifier(
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
                        AllowedGroupsModel(add=[str(g) for g in group_ids], remove=[])
                    ),
                ),
            )

            assert result is not None

            async with database_engine.begin_readonly_session() as session:
                associations = (
                    (
                        await session.execute(
                            sa.select(AssociationContainerRegistriesGroupsRow).where(
                                AssociationContainerRegistriesGroupsRow.registry_id
                                == registry_data.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )

                assert len(associations) == 2
                assert {a.group_id for a in associations} == set(group_ids)

            # Cleanup
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(AssociationContainerRegistriesGroupsRow).where(
                        AssociationContainerRegistriesGroupsRow.group_id.in_(group_ids)
                    )
                )

    @pytest.mark.asyncio
    async def test_modify_registry_remove_allowed_groups(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test removing allowed_groups from an existing registry"""
        registry_name = "test-ag-remove.example.com"
        project_name = "test-project"
        group_count = 3

        async with (
            self.create_test_registry(
                database_engine, registry_name, project_name
            ) as registry_data,
            self.create_test_groups(
                database_engine=database_engine,
                domain_name="test-domain-remove",
                group_count=group_count,
            ) as group_ids,
        ):
            # Given - Add groups first
            async with database_engine.begin_session() as session:
                for gid in group_ids:
                    assoc = AssociationContainerRegistriesGroupsRow()
                    assoc.registry_id = registry_data.id
                    assoc.group_id = gid
                    session.add(assoc)

            # When - Request to remove one group
            result = await repository.modify_registry(
                registry_data.id,
                ContainerRegistryModifier(
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
                        AllowedGroupsModel(add=[], remove=[str(group_ids[0])])
                    ),
                ),
            )

            assert result is not None

            async with database_engine.begin_readonly_session() as session:
                associations = (
                    (
                        await session.execute(
                            sa.select(AssociationContainerRegistriesGroupsRow).where(
                                AssociationContainerRegistriesGroupsRow.registry_id
                                == registry_data.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )

                assert len(associations) == group_count - 1
                assert {a.group_id for a in associations} == {group_ids[1], group_ids[2]}

    @pytest.mark.asyncio
    async def test_modify_registry_add_and_remove_allowed_groups(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test adding and removing allowed_groups simultaneously"""
        registry_name = "test-ag-both.example.com"
        project_name = "test-project"

        async with (
            self.create_test_registry(
                database_engine, registry_name, project_name
            ) as registry_data,
            self.create_test_groups(
                database_engine=database_engine, domain_name="test-domain-both", group_count=4
            ) as group_ids,
        ):
            # Add group 0, 1 initially
            async with database_engine.begin_session() as session:
                for gid in group_ids[:2]:
                    assoc = AssociationContainerRegistriesGroupsRow()
                    assoc.registry_id = registry_data.id
                    assoc.group_id = gid
                    session.add(assoc)

            # When - Remove group 0, add group 2, 3
            result = await repository.modify_registry(
                registry_data.id,
                ContainerRegistryModifier(
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
            )

            assert result is not None

            async with database_engine.begin_readonly_session() as session:
                associations = (
                    (
                        await session.execute(
                            sa.select(AssociationContainerRegistriesGroupsRow).where(
                                AssociationContainerRegistriesGroupsRow.registry_id
                                == registry_data.id
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
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test removing non-existent allowed_groups raises error"""
        async with (
            self.create_test_registry(
                database_engine, "test-ag-error.example.com", "test-project"
            ) as registry_data,
        ):
            modifier = ContainerRegistryModifier(
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
            )

            with pytest.raises(ContainerRegistryGroupsAssociationNotFound):
                await repository.modify_registry(registry_data.id, modifier)

    @pytest.mark.asyncio
    async def test_fetch_known_registries_without_querier(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test fetching known registries without querier returns all registries"""
        registry1_name = "test-registry1.example.com"
        registry2_name = "test-registry2.example.com"
        project1_name = "project-a"
        project2_name = "project-b"

        async with (
            self.create_test_registry(database_engine, registry1_name, project1_name),
            self.create_test_registry(database_engine, registry2_name, project2_name),
        ):
            # When
            result = await repository.get_known_registries(querier=None)

            # Then - Should return all known registries
            assert len(result) >= 2
            assert all(isinstance(r, ContainerRegistryLocationInfo) for r in result)

            # Verify our test registries are in the results
            registry_names = {r.registry_name for r in result}
            assert registry1_name in registry_names
            assert registry2_name in registry_names

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "querier, extract_field, ascending",
        [
            # Order by project ascending
            (Querier(orders=[ContainerRegistryOrders.project(ascending=True)]), "project", True),
            # Order by project descending
            (Querier(orders=[ContainerRegistryOrders.project(ascending=False)]), "project", False),
            # Order by registry_name ascending
            (
                Querier(orders=[ContainerRegistryOrders.registry_name(ascending=True)]),
                "registry_name",
                True,
            ),
            # Order by registry_name descending
            (
                Querier(orders=[ContainerRegistryOrders.registry_name(ascending=False)]),
                "registry_name",
                False,
            ),
        ],
    )
    async def test_fetch_known_registries_with_ordering(
        self,
        repository: ContainerRegistryRepository,
        database_engine: ExtendedAsyncSAEngine,
        querier: Querier,
        extract_field: str,
        ascending: bool,
    ) -> None:
        """Test fetching known registries with different ordering options"""
        registry1_name = "registry-a.example.com"
        registry2_name = "registry-b.example.com"
        registry3_name = "registry-c.example.com"
        project1_name = "project-x"
        project2_name = "project-y"
        project3_name = "project-z"

        async with (
            self.create_test_registry(database_engine, registry1_name, project1_name),
            self.create_test_registry(database_engine, registry2_name, project2_name),
            self.create_test_registry(database_engine, registry3_name, project3_name),
        ):
            # When
            results = await repository.get_known_registries(querier=querier)

            # Then - Should return ordered results
            assert len(results) >= 3

            # Verify ordering
            field_values = [getattr(result, extract_field) for result in results]

            if ascending:
                assert field_values == sorted(field_values)
            else:
                assert field_values == sorted(field_values, reverse=True)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "querier,expected_projects,expected_registries",
        [
            # project -> registry_name: same registry appears in order of projects
            (
                Querier(
                    orders=[
                        ContainerRegistryOrders.project(ascending=True),
                        ContainerRegistryOrders.registry_name(ascending=True),
                    ]
                ),
                ["project-a", "project-b", "project-c"],
                [
                    "registry-same.example.com",
                    "registry-same.example.com",
                    "registry-diff.example.com",
                ],
            ),
            # registry_name -> project: same registry groups together, then different
            (
                Querier(
                    orders=[
                        ContainerRegistryOrders.registry_name(ascending=True),
                        ContainerRegistryOrders.project(ascending=True),
                    ]
                ),
                ["project-c", "project-a", "project-b"],
                [
                    "registry-diff.example.com",
                    "registry-same.example.com",
                    "registry-same.example.com",
                ],
            ),
        ],
    )
    async def test_fetch_known_registries_with_multiple_ordering(
        self,
        repository: ContainerRegistryRepository,
        database_engine: ExtendedAsyncSAEngine,
        querier: Querier,
        expected_projects: list[str],
        expected_registries: list[str],
    ) -> None:
        """Test fetching known registries with multiple order conditions"""
        # Create registries: same registry_name (2), different registry_name (1), all different projects
        same_registry_name = "registry-same.example.com"
        diff_registry_name = "registry-diff.example.com"
        project1_name = "project-a"
        project2_name = "project-b"
        project3_name = "project-c"

        async with (
            self.create_test_registry(database_engine, same_registry_name, project1_name),
            self.create_test_registry(database_engine, same_registry_name, project2_name),
            self.create_test_registry(database_engine, diff_registry_name, project3_name),
        ):
            # When
            result = await repository.get_known_registries(querier=querier)

            # Then - Should return ordered results
            assert len(result) >= 3
            assert all(isinstance(r, ContainerRegistryLocationInfo) for r in result)

            # Filter results to only our test registries
            test_results = [
                r
                for r in result
                if r.registry_name in {same_registry_name, diff_registry_name}
                and r.project in {project1_name, project2_name, project3_name}
            ]

            # Verify we have all 3 registries
            assert len(test_results) == 3

            # Verify ordering matches expected
            projects = [r.project for r in test_results]
            registry_names = [r.registry_name for r in test_results]

            assert projects == expected_projects
            assert registry_names == expected_registries

    @pytest.mark.asyncio
    async def test_fetch_known_registries_with_multiple_ordering_mixed(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test fetching known registries with multiple projects and secondary ordering"""
        # Create registries to test multi-level ordering
        registry1_name = "registry-x.example.com"
        registry2_name = "registry-y.example.com"
        registry3_name = "registry-a.example.com"
        registry4_name = "registry-b.example.com"
        project1_name = "project-a"
        project2_name = "project-a"  # Same as project1
        project3_name = "project-b"
        project4_name = "project-b"  # Same as project3

        async with (
            self.create_test_registry(database_engine, registry1_name, project1_name),
            self.create_test_registry(database_engine, registry2_name, project2_name),
            self.create_test_registry(database_engine, registry3_name, project3_name),
            self.create_test_registry(database_engine, registry4_name, project4_name),
        ):
            # When - Order by project ascending, then registry_name descending
            querier = Querier(
                orders=[
                    ContainerRegistryOrders.project(ascending=True),
                    ContainerRegistryOrders.registry_name(ascending=False),
                ]
            )
            result = await repository.get_known_registries(querier=querier)

            # Then - Should return ordered results
            assert len(result) >= 4
            assert all(isinstance(r, ContainerRegistryLocationInfo) for r in result)

            # Filter to our test data
            test_results = [
                r
                for r in result
                if r.registry_name
                in {registry1_name, registry2_name, registry3_name, registry4_name}
            ]

            # Verify we have all 4 registries
            assert len(test_results) == 4

            # Group by project and verify ordering
            project_a_results = [r for r in test_results if r.project == "project-a"]
            project_b_results = [r for r in test_results if r.project == "project-b"]

            # Within project-a, registry_name should be descending
            project_a_names = [r.registry_name for r in project_a_results]
            assert project_a_names == sorted(project_a_names, reverse=True)
            assert project_a_names == [registry2_name, registry1_name]

            # Within project-b, registry_name should be descending
            project_b_names = [r.registry_name for r in project_b_results]
            assert project_b_names == sorted(project_b_names, reverse=True)
            assert project_b_names == [registry4_name, registry3_name]
