"""Test for vfolder RBAC migration with isolated database."""

import secrets
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

import pytest
import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker
from sqlalchemy.pool import NullPool

from ai.backend.common.types import HostPortPair
from ai.backend.logging import is_active as logging_active
from ai.backend.manager.models.alembic import invoked_programmatically
from ai.backend.manager.models.base import metadata, pgsql_connect_opts
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.migrate.vfolder import migrate_vfolder_data
from ai.backend.manager.models.rbac_models.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow

ALEMBIC_CONFIG_PATH = Path("alembic.ini")


@pytest.fixture
def test_db_name() -> str:
    """Generate a unique database name for testing."""
    return f"test_vfolder_rbac_{secrets.token_hex(8)}"


@pytest.fixture
def test_db_url(postgres_container: tuple[str, HostPortPair], test_db_name: str) -> str:
    """Create a database URL for the test database."""
    _, host_port = postgres_container
    db_user = "postgres"
    db_password = "develove"
    return f"postgresql+asyncpg://{db_user}:{db_password}@{host_port.host}:{host_port.port}/{test_db_name}"


@pytest.fixture
def admin_db_url(postgres_container: tuple[str, HostPortPair]) -> str:
    """Create a database URL for the admin database."""
    _, host_port = postgres_container
    db_user = "postgres"
    db_password = "develove"
    return f"postgresql+asyncpg://{db_user}:{db_password}@{host_port.host}:{host_port.port}/testing"


@pytest.fixture
def alembic_config(test_db_url: str) -> Config:
    """Create Alembic configuration for testing."""
    config = Config(ALEMBIC_CONFIG_PATH)
    config.set_main_option("script_location", "src/ai/backend/manager/models/alembic")
    config.set_main_option("sqlalchemy.url", test_db_url)
    logging_active.set(True)  # Why??
    return config


@pytest.fixture
async def db_engine_pre_migration(
    postgres_container: tuple[str, HostPortPair],
    test_db_name: str,
    alembic_config: Config,
    test_db_url: str,
    admin_db_url: str,
) -> AsyncIterator[Engine]:
    """
    Create a database engine with schema migrated up to revision before vfolder RBAC migration.
    This is the state before the vfolder RBAC migration.
    """
    # First create the test database
    admin_engine = create_async_engine(
        admin_db_url, poolclass=NullPool, isolation_level="AUTOCOMMIT"
    )

    def drop_and_create_db(connection: Connection) -> None:
        """Drop the test database if it exists and create a new one."""
        alembic_config.attributes["connection"] = connection
        connection.execute(sa.text(f'DROP DATABASE IF EXISTS "{test_db_name}";'))
        connection.execute(sa.text(f'CREATE DATABASE "{test_db_name}"'))

    async with admin_engine.connect() as conn:
        await conn.run_sync(drop_and_create_db)

    # Create engine for the test database
    engine = create_async_engine(
        test_db_url,
        poolclass=NullPool,
        echo=False,
        connect_args=pgsql_connect_opts,
    )

    invoked_programmatically.set(True)

    def create_all(connection: Connection, engine: Engine) -> None:
        alembic_config.attributes["connection"] = connection
        metadata.create_all(engine, checkfirst=False)
        # REVISION_BEFORE_VFOLDER_RBAC = "643deb439458"  # The revision before vfolder RBAC migration
        # target_revision = REVISION_BEFORE_VFOLDER_RBAC
        # connection.exec_driver_sql("CREATE TABLE alembic_version (\nversion_num varchar(32)\n);")
        # connection.exec_driver_sql(f"INSERT INTO alembic_version VALUES('{target_revision}')")

    async with engine.connect() as dbconn:
        async with dbconn.begin():
            await dbconn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            await dbconn.commit()
        async with dbconn.begin():
            await dbconn.run_sync(create_all, engine=engine.sync_engine)

    try:
        yield engine
    finally:
        # Cleanup: close connections and drop database
        await engine.dispose()

        def terminate(connection: Connection) -> None:
            """Terminate all connections to the test database and drop it."""
            alembic_config.attributes["connection"] = connection
            connection.execute(
                sa.text(
                    f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    f"WHERE datname = '{test_db_name}' AND pid <> pg_backend_pid()"
                )
            )
            connection.execute(sa.text(f"DROP DATABASE IF EXISTS {test_db_name}"))

        async with admin_engine.connect() as conn:
            await conn.run_sync(terminate)
        await admin_engine.dispose()


@dataclass
class TestUser:
    """Test user data."""

    id: str
    name: str
    email: str
    domain_name: str = "default"
    role: str = "user"


@dataclass
class TestGroup:
    """Test group (project) data."""

    id: str
    name: str
    domain_name: str = "default"


@dataclass
class TestVFolder:
    """Test vfolder data."""

    id: str
    name: str
    ownership_type: str  # "user" or "group"
    owner_id: str  # user uuid if ownership_type="user", group uuid if ownership_type="group"
    host: str = "test-host"
    domain_name: str = "default"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for database insertion."""
        return {
            "id": self.id,
            "name": self.name,
            "ownership_type": self.ownership_type,
            "user": self.owner_id if self.ownership_type == "user" else None,
            "group": self.owner_id if self.ownership_type == "group" else None,
            "host": self.host,
            "domain_name": self.domain_name,
        }

    def to_insert_dict(self) -> dict[str, Any]:
        """Convert to dict for database insertion with all required fields."""
        base_dict = self.to_dict()
        base_dict.update({
            "quota_scope_id": f"{self.ownership_type}:{self.owner_id}",
            "status": "ready",
            "usage_mode": "general",
            "permission": "rw",
            "max_files": 1000,
            "max_size": 10240,  # MBytes
            "num_files": 0,
            "cur_size": 0,
        })
        return base_dict


@dataclass
class TestVFolderPermission:
    """Test vfolder permission data."""

    id: str
    vfolder_id: str
    user_id: str
    permission: str  # "ro", "rw", "wd"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for database insertion."""
        return {
            "id": self.id,
            "vfolder": self.vfolder_id,
            "user": self.user_id,
            "permission": self.permission,
        }

    def to_insert_dict(self) -> dict[str, Any]:
        """Alias for to_dict for consistency."""
        return self.to_dict()


class VFolderRBACTestData:
    """Comprehensive test data for vfolder RBAC migration."""

    def __init__(self):
        # Create test users
        self.users = {
            "owner_user": TestUser(
                id=str(uuid.uuid4()),
                name="owner_user",
                email="owner@example.com",
            ),
            "member_user1": TestUser(
                id=str(uuid.uuid4()),
                name="member_user1",
                email="member1@example.com",
            ),
            "member_user2": TestUser(
                id=str(uuid.uuid4()),
                name="member_user2",
                email="member2@example.com",
            ),
            "external_user": TestUser(
                id=str(uuid.uuid4()),
                name="external_user",
                email="external@example.com",
            ),
        }

        # Create test groups
        self.groups = {
            "project1": TestGroup(
                id=str(uuid.uuid4()),
                name="project1",
            ),
            "project2": TestGroup(
                id=str(uuid.uuid4()),
                name="project2",
            ),
        }

        # Create test vfolders with various ownership scenarios
        self.vfolders = {
            # User-owned vfolders
            "user_vfolder_private": TestVFolder(
                id=str(uuid.uuid4()),
                name="user_vfolder_private",
                ownership_type="user",
                owner_id=self.users["owner_user"].id,
            ),
            "user_vfolder_shared_ro": TestVFolder(
                id=str(uuid.uuid4()),
                name="user_vfolder_shared_ro",
                ownership_type="user",
                owner_id=self.users["owner_user"].id,
            ),
            "user_vfolder_shared_rw": TestVFolder(
                id=str(uuid.uuid4()),
                name="user_vfolder_shared_rw",
                ownership_type="user",
                owner_id=self.users["owner_user"].id,
            ),
            "user_vfolder_shared_multiple": TestVFolder(
                id=str(uuid.uuid4()),
                name="user_vfolder_shared_multiple",
                ownership_type="user",
                owner_id=self.users["member_user1"].id,
            ),
            # Group-owned vfolders
            "group_vfolder_private": TestVFolder(
                id=str(uuid.uuid4()),
                name="group_vfolder_private",
                ownership_type="group",
                owner_id=self.groups["project1"].id,
            ),
            "group_vfolder_shared_ro": TestVFolder(
                id=str(uuid.uuid4()),
                name="group_vfolder_shared_ro",
                ownership_type="group",
                owner_id=self.groups["project1"].id,
            ),
            "group_vfolder_shared_mixed": TestVFolder(
                id=str(uuid.uuid4()),
                name="group_vfolder_shared_mixed",
                ownership_type="group",
                owner_id=self.groups["project2"].id,
            ),
        }

        # Create test permissions (vfolder invitations)
        self.permissions = [
            # User vfolder shared with read-only permission
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["user_vfolder_shared_ro"].id,
                user_id=self.users["member_user1"].id,
                permission="ro",
            ),
            # User vfolder shared with read-write permission
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["user_vfolder_shared_rw"].id,
                user_id=self.users["member_user2"].id,
                permission="rw",
            ),
            # User vfolder shared with multiple users with different permissions
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["user_vfolder_shared_multiple"].id,
                user_id=self.users["owner_user"].id,
                permission="ro",
            ),
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["user_vfolder_shared_multiple"].id,
                user_id=self.users["member_user2"].id,
                permission="rw",
            ),
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["user_vfolder_shared_multiple"].id,
                user_id=self.users["external_user"].id,
                permission="wd",
            ),
            # Group vfolder shared with external user (not in group)
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["group_vfolder_shared_ro"].id,
                user_id=self.users["external_user"].id,
                permission="ro",
            ),
            # Group vfolder shared with mixed permissions
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["group_vfolder_shared_mixed"].id,
                user_id=self.users["member_user1"].id,
                permission="ro",
            ),
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["group_vfolder_shared_mixed"].id,
                user_id=self.users["member_user2"].id,
                permission="rw",
            ),
            TestVFolderPermission(
                id=str(uuid.uuid4()),
                vfolder_id=self.vfolders["group_vfolder_shared_mixed"].id,
                user_id=self.users["external_user"].id,
                permission="wd",
            ),
        ]

    def get_vfolder_list(self) -> list[dict[str, Any]]:
        """Get all vfolders as list of dicts."""
        return [vf.to_dict() for vf in self.vfolders.values()]

    def get_vfolder_insert_list(self) -> list[dict[str, Any]]:
        """Get all vfolders as list of dicts for database insertion."""
        return [vf.to_insert_dict() for vf in self.vfolders.values()]

    def get_permission_list(self) -> list[dict[str, Any]]:
        """Get all permissions as list of dicts."""
        return [perm.to_dict() for perm in self.permissions]

    def get_permission_insert_list(self) -> list[dict[str, Any]]:
        """Get all permissions as list of dicts for database insertion."""
        return [perm.to_insert_dict() for perm in self.permissions]

    def get_vfolders_by_ownership(self, ownership_type: str) -> list[TestVFolder]:
        """Get vfolders filtered by ownership type."""
        return [vf for vf in self.vfolders.values() if vf.ownership_type == ownership_type]

    def get_permissions_by_vfolder(self, vfolder_id: str) -> list[TestVFolderPermission]:
        """Get permissions for a specific vfolder."""
        return [perm for perm in self.permissions if perm.vfolder_id == vfolder_id]

    def get_permissions_by_user(self, user_id: str) -> list[TestVFolderPermission]:
        """Get permissions granted to a specific user."""
        return [perm for perm in self.permissions if perm.user_id == user_id]


@pytest.fixture
def vfolder_rbac_test_data() -> VFolderRBACTestData:
    """Provide comprehensive test data for vfolder RBAC migration."""
    return VFolderRBACTestData()


@pytest.fixture
def test_scenarios(vfolder_rbac_test_data: VFolderRBACTestData) -> dict[str, Any]:
    """Provide specific test scenarios based on the test data."""
    data = vfolder_rbac_test_data

    return {
        "user_owned_private": {
            "description": "User-owned vfolder with no additional permissions",
            "vfolder": data.vfolders["user_vfolder_private"],
            "permissions": [],
            "expected_scope": ("user", data.users["owner_user"].id),
        },
        "user_owned_shared_single": {
            "description": "User-owned vfolder shared with one user (read-only)",
            "vfolder": data.vfolders["user_vfolder_shared_ro"],
            "permissions": data.get_permissions_by_vfolder(
                data.vfolders["user_vfolder_shared_ro"].id
            ),
            "expected_scope": ("user", data.users["owner_user"].id),
        },
        "user_owned_shared_multiple": {
            "description": "User-owned vfolder shared with multiple users with different permissions",
            "vfolder": data.vfolders["user_vfolder_shared_multiple"],
            "permissions": data.get_permissions_by_vfolder(
                data.vfolders["user_vfolder_shared_multiple"].id
            ),
            "expected_scope": ("user", data.users["member_user1"].id),
        },
        "group_owned_private": {
            "description": "Group-owned vfolder with no additional permissions",
            "vfolder": data.vfolders["group_vfolder_private"],
            "permissions": [],
            "expected_scope": ("project", data.groups["project1"].id),
        },
        "group_owned_shared_external": {
            "description": "Group-owned vfolder shared with external user",
            "vfolder": data.vfolders["group_vfolder_shared_ro"],
            "permissions": data.get_permissions_by_vfolder(
                data.vfolders["group_vfolder_shared_ro"].id
            ),
            "expected_scope": ("project", data.groups["project1"].id),
        },
        "group_owned_shared_mixed": {
            "description": "Group-owned vfolder with mixed permission levels",
            "vfolder": data.vfolders["group_vfolder_shared_mixed"],
            "permissions": data.get_permissions_by_vfolder(
                data.vfolders["group_vfolder_shared_mixed"].id
            ),
            "expected_scope": ("project", data.groups["project2"].id),
        },
    }


@pytest.fixture
def permission_mapping() -> dict[str, str]:
    """Mapping of vfolder permissions to expected RBAC operations."""
    return {
        "ro": "read",  # Read-only maps to read operation
        "rw": "read",  # Read-write also maps to read (write handled differently)
        "wd": "read",  # Write-delete also maps to read
    }


@pytest.fixture
async def populated_vfolder_db(db_engine_pre_migration, vfolder_rbac_test_data):
    """Populate the database with vfolder test data."""
    engine = db_engine_pre_migration
    data = vfolder_rbac_test_data

    async with engine.connect() as conn:
        async with conn.begin():
            # Insert domains (required for foreign keys)
            await conn.execute(
                sa.text("""
                    INSERT INTO domains (name, description, is_active, allowed_vfolder_hosts, allowed_docker_registries, dotfiles)
                    VALUES ('default', 'Default domain', true, '{}', '{}', '')
                    ON CONFLICT (name) DO NOTHING
                """)
            )

            # Insert user reesource policies
            await conn.execute(
                sa.text("""
                    INSERT INTO user_resource_policies (name, max_vfolder_count, max_quota_scope_size, max_session_count_per_model_session, max_customized_image_count)
                    VALUES ('default', 100, 100, 100, 100)
                    ON CONFLICT (name) DO NOTHING
                """)
            )

            # Insert users
            for user in data.users.values():
                await conn.execute(
                    sa.text("""
                        INSERT INTO users (uuid, email, username, password, 
                                        domain_name, role, status, resource_policy, sudo_session_enabled)
                        VALUES (:id, :email, :email, 'dummy_hash', 
                                :domain_name, :role, 'active', 'default', false)
                    """),
                    {
                        "id": user.id,
                        "email": user.email,
                        "domain_name": user.domain_name,
                        "role": user.role,
                    },
                )

            # Insert project resource policy
            await conn.execute(
                sa.text("""
                        INSERT INTO project_resource_policies (name, max_vfolder_count, max_quota_scope_size, max_network_count)
                        VALUES ('default', 100, 100, 100)
                        ON CONFLICT (name) DO NOTHING
                    """)
            )

            # Insert groups
            for group in data.groups.values():
                await conn.execute(
                    sa.text("""
                        INSERT INTO groups (id, name, is_active, domain_name, allowed_vfolder_hosts, dotfiles, resource_policy, type)
                        VALUES (:id, :name, true, :domain_name, '{}', '', 'default', 'general')
                    """),
                    {
                        "id": group.id,
                        "name": group.name,
                        "domain_name": group.domain_name,
                    },
                )

            # Insert vfolders
            for vfolder in data.vfolders.values():
                vf_data = vfolder.to_insert_dict()
                await conn.execute(
                    sa.text("""
                        INSERT INTO vfolders (id, name, ownership_type, "user", "group", host, 
                                            domain_name, quota_scope_id, status, usage_mode, 
                                            permission, max_files, max_size, num_files, cur_size, cloneable)
                        VALUES (:id, :name, :ownership_type, :user, :group, :host, 
                                :domain_name, :quota_scope_id, :status, :usage_mode, 
                                :permission, :max_files, :max_size, :num_files, :cur_size, true)
                    """),
                    vf_data,
                )

            # Insert vfolder permissions
            for perm in data.permissions:
                perm_data = perm.to_insert_dict()
                await conn.execute(
                    sa.text("""
                        INSERT INTO vfolder_permissions (id, vfolder, "user", permission)
                        VALUES (:id, :vfolder, :user, :permission)
                    """),
                    perm_data,
                )

    return data


class TestVFolderRBACMigrationWithAlembic:
    """Test vfolder RBAC migration using actual Alembic migrations."""

    async def test_populate_vfolder_data(
        self,
        db_engine_pre_migration: Engine,
        populated_vfolder_db: VFolderRBACTestData,
    ) -> None:
        """Test populating vfolder test data into database."""
        engine = db_engine_pre_migration
        data = populated_vfolder_db

        async with engine.connect() as conn:
            # Simple verification - just check counts
            result = await conn.execute(sa.text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            assert user_count == len(data.users), (
                f"Expected {len(data.users)} users, found {user_count}"
            )

            result = await conn.execute(sa.text("SELECT COUNT(*) FROM groups"))
            group_count = result.scalar()
            assert group_count == len(data.groups), (
                f"Expected {len(data.groups)} groups, found {group_count}"
            )

            result = await conn.execute(sa.text("SELECT COUNT(*) FROM vfolders"))
            vfolder_count = result.scalar()
            assert vfolder_count == len(data.vfolders), (
                f"Expected {len(data.vfolders)} vfolders, found {vfolder_count}"
            )

            result = await conn.execute(sa.text("SELECT COUNT(*) FROM vfolder_permissions"))
            permission_count = result.scalar()
            assert permission_count == len(data.permissions), (
                f"Expected {len(data.permissions)} permissions, found {permission_count}"
            )

        async with engine.connect() as conn:
            async with conn.begin():
                await conn.run_sync(migrate_vfolder_data)
            async_session_factory = sessionmaker(
                bind=conn, class_=AsyncSession, expire_on_commit=False
            )
            session = async_session_factory()
            async with session.begin():
                # 1. Verify all vfolders are in association_scopes_entities
                associations = await session.scalars(
                    # sa.select(AssociationScopesEntitiesRow)
                    sa.select(AssociationScopesEntitiesRow).where(
                        AssociationScopesEntitiesRow.entity_type == "vfolder"
                    )
                )
                association_rows = associations.all()

                assert len(association_rows) == len(data.vfolders), (
                    f"Expected {len(data.vfolders)} vfolder associations, found {len(association_rows)}"
                )

                # Create mapping for easy lookup
                associations_by_vfolder = {row.entity_id: row for row in association_rows}

                # Verify each vfolder's ownership mapping
                for vfolder in data.vfolders.values():
                    assoc = associations_by_vfolder.get(vfolder.id)
                    assert assoc is not None, f"VFolder {vfolder.id} not found in associations"

                    if vfolder.ownership_type == "user":
                        assert assoc.scope_type == "user", (
                            f"VFolder {vfolder.id} should have scope_type 'user'"
                        )
                        assert assoc.scope_id == vfolder.owner_id, (
                            f"VFolder {vfolder.id} scope_id mismatch"
                        )
                    else:  # group
                        assert assoc.scope_type == "project", (
                            f"VFolder {vfolder.id} should have scope_type 'project'"
                        )
                        assert assoc.scope_id == vfolder.owner_id, (
                            f"VFolder {vfolder.id} scope_id mismatch"
                        )

                # 2. Verify roles are created for each permission
                roles = await session.scalars(
                    sa.select(RoleRow).where(RoleRow.name.like("vfolder_granted_%"))  # type: ignore[attr-defined]
                )
                role_rows = roles.all()

                # Should have one role per unique vfolder that has permissions
                vfolders_with_permissions = {perm.vfolder_id for perm in data.permissions}
                assert len(role_rows) == len(vfolders_with_permissions), (
                    f"Expected {len(vfolders_with_permissions)} roles, found {len(role_rows)}"
                )

                # Create role mapping
                roles_by_name = {role.name: role for role in role_rows}

                # 3. Verify object permissions
                object_perms = await session.scalars(
                    sa.select(ObjectPermissionRow)
                    .where(ObjectPermissionRow.entity_type == "vfolder")
                    .options(selectinload(ObjectPermissionRow.role_row))
                )
                object_perm_rows = object_perms.all()

                inserted_obj_perm_vfolder_ids: set[str] = {
                    perm.vfolder_id for perm in data.permissions
                }
                row_ids = {op.entity_id for op in object_perm_rows}
                assert len(row_ids) == len(inserted_obj_perm_vfolder_ids), (
                    f"Expected {len(inserted_obj_perm_vfolder_ids)} object permissions, found {len(object_perm_rows)}"
                )

                # Verify each permission
                for perm in data.permissions:
                    expected_role_name = f"vfolder_granted_{perm.vfolder_id}"
                    role = roles_by_name.get(expected_role_name)
                    assert role is not None, f"Role {expected_role_name} not found"

                    # Find corresponding object permission
                    obj_perm = next(
                        (
                            op
                            for op in object_perm_rows
                            if op.entity_id == perm.vfolder_id and op.role_id == role.id
                        ),
                        None,
                    )
                    assert obj_perm is not None, (
                        f"Object permission not found for vfolder {perm.vfolder_id} with role {role.id}"
                    )

                    # All permissions map to 'read' operation in migration
                    assert obj_perm.operation == "read", (
                        f"Expected operation 'read' for vfolder {perm.vfolder_id}, got {obj_perm.operation}"
                    )
