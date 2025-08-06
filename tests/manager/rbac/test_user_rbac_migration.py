"""Test for user RBAC migration module."""

import uuid
from dataclasses import dataclass

import pytest

from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migrate.user import (
    ROLE_NAME_PREFIX,
    UserData,
    user_row_to_rbac_migration_data,
)
from ai.backend.manager.models.user import UserRole


@dataclass
class MockUserGroupAssociation:
    """Mock user-group association."""

    group_id: uuid.UUID


@dataclass
class MockUserRow:
    """Mock UserRow for testing."""

    uuid: uuid.UUID
    username: str
    domain_name: str
    role: UserRole
    groups: list[MockUserGroupAssociation]


@pytest.fixture
def mock_regular_user():
    """Create a mock regular user."""
    user_id = uuid.uuid4()
    group_id = uuid.uuid4()
    return MockUserRow(
        uuid=user_id,
        username="testuser",
        domain_name="default",
        role=UserRole.USER,
        groups=[MockUserGroupAssociation(group_id=group_id)],
    )


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user."""
    user_id = uuid.uuid4()
    group1_id = uuid.uuid4()
    group2_id = uuid.uuid4()
    return MockUserRow(
        uuid=user_id,
        username="adminuser",
        domain_name="default",
        role=UserRole.ADMIN,
        groups=[
            MockUserGroupAssociation(group_id=group1_id),
            MockUserGroupAssociation(group_id=group2_id),
        ],
    )


@pytest.fixture
def mock_user_no_groups():
    """Create a mock user with no groups."""
    user_id = uuid.uuid4()
    return MockUserRow(
        uuid=user_id,
        username="nogroups",
        domain_name="testing",
        role=UserRole.USER,
        groups=[],
    )


class TestUserDataClass:
    """Test UserData class methods."""

    def test_from_user_row(self, mock_regular_user):
        """Test creating UserData from UserRow."""
        user_data = UserData.from_user_row(mock_regular_user)

        assert user_data.id == mock_regular_user.uuid
        assert user_data.username == mock_regular_user.username
        assert user_data.domain == mock_regular_user.domain_name
        assert user_data.role == mock_regular_user.role
        assert len(user_data.registered_projects) == 1
        assert user_data.registered_projects[0].id == mock_regular_user.groups[0].group_id

    def test_to_role_create_input_basic(self, mock_regular_user):
        """Test converting UserData to role create input."""
        user_data = UserData.from_user_row(mock_regular_user)
        result = user_data.to_role_create_input()

        # Check role creation
        assert len(result.roles) == 1
        role = result.roles[0]
        assert role.name == f"{ROLE_NAME_PREFIX}{mock_regular_user.username}"

        # Check user-role association
        assert len(result.user_roles) == 1
        user_role = result.user_roles[0]
        assert user_role.user_id == mock_regular_user.uuid
        assert user_role.role_id == role.id

        # Check basic user permissions (7 base permissions + 1 project permission)
        assert len(result.scope_permissions) == 8

        # Check association scopes entities (1 for project)
        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]
        assert assoc.scope_id.scope_type == ScopeType.PROJECT
        assert assoc.scope_id.scope_id == str(mock_regular_user.groups[0].group_id)
        assert assoc.object_id.entity_type == EntityType.USER
        assert assoc.object_id.entity_id == str(mock_regular_user.uuid)

    def test_to_role_create_input_multiple_projects(self, mock_admin_user):
        """Test converting UserData with multiple projects."""
        user_data = UserData.from_user_row(mock_admin_user)
        result = user_data.to_role_create_input()

        # Check scope permissions (7 base + 2 project permissions)
        assert len(result.scope_permissions) == 9

        # Check association scopes entities (2 for projects)
        assert len(result.association_scopes_entities) == 2
        project_ids = {assoc.scope_id.scope_id for assoc in result.association_scopes_entities}
        expected_ids = {str(g.group_id) for g in mock_admin_user.groups}
        assert project_ids == expected_ids

    def test_to_role_create_input_no_projects(self, mock_user_no_groups):
        """Test converting UserData with no projects."""
        user_data = UserData.from_user_row(mock_user_no_groups)
        result = user_data.to_role_create_input()

        # Check scope permissions (only 7 base permissions)
        assert len(result.scope_permissions) == 7

        # Check no association scopes entities
        assert len(result.association_scopes_entities) == 0

    def test_scope_permissions_structure(self, mock_regular_user):
        """Test the structure of generated scope permissions."""
        user_data = UserData.from_user_row(mock_regular_user)
        result = user_data.to_role_create_input()

        # Extract user-scoped permissions
        user_permissions = [p for p in result.scope_permissions if p.scope_type == ScopeType.USER]

        # Should have all 7 operations for user entity
        expected_operations = {
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.GRANT_ALL,
            OperationType.GRANT_READ,
            OperationType.GRANT_UPDATE,
            OperationType.GRANT_SOFT_DELETE,
        }
        actual_operations = {p.operation for p in user_permissions}
        assert actual_operations == expected_operations

        # All should target the same user
        for perm in user_permissions:
            assert perm.scope_id == str(mock_regular_user.uuid)
            assert perm.entity_type == EntityType.USER


class TestUserConversion:
    """Test user conversion function."""

    def test_user_row_to_rbac_migration_data(self, mock_regular_user):
        """Test converting UserRow to RBAC migration data."""
        result = user_row_to_rbac_migration_data(mock_regular_user)

        assert len(result.roles) == 1
        assert result.roles[0].name == f"{ROLE_NAME_PREFIX}{mock_regular_user.username}"
        assert len(result.user_roles) == 1
        assert len(result.scope_permissions) == 8  # 7 base + 1 project
        assert len(result.association_scopes_entities) == 1


class TestComplexScenarios:
    """Test complex migration scenarios."""

    @pytest.fixture
    def test_users(self):
        """Create multiple test users."""
        users = []

        # User with multiple projects
        user1 = MockUserRow(
            uuid=uuid.uuid4(),
            username="multiproject",
            domain_name="default",
            role=UserRole.USER,
            groups=[
                MockUserGroupAssociation(group_id=uuid.uuid4()),
                MockUserGroupAssociation(group_id=uuid.uuid4()),
                MockUserGroupAssociation(group_id=uuid.uuid4()),
            ],
        )
        users.append(user1)

        # Admin user
        user2 = MockUserRow(
            uuid=uuid.uuid4(),
            username="superadmin",
            domain_name="default",
            role=UserRole.SUPERADMIN,
            groups=[MockUserGroupAssociation(group_id=uuid.uuid4())],
        )
        users.append(user2)

        # User with special characters in username
        user3 = MockUserRow(
            uuid=uuid.uuid4(),
            username="user.with-special_chars",
            domain_name="testing",
            role=UserRole.USER,
            groups=[],
        )
        users.append(user3)

        return users

    def test_multiple_users_different_roles(self, test_users):
        """Test converting multiple users with different roles."""
        results = []
        for user in test_users:
            result = user_row_to_rbac_migration_data(user)
            results.append(result)

        # Check each user gets unique role
        role_names = {r.roles[0].name for r in results}
        assert len(role_names) == len(test_users)

        # Check role names are properly formatted
        for user, result in zip(test_users, results):
            assert result.roles[0].name == f"{ROLE_NAME_PREFIX}{user.username}"

    def test_project_associations_consistency(self, test_users):
        """Test that project associations are consistent."""
        user_with_projects = test_users[0]  # multiproject user
        result = user_row_to_rbac_migration_data(user_with_projects)

        # Count project-scoped permissions
        project_permissions = [
            p for p in result.scope_permissions if p.scope_type == ScopeType.PROJECT
        ]

        # Should have one READ permission per project
        assert len(project_permissions) == len(user_with_projects.groups)

        # All permissions should be READ operations
        for perm in project_permissions:
            assert perm.operation == OperationType.READ
            assert perm.entity_type == EntityType.USER

    def test_constants(self):
        """Test module constants."""
        assert ROLE_NAME_PREFIX == "role_"
