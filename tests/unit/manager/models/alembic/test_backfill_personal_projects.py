"""Verifies the personal-project backfill migration against a real database.

Static analysis does not reach the migration's SQL, so the data migration is exercised
here: representative users go in, the backfill runs, and the rows it wrote are read
back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.alembic.versions.c7a4f1e9b023_backfill_personal_projects import (
    backfill,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    AssociationScopesEntitiesRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]


@dataclass
class DomainFixture:
    """The domain the backfilled users belong to."""

    name: DomainName
    id: DomainID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def domain(db: ExtendedAsyncSAEngine) -> DomainFixture:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    async with db.begin_session() as session:
        session.add(
            DomainRow(
                id=domain_id,
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
        )
        session.add(
            ProjectResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        session.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        session.add(
            VirtualEntityRow(entity_type="domain", entity_id=domain_id),
        )
        await session.commit()
    return DomainFixture(name=domain_name, id=domain_id)


async def _add_user(db: ExtendedAsyncSAEngine, domain: DomainFixture, username: str) -> uuid.UUID:
    """A user inserted directly, as one predating the personal-project path would be."""
    user_uuid = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            UserRow(
                uuid=user_uuid,
                username=username,
                email=f"{uuid.uuid4().hex[:8]}@test.local",
                password=PasswordInfo(
                    password="test-password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=domain.id,
                domain_name=domain.name,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                resource_policy="default",
            )
        )
        session.add(VirtualEntityRow(entity_type="user", entity_id=user_uuid))
        await session.commit()
    return user_uuid


async def _add_project(
    db: ExtendedAsyncSAEngine,
    domain: DomainFixture,
    name: str,
    project_type: ProjectType,
    creator_id: uuid.UUID | None = None,
) -> uuid.UUID:
    project_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            ProjectRow(
                id=project_id,
                name=name,
                domain_name=domain.name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                resource_policy="default",
                type=project_type,
                creator_id=creator_id,
            )
        )
        await session.commit()
    return project_id


async def _run_backfill(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(backfill)


async def _personal_projects(db: ExtendedAsyncSAEngine, domain: DomainFixture) -> list[ProjectRow]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(ProjectRow).where(
                        ProjectRow.domain_name == domain.name,
                        ProjectRow.type == ProjectType.PERSONAL,
                    )
                )
            ).all()
        )


class TestPersonalProjectBackfill:
    async def test_creates_one_project_per_user_named_after_the_username(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        await _add_user(db, domain, "alice")
        await _add_user(db, domain, "bob")

        await _run_backfill(db)

        projects = await _personal_projects(db, domain)
        assert sorted(p.name for p in projects) == ["alice", "bob"]
        assert all(p.resource_policy == "default" for p in projects)
        assert all(p.total_resource_slots == ResourceSlot() for p in projects)

    async def test_a_username_that_is_not_a_slug_is_slugified(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        """Signup fills the username with the e-mail address, which is not a slug."""
        await _add_user(db, domain, "alice@test.local")

        await _run_backfill(db)

        assert [p.name for p in await _personal_projects(db, domain)] == ["alice-test.local"]

    async def test_names_colliding_with_each_other_get_a_suffix(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        await _add_user(db, domain, "alice.test")
        await _add_user(db, domain, "alice@test")
        await _add_user(db, domain, "alice test")

        await _run_backfill(db)

        projects = await _personal_projects(db, domain)
        assert sorted(p.name for p in projects) == ["alice-test", "alice-test-2", "alice.test"]

    async def test_a_name_an_existing_project_holds_gets_a_suffix(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        await _add_project(db, domain, "alice", ProjectType.GENERAL)
        await _add_user(db, domain, "alice")

        await _run_backfill(db)

        assert [p.name for p in await _personal_projects(db, domain)] == ["alice-2"]

    async def test_running_it_again_creates_nothing(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        await _add_user(db, domain, "alice")

        await _run_backfill(db)
        await _run_backfill(db)

        assert len(await _personal_projects(db, domain)) == 1

    async def test_a_user_that_already_has_one_is_left_alone(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        user_uuid = await _add_user(db, domain, "alice")
        await _add_project(db, domain, "alice-existing", ProjectType.PERSONAL, creator_id=user_uuid)

        await _run_backfill(db)

        assert [p.name for p in await _personal_projects(db, domain)] == ["alice-existing"]

    async def test_the_project_records_the_user_it_was_created_for(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        user_uuid = await _add_user(db, domain, "alice")

        await _run_backfill(db)

        assert [p.creator_id for p in await _personal_projects(db, domain)] == [user_uuid]
