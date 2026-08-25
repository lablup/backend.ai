"""Real-DB tests for answering an entity invitation.

Covers what the guards decide (whose invitation it is, whether it is still open) and
what acceptance writes into the RBAC graph — a membership that widens rather than
replaces what the invitee already held. Creating one is covered where the open-offer
conflict is: everything else about it is a plain entity insert.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.entity_invitation.types import (
    EntityInvitationData,
    EntityInvitationStatus,
)
from ai.backend.manager.errors.entity_invitation import (
    DuplicateEntityInvitationError,
    EntityInvitationNotFound,
)
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_invitation.creators import EntityInvitationCreator
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.specs.membership import EntityGrant
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.entity_invitation.repository import EntityInvitationRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

ensure_all_tables_registered()

_DOMAIN = "invitation-test-domain"
_DOMAIN_ID = DomainID(uuid4())
_POLICY = "invitation-test-policy"
_TARGET_TYPE = EntityType("vfolder")

_INVITER_ID = UserID(uuid4())
_INVITEE_ID = UserID(uuid4())
_OUTSIDER_ID = UserID(uuid4())
_INVITEE_EMAIL = "invitee@example.com"


def _target() -> RuntimeEntityID:
    return RuntimeEntityID(_TARGET_TYPE, _TARGET_ID)


_TARGET_ID = uuid4()


def _creator(
    email: str = _INVITEE_EMAIL,
    cap: Permission | None = Permission.READ,
) -> EntityInvitationCreator:
    return EntityInvitationCreator(
        inviter_user_id=_INVITER_ID,
        invitee_email=email,
        target=_target(),
        permission_cap=cap,
    )


def _password() -> PasswordInfo:
    return PasswordInfo(
        password="test_password",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


def _user(user_id: UserID, email: str) -> UserRow:
    return UserRow(
        uuid=user_id,
        username=f"u-{user_id.hex[:8]}",
        email=email,
        password=_password(),
        need_password_change=False,
        domain_name=_DOMAIN,
        domain_id=_DOMAIN_ID,
        resource_policy=_POLICY,
    )


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            VirtualScopeRow,
            EntityMembershipRow,
            ScopeBindingRow,
            EntityLabelRow,
            RoleRow,
            PermissionRow,
            DomainRow,
            UserResourcePolicyRow,
            UserRow,
            EntityInvitationRow,
        ],
    ):
        async with database_connection.begin_session() as session:
            session.add(DomainRow(id=_DOMAIN_ID, name=_DOMAIN, total_resource_slots=ResourceSlot()))
            session.add(
                UserResourcePolicyRow(
                    name=_POLICY,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            session.add_all([
                _user(_INVITER_ID, "inviter@example.com"),
                _user(_INVITEE_ID, _INVITEE_EMAIL),
                _user(_OUTSIDER_ID, "outsider@example.com"),
            ])
            await session.flush()
            # The target entity and the people are reachable in the graph; the
            # invitation joins the target and the grant lands in the invitee's scope.
            session.add_all([
                VirtualScopeRow(scope_type=_TARGET_TYPE, scope_id=_TARGET_ID),
                VirtualScopeRow(scope_type=USER_ENTITY_TYPE, scope_id=_INVITEE_ID),
                VirtualScopeRow(scope_type=USER_ENTITY_TYPE, scope_id=_OUTSIDER_ID),
            ])
        yield database_connection


@pytest.fixture
def ops(database: ExtendedAsyncSAEngine) -> OpsRepository[EntityInvitationData]:
    return OpsRepository(V2DBOpsProvider(database))


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> EntityInvitationRepository:
    return EntityInvitationRepository(V2DBOpsProvider(database))


async def _status(
    database: ExtendedAsyncSAEngine, invitation_id: EntityInvitationID
) -> EntityInvitationStatus:
    async with database.begin_readonly_session() as session:
        return (
            await session.execute(
                sa.select(EntityInvitationRow.status).where(EntityInvitationRow.id == invitation_id)
            )
        ).scalar_one()


async def _cap(database: ExtendedAsyncSAEngine, grantee: UserID) -> tuple[bool, Permission | None]:
    """Whether the invitee holds the target at all, and under what ceiling."""
    async with database.begin_readonly_session() as session:
        rows = (
            await session.execute(
                sa.select(EntityMembershipRow.permission_cap)
                .join(
                    VirtualScopeRow,
                    VirtualScopeRow.id == EntityMembershipRow.virtual_scope_id,
                )
                .where(
                    VirtualScopeRow.scope_type == USER_ENTITY_TYPE,
                    VirtualScopeRow.scope_id == grantee,
                    EntityMembershipRow.entity_type == _TARGET_TYPE,
                    EntityMembershipRow.entity_id == _TARGET_ID,
                )
            )
        ).all()
    if not rows:
        return False, None
    return True, rows[0][0]


async def _grant(database: ExtendedAsyncSAEngine, cap: Permission | None) -> None:
    async with V2DBOpsProvider(database).write_ops() as w:
        await w.grant_entities([
            EntityGrant(entity=_target(), grantee=_INVITEE_ID, permission_cap=cap)
        ])


class TestAccept:
    async def test_settles_the_invitation_and_grants_the_target(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        created = await ops.create_entity(_creator())
        data = await repository.accept(created.id, _INVITEE_ID)
        assert data.status == EntityInvitationStatus.ACCEPTED
        assert await _status(database, created.id) == EntityInvitationStatus.ACCEPTED
        assert await _cap(database, _INVITEE_ID) == (True, Permission.READ)

    async def test_widens_what_the_invitee_already_held(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        await _grant(database, Permission.UPDATE)
        created = await ops.create_entity(_creator(cap=Permission.READ))
        await repository.accept(created.id, _INVITEE_ID)
        assert await _cap(database, _INVITEE_ID) == (
            True,
            Permission.READ | Permission.UPDATE,
        )

    async def test_keeps_an_absent_ceiling_absent(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        await _grant(database, None)
        created = await ops.create_entity(_creator(cap=Permission.READ))
        await repository.accept(created.id, _INVITEE_ID)
        assert await _cap(database, _INVITEE_ID) == (True, None)

    async def test_somebody_elses_invitation_is_not_found(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        created = await ops.create_entity(_creator())
        with pytest.raises(EntityInvitationNotFound):
            await repository.accept(created.id, _OUTSIDER_ID)
        assert await _status(database, created.id) == EntityInvitationStatus.PENDING
        assert await _cap(database, _OUTSIDER_ID) == (False, None)

    async def test_an_answered_invitation_is_not_found(
        self,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        created = await ops.create_entity(_creator())
        await repository.accept(created.id, _INVITEE_ID)
        with pytest.raises(EntityInvitationNotFound):
            await repository.accept(created.id, _INVITEE_ID)

    async def test_an_invitation_that_was_never_there_is_not_found(
        self,
        repository: EntityInvitationRepository,
    ) -> None:
        with pytest.raises(EntityInvitationNotFound):
            await repository.accept(EntityInvitationID(uuid4()), _INVITEE_ID)


class TestReject:
    async def test_settles_the_invitation_and_grants_nothing(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        created = await ops.create_entity(_creator())
        data = await repository.reject(created.id, _INVITEE_ID)
        assert data.status == EntityInvitationStatus.REJECTED
        assert await _cap(database, _INVITEE_ID) == (False, None)

    async def test_somebody_elses_invitation_is_not_found(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        created = await ops.create_entity(_creator())
        with pytest.raises(EntityInvitationNotFound):
            await repository.reject(created.id, _OUTSIDER_ID)
        assert await _status(database, created.id) == EntityInvitationStatus.PENDING


class TestCancel:
    async def test_withdraws_a_pending_invitation(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        created = await ops.create_entity(_creator())
        data = await repository.cancel(created.id)
        assert data.status == EntityInvitationStatus.CANCELED
        assert await _cap(database, _INVITEE_ID) == (False, None)

    async def test_an_answered_invitation_is_not_found(
        self,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        created = await ops.create_entity(_creator())
        await repository.cancel(created.id)
        with pytest.raises(EntityInvitationNotFound):
            await repository.cancel(created.id)


class TestCreate:
    async def test_a_second_open_offer_conflicts(
        self,
        ops: OpsRepository[EntityInvitationData],
    ) -> None:
        await ops.create_entity(_creator())
        with pytest.raises(DuplicateEntityInvitationError):
            await ops.create_entity(_creator())

    async def test_a_new_offer_after_a_rejection_is_allowed(
        self,
        ops: OpsRepository[EntityInvitationData],
        repository: EntityInvitationRepository,
    ) -> None:
        first = await ops.create_entity(_creator())
        await repository.reject(first.id, _INVITEE_ID)
        second = await ops.create_entity(_creator())
        assert second.id != first.id

    async def test_the_invitation_joins_the_entity_it_offers(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityInvitationData],
    ) -> None:
        created = await ops.create_entity(_creator())
        async with database.begin_readonly_session() as session:
            joined: list[UUID] = list(
                (
                    await session.execute(
                        sa.select(EntityMembershipRow.entity_id)
                        .join(
                            VirtualScopeRow,
                            VirtualScopeRow.id == EntityMembershipRow.virtual_scope_id,
                        )
                        .where(
                            VirtualScopeRow.scope_type == _TARGET_TYPE,
                            VirtualScopeRow.scope_id == _TARGET_ID,
                            EntityMembershipRow.entity_type == "entity_invitation",
                        )
                    )
                ).scalars()
            )
        assert joined == [created.id]
