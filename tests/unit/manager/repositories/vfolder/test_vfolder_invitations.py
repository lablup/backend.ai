"""
Tests for VfolderRepository invitation getters focused on the inviter_username
fallback behavior introduced for BA-6193 (SSO-created accounts with empty email).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.vfolder.types import (
    VFolderInvitationState,
    VFolderMountPermission,
    VFolderOwnershipType,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import (
    VFolderInvitationRow,
    VFolderRow,
)
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory, DomainFixtureData


def _password() -> PasswordInfo:
    return PasswordInfo(
        password="test_password",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestInvitationGettersUsernameFallback:
    """Inviter username fallback (BA-6193) for invitation getter methods."""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK order: parents first
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                VFolderRow,
                VFolderInvitationRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_domain(
        self,
        domain_factory: DomainFactory,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        return await domain_factory(db_with_cleanup)

    @pytest.fixture
    async def user_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        policy_name = f"user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(policy)
        return policy_name

    async def _create_user(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        resource_policy: str,
        email: str,
        username: str | None,
    ) -> UserRow:
        user_uuid = uuid.uuid4()
        async with db.begin_session() as session:
            user = UserRow(
                uuid=user_uuid,
                username=username,
                email=email,
                password=_password(),
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=resource_policy,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    @pytest.fixture
    async def normal_inviter(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        user_resource_policy: str,
    ) -> UserRow:
        return await self._create_user(
            db_with_cleanup,
            domain_name=sample_domain.domain_name,
            resource_policy=user_resource_policy,
            email=f"inviter-{uuid.uuid4().hex[:8]}@example.com",
            username=f"inviter-{uuid.uuid4().hex[:8]}",
        )

    @pytest.fixture
    async def username_null_inviter(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        user_resource_policy: str,
    ) -> UserRow:
        return await self._create_user(
            db_with_cleanup,
            domain_name=sample_domain.domain_name,
            resource_policy=user_resource_policy,
            email=f"nullname-{uuid.uuid4().hex[:8]}@example.com",
            username=None,
        )

    @pytest.fixture
    async def invitee_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        user_resource_policy: str,
    ) -> UserRow:
        return await self._create_user(
            db_with_cleanup,
            domain_name=sample_domain.domain_name,
            resource_policy=user_resource_policy,
            email=f"invitee-{uuid.uuid4().hex[:8]}@example.com",
            username=f"invitee-{uuid.uuid4().hex[:8]}",
        )

    async def _create_vfolder(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        owner: UserRow,
    ) -> VFolderRow:
        vfolder_id = uuid.uuid4()
        async with db.begin_session() as session:
            vfolder = VFolderRow(
                id=vfolder_id,
                host="local",
                domain_name=domain_name,
                quota_scope_id=QuotaScopeID(QuotaScopeType.USER, owner.uuid),
                name=f"vf-{vfolder_id.hex[:8]}",
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.READ_WRITE,
                ownership_type=VFolderOwnershipType.USER,
                user=owner.uuid,
            )
            session.add(vfolder)
            await session.flush()
            await session.refresh(vfolder)
            return vfolder

    async def _create_invitation(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        vfolder: VFolderRow,
        inviter_email: str,
        invitee_email: str,
    ) -> VFolderInvitationRow:
        async with db.begin_session() as session:
            invitation = VFolderInvitationRow(
                vfolder=vfolder.id,
                inviter=inviter_email,
                invitee=invitee_email,
                permission=VFolderMountPermission.READ_ONLY,
                state=VFolderInvitationState.PENDING,
            )
            session.add(invitation)
            await session.flush()
            await session.refresh(invitation)
            return invitation

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> VfolderRepository:
        return VfolderRepository(db=db_with_cleanup)

    # ------------------------------------------------------------------
    # get_invitation_by_id
    # ------------------------------------------------------------------

    async def test_get_invitation_by_id_returns_username(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        normal_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup, domain_name=sample_domain.domain_name, owner=normal_inviter
        )
        invitation = await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=normal_inviter.email,
            invitee_email=invitee_user.email,
        )

        result = await repository.get_invitation_by_id(invitation.id)

        assert result is not None
        assert result.inviter == normal_inviter.email
        assert result.inviter_username == normal_inviter.username

    async def test_get_invitation_by_id_no_matching_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        normal_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup, domain_name=sample_domain.domain_name, owner=normal_inviter
        )
        invitation = await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email="orphan-inviter@example.com",
            invitee_email=invitee_user.email,
        )

        result = await repository.get_invitation_by_id(invitation.id)

        assert result is not None
        assert result.inviter == "orphan-inviter@example.com"
        assert result.inviter_username is None

    async def test_get_invitation_by_id_username_null(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        username_null_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup,
            domain_name=sample_domain.domain_name,
            owner=username_null_inviter,
        )
        invitation = await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=username_null_inviter.email,
            invitee_email=invitee_user.email,
        )

        result = await repository.get_invitation_by_id(invitation.id)

        assert result is not None
        assert result.inviter_username is None

    # ------------------------------------------------------------------
    # get_pending_invitations_for_user
    # ------------------------------------------------------------------

    async def test_get_pending_invitations_returns_username(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        normal_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup, domain_name=sample_domain.domain_name, owner=normal_inviter
        )
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=normal_inviter.email,
            invitee_email=invitee_user.email,
        )

        results = await repository.get_pending_invitations_for_user(invitee_user.email)

        assert len(results) == 1
        invitation_data, _ = results[0]
        assert invitation_data.inviter == normal_inviter.email
        assert invitation_data.inviter_username == normal_inviter.username

    async def test_get_pending_invitations_no_matching_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        normal_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup, domain_name=sample_domain.domain_name, owner=normal_inviter
        )
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email="orphan-inviter@example.com",
            invitee_email=invitee_user.email,
        )

        results = await repository.get_pending_invitations_for_user(invitee_user.email)

        assert len(results) == 1
        invitation_data, _ = results[0]
        assert invitation_data.inviter_username is None

    async def test_get_pending_invitations_username_null(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        username_null_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup,
            domain_name=sample_domain.domain_name,
            owner=username_null_inviter,
        )
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=username_null_inviter.email,
            invitee_email=invitee_user.email,
        )

        results = await repository.get_pending_invitations_for_user(invitee_user.email)

        assert len(results) == 1
        invitation_data, _ = results[0]
        assert invitation_data.inviter_username is None

    # ------------------------------------------------------------------
    # get_sent_invitations_for_user
    # ------------------------------------------------------------------

    async def test_get_sent_invitations_returns_username(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        normal_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup, domain_name=sample_domain.domain_name, owner=normal_inviter
        )
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=normal_inviter.email,
            invitee_email=invitee_user.email,
        )

        results = await repository.get_sent_invitations_for_user(normal_inviter.email)

        assert len(results) == 1
        invitation_data, _ = results[0]
        assert invitation_data.inviter == normal_inviter.email
        assert invitation_data.inviter_username == normal_inviter.username

    async def test_get_sent_invitations_no_matching_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        normal_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        # Inviter row has an email that does not match any UserRow.
        vfolder = await self._create_vfolder(
            db_with_cleanup, domain_name=sample_domain.domain_name, owner=normal_inviter
        )
        orphan_email = "orphan-inviter@example.com"
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=orphan_email,
            invitee_email=invitee_user.email,
        )

        results = await repository.get_sent_invitations_for_user(orphan_email)

        assert len(results) == 1
        invitation_data, _ = results[0]
        assert invitation_data.inviter_username is None

    async def test_get_sent_invitations_username_null(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        username_null_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup,
            domain_name=sample_domain.domain_name,
            owner=username_null_inviter,
        )
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=username_null_inviter.email,
            invitee_email=invitee_user.email,
        )

        results = await repository.get_sent_invitations_for_user(username_null_inviter.email)

        assert len(results) == 1
        invitation_data, _ = results[0]
        assert invitation_data.inviter_username is None

    # ------------------------------------------------------------------
    # get_vfolder_invitations_by_vfolder
    # ------------------------------------------------------------------

    async def test_get_vfolder_invitations_returns_username(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        normal_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup, domain_name=sample_domain.domain_name, owner=normal_inviter
        )
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=normal_inviter.email,
            invitee_email=invitee_user.email,
        )

        results = await repository.get_vfolder_invitations_by_vfolder(vfolder.id)

        assert len(results) == 1
        assert results[0].inviter == normal_inviter.email
        assert results[0].inviter_username == normal_inviter.username

    async def test_get_vfolder_invitations_no_matching_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        normal_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup, domain_name=sample_domain.domain_name, owner=normal_inviter
        )
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email="orphan-inviter@example.com",
            invitee_email=invitee_user.email,
        )

        results = await repository.get_vfolder_invitations_by_vfolder(vfolder.id)

        assert len(results) == 1
        assert results[0].inviter_username is None

    async def test_get_vfolder_invitations_username_null(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        username_null_inviter: UserRow,
        invitee_user: UserRow,
        repository: VfolderRepository,
    ) -> None:
        vfolder = await self._create_vfolder(
            db_with_cleanup,
            domain_name=sample_domain.domain_name,
            owner=username_null_inviter,
        )
        await self._create_invitation(
            db_with_cleanup,
            vfolder=vfolder,
            inviter_email=username_null_inviter.email,
            invitee_email=invitee_user.email,
        )

        results = await repository.get_vfolder_invitations_by_vfolder(vfolder.id)

        assert len(results) == 1
        assert results[0].inviter_username is None
