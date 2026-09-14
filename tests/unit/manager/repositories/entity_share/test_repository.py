"""Real-DB tests for answering an entity invitation.

Covers what the guards decide (whose invitation it is, whether it is still open) and
what acceptance writes into the RBAC graph — a membership that widens rather than
replaces what the invitee already held. Creating one is covered where the open-offer
conflict is: everything else about it is a plain entity insert.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import aliased

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, RuntimeEntityID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.entity_share.types import (
    EntityShareData,
    EntityShareStatus,
)
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.entity_share import (
    EntityShareNotFound,
    ShareToAPersonalProject,
    ShareToTheOwningScope,
)
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_share.creators import EntityShareCreator
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
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
from ai.backend.manager.repositories.entity_share.repository import EntityShareRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

ensure_all_tables_registered()

_DOMAIN = "invitation-test-domain"
_DOMAIN_ID = DomainID(uuid4())
_POLICY = "invitation-test-policy"
_TARGET_TYPE = VFolderEntityType()

_INVITER_ID = UserID(uuid4())
_INVITEE_ID = UserID(uuid4())
_INVITEE_PROJECT_ID = ProjectID(uuid4())
_TEAM_PROJECT_ID = ProjectID(uuid4())
_OUTSIDER_PROJECT_ID = ProjectID(uuid4())
_OUTSIDER_ID = UserID(uuid4())
_INVITEE_EMAIL = "invitee@example.com"


def _target() -> RuntimeEntityID:
    return RuntimeEntityID(_TARGET_TYPE, _TARGET_ID)


_TARGET_ID = uuid4()


def _creator(
    email: str = _INVITEE_EMAIL,
    cap: Permission | None = Permission.READ,
    expires_at: datetime | None = None,
) -> EntityShareCreator:
    return EntityShareCreator(
        sharer_user_id=_INVITER_ID,
        recipient_email=email,
        target=_target(),
        permission_cap=cap,
        expires_at=expires_at,
    )


def _creator_to(
    recipient: EntityIdentifier, cap: Permission | None = Permission.READ
) -> EntityShareCreator:
    """An offer naming a scope rather than an address."""
    return EntityShareCreator(
        sharer_user_id=_INVITER_ID,
        recipient=recipient,
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


def _personal_project(project_id: ProjectID, creator_id: UserID) -> ProjectRow:
    return ProjectRow(
        id=project_id,
        name=f"p-{project_id.hex[:8]}",
        domain_name=_DOMAIN,
        type=ProjectType.PERSONAL,
        creator_id=creator_id,
        resource_policy=_POLICY,
        total_resource_slots=ResourceSlot(),
    )


def _team_project(project_id: ProjectID) -> ProjectRow:
    """A project people share into, which belongs to nobody in particular."""
    return ProjectRow(
        id=project_id,
        name=f"t-{project_id.hex[:8]}",
        domain_name=_DOMAIN,
        type=ProjectType.GENERAL,
        resource_policy=_POLICY,
        total_resource_slots=ResourceSlot(),
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
            VirtualEntityRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
            ScopeBindingRow,
            EntityLabelRow,
            RoleRow,
            PermissionRow,
            DomainRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            UserRow,
            ProjectRow,
            EntityShareRow,
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
            session.add(
                ProjectResourcePolicyRow(
                    name=_POLICY,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=0,
                )
            )
            session.add_all([
                _user(_INVITER_ID, "inviter@example.com"),
                _user(_INVITEE_ID, _INVITEE_EMAIL),
                _user(_OUTSIDER_ID, "outsider@example.com"),
            ])
            await session.flush()
            # Every account has the project that is theirs alone, which is where what
            # they take lands.
            session.add_all([
                _personal_project(_INVITEE_PROJECT_ID, _INVITEE_ID),
                _personal_project(_OUTSIDER_PROJECT_ID, _OUTSIDER_ID),
                _team_project(_TEAM_PROJECT_ID),
            ])
            await session.flush()
            # The target entity and the people are reachable in the graph; the
            # invitation joins the target and the grant lands in the invitee's scope.
            session.add_all([
                VirtualEntityRow(entity_type=_TARGET_TYPE, entity_id=_TARGET_ID),
                VirtualEntityRow(entity_type=UserEntityType(), entity_id=_INVITEE_ID),
                VirtualEntityRow(entity_type=UserEntityType(), entity_id=_OUTSIDER_ID),
                VirtualEntityRow(entity_type=ProjectEntityType(), entity_id=_INVITEE_PROJECT_ID),
                VirtualEntityRow(entity_type=ProjectEntityType(), entity_id=_OUTSIDER_PROJECT_ID),
                VirtualEntityRow(entity_type=ProjectEntityType(), entity_id=_TEAM_PROJECT_ID),
            ])
        yield database_connection


@pytest.fixture
def ops(database: ExtendedAsyncSAEngine) -> OpsRepository[EntityShareData]:
    return OpsRepository(V2DBOpsProvider(database))


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> EntityShareRepository:
    return EntityShareRepository(ShareOpsProvider(database))


async def _status(database: ExtendedAsyncSAEngine, share_id: EntityShareID) -> EntityShareStatus:
    async with database.begin_readonly_session() as session:
        return (
            await session.execute(
                sa.select(EntityShareRow.status).where(EntityShareRow.id == share_id)
            )
        ).scalar_one()


async def _cap(
    database: ExtendedAsyncSAEngine, grantee: EntityIdentifier
) -> tuple[bool, Permission | None]:
    """Whether the scope holds the target at all, and under what ceiling."""
    target = aliased(VirtualEntityRow, name="target_virtual_entity")
    async with database.begin_readonly_session() as session:
        rows = (
            await session.execute(
                sa.select(
                    EntityMembershipRow.virtual_entity_id, EntityMembershipRow.member_entity_id
                )
                .join(
                    VirtualEntityRow,
                    VirtualEntityRow.id == EntityMembershipRow.virtual_entity_id,
                )
                .join(target, target.id == EntityMembershipRow.member_entity_id)
                .where(
                    VirtualEntityRow.entity_type == grantee.entity_type(),
                    VirtualEntityRow.entity_id == grantee,
                    target.entity_type == _TARGET_TYPE,
                    target.entity_id == _TARGET_ID,
                )
            )
        ).all()
        if not rows:
            return False, None
        cap = await VirtualEntitySeeder().edge_cap(
            session, rows[0].virtual_entity_id, rows[0].member_entity_id
        )
    return True, cap


async def _share(database: ExtendedAsyncSAEngine, cap: Permission) -> None:
    async with ShareOpsProvider(database).write_ops() as w:
        await w.replace_share(_INVITEE_PROJECT_ID, _target(), cap)


async def _belong(database: ExtendedAsyncSAEngine) -> None:
    """A belonging edge to the target: no ceiling, which a share never states."""
    await _share(database, Permission.NONE)
    async with database.begin_session() as sess:
        await sess.execute(
            sa.update(EntityMembershipRow)
            .values(capped=False)
            .where(EntityMembershipRow.capped.is_(True))
        )


class TestAccept:
    async def test_settles_the_invitation_and_grants_the_target(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        data = await repository.accept(created.id, _INVITEE_ID)
        assert data.status == EntityShareStatus.ACCEPTED
        assert await _status(database, created.id) == EntityShareStatus.ACCEPTED
        assert await _cap(database, _INVITEE_PROJECT_ID) == (True, Permission.READ)

    async def test_widens_what_the_invitee_already_held(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        await _share(database, Permission.UPDATE)
        created = await repository.create(_creator(cap=Permission.READ))
        await repository.accept(created.id, _INVITEE_ID)
        assert await _cap(database, _INVITEE_PROJECT_ID) == (
            True,
            Permission.READ | Permission.UPDATE,
        )

    async def test_keeps_an_absent_ceiling_absent(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        await _belong(database)
        created = await repository.create(_creator(cap=Permission.READ))
        await repository.accept(created.id, _INVITEE_ID)
        assert await _cap(database, _INVITEE_PROJECT_ID) == (True, None)

    async def test_somebody_elses_invitation_is_not_found(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        with pytest.raises(EntityShareNotFound):
            await repository.accept(created.id, _OUTSIDER_ID)
        assert await _status(database, created.id) == EntityShareStatus.PENDING
        assert await _cap(database, _OUTSIDER_ID) == (False, None)

    async def test_an_answered_invitation_is_not_found(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        await repository.accept(created.id, _INVITEE_ID)
        with pytest.raises(EntityShareNotFound):
            await repository.accept(created.id, _INVITEE_ID)

    async def test_an_invitation_that_was_never_there_is_not_found(
        self,
        repository: EntityShareRepository,
    ) -> None:
        with pytest.raises(EntityShareNotFound):
            await repository.accept(EntityShareID(uuid4()), _INVITEE_ID)


class TestReject:
    async def test_settles_the_invitation_and_grants_nothing(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        data = await repository.reject(created.id, _INVITEE_ID)
        assert data.status == EntityShareStatus.REJECTED
        assert await _cap(database, _INVITEE_PROJECT_ID) == (False, None)

    async def test_somebody_elses_invitation_is_not_found(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        with pytest.raises(EntityShareNotFound):
            await repository.reject(created.id, _OUTSIDER_ID)
        assert await _status(database, created.id) == EntityShareStatus.PENDING


class TestCancel:
    async def test_withdraws_a_pending_invitation(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        data = await repository.cancel(created.id)
        assert data.status == EntityShareStatus.CANCELED
        assert await _cap(database, _INVITEE_PROJECT_ID) == (False, None)

    async def test_an_answered_invitation_is_not_found(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        await repository.cancel(created.id)
        with pytest.raises(EntityShareNotFound):
            await repository.cancel(created.id)


class TestCreate:
    async def test_offering_again_restates_the_one_standing(
        self,
        repository: EntityShareRepository,
    ) -> None:
        first = await repository.create(_creator(cap=Permission.READ))
        again = await repository.create(_creator(cap=Permission.UPDATE))
        assert again.id == first.id
        assert again.permission_cap == Permission.UPDATE

    async def test_offering_again_to_a_taken_share_states_what_it_lends(
        self,
        database: ExtendedAsyncSAEngine,
        repository: EntityShareRepository,
    ) -> None:
        offered = await repository.create(_creator(cap=Permission.READ | Permission.UPDATE))
        await repository.accept(offered.id, _INVITEE_ID)
        await repository.create(_creator(cap=Permission.READ))
        assert await _cap(database, _INVITEE_PROJECT_ID) == (True, Permission.READ)

    async def test_a_new_offer_after_a_rejection_is_allowed(
        self,
        repository: EntityShareRepository,
    ) -> None:
        first = await repository.create(_creator())
        await repository.reject(first.id, _INVITEE_ID)
        second = await repository.create(_creator())
        assert second.id != first.id

    async def test_the_invitation_joins_the_entity_it_offers(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        member = aliased(VirtualEntityRow, name="member_virtual_entity")
        async with database.begin_readonly_session() as session:
            joined: list[UUID] = list(
                (
                    await session.execute(
                        sa.select(member.entity_id)
                        .join(
                            EntityMembershipRow,
                            EntityMembershipRow.member_entity_id == member.id,
                        )
                        .join(
                            VirtualEntityRow,
                            VirtualEntityRow.id == EntityMembershipRow.virtual_entity_id,
                        )
                        .where(
                            VirtualEntityRow.entity_type == _TARGET_TYPE,
                            VirtualEntityRow.entity_id == _TARGET_ID,
                            member.entity_type == "entity_share",
                        )
                    )
                ).scalars()
            )
        assert joined == [created.id]


class TestAProjectAnswering:
    async def test_a_project_takes_what_it_was_offered(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator_to(_TEAM_PROJECT_ID))
        data = await repository.accept(created.id, _TEAM_PROJECT_ID)
        assert data.status == EntityShareStatus.ACCEPTED
        assert data.recipient == RuntimeEntityID(ProjectEntityType(), _TEAM_PROJECT_ID)
        assert await _cap(database, _TEAM_PROJECT_ID) == (True, Permission.READ)

    async def test_a_project_gives_back_what_it_took(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator_to(_TEAM_PROJECT_ID))
        await repository.accept(created.id, _TEAM_PROJECT_ID)
        await repository.leave(created.id, _TEAM_PROJECT_ID)
        assert await _status(database, created.id) == EntityShareStatus.REVOKED
        assert await _cap(database, _TEAM_PROJECT_ID) == (False, None)

    async def test_an_offer_addressed_elsewhere_is_not_found(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator_to(_TEAM_PROJECT_ID))
        with pytest.raises(EntityShareNotFound):
            await repository.accept(created.id, _INVITEE_ID)


class TestExpiry:
    async def test_an_offer_out_of_time_is_not_found(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        past = datetime.now(UTC) - timedelta(minutes=1)
        created = await repository.create(_creator(expires_at=past))
        with pytest.raises(EntityShareNotFound):
            await repository.accept(created.id, _INVITEE_ID)

    async def test_an_offer_still_in_time_is_taken(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        ahead = datetime.now(UTC) + timedelta(minutes=1)
        created = await repository.create(_creator(expires_at=ahead))
        data = await repository.accept(created.id, _INVITEE_ID)
        assert data.status == EntityShareStatus.ACCEPTED


class TestAddressedByEmail:
    async def test_answering_records_the_scope_that_answered(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        assert created.recipient is None
        data = await repository.accept(created.id, _INVITEE_ID)
        assert data.recipient == RuntimeEntityID(UserEntityType(), _INVITEE_ID)


class TestRevoke:
    async def test_takes_the_entity_from_where_it_landed(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        await repository.accept(created.id, _INVITEE_ID)
        await repository.revoke(created.id)
        assert await _status(database, created.id) == EntityShareStatus.REVOKED
        assert await _cap(database, _INVITEE_PROJECT_ID) == (False, None)

    async def test_a_pending_offer_is_not_found(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        with pytest.raises(EntityShareNotFound):
            await repository.revoke(created.id)

    async def test_cancel_does_not_reach_what_was_taken(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        created = await repository.create(_creator())
        await repository.accept(created.id, _INVITEE_ID)
        with pytest.raises(EntityShareNotFound):
            await repository.cancel(created.id)


class TestWhatCannotBeNamed:
    async def test_an_entity_outside_the_graph_cannot_be_offered(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        """The graph holds the pair unique and the row points at it, so an entity with
        no node has nothing to point at."""
        stranger = RuntimeEntityID(_TARGET_TYPE, uuid4())
        with pytest.raises(BackendAIError):
            await repository.create(
                EntityShareCreator(
                    sharer_user_id=_INVITER_ID,
                    recipient_email=_INVITEE_EMAIL,
                    target=stranger,
                    permission_cap=Permission.READ,
                )
            )

    async def test_a_scope_outside_the_graph_cannot_receive(
        self,
        ops: OpsRepository[EntityShareData],
        repository: EntityShareRepository,
    ) -> None:
        stranger = ProjectID(uuid4())
        with pytest.raises(BackendAIError):
            await repository.create(_creator_to(stranger))


class TestWhatIsRefused:
    async def test_a_scope_owning_the_entity_is_refused(
        self,
        database: ExtendedAsyncSAEngine,
        repository: EntityShareRepository,
    ) -> None:
        """Lending states what holds now, so an owner would end up with less."""
        async with ShareOpsProvider(database).write_ops() as w:
            await w.transfer([], [_TEAM_PROJECT_ID], _target())
        with pytest.raises(ShareToTheOwningScope):
            await repository.create(_creator_to(_TEAM_PROJECT_ID))

    async def test_a_personal_project_is_refused(
        self,
        repository: EntityShareRepository,
    ) -> None:
        """A person is reached as a person, so their own project is not a second handle."""
        with pytest.raises(ShareToAPersonalProject):
            await repository.create(_creator_to(_INVITEE_PROJECT_ID))


class TestRestatingCarriesTheMoment:
    async def test_restating_an_offer_takes_the_new_sender_and_moment(
        self,
        database: ExtendedAsyncSAEngine,
        repository: EntityShareRepository,
    ) -> None:
        first = await repository.create(
            _creator(expires_at=datetime.now(UTC) + timedelta(minutes=5))
        )
        ahead = datetime.now(UTC) + timedelta(hours=1)
        again = await repository.create(
            EntityShareCreator(
                sharer_user_id=_OUTSIDER_ID,
                recipient_email=_INVITEE_EMAIL,
                target=_target(),
                permission_cap=Permission.READ,
                expires_at=ahead,
            )
        )
        assert again.id == first.id
        assert again.sharer_user_id == _OUTSIDER_ID
        assert first.expires_at is not None
        assert again.expires_at is not None
        assert again.expires_at > first.expires_at

    async def test_taking_an_offer_clears_the_moment(
        self,
        repository: EntityShareRepository,
    ) -> None:
        offered = await repository.create(
            _creator(expires_at=datetime.now(UTC) + timedelta(minutes=5))
        )
        taken = await repository.accept(offered.id, _INVITEE_ID)
        assert taken.expires_at is None

    async def test_restating_a_taken_share_keeps_its_sender_and_no_moment(
        self,
        repository: EntityShareRepository,
    ) -> None:
        offered = await repository.create(_creator())
        await repository.accept(offered.id, _INVITEE_ID)
        again = await repository.create(
            EntityShareCreator(
                sharer_user_id=_OUTSIDER_ID,
                recipient_email=_INVITEE_EMAIL,
                target=_target(),
                permission_cap=Permission.UPDATE,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        assert again.sharer_user_id == _INVITER_ID
        assert again.expires_at is None
        assert again.permission_cap == Permission.UPDATE

    async def test_an_ended_offer_is_left_alone(
        self,
        database: ExtendedAsyncSAEngine,
        repository: EntityShareRepository,
    ) -> None:
        first = await repository.create(_creator())
        await repository.reject(first.id, _INVITEE_ID)
        second = await repository.create(_creator())
        assert second.id != first.id
        assert await _status(database, first.id) == EntityShareStatus.REJECTED
