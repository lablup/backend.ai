"""
Tests for PermissionControllerRepository scope search functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.permission.types import GLOBAL_SCOPE_ID, ScopeType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import PasswordHashAlgorithm, PasswordInfo, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.options import (
    DomainScopeConditions,
    DomainScopeOrders,
    ProjectScopeConditions,
    ProjectScopeOrders,
    UserScopeConditions,
    UserScopeOrders,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=16,
    )


class TestSearchDomainScopes:
    """Tests for searching domain scopes."""

    @pytest.fixture
    async def db_with_scope_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables required for scope search tests."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def permission_controller_repository(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        """Create PermissionControllerRepository instance."""
        return PermissionControllerRepository(db_with_scope_tables)

    @pytest.fixture
    async def sample_domains(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> list[str]:
        """Create sample domains for testing."""
        domain_names = ["test-domain-alpha", "test-domain-beta", "prod-domain"]

        async with db_with_scope_tables.begin_session() as db_sess:
            for name in domain_names:
                domain = DomainRow(
                    name=name,
                    description=f"Test domain: {name}",
                    is_active=True,
                )
                db_sess.add(domain)
            await db_sess.flush()

        return domain_names

    @pytest.fixture
    async def sample_domains_for_pagination(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> list[str]:
        """Create 15 sample domains for pagination testing."""
        domain_names = [f"domain-{i:02d}" for i in range(15)]

        async with db_with_scope_tables.begin_session() as db_sess:
            for name in domain_names:
                domain = DomainRow(
                    name=name,
                    description=f"Test domain: {name}",
                    is_active=True,
                )
                db_sess.add(domain)
            await db_sess.flush()

        return domain_names

    @pytest.mark.asyncio
    async def test_search_domain_scopes_returns_domains(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_domains: list[str],
    ) -> None:
        """Test basic domain scope search returns all domains."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.DOMAIN, querier)

        assert result.total_count == len(sample_domains)
        assert len(result.items) == len(sample_domains)
        for item in result.items:
            assert item.id.scope_type == ScopeType.DOMAIN
            assert item.name in sample_domains

    @pytest.mark.asyncio
    async def test_search_domain_scopes_with_name_contains_filter(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_domains: list[str],
    ) -> None:
        """Test domain search with name contains filter."""
        spec = StringMatchSpec(value="test", case_insensitive=True, negated=False)
        querier = BatchQuerier(
            conditions=[DomainScopeConditions.by_name_contains(spec)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.DOMAIN, querier)

        # sample_domains has "test-domain-alpha", "test-domain-beta", "prod-domain"
        # Only domains containing "test" should be returned
        assert result.total_count == 2
        for item in result.items:
            assert "test" in item.name.lower()

    @pytest.mark.asyncio
    async def test_search_domain_scopes_with_name_equals_filter(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_domains: list[str],
    ) -> None:
        """Test domain search with exact name match filter."""
        target_name = sample_domains[0]
        spec = StringMatchSpec(value=target_name, case_insensitive=False, negated=False)
        querier = BatchQuerier(
            conditions=[DomainScopeConditions.by_name_equals(spec)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.DOMAIN, querier)

        assert result.total_count == 1
        assert result.items[0].name == target_name

    @pytest.mark.asyncio
    async def test_search_domain_scopes_with_name_starts_with_filter(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_domains: list[str],
    ) -> None:
        """Test domain search with name starts with filter."""
        spec = StringMatchSpec(value="test-", case_insensitive=False, negated=False)
        querier = BatchQuerier(
            conditions=[DomainScopeConditions.by_name_starts_with(spec)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.DOMAIN, querier)

        assert result.total_count == 2
        for item in result.items:
            assert item.name.startswith("test-")

    @pytest.mark.asyncio
    async def test_search_domain_scopes_with_ordering_name_ascending(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_domains: list[str],
    ) -> None:
        """Test domain search with name ascending order."""
        querier = BatchQuerier(
            conditions=[],
            orders=[DomainScopeOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.DOMAIN, querier)

        names = [item.name for item in result.items]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_search_domain_scopes_with_ordering_name_descending(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_domains: list[str],
    ) -> None:
        """Test domain search with name descending order."""
        querier = BatchQuerier(
            conditions=[],
            orders=[DomainScopeOrders.name(ascending=False)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.DOMAIN, querier)

        names = [item.name for item in result.items]
        assert names == sorted(names, reverse=True)

    @pytest.mark.asyncio
    async def test_search_domain_scopes_with_pagination(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_domains_for_pagination: list[str],
    ) -> None:
        """Test domain search with offset pagination."""
        # First page
        querier_page1 = BatchQuerier(
            conditions=[],
            orders=[DomainScopeOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=5, offset=0),
        )
        result_page1 = await permission_controller_repository.search_scopes(
            ScopeType.DOMAIN, querier_page1
        )

        assert len(result_page1.items) == 5
        assert result_page1.total_count == 15
        assert result_page1.has_next_page is True
        assert result_page1.has_previous_page is False

        # Second page
        querier_page2 = BatchQuerier(
            conditions=[],
            orders=[DomainScopeOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=5, offset=5),
        )
        result_page2 = await permission_controller_repository.search_scopes(
            ScopeType.DOMAIN, querier_page2
        )

        assert len(result_page2.items) == 5
        assert result_page2.has_next_page is True
        assert result_page2.has_previous_page is True

        # Verify no overlap between pages
        page1_names = {item.name for item in result_page1.items}
        page2_names = {item.name for item in result_page2.items}
        assert page1_names.isdisjoint(page2_names)


class TestSearchProjectScopes:
    """Tests for searching project (group) scopes."""

    @pytest.fixture
    async def db_with_scope_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables required for scope search tests."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def permission_controller_repository(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        """Create PermissionControllerRepository instance."""
        return PermissionControllerRepository(db_with_scope_tables)

    @pytest.fixture
    async def sample_domain_with_policy(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> tuple[str, str]:
        """Create a sample domain and project resource policy for projects."""
        domain_name = "test-domain-for-projects"
        policy_name = "test-project-policy"

        async with db_with_scope_tables.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for projects",
                is_active=True,
            )
            db_sess.add(domain)

            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(policy)
            await db_sess.flush()

        return domain_name, policy_name

    @pytest.fixture
    async def sample_projects(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
        sample_domain_with_policy: tuple[str, str],
    ) -> list[uuid.UUID]:
        """Create sample projects (groups) for testing."""
        domain_name, policy_name = sample_domain_with_policy
        project_ids: list[uuid.UUID] = []

        async with db_with_scope_tables.begin_session() as db_sess:
            project_names = ["project-alpha", "project-beta", "project-gamma"]

            for name in project_names:
                project_id = uuid.uuid4()
                project = GroupRow(
                    id=project_id,
                    name=name,
                    description=f"Test project: {name}",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot({}),
                    resource_policy=policy_name,
                )
                db_sess.add(project)
                project_ids.append(project_id)
            await db_sess.flush()

        return project_ids

    @pytest.fixture
    async def sample_projects_for_pagination(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
        sample_domain_with_policy: tuple[str, str],
    ) -> list[uuid.UUID]:
        """Create 15 sample projects for pagination testing."""
        domain_name, policy_name = sample_domain_with_policy
        project_ids: list[uuid.UUID] = []

        async with db_with_scope_tables.begin_session() as db_sess:
            for i in range(15):
                project_id = uuid.uuid4()
                project = GroupRow(
                    id=project_id,
                    name=f"project-{i:02d}",
                    description=f"Test project {i}",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot({}),
                    resource_policy=policy_name,
                )
                db_sess.add(project)
                project_ids.append(project_id)
            await db_sess.flush()

        return project_ids

    @pytest.mark.asyncio
    async def test_search_project_scopes_returns_groups(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_projects: list[uuid.UUID],
    ) -> None:
        """Test basic project scope search returns all projects."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.PROJECT, querier)

        assert result.total_count == len(sample_projects)
        for item in result.items:
            assert item.id.scope_type == ScopeType.PROJECT

    @pytest.mark.asyncio
    async def test_search_project_scopes_with_name_contains_filter(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_projects: list[uuid.UUID],
    ) -> None:
        """Test project search with name contains filter."""
        spec = StringMatchSpec(value="alpha", case_insensitive=True, negated=False)
        querier = BatchQuerier(
            conditions=[ProjectScopeConditions.by_name_contains(spec)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.PROJECT, querier)

        assert result.total_count == 1
        assert "alpha" in result.items[0].name.lower()

    @pytest.mark.asyncio
    async def test_search_project_scopes_with_ordering(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_projects: list[uuid.UUID],
    ) -> None:
        """Test project search with name ordering."""
        querier = BatchQuerier(
            conditions=[],
            orders=[ProjectScopeOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.PROJECT, querier)

        names = [item.name for item in result.items]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_search_project_scopes_with_pagination(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_projects_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test project search with pagination."""
        querier = BatchQuerier(
            conditions=[],
            orders=[ProjectScopeOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=5, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.PROJECT, querier)

        assert len(result.items) == 5
        assert result.total_count == 15
        assert result.has_next_page is True


class TestSearchUserScopes:
    """Tests for searching user scopes."""

    @pytest.fixture
    async def db_with_scope_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables required for scope search tests."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def permission_controller_repository(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        """Create PermissionControllerRepository instance."""
        return PermissionControllerRepository(db_with_scope_tables)

    @pytest.fixture
    async def sample_domain_with_user_policy(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> tuple[str, str]:
        """Create a sample domain and user resource policy for users."""
        domain_name = "test-domain-for-users"
        policy_name = "test-user-policy"

        async with db_with_scope_tables.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for users",
                is_active=True,
            )
            db_sess.add(domain)

            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(policy)
            await db_sess.flush()

        return domain_name, policy_name

    @pytest.fixture
    async def sample_users(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
        sample_domain_with_user_policy: tuple[str, str],
    ) -> list[uuid.UUID]:
        """Create sample users for testing."""
        domain_name, policy_name = sample_domain_with_user_policy
        user_ids: list[uuid.UUID] = []

        async with db_with_scope_tables.begin_session() as db_sess:
            users_data = [
                ("user-alpha", "alpha@example.com"),
                ("user-beta", "beta@example.com"),
                ("user-gamma", "gamma@test.org"),
            ]

            for username, email in users_data:
                user_id = uuid.uuid4()
                user = UserRow(
                    uuid=user_id,
                    username=username,
                    email=email,
                    password=create_test_password_info("test_password"),
                    domain_name=domain_name,
                    resource_policy=policy_name,
                    status=UserStatus.ACTIVE,
                    need_password_change=False,
                )
                db_sess.add(user)
                user_ids.append(user_id)
            await db_sess.flush()

        return user_ids

    @pytest.fixture
    async def sample_users_for_pagination(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
        sample_domain_with_user_policy: tuple[str, str],
    ) -> list[uuid.UUID]:
        """Create 15 sample users for pagination testing."""
        domain_name, policy_name = sample_domain_with_user_policy
        user_ids: list[uuid.UUID] = []

        async with db_with_scope_tables.begin_session() as db_sess:
            for i in range(15):
                user_id = uuid.uuid4()
                user = UserRow(
                    uuid=user_id,
                    username=f"user-{i:02d}",
                    email=f"user{i:02d}@example.com",
                    password=create_test_password_info("test_password"),
                    domain_name=domain_name,
                    resource_policy=policy_name,
                    status=UserStatus.ACTIVE,
                    need_password_change=False,
                )
                db_sess.add(user)
                user_ids.append(user_id)
            await db_sess.flush()

        return user_ids

    @pytest.mark.asyncio
    async def test_search_user_scopes_returns_users(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_users: list[uuid.UUID],
    ) -> None:
        """Test basic user scope search returns all users."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.USER, querier)

        assert result.total_count == len(sample_users)
        for item in result.items:
            assert item.id.scope_type == ScopeType.USER

    @pytest.mark.asyncio
    async def test_search_user_scopes_filters_username_or_email(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_users: list[uuid.UUID],
    ) -> None:
        """Test user search filters by username OR email."""
        # Search for "example" which is in email addresses
        spec = StringMatchSpec(value="example", case_insensitive=True, negated=False)
        querier = BatchQuerier(
            conditions=[UserScopeConditions.by_name_contains(spec)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.USER, querier)

        # Users with "example" in email: alpha@example.com, beta@example.com
        assert result.total_count == 2

    @pytest.mark.asyncio
    async def test_search_user_scopes_with_ordering(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_users: list[uuid.UUID],
    ) -> None:
        """Test user search with username ordering."""
        querier = BatchQuerier(
            conditions=[],
            orders=[UserScopeOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.USER, querier)

        names = [item.name for item in result.items]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_search_user_scopes_with_pagination(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_users_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test user search with pagination."""
        querier = BatchQuerier(
            conditions=[],
            orders=[UserScopeOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=5, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.USER, querier)

        assert len(result.items) == 5
        assert result.total_count == 15
        assert result.has_next_page is True


class TestSearchGlobalScope:
    """Tests for global scope search."""

    @pytest.fixture
    async def db_with_scope_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables required for scope search tests."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def permission_controller_repository(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        """Create PermissionControllerRepository instance."""
        return PermissionControllerRepository(db_with_scope_tables)

    @pytest.mark.asyncio
    async def test_search_scopes_global_returns_static_result(
        self,
        permission_controller_repository: PermissionControllerRepository,
    ) -> None:
        """Test global scope returns single static result."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.GLOBAL, querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].id.scope_type == ScopeType.GLOBAL
        assert result.items[0].id.scope_id == GLOBAL_SCOPE_ID
        assert result.items[0].name == GLOBAL_SCOPE_ID
        assert result.has_next_page is False
        assert result.has_previous_page is False


class TestSearchScopesEmptyResult:
    """Tests for empty result handling."""

    @pytest.fixture
    async def db_with_scope_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables required for scope search tests."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def permission_controller_repository(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        """Create PermissionControllerRepository instance."""
        return PermissionControllerRepository(db_with_scope_tables)

    @pytest.fixture
    async def sample_domains(
        self,
        db_with_scope_tables: ExtendedAsyncSAEngine,
    ) -> list[str]:
        """Create sample domains for testing."""
        domain_names = ["test-domain-alpha", "test-domain-beta", "prod-domain"]

        async with db_with_scope_tables.begin_session() as db_sess:
            for name in domain_names:
                domain = DomainRow(
                    name=name,
                    description=f"Test domain: {name}",
                    is_active=True,
                )
                db_sess.add(domain)
            await db_sess.flush()

        return domain_names

    @pytest.mark.asyncio
    async def test_search_scopes_empty_result(
        self,
        permission_controller_repository: PermissionControllerRepository,
        sample_domains: list[str],
    ) -> None:
        """Test search with no matching results returns empty list."""
        # Search for non-existent domain name
        spec = StringMatchSpec(
            value="nonexistent-domain-xyz", case_insensitive=False, negated=False
        )
        querier = BatchQuerier(
            conditions=[DomainScopeConditions.by_name_equals(spec)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await permission_controller_repository.search_scopes(ScopeType.DOMAIN, querier)

        assert result.total_count == 0
        assert len(result.items) == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False
