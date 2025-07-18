"""
Tests for GroupRepository functionality.
Tests the repository layer with real database operations.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.group import ProjectType, groups
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserStatus, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.group.admin_repository import AdminGroupRepository
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.services.group.types import GroupCreator, GroupData, GroupModifier
from ai.backend.manager.types import OptionalState, TriState


class TestGroupRepository:
    """Test cases for GroupRepository"""

    @pytest.fixture
    def group_repository(
        self, database_fixture, database_engine: ExtendedAsyncSAEngine
    ) -> GroupRepository:
        """Create GroupRepository instance with real database"""
        mock_config_provider = MagicMock(spec=ManagerConfigProvider)
        mock_valkey_stat_client = MagicMock(spec=ValkeyStatClient)

        return GroupRepository(
            db=database_engine,
            config_provider=mock_config_provider,
            valkey_stat_client=mock_valkey_stat_client,
        )

    @pytest.fixture
    def admin_group_repository(
        self, database_fixture, database_engine: ExtendedAsyncSAEngine
    ) -> AdminGroupRepository:
        """Create AdminGroupRepository instance with real database"""
        mock_storage_manager = MagicMock(spec=StorageSessionManager)

        return AdminGroupRepository(
            db=database_engine,
            storage_manager=mock_storage_manager,
        )

    @pytest.fixture
    def sample_group_creator(self) -> GroupCreator:
        """Create group creator for testing"""
        return GroupCreator(
            name="test-group",
            domain_name="default",
            description="Test group description",
            is_active=True,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
            allowed_vfolder_hosts={"local": "modify-vfolder,upload-file,download-file"},
            integration_id="test-integration",
            resource_policy="default",
            type=ProjectType.GENERAL,
        )

    @asynccontextmanager
    async def create_test_group(
        self,
        database_engine: ExtendedAsyncSAEngine,
        name: str = "test-group",
        domain_name: str = "default",
        description: str = "Test group",
        is_active: bool = True,
    ) -> AsyncGenerator[GroupData, None]:
        """Create a test group and ensure cleanup"""
        group_id = uuid.uuid4()

        # Create group
        async with database_engine.begin() as conn:
            group_data = {
                "id": group_id,
                "name": name,
                "description": description,
                "is_active": is_active,
                "domain_name": domain_name,
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "integration_id": "test-integration",
                "resource_policy": "default",
                "type": ProjectType.GENERAL,
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
            }

            result = await conn.execute(sa.insert(groups).values(group_data).returning(groups))
            group_row = result.first()
            await conn.commit()

            group_data_obj = GroupData.from_row(group_row)
            assert group_data_obj is not None

        try:
            yield group_data_obj
        finally:
            # Cleanup with a separate connection
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(groups).where(groups.c.id == group_id))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_create_group_success(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        sample_group_creator: GroupCreator,
    ) -> None:
        """Test successful group creation"""
        # Ensure group doesn't exist
        async with database_engine.begin() as conn:
            result = await conn.execute(
                sa.select(groups).where(groups.c.name == sample_group_creator.name)
            )
            assert result.first() is None

        # Create group
        created_group = await group_repository.create(sample_group_creator)

        try:
            assert created_group.name == sample_group_creator.name
            assert created_group.description == sample_group_creator.description
            assert created_group.is_active == sample_group_creator.is_active
            assert created_group.domain_name == sample_group_creator.domain_name
            assert created_group.integration_id == sample_group_creator.integration_id
            assert created_group.resource_policy == sample_group_creator.resource_policy
            assert created_group.type == sample_group_creator.type

            # Verify group exists in database
            async with database_engine.begin() as conn:
                result = await conn.execute(
                    sa.select(groups).where(groups.c.name == sample_group_creator.name)
                )
                group_row = result.first()
                assert group_row is not None
                assert group_row.name == sample_group_creator.name
                assert group_row.domain_name == sample_group_creator.domain_name

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(
                    sa.delete(groups).where(groups.c.name == sample_group_creator.name)
                )
                await conn.commit()

    @pytest.mark.asyncio
    async def test_create_group_duplicate_name(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        sample_group_creator: GroupCreator,
    ) -> None:
        """Test group creation with duplicate name"""
        # Create group first
        await group_repository.create(sample_group_creator)

        try:
            # Try to create another group with same name in same domain
            duplicate_creator = GroupCreator(
                name=sample_group_creator.name,  # Same name
                domain_name=sample_group_creator.domain_name,  # Same domain
                description="Duplicate group",
                is_active=True,
                resource_policy="default",
                type=ProjectType.GENERAL,
            )

            with pytest.raises(IntegrityError):
                await group_repository.create(duplicate_creator)

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(
                    sa.delete(groups).where(groups.c.name == sample_group_creator.name)
                )
                await conn.commit()

    @pytest.mark.asyncio
    async def test_modify_group_success(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test successful group modification"""
        async with self.create_test_group(database_engine, "modify-test") as group:
            # Create modifier
            modifier = GroupModifier(
                description=TriState.update("Updated description"),
                total_resource_slots=OptionalState.update(
                    ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None)
                ),
                allowed_vfolder_hosts=OptionalState.update({
                    "local": "modify-vfolder,download-file"
                }),
            )

            # Modify group
            modified_group = await group_repository.modify_validated(
                group.id, modifier, UserRole.ADMIN, "set", []
            )

            assert modified_group is not None
            assert modified_group.id == group.id
            assert modified_group.description == "Updated description"

            # Verify changes in database
            async with database_engine.begin() as conn:
                result = await conn.execute(sa.select(groups).where(groups.c.id == group.id))
                group_row = result.first()
                assert group_row is not None
                assert group_row.description == "Updated description"

    @pytest.mark.asyncio
    async def test_modify_group_not_found(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test group modification when group not found"""
        modifier = GroupModifier(
            description=TriState.update("Updated description"),
        )

        fake_group_id = uuid.uuid4()
        result = await group_repository.modify_validated(
            fake_group_id, modifier, UserRole.ADMIN, "set", []
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_mark_inactive_success(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test successful group soft deletion"""
        async with self.create_test_group(database_engine, "inactive-test") as group:
            # Mark group as inactive
            result = await group_repository.mark_inactive(group.id)

            assert result is True

            # Verify group is marked as inactive
            async with database_engine.begin() as conn:
                result = await conn.execute(sa.select(groups).where(groups.c.id == group.id))
                group_row = result.first()
                assert group_row is not None
                assert group_row.is_active is False

    @pytest.mark.asyncio
    async def test_mark_inactive_not_found(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test group soft deletion when group not found"""
        fake_group_id = uuid.uuid4()
        result = await group_repository.mark_inactive(fake_group_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_create_group_with_all_fields(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test creating group with all possible fields"""
        comprehensive_creator = GroupCreator(
            name="comprehensive-group",
            domain_name="default",
            description="Comprehensive group with all features",
            is_active=True,
            total_resource_slots=ResourceSlot.from_user_input(
                {"cpu": "16", "mem": "32g", "cuda.device": "2"}, None
            ),
            allowed_vfolder_hosts={
                "local": "modify-vfolder,upload-file,download-file",
                "shared": "download-file",
            },
            integration_id="comprehensive-integration",
            resource_policy="default",
            type=ProjectType.GENERAL,
        )

        created_group = await group_repository.create(comprehensive_creator)

        try:
            assert created_group.name == "comprehensive-group"
            assert created_group.description == "Comprehensive group with all features"
            assert created_group.is_active is True
            assert created_group.domain_name == "default"
            assert created_group.integration_id == "comprehensive-integration"
            assert created_group.resource_policy == "default"
            assert created_group.type == ProjectType.GENERAL

            # Verify in database
            async with database_engine.begin() as conn:
                result = await conn.execute(
                    sa.select(groups).where(groups.c.name == "comprehensive-group")
                )
                group_row = result.first()
                assert group_row is not None
                assert group_row.name == "comprehensive-group"
                assert group_row.is_active is True
                assert group_row.domain_name == "default"

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(groups).where(groups.c.name == "comprehensive-group"))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_create_model_store_group(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test creating model store group"""
        model_store_creator = GroupCreator(
            name="model-store-test",
            domain_name="default",
            description="Model store group",
            is_active=True,
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts={},
            integration_id=None,
            resource_policy="default",
            type=ProjectType.MODEL_STORE,
        )

        created_group = await group_repository.create(model_store_creator)

        try:
            assert created_group.name == "model-store-test"
            assert created_group.type == ProjectType.MODEL_STORE
            assert created_group.is_active is True

            # Verify in database
            async with database_engine.begin() as conn:
                result = await conn.execute(
                    sa.select(groups).where(groups.c.name == "model-store-test")
                )
                group_row = result.first()
                assert group_row is not None
                assert group_row.type == ProjectType.MODEL_STORE

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(groups).where(groups.c.name == "model-store-test"))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_get_container_stats_for_period(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test getting container stats for a period"""
        async with self.create_test_group(database_engine, "stats-test") as group:
            # Test date range
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()

            # Get stats (should return empty list for new group)
            stats = await group_repository.get_container_stats_for_period(
                start_date, end_date, [group.id]
            )

            # Should return empty list for a group with no sessions
            assert isinstance(stats, list)
            assert len(stats) == 0

    @pytest.mark.asyncio
    async def test_fetch_project_resource_usage(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test fetching project resource usage"""
        async with self.create_test_group(database_engine, "usage-test") as group:
            # Test date range
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()

            # Get usage (should return empty list for new group)
            usage = await group_repository.fetch_project_resource_usage(
                start_date, end_date, [group.id]
            )

            # Should return empty list for a group with no usage
            assert isinstance(usage, list)
            assert len(usage) == 0

    @pytest.mark.asyncio
    async def test_group_creator_validation(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test GroupCreator validation and field mapping"""
        # Test minimal GroupCreator
        minimal_creator = GroupCreator(
            name="minimal-group",
            domain_name="default",
            description="Minimal group",
            is_active=True,
            resource_policy="default",
            type=ProjectType.GENERAL,
        )

        created_group = await group_repository.create(minimal_creator)

        try:
            assert created_group.name == "minimal-group"
            assert created_group.domain_name == "default"
            assert created_group.description == "Minimal group"
            assert created_group.is_active is True
            assert created_group.resource_policy == "default"
            assert created_group.type == ProjectType.GENERAL
            assert created_group.integration_id is None
            assert created_group.total_resource_slots == {}
            assert created_group.allowed_vfolder_hosts == {}

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(groups).where(groups.c.name == "minimal-group"))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_group_modifier_validation(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test GroupModifier validation and field mapping"""
        async with self.create_test_group(database_engine, "modifier-test") as group:
            # Test comprehensive GroupModifier
            modifier = GroupModifier(
                description=TriState.update("Modified description"),
                is_active=OptionalState.update(False),
                total_resource_slots=OptionalState.update(
                    ResourceSlot.from_user_input({"cpu": "2", "mem": "4g"}, None)
                ),
                allowed_vfolder_hosts=OptionalState.update({"shared": "download-file"}),
                integration_id=OptionalState.update("new-integration"),
                resource_policy=OptionalState.update("new-policy"),
            )

            # Apply modifications
            modified_group = await group_repository.modify_validated(
                group.id, modifier, UserRole.ADMIN, None, None
            )

            assert modified_group is not None
            assert modified_group.description == "Modified description"
            assert modified_group.is_active is False
            assert modified_group.integration_id == "new-integration"
            assert modified_group.resource_policy == "new-policy"

            # Verify changes persisted in database
            async with database_engine.begin() as conn:
                result = await conn.execute(sa.select(groups).where(groups.c.id == group.id))
                group_row = result.first()
                assert group_row is not None
                assert group_row.description == "Modified description"
                assert group_row.is_active is False
                assert group_row.integration_id == "new-integration"
                assert group_row.resource_policy == "new-policy"

    @pytest.mark.asyncio
    async def test_group_user_membership_add(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test adding users to group membership"""
        async with self.create_test_group(database_engine, "membership-test") as group:
            # Create test users
            user_uuids = [uuid.uuid4(), uuid.uuid4()]

            async with database_engine.begin() as conn:
                # Add test users to database
                for user_uuid in user_uuids:
                    await conn.execute(
                        sa.insert(users).values({
                            "uuid": user_uuid,
                            "username": f"testuser-{user_uuid}",
                            "email": f"test-{user_uuid}@example.com",
                            "password": "hashed_password",
                            "full_name": f"Test User {user_uuid}",
                            "status": UserStatus.ACTIVE,
                            "role": UserRole.USER,
                            "domain_name": "default",
                            "created_at": datetime.now(),
                            "modified_at": datetime.now(),
                        })
                    )
                await conn.commit()

            try:
                # Add users to group
                modifier = GroupModifier()
                result = await group_repository.modify_validated(
                    group.id, modifier, UserRole.ADMIN, "add", user_uuids
                )

                # Verify users were added to group
                async with database_engine.begin() as conn:
                    from ai.backend.manager.models.group import association_groups_users

                    result = await conn.execute(
                        sa.select(association_groups_users).where(
                            association_groups_users.c.group_id == group.id
                        )
                    )
                    memberships = result.fetchall()
                    assert len(memberships) == 2
                    member_uuids = [row.user_id for row in memberships]
                    assert all(user_uuid in member_uuids for user_uuid in user_uuids)

            finally:
                # Cleanup users
                async with database_engine.begin() as conn:
                    await conn.execute(sa.delete(users).where(users.c.uuid.in_(user_uuids)))
                    await conn.commit()

    @pytest.mark.asyncio
    async def test_group_user_membership_remove(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test removing users from group membership"""
        async with self.create_test_group(database_engine, "membership-remove-test") as group:
            # Create test users
            user_uuids = [uuid.uuid4(), uuid.uuid4()]

            async with database_engine.begin() as conn:
                # Add test users to database
                for user_uuid in user_uuids:
                    await conn.execute(
                        sa.insert(users).values({
                            "uuid": user_uuid,
                            "username": f"testuser-{user_uuid}",
                            "email": f"test-{user_uuid}@example.com",
                            "password": "hashed_password",
                            "full_name": f"Test User {user_uuid}",
                            "status": UserStatus.ACTIVE,
                            "role": UserRole.USER,
                            "domain_name": "default",
                            "created_at": datetime.now(),
                            "modified_at": datetime.now(),
                        })
                    )

                # Add users to group first
                from ai.backend.manager.models.group import association_groups_users

                for user_uuid in user_uuids:
                    await conn.execute(
                        sa.insert(association_groups_users).values({
                            "user_id": user_uuid,
                            "group_id": group.id,
                        })
                    )
                await conn.commit()

            try:
                # Remove one user from group
                modifier = GroupModifier()
                result = await group_repository.modify_validated(
                    group.id, modifier, UserRole.ADMIN, "remove", [user_uuids[0]]
                )

                # Verify user was removed from group
                async with database_engine.begin() as conn:
                    from ai.backend.manager.models.group import association_groups_users

                    result = await conn.execute(
                        sa.select(association_groups_users).where(
                            association_groups_users.c.group_id == group.id
                        )
                    )
                    memberships = result.fetchall()
                    assert len(memberships) == 1
                    assert memberships[0].user_id == user_uuids[1]

            finally:
                # Cleanup users
                async with database_engine.begin() as conn:
                    await conn.execute(sa.delete(users).where(users.c.uuid.in_(user_uuids)))
                    await conn.commit()

    @pytest.mark.asyncio
    async def test_repository_methods_exist(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
    ) -> None:
        """Test that all expected repository methods exist"""
        # Test method existence for complex operations
        assert hasattr(group_repository, "create")
        assert hasattr(group_repository, "modify_validated")
        assert hasattr(group_repository, "mark_inactive")
        assert hasattr(group_repository, "get_container_stats_for_period")
        assert hasattr(group_repository, "fetch_project_resource_usage")


class TestAdminGroupRepository:
    """Test cases for AdminGroupRepository"""

    @pytest.fixture
    def admin_group_repository(
        self, database_fixture, database_engine: ExtendedAsyncSAEngine
    ) -> AdminGroupRepository:
        """Create AdminGroupRepository instance with real database"""
        mock_storage_manager = MagicMock(spec=StorageSessionManager)

        return AdminGroupRepository(
            db=database_engine,
            storage_manager=mock_storage_manager,
        )

    @asynccontextmanager
    async def create_test_group_for_purge(
        self,
        database_engine: ExtendedAsyncSAEngine,
        name: str = "purge-test",
        domain_name: str = "default",
        is_active: bool = False,  # Inactive for purging
    ) -> AsyncGenerator[GroupData, None]:
        """Create a test group for purge testing"""
        group_id = uuid.uuid4()

        # Create group
        async with database_engine.begin() as conn:
            group_data = {
                "id": group_id,
                "name": name,
                "description": "Test group for purging",
                "is_active": is_active,
                "domain_name": domain_name,
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "integration_id": "test-integration",
                "resource_policy": "default",
                "type": ProjectType.GENERAL,
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
            }

            result = await conn.execute(sa.insert(groups).values(group_data).returning(groups))
            group_row = result.first()
            await conn.commit()

            group_data_obj = GroupData.from_row(group_row)
            assert group_data_obj is not None

        try:
            yield group_data_obj
        finally:
            # Cleanup (if not already purged) with a separate connection
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(groups).where(groups.c.id == group_id))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_purge_group_success(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
    ) -> None:
        """Test successful group purging"""
        async with self.create_test_group_for_purge(database_engine, "purge-success") as group:
            # Purge group (should succeed since no dependencies)
            result = await admin_group_repository.purge_group_force(group.id)

            assert result is True

            # Verify group is completely removed
            async with database_engine.begin() as conn:
                query_result = await conn.execute(sa.select(groups).where(groups.c.id == group.id))
                group_row = query_result.first()
                assert group_row is None

    @pytest.mark.asyncio
    async def test_purge_group_not_found(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
    ) -> None:
        """Test group purging when group not found"""
        fake_group_id = uuid.uuid4()
        result = await admin_group_repository.purge_group_force(fake_group_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_purge_group_with_dependency_checks(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
    ) -> None:
        """Test group purging with proper dependency validation"""
        async with self.create_test_group_for_purge(database_engine, "dependency-test") as group:
            # Test dependency check methods exist and return expected types
            async with database_engine.begin_session() as session:
                # Check vfolders mounted to active kernels
                has_mounted_vfolders = (
                    await admin_group_repository._check_group_vfolders_mounted_to_active_kernels(
                        session, group.id
                    )
                )
                assert isinstance(has_mounted_vfolders, bool)
                assert has_mounted_vfolders is False  # No active kernels for new group

                # Check active kernels
                has_active_kernels = await admin_group_repository._check_group_has_active_kernels(
                    session, group.id
                )
                assert isinstance(has_active_kernels, bool)
                assert has_active_kernels is False  # No active kernels for new group

            # Purge should succeed since no dependencies
            result = await admin_group_repository.purge_group_force(group.id)
            assert result is True

            # Verify group is completely removed
            async with database_engine.begin() as conn:
                query_result = await conn.execute(sa.select(groups).where(groups.c.id == group.id))
                group_row = query_result.first()
                assert group_row is None

    @pytest.mark.asyncio
    async def test_purge_group_error_handling(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
    ) -> None:
        """Test error handling in purge operations"""
        from ai.backend.manager.errors.resource import GroupNotFound

        # Test purging non-existent group
        fake_group_id = uuid.uuid4()

        with pytest.raises(GroupNotFound):
            await admin_group_repository.purge_group_force(fake_group_id)

    @pytest.mark.asyncio
    async def test_vfolder_deletion_count(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
    ) -> None:
        """Test vfolder deletion returns correct count"""
        async with self.create_test_group_for_purge(database_engine, "vfolder-test") as group:
            # Test vfolder deletion (should return 0 for group with no vfolders)
            deleted_count = await admin_group_repository._delete_group_vfolders(group.id)
            assert isinstance(deleted_count, int)
            assert deleted_count == 0  # No vfolders for new group

    @pytest.mark.asyncio
    async def test_kernel_and_session_deletion(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
    ) -> None:
        """Test kernel and session deletion operations"""
        async with self.create_test_group_for_purge(database_engine, "deletion-test") as group:
            async with database_engine.begin_session() as session:
                # Test kernel deletion (should return 0 for group with no kernels)
                deleted_kernels = await admin_group_repository._delete_group_kernels(
                    session, group.id
                )
                assert isinstance(deleted_kernels, int)
                assert deleted_kernels == 0  # No kernels for new group

                # Test session deletion (should return 0 for group with no sessions)
                deleted_sessions = await admin_group_repository._delete_group_sessions(
                    session, group.id
                )
                assert isinstance(deleted_sessions, int)
                assert deleted_sessions == 0  # No sessions for new group

                # Test endpoint deletion (should complete without error)
                try:
                    await admin_group_repository._delete_group_endpoints(session, group.id)
                    # Should not raise any exception for group with no endpoints
                except Exception as e:
                    pytest.fail(f"Endpoint deletion failed unexpectedly: {e}")

    @pytest.mark.asyncio
    async def test_comprehensive_purge_workflow(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
    ) -> None:
        """Test complete purge workflow with multiple cleanup operations"""
        async with self.create_test_group_for_purge(
            database_engine, "comprehensive-purge"
        ) as group:
            # Verify group exists before purge
            async with database_engine.begin() as conn:
                result = await conn.execute(sa.select(groups).where(groups.c.id == group.id))
                group_row = result.first()
                assert group_row is not None
                assert group_row.name == "comprehensive-purge"
                assert group_row.is_active is False  # Created as inactive for purging

            # Perform comprehensive purge
            result = await admin_group_repository.purge_group_force(group.id)
            assert result is True

            # Verify complete removal
            async with database_engine.begin() as conn:
                result = await conn.execute(sa.select(groups).where(groups.c.id == group.id))
                group_row = result.first()
                assert group_row is None
