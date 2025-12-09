"""
Tests for DomainRepository functionality.
Tests the repository layer with real database operations.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import DomainNotFound, InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.domain.types import (
    DomainCreator,
    DomainData,
    DomainModifier,
    UserInfo,
)
from ai.backend.manager.models.domain import domains, row_to_data
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.user import UserRole, UserStatus, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.types import TriState


class TestDomainRepository:
    """Test cases for DomainRepository"""

    @pytest.fixture
    def domain_repository(
        self, database_fixture, database_engine: ExtendedAsyncSAEngine
    ) -> DomainRepository:
        """Create DomainRepository instance with real database"""

        repo = DomainRepository(db=database_engine)

        # Create mock for _role_manager
        mock_role_manager = MagicMock()
        mock_role_manager.create_system_role = AsyncMock(return_value=None)
        repo._role_manager = mock_role_manager

        return repo

    @pytest.fixture
    def sample_domain_creator(self) -> DomainCreator:
        """Create domain creator for testing"""
        return DomainCreator(
            name="test-domain",
            description="Test domain description",
            is_active=True,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "10", "mem": "20g"}, None),
            allowed_vfolder_hosts={"local": ["modify-vfolder", "upload-file", "download-file"]},
            allowed_docker_registries=["registry.example.com"],
            integration_id="test-integration",
            dotfiles=b"test dotfiles",
        )

    @pytest.fixture
    def user_info(self) -> UserInfo:
        """Create user info for testing"""
        return UserInfo(id=uuid.uuid4(), role=UserRole.SUPERADMIN, domain_name="default")

    @asynccontextmanager
    async def create_test_domain(
        self,
        database_engine: ExtendedAsyncSAEngine,
        name: str = "test-domain",
        description: str = "Test domain",
        is_active: bool = True,
    ) -> AsyncGenerator[DomainData, None]:
        """Create a test domain and ensure cleanup"""
        async with database_engine.begin() as conn:
            # Create domain
            domain_data = {
                "name": name,
                "description": description,
                "is_active": is_active,
                "total_resource_slots": ResourceSlot.from_user_input(
                    {"cpu": "8", "mem": "16g"}, None
                ),
                "allowed_vfolder_hosts": VFolderHostPermissionMap({
                    "local": ["modify-vfolder", "upload-file", "download-file"]
                }),
                "allowed_docker_registries": ["registry.example.com"],
                "dotfiles": b"test dotfiles",
                "integration_id": "test-integration",
            }

            result = await conn.execute(sa.insert(domains).values(domain_data).returning(domains))
            domain_row = result.first()

            # Create model-store group for the domain
            group_data = {
                "id": uuid.uuid4(),
                "name": "model-store",
                "description": f"Model store group for {name}",
                "domain_name": name,
                "is_active": True,
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
                "type": "GENERAL",
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "integration_id": None,
                "resource_policy": "default",
            }

            await conn.execute(sa.insert(groups).values(group_data))
            await conn.commit()

            assert domain_row is not None
            domain_data_obj = row_to_data(domain_row)

            try:
                yield domain_data_obj
            finally:
                # Cleanup
                await conn.execute(sa.delete(groups).where(groups.c.domain_name == name))
                await conn.execute(sa.delete(domains).where(domains.c.name == name))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_create_domain_validated_success(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
        sample_domain_creator: DomainCreator,
    ) -> None:
        """Test successful domain creation"""
        # Ensure domain doesn't exist
        async with database_engine.begin() as conn:
            result = await conn.execute(
                sa.select(domains).where(domains.c.name == sample_domain_creator.name)
            )
            assert result.first() is None

        # Create domain
        created_domain = await domain_repository.create_domain_validated(sample_domain_creator)

        try:
            assert created_domain.name == sample_domain_creator.name
            assert created_domain.description == sample_domain_creator.description
            assert created_domain.is_active == sample_domain_creator.is_active
            assert created_domain.total_resource_slots == sample_domain_creator.total_resource_slots
            assert created_domain.integration_id == sample_domain_creator.integration_id

            # Verify domain exists in database
            async with database_engine.begin() as conn:
                result = await conn.execute(
                    sa.select(domains).where(domains.c.name == sample_domain_creator.name)
                )
                domain_row = result.first()
                assert domain_row is not None
                assert domain_row.name == sample_domain_creator.name

                # Verify model-store group was created
                result = await conn.execute(
                    sa.select(groups).where(groups.c.domain_name == sample_domain_creator.name)
                )
                group_row = result.first()
                assert group_row is not None
                assert group_row.name == "model-store"

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(
                    sa.delete(groups).where(groups.c.domain_name == sample_domain_creator.name)
                )
                await conn.execute(
                    sa.delete(domains).where(domains.c.name == sample_domain_creator.name)
                )
                await conn.commit()

    @pytest.mark.asyncio
    async def test_create_domain_validated_duplicate_name(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
        sample_domain_creator: DomainCreator,
    ) -> None:
        """Test domain creation with duplicate name"""
        # Create domain first
        await domain_repository.create_domain_validated(sample_domain_creator)

        try:
            # Try to create another domain with same name
            duplicate_creator = DomainCreator(
                name=sample_domain_creator.name,  # Same name
                description="Duplicate domain",
                is_active=True,
            )

            with pytest.raises(InvalidAPIParameters):
                await domain_repository.create_domain_validated(duplicate_creator)

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(
                    sa.delete(groups).where(groups.c.domain_name == sample_domain_creator.name)
                )
                await conn.execute(
                    sa.delete(domains).where(domains.c.name == sample_domain_creator.name)
                )
                await conn.commit()

    @pytest.mark.asyncio
    async def test_modify_domain_validated_success(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test successful domain modification"""
        # Create a test domain directly
        domain_name = "modify-test-simple"
        domain_creator = DomainCreator(
            name=domain_name,
            description="Original description",
            is_active=True,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "10", "mem": "20g"}, None),
            allowed_vfolder_hosts={"local": ["modify-vfolder"]},
            allowed_docker_registries=["registry.example.com"],
            integration_id="test-integration",
            dotfiles=b"test dotfiles",
        )

        # Create domain
        await domain_repository.create_domain_validated(domain_creator)

        try:
            # Create modifier
            modifier = DomainModifier(
                description=TriState.update("Updated description"),
                total_resource_slots=TriState.update(
                    ResourceSlot.from_user_input({"cpu": "20", "mem": "40g"}, None)
                ),
            )

            # Modify domain
            modified_domain = await domain_repository.modify_domain_validated(domain_name, modifier)

            assert modified_domain is not None
            assert modified_domain.name == domain_name
            assert modified_domain.description == "Updated description"

            # Verify changes in database
            async with database_engine.begin() as conn:
                result = await conn.execute(sa.select(domains).where(domains.c.name == domain_name))
                domain_row = result.first()
                assert domain_row is not None
                assert domain_row.description == "Updated description"

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(groups).where(groups.c.domain_name == domain_name))
                await conn.execute(sa.delete(domains).where(domains.c.name == domain_name))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_modify_domain_validated_not_found(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test domain modification when domain not found"""
        modifier = DomainModifier(
            description=TriState.update("Updated description"),
        )

        with pytest.raises(DomainNotFound):
            await domain_repository.modify_domain_validated("nonexistent-domain", modifier)

    @pytest.mark.asyncio
    async def test_soft_delete_domain_validated_success(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test successful domain soft deletion"""
        # Create a test domain directly
        domain_name = "delete-test-simple"
        domain_creator = DomainCreator(
            name=domain_name,
            description="Test domain for deletion",
            is_active=True,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "10", "mem": "20g"}, None),
            allowed_vfolder_hosts={"local": ["modify-vfolder"]},
            allowed_docker_registries=["registry.example.com"],
            integration_id="test-integration",
            dotfiles=b"test dotfiles",
        )

        # Create domain
        await domain_repository.create_domain_validated(domain_creator)

        try:
            # Soft delete domain (now returns None)
            await domain_repository.soft_delete_domain_validated(domain_name)

            # Verify domain is marked as inactive
            async with database_engine.begin() as conn:
                result = await conn.execute(sa.select(domains).where(domains.c.name == domain_name))
                domain_row = result.first()
                assert domain_row is not None
                assert domain_row.is_active is False

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(groups).where(groups.c.domain_name == domain_name))
                await conn.execute(sa.delete(domains).where(domains.c.name == domain_name))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_soft_delete_domain_validated_not_found(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test domain soft deletion when domain not found"""
        with pytest.raises(DomainNotFound):
            await domain_repository.soft_delete_domain_validated("nonexistent-domain")

    @pytest.mark.asyncio
    async def test_purge_domain_validated_success(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test successful domain purging"""
        domain_name = "purge-test"

        # Create domain manually for purge test
        async with database_engine.begin() as conn:
            domain_data = {
                "name": domain_name,
                "description": "Test domain for purging",
                "is_active": False,  # Inactive domain for purging
                "total_resource_slots": ResourceSlot.from_user_input(
                    {"cpu": "8", "mem": "16g"}, None
                ),
                "allowed_vfolder_hosts": VFolderHostPermissionMap({
                    "local": ["modify-vfolder", "upload-file", "download-file"]
                }),
                "allowed_docker_registries": ["registry.example.com"],
                "dotfiles": b"test dotfiles",
                "integration_id": "test-integration",
            }

            await conn.execute(sa.insert(domains).values(domain_data))
            await conn.commit()

        try:
            # Purge domain (should succeed since no users/groups/kernels)
            result = await domain_repository.purge_domain_validated(domain_name)

            assert result is True

            # Verify domain is completely removed
            async with database_engine.begin() as conn:
                result = await conn.execute(sa.select(domains).where(domains.c.name == domain_name))
                domain_row = result.first()
                assert domain_row is None

        except Exception:
            # Cleanup if test fails
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(domains).where(domains.c.name == domain_name))
                await conn.commit()
            raise

    @pytest.mark.asyncio
    async def test_purge_domain_validated_with_users(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test domain purging when domain has users"""
        domain_name = "purge-with-users-test"

        # Create domain and user
        async with database_engine.begin() as conn:
            domain_data = {
                "name": domain_name,
                "description": "Test domain with users",
                "is_active": False,
                "total_resource_slots": ResourceSlot.from_user_input(
                    {"cpu": "8", "mem": "16g"}, None
                ),
                "allowed_vfolder_hosts": VFolderHostPermissionMap({
                    "local": ["modify-vfolder", "upload-file", "download-file"]
                }),
                "allowed_docker_registries": ["registry.example.com"],
                "dotfiles": b"test dotfiles",
                "integration_id": "test-integration",
            }

            await conn.execute(sa.insert(domains).values(domain_data))

            # Create user in domain
            from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
            from ai.backend.manager.models.hasher.types import PasswordInfo

            password_info = PasswordInfo(
                password="test_password",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=600_000,
                salt_size=32,
            )

            user_data = {
                "uuid": uuid.uuid4(),
                "username": "testuser",
                "email": "test@example.com",
                "password": password_info,
                "need_password_change": False,
                "full_name": "Test User",
                "description": "Test user",
                "status": UserStatus.ACTIVE,
                "domain_name": domain_name,
                "role": UserRole.USER,
                "created_at": datetime.now(),
                "modified_at": datetime.now(),
                "allowed_client_ip": None,
                "resource_policy": "default",
                "totp_activated": False,
                "sudo_session_enabled": False,
                "container_uid": None,
                "container_main_gid": None,
                "container_gids": None,
            }

            await conn.execute(sa.insert(users).values(user_data))
            await conn.commit()

        try:
            # Try to purge domain (should fail due to users)
            with pytest.raises(RuntimeError) as exc_info:
                await domain_repository.purge_domain_validated(domain_name)

            assert "There are users bound to the domain" in str(exc_info.value)

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(users).where(users.c.domain_name == domain_name))
                await conn.execute(sa.delete(domains).where(domains.c.name == domain_name))
                await conn.commit()

    @pytest.mark.asyncio
    async def test_purge_domain_validated_not_found(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test domain purging when domain not found"""
        result = await domain_repository.purge_domain_validated("nonexistent-domain")

        assert result is False

    @pytest.mark.asyncio
    async def test_create_domain_with_all_fields(
        self,
        database_fixture,
        database_engine: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test creating domain with all possible fields"""
        comprehensive_creator = DomainCreator(
            name="comprehensive-domain",
            description="Comprehensive domain with all features",
            is_active=True,
            total_resource_slots=ResourceSlot.from_user_input(
                {"cpu": "100", "mem": "500g", "cuda.device": "8"}, None
            ),
            allowed_vfolder_hosts={
                "local": ["modify-vfolder", "upload-file", "download-file"],
                "shared": ["download-file"],
                "scratch": ["modify-vfolder", "upload-file", "download-file"],
            },
            allowed_docker_registries=["docker.io", "registry.example.com", "private.registry"],
            integration_id="comprehensive-integration",
            dotfiles=b"comprehensive dotfiles configuration",
        )

        created_domain = await domain_repository.create_domain_validated(comprehensive_creator)

        try:
            assert created_domain.name == "comprehensive-domain"
            assert created_domain.description == "Comprehensive domain with all features"
            assert created_domain.is_active is True
            assert created_domain.total_resource_slots == ResourceSlot.from_user_input(
                {"cpu": "100", "mem": "500g", "cuda.device": "8"}, None
            )
            assert created_domain.integration_id == "comprehensive-integration"
            assert len(created_domain.allowed_docker_registries) == 3
            assert created_domain.dotfiles == b"comprehensive dotfiles configuration"

            # Verify in database
            async with database_engine.begin() as conn:
                result = await conn.execute(
                    sa.select(domains).where(domains.c.name == "comprehensive-domain")
                )
                domain_row = result.first()
                assert domain_row is not None
                assert domain_row.name == "comprehensive-domain"
                assert domain_row.is_active is True

        finally:
            # Cleanup
            async with database_engine.begin() as conn:
                await conn.execute(
                    sa.delete(groups).where(groups.c.domain_name == "comprehensive-domain")
                )
                await conn.execute(
                    sa.delete(domains).where(domains.c.name == "comprehensive-domain")
                )
                await conn.commit()
