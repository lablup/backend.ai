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
    ProjectData,
    UserData,
    map_role_to_project,
    project_row_to_rbac_migration_data,
    user_row_to_rbac_migration_data,
)
from ai.backend.manager.models.user import UserRole


@dataclass
class MockUserGroupAssociation:
    """Mock user-group association."""

    user_id: uuid.UUID


@dataclass
class MockGroupRow:
    """Mock GroupRow for testing."""

    id: uuid.UUID
    users: list[MockUserGroupAssociation]


@dataclass
class MockUserRow:
    """Mock UserRow for testing."""

    uuid: uuid.UUID
    username: str
    domain_name: str
    role: UserRole


@pytest.fixture
def mock_regular_user():
    """Create a mock regular user."""
    user_id = uuid.uuid4()
    return MockUserRow(
        uuid=user_id,
        username="testuser",
        domain_name="default",
        role=UserRole.USER,
    )


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user."""
    user_id = uuid.uuid4()
    return MockUserRow(
        uuid=user_id,
        username="adminuser",
        domain_name="default",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_project():
    """Create a mock project with users."""
    project_id = uuid.uuid4()
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    return MockGroupRow(
        id=project_id,
        users=[
            MockUserGroupAssociation(user_id=user1_id),
            MockUserGroupAssociation(user_id=user2_id),
        ],
    )


@pytest.fixture
def mock_empty_project():
    """Create a mock project with no users."""
    project_id = uuid.uuid4()
    return MockGroupRow(
        id=project_id,
        users=[],
    )


class TestUserDataClass:
    """Test UserData class methods."""

    def test_from_row(self, mock_regular_user):
        """Test creating UserData from UserRow."""
        user_data = UserData.from_row(mock_regular_user)

        assert user_data.id == mock_regular_user.uuid
        assert user_data.username == mock_regular_user.username
        assert user_data.domain == mock_regular_user.domain_name
        assert user_data.role == mock_regular_user.role

    def test_role_name_property(self, mock_regular_user):
        """Test role_name property."""
        user_data = UserData.from_row(mock_regular_user)
        expected_name = f"{ROLE_NAME_PREFIX}user_{mock_regular_user.username}"
        assert user_data.role_name == expected_name

    def test_to_rbac_input_data(self, mock_regular_user):
        """Test converting UserData to RBAC input data."""
        user_data = UserData.from_row(mock_regular_user)
        result = user_data.to_rbac_input_data()

        # Check role creation
        assert len(result.roles) == 1
        role = result.roles[0]
        assert role.name == user_data.role_name

        # Check user-role association
        assert len(result.user_roles) == 1
        user_role = result.user_roles[0]
        assert user_role.user_id == mock_regular_user.uuid
        assert user_role.role_id == role.id

        # Check scope permissions (7 user permissions)
        assert len(result.scope_permissions) == 7

        # Check no association scopes entities for user
        assert (
            result.association_scopes_entities is None
            or len(result.association_scopes_entities) == 0
        )

    def test_scope_permissions_structure(self, mock_regular_user):
        """Test the structure of generated scope permissions."""
        user_data = UserData.from_row(mock_regular_user)
        result = user_data.to_rbac_input_data()

        # All permissions should be user-scoped
        for perm in result.scope_permissions:
            assert perm.scope_type == ScopeType.USER
            assert perm.scope_id == str(mock_regular_user.uuid)
            assert perm.entity_type == EntityType.USER

        # Should have all 7 operations
        expected_operations = {
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.GRANT_ALL,
            OperationType.GRANT_READ,
            OperationType.GRANT_UPDATE,
            OperationType.GRANT_SOFT_DELETE,
        }
        actual_operations = {p.operation for p in result.scope_permissions}
        assert actual_operations == expected_operations


class TestProjectDataClass:
    """Test ProjectData class methods."""

    def test_from_row(self, mock_project):
        """Test creating ProjectData from GroupRow."""
        project_data = ProjectData.from_row(mock_project)
        assert project_data.id == mock_project.id

    def test_role_name_property(self, mock_project):
        """Test role_name property."""
        project_data = ProjectData.from_row(mock_project)
        expected_name = f"{ROLE_NAME_PREFIX}project_{str(mock_project.id)[:8]}"
        assert project_data.role_name == expected_name

    def test_to_rbac_input_data(self, mock_project):
        """Test converting ProjectData to RBAC input data."""
        project_data = ProjectData.from_row(mock_project)
        result = project_data.to_rbac_input_data()

        # Check role creation
        assert len(result.roles) == 1
        role = result.roles[0]
        assert role.name == project_data.role_name

        # Check no user-role associations (handled separately)
        assert result.user_roles is None or len(result.user_roles) == 0

        # Check scope permissions (1 project permission)
        assert len(result.scope_permissions) == 1
        perm = result.scope_permissions[0]
        assert perm.scope_type == ScopeType.PROJECT
        assert perm.scope_id == str(mock_project.id)
        assert perm.entity_type == EntityType.USER
        assert perm.operation == OperationType.READ

        # Check no association scopes entities
        assert (
            result.association_scopes_entities is None
            or len(result.association_scopes_entities) == 0
        )


class TestConversionFunctions:
    """Test conversion functions."""

    def test_user_row_to_rbac_migration_data(self, mock_regular_user):
        """Test converting UserRow to RBAC migration data."""
        result = user_row_to_rbac_migration_data(mock_regular_user)

        assert len(result.roles) == 1
        assert result.roles[0].name == f"{ROLE_NAME_PREFIX}user_{mock_regular_user.username}"
        assert len(result.user_roles) == 1
        assert len(result.scope_permissions) == 7

    def test_project_row_to_rbac_migration_data(self, mock_project):
        """Test converting GroupRow to RBAC migration data."""
        result = project_row_to_rbac_migration_data(mock_project)

        assert len(result.roles) == 1
        assert result.roles[0].name.startswith(f"{ROLE_NAME_PREFIX}project_")
        assert len(result.scope_permissions) == 1


class TestRoleProjectMapping:
    """Test role to project mapping function."""

    def test_map_role_to_project_with_users(self, mock_project):
        """Test mapping role to project with users."""
        role_id = uuid.uuid4()
        result = map_role_to_project(role_id, mock_project)

        # Check user-role associations
        assert len(result.user_roles) == len(mock_project.users)
        for i, user_role in enumerate(result.user_roles):
            assert user_role.user_id == mock_project.users[i].user_id
            assert user_role.role_id == role_id

        # Check association scopes entities
        assert len(result.association_scopes_entities) == len(mock_project.users)
        for i, assoc in enumerate(result.association_scopes_entities):
            assert assoc.scope_id.scope_type == ScopeType.PROJECT
            assert assoc.scope_id.scope_id == str(mock_project.id)
            assert assoc.object_id.entity_type == EntityType.USER
            assert assoc.object_id.entity_id == str(mock_project.users[i].user_id)

        # Check no roles or permissions in mapping result
        assert result.roles is None or len(result.roles) == 0
        assert result.scope_permissions is None or len(result.scope_permissions) == 0

    def test_map_role_to_project_empty(self, mock_empty_project):
        """Test mapping role to empty project."""
        role_id = uuid.uuid4()
        result = map_role_to_project(role_id, mock_empty_project)

        # Should have empty lists
        assert len(result.user_roles) == 0
        assert len(result.association_scopes_entities) == 0


class TestComplexScenarios:
    """Test complex migration scenarios."""

    @pytest.fixture
    def test_data(self):
        """Create comprehensive test data."""
        users = [
            MockUserRow(
                uuid=uuid.uuid4(),
                username="user1",
                domain_name="default",
                role=UserRole.USER,
            ),
            MockUserRow(
                uuid=uuid.uuid4(),
                username="admin1",
                domain_name="default",
                role=UserRole.ADMIN,
            ),
            MockUserRow(
                uuid=uuid.uuid4(),
                username="superadmin",
                domain_name="testing",
                role=UserRole.SUPERADMIN,
            ),
        ]

        projects = [
            MockGroupRow(
                id=uuid.uuid4(),
                users=[
                    MockUserGroupAssociation(user_id=users[0].uuid),
                    MockUserGroupAssociation(user_id=users[1].uuid),
                ],
            ),
            MockGroupRow(
                id=uuid.uuid4(),
                users=[
                    MockUserGroupAssociation(user_id=users[0].uuid),
                    MockUserGroupAssociation(user_id=users[2].uuid),
                ],
            ),
        ]

        return {"users": users, "projects": projects}

    def test_multiple_users_conversion(self, test_data):
        """Test converting multiple users."""
        results = []
        for user in test_data["users"]:
            result = user_row_to_rbac_migration_data(user)
            results.append(result)

        # Check each user gets unique role
        role_names = {r.roles[0].name for r in results}
        assert len(role_names) == len(test_data["users"])

        # Verify all have proper permissions
        for result in results:
            assert len(result.scope_permissions) == 7
            assert len(result.user_roles) == 1

    def test_multiple_projects_conversion(self, test_data):
        """Test converting multiple projects."""
        project_results = []
        role_ids = []

        # Convert projects
        for project in test_data["projects"]:
            result = project_row_to_rbac_migration_data(project)
            project_results.append(result)
            role_ids.append(result.roles[0].id)

        # Map users to projects
        mapping_results = []
        for i, project in enumerate(test_data["projects"]):
            mapping = map_role_to_project(role_ids[i], project)
            mapping_results.append(mapping)

        # Verify project conversions
        for result in project_results:
            assert len(result.roles) == 1
            assert len(result.scope_permissions) == 1

        # Verify mappings
        for i, mapping in enumerate(mapping_results):
            expected_user_count = len(test_data["projects"][i].users)
            assert len(mapping.user_roles) == expected_user_count
            assert len(mapping.association_scopes_entities) == expected_user_count

    def test_user_in_multiple_projects(self, test_data):
        """Test handling users in multiple projects."""
        # User 0 is in both projects
        user = test_data["users"][0]

        # Create project roles and mappings
        mappings = []
        for project in test_data["projects"]:
            # Create project role
            project_result = project_row_to_rbac_migration_data(project)
            role_id = project_result.roles[0].id
            assert role_id is not None  # Type guard

            # Map users to project
            mapping = map_role_to_project(role_id, project)
            mappings.append(mapping)

        # Count how many times user appears in mappings
        user_role_count = sum(
            1
            for mapping in mappings
            for user_role in mapping.user_roles
            if user_role.user_id == user.uuid
        )

        # User should appear in both project mappings
        assert user_role_count == 2

    def test_constants(self):
        """Test module constants."""
        assert ROLE_NAME_PREFIX == "role_"
