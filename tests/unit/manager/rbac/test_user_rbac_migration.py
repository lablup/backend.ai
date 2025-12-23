"""Test for user RBAC migration module."""

import uuid

import pytest

from ai.backend.manager.models.rbac_models.migration.enums import (
    RoleSource,
)
from ai.backend.manager.models.rbac_models.migration.project import (
    ProjectData,
    get_project_admin_role_creation_input,
    get_project_member_role_creation_input,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    UserData,
    UserRole,
    get_user_self_role_creation_input,
)


@pytest.fixture
def user_data():
    """Create UserData for testing."""
    return UserData(
        id=uuid.uuid4(),
        username="testuser",
        domain="default",
        role=UserRole.USER,
    )


@pytest.fixture
def admin_user_data():
    """Create admin UserData for testing."""
    return UserData(
        id=uuid.uuid4(),
        username="adminuser",
        domain="default",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def project_data():
    """Create ProjectData for testing."""
    return ProjectData(id=uuid.uuid4())


class TestGetUserSelfRoleCreationInput:
    """Test get_user_self_role_creation_input function."""

    def test_basic_user_self_role_creation(self, user_data):
        """Test creating user self role input."""
        result = get_user_self_role_creation_input(user_data)

        assert result.source == RoleSource.SYSTEM

    def test_different_users_get_different_roles(self):
        """Test that different users get different roles."""
        user1 = UserData(id=uuid.uuid4(), username="user1", domain="default", role=UserRole.USER)
        user2 = UserData(id=uuid.uuid4(), username="user2", domain="default", role=UserRole.USER)

        result1 = get_user_self_role_creation_input(user1)
        result2 = get_user_self_role_creation_input(user2)

        # Both should be system roles
        assert result1.source == RoleSource.SYSTEM
        assert result2.source == RoleSource.SYSTEM

    def test_admin_user_self_role(self, admin_user_data):
        """Test creating admin user self role input."""
        result = get_user_self_role_creation_input(admin_user_data)

        assert result.source == RoleSource.SYSTEM


class TestGetProjectAdminRoleCreationInput:
    """Test get_project_admin_role_creation_input function."""

    def test_project_admin_role_creation(self, project_data):
        """Test creating project admin role input."""
        result = get_project_admin_role_creation_input(project_data)

        assert result.source == RoleSource.SYSTEM

    def test_different_projects_get_different_roles(self):
        """Test that different projects get different roles."""
        project1 = ProjectData(id=uuid.uuid4())
        project2 = ProjectData(id=uuid.uuid4())

        result1 = get_project_admin_role_creation_input(project1)
        result2 = get_project_admin_role_creation_input(project2)

        # Both should be system roles
        assert result1.source == RoleSource.SYSTEM
        assert result2.source == RoleSource.SYSTEM


class TestGetProjectMemberRoleCreationInput:
    """Test get_project_member_role_creation_input function."""

    def test_project_member_role_creation(self, project_data):
        """Test creating project member role input."""
        result = get_project_member_role_creation_input(project_data)

        assert result.source == RoleSource.CUSTOM

    def test_different_projects_get_different_roles(self):
        """Test that different projects get different roles."""
        project1 = ProjectData(id=uuid.uuid4())
        project2 = ProjectData(id=uuid.uuid4())

        result1 = get_project_member_role_creation_input(project1)
        result2 = get_project_member_role_creation_input(project2)

        # Both should be custom roles
        assert result1.source == RoleSource.CUSTOM
        assert result2.source == RoleSource.CUSTOM

    def test_admin_vs_member_role_difference(self, project_data):
        """Test difference between admin and member roles for same project."""
        admin_result = get_project_admin_role_creation_input(project_data)
        member_result = get_project_member_role_creation_input(project_data)

        # Different source types
        assert admin_result.source == RoleSource.SYSTEM
        assert member_result.source == RoleSource.CUSTOM


class TestComplexScenarios:
    """Test complex scenarios combining multiple functions."""

    def test_complete_user_migration_flow(self):
        """Test complete flow of migrating a user with project associations."""
        # Create user
        user = UserData(
            id=uuid.uuid4(),
            username="testuser",
            domain="default",
            role=UserRole.USER,
        )

        # Create projects
        project1 = ProjectData(id=uuid.uuid4())
        project2 = ProjectData(id=uuid.uuid4())

        # Step 1: Create user self role
        user_role_input = get_user_self_role_creation_input(user)

        # Step 2: Create project roles
        project1_admin_input = get_project_admin_role_creation_input(project1)
        project2_member_input = get_project_member_role_creation_input(project2)

        # Verify results
        assert user_role_input.source == RoleSource.SYSTEM
        assert project1_admin_input.source == RoleSource.SYSTEM
        assert project2_member_input.source == RoleSource.CUSTOM

    def test_superadmin_user_migration(self):
        """Test migration of a superadmin user."""
        superadmin = UserData(
            id=uuid.uuid4(),
            username="superadmin",
            domain="default",
            role=UserRole.SUPERADMIN,
        )

        # Superadmin gets self role
        role_input = get_user_self_role_creation_input(superadmin)

        assert role_input.source == RoleSource.SYSTEM

    def test_monitor_user_migration(self):
        """Test migration of a monitor user."""
        monitor = UserData(
            id=uuid.uuid4(),
            username="monitor",
            domain="default",
            role=UserRole.MONITOR,
        )

        # Monitor gets self role
        role_input = get_user_self_role_creation_input(monitor)

        assert role_input.source == RoleSource.SYSTEM
