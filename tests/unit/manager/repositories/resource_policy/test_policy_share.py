"""Real-DB tests for the share that puts a scope's resource policy within its reach.

A policy is a global catalog row, so what a scope reaches is the capped share these
writes state. Restating is the whole surface: the same call lends the current policy
and takes back the one before it.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from typing import Any, Final
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import aliased

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import AccessKey, ResourceSlot, SecretKey
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables

ensure_all_tables_registered()

_DOMAIN = "policy-share-domain"
_DOMAIN_ID = DomainID(uuid4())
_USER_ID = UserID(uuid4())
_PROJECT_ID = ProjectID(uuid4())
# Two of each kind, so reassignment has somewhere to move to.
_FIRST = "policy-share-first"
_SECOND = "policy-share-second"

# The entity type each policy row stands for.
_POLICY_TYPES: Final[Mapping[Any, EntityType]] = {
    UserResourcePolicyRow: UserResourcePolicyEntityType(),
    ProjectResourcePolicyRow: ProjectResourcePolicyEntityType(),
    KeyPairResourcePolicyRow: KeyPairResourcePolicyEntityType(),
}


def _password() -> PasswordInfo:
    return PasswordInfo(
        password="test_password",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


def _user_policy(name: str) -> UserResourcePolicyRow:
    return UserResourcePolicyRow(
        name=name,
        max_vfolder_count=0,
        max_quota_scope_size=-1,
        max_session_count_per_model_session=10,
        max_customized_image_count=10,
    )


def _project_policy(name: str) -> ProjectResourcePolicyRow:
    return ProjectResourcePolicyRow(
        name=name, max_vfolder_count=0, max_quota_scope_size=-1, max_network_count=0
    )


def _keypair_policy(name: str) -> KeyPairResourcePolicyRow:
    return KeyPairResourcePolicyRow(
        name=name,
        total_resource_slots=ResourceSlot(),
        max_concurrent_sessions=10,
        max_containers_per_session=1,
        idle_timeout=0,
    )


def _keypair(access_key: str, policy: str, *, is_default: bool, is_active: bool) -> KeyPairRow:
    return KeyPairRow(
        access_key=AccessKey(access_key),
        secret_key=SecretValue(SecretKey(f"SK{uuid4().hex[:38]}")),
        user=_USER_ID,
        is_active=is_active,
        is_admin=False,
        is_default=is_default,
        resource_policy=policy,
    )


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            VirtualEntityRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            ScopeBindingRow,
            DomainRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            ProjectRow,
            KeyPairRow,
        ],
    ):
        async with database_connection.begin_session() as session:
            session.add(DomainRow(id=_DOMAIN_ID, name=_DOMAIN, total_resource_slots=ResourceSlot()))
            for name in (_FIRST, _SECOND):
                session.add(_user_policy(name))
                session.add(_project_policy(name))
                session.add(_keypair_policy(name))
            await session.flush()
            session.add(
                UserRow(
                    uuid=_USER_ID,
                    username="policy-share-user",
                    email="policy-share@example.com",
                    password=_password(),
                    need_password_change=False,
                    domain_name=_DOMAIN,
                    domain_id=_DOMAIN_ID,
                    resource_policy=_FIRST,
                )
            )
            session.add(
                ProjectRow(
                    id=_PROJECT_ID,
                    name="policy-share-project",
                    domain_name=_DOMAIN,
                    type=ProjectType.GENERAL,
                    resource_policy=_FIRST,
                    total_resource_slots=ResourceSlot(),
                )
            )
            await session.flush()
        yield database_connection


async def _shared_policies(
    db: ExtendedAsyncSAEngine, scope: EntityIdentifier, policy_row: Any
) -> list[tuple[str, bool, list[Permission]]]:
    """What the scope holds of that policy kind: the policy's name, whether the edge is
    capped, and the operations the cap lends."""
    entity_type = _POLICY_TYPES[policy_row]
    scope_node = aliased(VirtualEntityRow)
    policy_node = aliased(VirtualEntityRow)
    async with db.begin_readonly_session() as session:
        rows = (
            await session.execute(
                sa.select(
                    policy_row.name,
                    EntityMembershipRow.capped,
                    EntityMembershipRow.id,
                )
                .select_from(EntityMembershipRow)
                .join(scope_node, scope_node.id == EntityMembershipRow.virtual_entity_id)
                .join(policy_node, policy_node.id == EntityMembershipRow.member_entity_id)
                .join(policy_row, policy_row.uuid == policy_node.entity_id)
                .where(
                    scope_node.entity_type == scope.entity_type(),
                    scope_node.entity_id == scope,
                    policy_node.entity_type == entity_type,
                )
            )
        ).all()
        held: list[tuple[str, bool, list[Permission]]] = []
        for row in rows:
            caps = (
                await session.scalars(
                    sa.select(EntityMembershipCapRow.permission).where(
                        EntityMembershipCapRow.membership_id == row.id
                    )
                )
            ).all()
            held.append((row.name, row.capped, sorted(caps, key=int)))
        return held


class TestTheScopeReachesItsOwnPolicy:
    async def test_the_user_is_lent_their_user_policy_capped_to_read(
        self, database: ExtendedAsyncSAEngine
    ) -> None:
        async with ResourcePolicyOpsProvider(database).write_ops() as w:
            await w.restate_user_resource_policy_share(_USER_ID)
        assert await _shared_policies(database, _USER_ID, UserResourcePolicyRow) == [
            (_FIRST, True, [Permission.READ])
        ]

    async def test_the_project_is_lent_its_project_policy_capped_to_read(
        self, database: ExtendedAsyncSAEngine
    ) -> None:
        async with ResourcePolicyOpsProvider(database).write_ops() as w:
            await w.restate_project_resource_policy_share(_PROJECT_ID)
        assert await _shared_policies(database, _PROJECT_ID, ProjectResourcePolicyRow) == [
            (_FIRST, True, [Permission.READ])
        ]

    async def test_reassigning_the_policy_leaves_only_the_new_one(
        self, database: ExtendedAsyncSAEngine
    ) -> None:
        provider = ResourcePolicyOpsProvider(database)
        async with provider.write_ops() as w:
            await w.restate_user_resource_policy_share(_USER_ID)
        async with database.begin_session() as session:
            await session.execute(
                sa.update(UserRow).where(UserRow.uuid == _USER_ID).values(resource_policy=_SECOND)
            )
        async with provider.write_ops() as w:
            await w.restate_user_resource_policy_share(_USER_ID)
        assert await _shared_policies(database, _USER_ID, UserResourcePolicyRow) == [
            (_SECOND, True, [Permission.READ])
        ]

    async def test_the_default_key_names_the_keypair_policy(
        self, database: ExtendedAsyncSAEngine
    ) -> None:
        async with database.begin_session() as session:
            session.add(_keypair("AKFIRST", _SECOND, is_default=False, is_active=True))
            session.add(_keypair("AKDEFAULT", _FIRST, is_default=True, is_active=True))
            await session.flush()
        async with ResourcePolicyOpsProvider(database).write_ops() as w:
            await w.restate_keypair_resource_policy_share(_USER_ID)
        assert await _shared_policies(database, _USER_ID, KeyPairResourcePolicyRow) == [
            (_FIRST, True, [Permission.READ])
        ]

    async def test_a_user_with_no_active_key_is_lent_no_keypair_policy(
        self, database: ExtendedAsyncSAEngine
    ) -> None:
        async with database.begin_session() as session:
            session.add(_keypair("AKINACTIVE", _FIRST, is_default=True, is_active=False))
            await session.flush()
        async with ResourcePolicyOpsProvider(database).write_ops() as w:
            await w.restate_keypair_resource_policy_share(_USER_ID)
        assert await _shared_policies(database, _USER_ID, KeyPairResourcePolicyRow) == []


class TestTheScopeIsNotLentSomebodyElsesPolicy:
    async def test_the_user_scope_reaches_no_project_policy(
        self, database: ExtendedAsyncSAEngine
    ) -> None:
        async with ResourcePolicyOpsProvider(database).write_ops() as w:
            await w.restate_user_resource_policy_share(_USER_ID)
        assert await _shared_policies(database, _USER_ID, ProjectResourcePolicyRow) == []

    async def test_the_project_scope_reaches_no_user_policy(
        self, database: ExtendedAsyncSAEngine
    ) -> None:
        async with ResourcePolicyOpsProvider(database).write_ops() as w:
            await w.restate_project_resource_policy_share(_PROJECT_ID)
        assert await _shared_policies(database, _PROJECT_ID, UserResourcePolicyRow) == []
