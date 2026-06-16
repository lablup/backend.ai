"""Tests for PermissionDBSource role invitation methods."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.action.rbac_role_invitation import (
    CreateRoleInvitationByEmailAction,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.role_invitation.types import RoleInvitationState
from ai.backend.manager.errors.role_invitation import (
    RoleInvitationInvalidState,
    RoleInvitationNotFound,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.group.row import AssocGroupUserRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables

# ── shared fixtures ──────────────────────────────────────────────


@pytest.fixture
def password_info() -> PasswordInfo:
    return PasswordInfo(
        password="pw",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            DomainRow,
            ScalingGroupRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            RoleRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            GroupRow,
            AssocGroupUserRow,
            AssociationScopesEntitiesRow,
            ContainerRegistryRow,
            ImageRow,
            VFolderRow,
            EndpointRow,
            SessionRow,
            AgentRow,
            KernelRow,
            ReplicaGroupRow,
            RoutingRow,
            ResourcePresetRow,
            RoleInvitationRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def domain_name(db: ExtendedAsyncSAEngine) -> str:
    name = f"dom-{uuid.uuid4().hex[:8]}"
    async with db.begin_session() as s:
        s.add(
            DomainRow(
                name=name,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
        )
        await s.commit()
    return name


@pytest.fixture
async def user_policy(db: ExtendedAsyncSAEngine) -> str:
    name = f"pol-{uuid.uuid4().hex[:8]}"
    async with db.begin_session() as s:
        s.add(
            UserResourcePolicyRow(
                name=name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await s.commit()
    return name


async def _add_user(
    db: ExtendedAsyncSAEngine,
    domain_name: str,
    policy: str,
    pw: PasswordInfo,
    email: str,
) -> uuid.UUID:
    uid = uuid.uuid4()
    async with db.begin_session() as s:
        s.add(
            UserRow(
                uuid=uid,
                username=f"u-{uid.hex[:8]}",
                email=email,
                password=pw,
                need_password_change=False,
                full_name="",
                description="",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=policy,
            )
        )
        await s.commit()
    return uid


@pytest.fixture
async def inviter(
    db: ExtendedAsyncSAEngine,
    domain_name: str,
    user_policy: str,
    password_info: PasswordInfo,
) -> uuid.UUID:
    return await _add_user(db, domain_name, user_policy, password_info, "inviter@test.io")


@pytest.fixture
def invitee_email() -> str:
    return "invitee@test.io"


@pytest.fixture
async def invitee(
    db: ExtendedAsyncSAEngine,
    domain_name: str,
    user_policy: str,
    password_info: PasswordInfo,
    invitee_email: str,
) -> uuid.UUID:
    return await _add_user(db, domain_name, user_policy, password_info, invitee_email)


@pytest.fixture
async def role_id(db: ExtendedAsyncSAEngine) -> uuid.UUID:
    rid = uuid.uuid4()
    async with db.begin_session() as s:
        s.add(RoleRow(id=rid, name=f"role-{rid.hex[:8]}"))
        await s.commit()
    return rid


@pytest.fixture
def perm_db(db: ExtendedAsyncSAEngine) -> PermissionDBSource:
    return PermissionDBSource(db=db)


async def _insert_invitation(
    db: ExtendedAsyncSAEngine,
    inviter: uuid.UUID,
    invitee: uuid.UUID,
    role_id: uuid.UUID,
    state: RoleInvitationState = RoleInvitationState.PENDING,
) -> uuid.UUID:
    iid = uuid.uuid4()
    async with db.begin_session() as s:
        s.add(
            RoleInvitationRow(
                id=iid,
                inviter_user_id=inviter,
                invitee_user_id=invitee,
                role_id=role_id,
                state=state,
            )
        )
        await s.commit()
    return iid


# ── create ───────────────────────────────────────────────────────


class TestCreateRoleInvitation:
    @pytest.fixture
    def create_action(
        self,
        invitee_email: str,
        inviter: uuid.UUID,
        role_id: uuid.UUID,
    ) -> CreateRoleInvitationByEmailAction:
        return CreateRoleInvitationByEmailAction(
            invitee_emails=[invitee_email],
            inviter_user_id=inviter,
            role_id=role_id,
        )

    async def test_success_by_email(
        self,
        perm_db: PermissionDBSource,
        invitee: uuid.UUID,
        create_action: CreateRoleInvitationByEmailAction,
    ) -> None:
        result = await perm_db.create_invitation_by_email(
            invitee_emails=create_action.invitee_emails,
            inviter_user_id=create_action.inviter_user_id,
            role_id=create_action.role_id,
        )

        assert len(result.created) == 1
        assert result.created[0].invitee_user_id == invitee
        assert result.created[0].state == RoleInvitationState.PENDING

    async def test_unknown_email_skipped(
        self,
        perm_db: PermissionDBSource,
        inviter: uuid.UUID,
        role_id: uuid.UUID,
    ) -> None:
        action = CreateRoleInvitationByEmailAction(
            invitee_emails=["nobody@test.io"],
            inviter_user_id=inviter,
            role_id=role_id,
        )
        result = await perm_db.create_invitation_by_email(
            invitee_emails=action.invitee_emails,
            inviter_user_id=action.inviter_user_id,
            role_id=action.role_id,
        )

        assert len(result.created) == 0

    async def test_duplicate_active_invitation_skipped(
        self,
        perm_db: PermissionDBSource,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
        create_action: CreateRoleInvitationByEmailAction,
    ) -> None:
        await _insert_invitation(db, inviter, invitee, role_id)

        result = await perm_db.create_invitation_by_email(
            invitee_emails=create_action.invitee_emails,
            inviter_user_id=create_action.inviter_user_id,
            role_id=create_action.role_id,
        )

        assert len(result.created) == 0


# ── accept ───────────────────────────────────────────────────────


class TestAcceptRoleInvitation:
    @pytest.fixture
    async def pending_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(db, inviter, invitee, role_id)

    @pytest.fixture
    async def rejected_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(
            db, inviter, invitee, role_id, state=RoleInvitationState.REJECTED
        )

    @pytest.fixture
    async def canceled_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(
            db, inviter, invitee, role_id, state=RoleInvitationState.CANCELED
        )

    async def test_success(
        self,
        perm_db: PermissionDBSource,
        pending_id: uuid.UUID,
    ) -> None:
        result = await perm_db.accept_invitation(pending_id)

        assert result.state == RoleInvitationState.ACCEPTED

    async def test_not_found(self, perm_db: PermissionDBSource) -> None:
        with pytest.raises(RoleInvitationNotFound):
            await perm_db.accept_invitation(uuid.uuid4())

    async def test_already_rejected_fails(
        self,
        perm_db: PermissionDBSource,
        rejected_id: uuid.UUID,
    ) -> None:
        with pytest.raises(RoleInvitationInvalidState):
            await perm_db.accept_invitation(rejected_id)

    async def test_already_canceled_fails(
        self,
        perm_db: PermissionDBSource,
        canceled_id: uuid.UUID,
    ) -> None:
        with pytest.raises(RoleInvitationInvalidState):
            await perm_db.accept_invitation(canceled_id)


# ── reject ───────────────────────────────────────────────────────


class TestRejectRoleInvitation:
    @pytest.fixture
    async def pending_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(db, inviter, invitee, role_id)

    @pytest.fixture
    async def rejected_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(
            db, inviter, invitee, role_id, state=RoleInvitationState.REJECTED
        )

    @pytest.fixture
    async def accepted_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(
            db, inviter, invitee, role_id, state=RoleInvitationState.ACCEPTED
        )

    async def test_success(
        self,
        perm_db: PermissionDBSource,
        pending_id: uuid.UUID,
    ) -> None:
        result = await perm_db.reject_invitation(pending_id)

        assert result.state == RoleInvitationState.REJECTED

    async def test_not_found(self, perm_db: PermissionDBSource) -> None:
        with pytest.raises(RoleInvitationNotFound):
            await perm_db.reject_invitation(uuid.uuid4())

    async def test_already_rejected_is_idempotent(
        self,
        perm_db: PermissionDBSource,
        rejected_id: uuid.UUID,
    ) -> None:
        result = await perm_db.reject_invitation(rejected_id)

        assert result.state == RoleInvitationState.REJECTED

    async def test_already_accepted_fails(
        self,
        perm_db: PermissionDBSource,
        accepted_id: uuid.UUID,
    ) -> None:
        with pytest.raises(RoleInvitationInvalidState):
            await perm_db.reject_invitation(accepted_id)


# ── cancel ───────────────────────────────────────────────────────


class TestCancelRoleInvitation:
    @pytest.fixture
    async def pending_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(db, inviter, invitee, role_id)

    @pytest.fixture
    async def canceled_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(
            db, inviter, invitee, role_id, state=RoleInvitationState.CANCELED
        )

    @pytest.fixture
    async def accepted_id(
        self,
        db: ExtendedAsyncSAEngine,
        inviter: uuid.UUID,
        invitee: uuid.UUID,
        role_id: uuid.UUID,
    ) -> uuid.UUID:
        return await _insert_invitation(
            db, inviter, invitee, role_id, state=RoleInvitationState.ACCEPTED
        )

    async def test_success(
        self,
        perm_db: PermissionDBSource,
        pending_id: uuid.UUID,
    ) -> None:
        result = await perm_db.cancel_invitation(pending_id)

        assert result.state == RoleInvitationState.CANCELED

    async def test_not_found(self, perm_db: PermissionDBSource) -> None:
        with pytest.raises(RoleInvitationNotFound):
            await perm_db.cancel_invitation(uuid.uuid4())

    async def test_already_canceled_is_idempotent(
        self,
        perm_db: PermissionDBSource,
        canceled_id: uuid.UUID,
    ) -> None:
        result = await perm_db.cancel_invitation(canceled_id)

        assert result.state == RoleInvitationState.CANCELED

    async def test_already_accepted_fails(
        self,
        perm_db: PermissionDBSource,
        accepted_id: uuid.UUID,
    ) -> None:
        with pytest.raises(RoleInvitationInvalidState):
            await perm_db.cancel_invitation(accepted_id)
