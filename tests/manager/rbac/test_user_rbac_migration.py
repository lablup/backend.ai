"""Test for user RBAC migration module."""

import uuid

import pytest

from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    ADMIN_OPERATIONS,
    USER_SELF_SCOPE_OPERATIONS,
    ProjectData,
    ProjectUserAssociationData,
    UserData,
    UserRole,
    create_project_admin_role_and_permissions,
    create_project_member_role_and_permissions,
    create_user_self_role_and_permissions,
    map_user_to_project_role,
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


@pytest.fixture
def project_user_association():
    """Create ProjectUserAssociationData for testing."""
    return ProjectUserAssociationData(
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )


class TestCreateUserSelfRoleAndPermissions:
    """Test create_user_self_role_and_permissions function."""

    def test_basic_user_self_role_creation(self, user_data):
        """Test creating user self role and permissions."""
        result = create_user_self_role_and_permissions(user_data)

        # Check role creation
        assert len(result.roles) == 1
        role = result.roles[0]
        assert role.id is not None

        # Check user-role association
        assert len(result.user_roles) == 1
        user_role = result.user_roles[0]
        assert user_role.user_id == user_data.id
        assert user_role.role_id == role.id

        # Check scope permissions
        assert len(result.scope_permissions) == len(USER_SELF_SCOPE_OPERATIONS)
        for perm in result.scope_permissions:
            assert perm.role_id == role.id
            assert perm.scope_type == ScopeType.USER
            assert perm.scope_id == str(user_data.id)
            assert perm.entity_type == EntityType.USER
            assert perm.operation in USER_SELF_SCOPE_OPERATIONS

        # Check no association scopes entities
        assert (
            result.association_scopes_entities is None
            or len(result.association_scopes_entities) == 0
        )

    def test_user_self_permissions_completeness(self, user_data):
        """Test that all expected user self operations are included."""
        result = create_user_self_role_and_permissions(user_data)

        operations = {perm.operation for perm in result.scope_permissions}
        expected_operations = set(USER_SELF_SCOPE_OPERATIONS)

        assert operations == expected_operations

        # Verify specific operations are included
        assert OperationType.READ in operations
        assert OperationType.UPDATE in operations
        assert OperationType.SOFT_DELETE in operations
        assert OperationType.GRANT_ALL in operations
        assert OperationType.GRANT_READ in operations
        assert OperationType.GRANT_UPDATE in operations

        # Verify certain operations are NOT included
        assert OperationType.CREATE not in operations
        assert OperationType.HARD_DELETE not in operations

    def test_different_users_get_different_roles(self):
        """Test that different users get different role names and IDs."""
        user1 = UserData(id=uuid.uuid4(), username="user1", domain="default", role=UserRole.USER)
        user2 = UserData(id=uuid.uuid4(), username="user2", domain="default", role=UserRole.USER)

        result1 = create_user_self_role_and_permissions(user1)
        result2 = create_user_self_role_and_permissions(user2)

        # Different role IDs
        assert result1.roles[0].id != result2.roles[0].id


class TestCreateProjectAdminRoleAndPermissions:
    """Test create_project_admin_role_and_permissions function."""

    def test_project_admin_role_creation(self, project_data):
        """Test creating project admin role and permissions."""
        result = create_project_admin_role_and_permissions(project_data)

        # Check role creation
        assert len(result.roles) == 1
        role = result.roles[0]
        assert role.id is not None

        # Check no user-role associations (handled separately)
        assert result.user_roles is None or len(result.user_roles) == 0

        # Check scope permissions
        assert len(result.scope_permissions) == len(ADMIN_OPERATIONS)
        for perm in result.scope_permissions:
            assert perm.role_id == role.id
            assert perm.scope_type == ScopeType.PROJECT
            assert perm.scope_id == str(project_data.id)
            assert perm.entity_type == EntityType.USER
            assert perm.operation in ADMIN_OPERATIONS

        # Check no association scopes entities
        assert (
            result.association_scopes_entities is None
            or len(result.association_scopes_entities) == 0
        )

    def test_admin_permissions_completeness(self, project_data):
        """Test that all admin operations are included."""
        result = create_project_admin_role_and_permissions(project_data)

        operations = {perm.operation for perm in result.scope_permissions}
        expected_operations = set(ADMIN_OPERATIONS)

        assert operations == expected_operations

        # Verify all CRUD operations
        assert OperationType.CREATE in operations
        assert OperationType.READ in operations
        assert OperationType.UPDATE in operations
        assert OperationType.SOFT_DELETE in operations
        assert OperationType.HARD_DELETE in operations

        # Verify all grant operations
        assert OperationType.GRANT_ALL in operations
        assert OperationType.GRANT_READ in operations
        assert OperationType.GRANT_UPDATE in operations
        assert OperationType.GRANT_SOFT_DELETE in operations
        assert OperationType.GRANT_HARD_DELETE in operations


class TestCreateProjectUserRoleAndPermissions:
    """Test create_project_member_role_and_permissions function."""

    def test_project_user_role_creation(self, project_data):
        """Test creating project user role and permissions."""
        result = create_project_member_role_and_permissions(project_data)

        # Check role creation
        assert len(result.roles) == 1
        role = result.roles[0]
        assert role.id is not None

        # Check no user-role associations (handled separately)
        assert result.user_roles is None or len(result.user_roles) == 0

        # Check scope permissions - should only have READ
        assert len(result.scope_permissions) == 1
        perm = result.scope_permissions[0]
        assert perm.role_id == role.id
        assert perm.scope_type == ScopeType.PROJECT
        assert perm.scope_id == str(project_data.id)
        assert perm.entity_type == EntityType.USER
        assert perm.operation == OperationType.READ

        # Check no association scopes entities
        assert (
            result.association_scopes_entities is None
            or len(result.association_scopes_entities) == 0
        )


class TestMapUserToProjectRole:
    """Test map_user_to_project_role function."""

    def test_basic_user_project_mapping(self, project_user_association):
        """Test mapping user to project role."""
        role_id = uuid.uuid4()
        result = map_user_to_project_role(role_id, project_user_association)

        # Check user-role association
        assert len(result.user_roles) == 1
        user_role = result.user_roles[0]
        assert user_role.user_id == project_user_association.user_id
        assert user_role.role_id == role_id

        # Check association scopes entities
        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]
        assert assoc.scope_id.scope_type == ScopeType.PROJECT
        assert assoc.scope_id.scope_id == str(project_user_association.project_id)
        assert assoc.object_id.entity_type == EntityType.USER
        assert assoc.object_id.entity_id == str(project_user_association.user_id)

        # Check no roles or permissions in mapping result
        assert result.roles is None or len(result.roles) == 0
        assert result.scope_permissions is None or len(result.scope_permissions) == 0

    def test_multiple_users_same_project(self):
        """Test mapping multiple users to the same project role."""
        project_id = uuid.uuid4()
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4() for _ in range(3)]

        results = []
        for user_id in user_ids:
            association = ProjectUserAssociationData(
                project_id=project_id,
                user_id=user_id,
            )
            result = map_user_to_project_role(role_id, association)
            results.append(result)

        # All should have the same role_id but different user_ids
        for user_id, result in zip(user_ids, results):
            assert result.user_roles[0].role_id == role_id
            assert result.user_roles[0].user_id == user_id
            assert result.association_scopes_entities[0].scope_id.scope_id == str(project_id)
            assert result.association_scopes_entities[0].object_id.entity_id == str(user_id)

    def test_same_user_multiple_projects(self):
        """Test mapping the same user to multiple project roles."""
        user_id = uuid.uuid4()
        projects = [
            (uuid.uuid4(), uuid.uuid4()),  # (project_id, role_id)
            (uuid.uuid4(), uuid.uuid4()),
            (uuid.uuid4(), uuid.uuid4()),
        ]

        results = []
        for project_id, role_id in projects:
            association = ProjectUserAssociationData(
                project_id=project_id,
                user_id=user_id,
            )
            result = map_user_to_project_role(role_id, association)
            results.append(result)

        # Same user but different projects and roles
        for project, result in zip(projects, results):
            assert result.user_roles[0].user_id == user_id
            assert result.user_roles[0].role_id == project[1]
            assert result.association_scopes_entities[0].scope_id.scope_id == str(project[0])
            assert result.association_scopes_entities[0].object_id.entity_id == str(user_id)


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
        user_result = create_user_self_role_and_permissions(user)

        # Step 2: Create project roles
        project1_admin_result = create_project_admin_role_and_permissions(project1)
        project2_user_result = create_project_member_role_and_permissions(project2)

        # Step 3: Map user to projects
        # User is admin in project1
        association1 = ProjectUserAssociationData(project_id=project1.id, user_id=user.id)
        admin_role_id = project1_admin_result.roles[0].id
        assert admin_role_id is not None  # Type guard
        mapping1 = map_user_to_project_role(admin_role_id, association1)

        # User is regular member in project2
        association2 = ProjectUserAssociationData(project_id=project2.id, user_id=user.id)
        user_role_id = project2_user_result.roles[0].id
        assert user_role_id is not None  # Type guard
        mapping2 = map_user_to_project_role(user_role_id, association2)

        # Verify results
        assert len(user_result.scope_permissions) == len(USER_SELF_SCOPE_OPERATIONS)
        assert len(project1_admin_result.scope_permissions) == len(ADMIN_OPERATIONS)

        assert mapping1.user_roles[0].user_id == user.id
        assert mapping2.user_roles[0].user_id == user.id
        assert mapping1.user_roles[0].role_id != mapping2.user_roles[0].role_id
