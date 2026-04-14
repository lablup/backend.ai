"""
Repository-level tests for ``query_userinfo`` delegation behavior (BA-5608).

These tests use a real DB via ``with_tables`` to verify that ``query_userinfo``
resolves the *owner's* role/group membership — not the requester's — when an
admin creates a session on behalf of another user via ``owner_access_key``.

Three scenarios are covered:

1. owner has group access AND requester has group access (admin → user, both
   in the same project) — should succeed and return the owner's UUID.
2. owner has group access, requester does NOT (admin can act on behalf via
   privilege escalation, but the target group is only reachable through the
   *owner's* explicit membership) — should still succeed because the owner's
   role/agus is what matters.
3. owner does NOT have group access (no agus row) — should raise
   ``ValueError("Invalid group")`` even though the requester is admin.
   Pre-fix this incorrectly succeeded because the requester's role bypassed
   the USER agus check.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.utils import query_userinfo
from ai.backend.testutils.db import with_tables


def _password_info() -> PasswordInfo:
    return PasswordInfo(
        password="test_password",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


@dataclass
class _Fixture:
    domain_name: str
    group_with_owner_id: uuid.UUID
    group_without_owner_id: uuid.UUID
    admin_uuid: uuid.UUID
    admin_access_key: AccessKey
    admin_resource_policy: dict[str, str]
    owner_uuid: uuid.UUID
    owner_access_key: AccessKey


@pytest.fixture
async def db_with_tables(
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
            ImageRow,
            VFolderRow,
            EndpointRow,
            SessionRow,
            AgentRow,
            KernelRow,
            RoutingRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def seeded(
    db_with_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[_Fixture, None]:
    """
    Seed:

    - one domain
    - two groups in that domain (G_with_owner, G_without_owner)
    - one keypair resource policy
    - admin user (role=ADMIN) + admin keypair
    - regular owner user (role=USER) + owner keypair
    - agus row linking owner → G_with_owner only
    - admin is also a member of G_with_owner (so admin can self-create there)
    """
    postfix = uuid.uuid4().hex[:8]
    domain_name = f"d-{postfix}"
    rp_name = f"rp-{postfix}"
    group_with_owner_id = uuid.uuid4()
    group_without_owner_id = uuid.uuid4()
    admin_uuid = uuid.uuid4()
    owner_uuid = uuid.uuid4()
    admin_ak = AccessKey(f"AKADMIN{postfix.upper()}"[:20])
    owner_ak = AccessKey(f"AKOWNER{postfix.upper()}"[:20])

    async with db_with_tables.begin_session() as db_sess:
        db_sess.add(DomainRow(name=domain_name, total_resource_slots=ResourceSlot()))
        db_sess.add(
            UserResourcePolicyRow(
                name=rp_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        db_sess.add(
            ProjectResourcePolicyRow(
                name=rp_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        db_sess.add(
            KeyPairResourcePolicyRow(
                name=rp_name,
                total_resource_slots=ResourceSlot(),
                max_concurrent_sessions=10,
                max_containers_per_session=1,
                idle_timeout=0,
                allowed_vfolder_hosts={},
            )
        )
        db_sess.add(
            GroupRow(
                id=group_with_owner_id,
                name=f"g-with-{postfix}",
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=rp_name,
            )
        )
        db_sess.add(
            GroupRow(
                id=group_without_owner_id,
                name=f"g-without-{postfix}",
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=rp_name,
            )
        )
        db_sess.add(
            UserRow(
                uuid=admin_uuid,
                email=f"admin-{postfix}@lablup.com",
                username=f"admin-{postfix}",
                password=_password_info(),
                domain_name=domain_name,
                role=UserRole.ADMIN,
                resource_policy=rp_name,
            )
        )
        db_sess.add(
            UserRow(
                uuid=owner_uuid,
                email=f"owner-{postfix}@lablup.com",
                username=f"owner-{postfix}",
                password=_password_info(),
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=rp_name,
            )
        )
        await db_sess.flush()
        db_sess.add(
            KeyPairRow(
                user_id=f"admin-{postfix}@lablup.com",
                access_key=admin_ak,
                secret_key="s" * 40,
                is_active=True,
                is_admin=True,
                resource_policy=rp_name,
                rate_limit=1000,
                user=admin_uuid,
            )
        )
        db_sess.add(
            KeyPairRow(
                user_id=f"owner-{postfix}@lablup.com",
                access_key=owner_ak,
                secret_key="s" * 40,
                is_active=True,
                is_admin=False,
                resource_policy=rp_name,
                rate_limit=1000,
                user=owner_uuid,
            )
        )
        # Owner is a member of group_with_owner only.
        db_sess.add(AssocGroupUserRow(user_id=owner_uuid, group_id=group_with_owner_id))
        await db_sess.commit()

    admin_resource_policy = {"name": rp_name}
    yield _Fixture(
        domain_name=domain_name,
        group_with_owner_id=group_with_owner_id,
        group_without_owner_id=group_without_owner_id,
        admin_uuid=admin_uuid,
        admin_access_key=admin_ak,
        admin_resource_policy=admin_resource_policy,
        owner_uuid=owner_uuid,
        owner_access_key=owner_ak,
    )


class TestQueryUserinfoDelegation:
    """BA-5608: query_userinfo must resolve owner's role and membership."""

    async def test_owner_and_requester_both_have_access(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """Scenario 1: admin delegates to owner; both belong to the target group."""
        async with db_with_tables.begin_readonly() as conn:
            ctx = await query_userinfo(
                conn,
                requester_uuid=seeded.admin_uuid,
                requester_access_key=seeded.admin_access_key,
                requester_role=UserRole.ADMIN,
                requester_domain=seeded.domain_name,
                keypair_resource_policy=seeded.admin_resource_policy,
                requesting_domain=seeded.domain_name,
                requesting_group=seeded.group_with_owner_id,
                query_on_behalf_of=seeded.owner_access_key,
            )
        assert ctx.owner_uuid == seeded.owner_uuid
        assert ctx.owner_role == UserRole.USER
        assert ctx.group_id == seeded.group_with_owner_id

    async def test_only_owner_has_group_membership(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """
        Scenario 2: requester admin has no agus row for the target group, but
        the owner does. The fix means USER-path agus check runs against the
        owner — so this must succeed.
        """
        async with db_with_tables.begin_readonly() as conn:
            ctx = await query_userinfo(
                conn,
                requester_uuid=seeded.admin_uuid,
                requester_access_key=seeded.admin_access_key,
                requester_role=UserRole.ADMIN,
                requester_domain=seeded.domain_name,
                keypair_resource_policy=seeded.admin_resource_policy,
                requesting_domain=seeded.domain_name,
                requesting_group=seeded.group_with_owner_id,
                query_on_behalf_of=seeded.owner_access_key,
            )
        assert ctx.owner_uuid == seeded.owner_uuid
        assert ctx.owner_role == UserRole.USER

    async def test_owner_has_no_group_access_must_fail(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """
        Scenario 3: owner has NO agus membership in the target group. The
        delegated request must be rejected, even though the requester is an
        admin. Pre-fix the requester's role short-circuited the USER path,
        causing this to incorrectly succeed.
        """
        async with db_with_tables.begin_readonly() as conn:
            with pytest.raises(ValueError, match="Invalid group"):
                await query_userinfo(
                    conn,
                    requester_uuid=seeded.admin_uuid,
                    requester_access_key=seeded.admin_access_key,
                    requester_role=UserRole.ADMIN,
                    requester_domain=seeded.domain_name,
                    keypair_resource_policy=seeded.admin_resource_policy,
                    requesting_domain=seeded.domain_name,
                    requesting_group=seeded.group_without_owner_id,
                    query_on_behalf_of=seeded.owner_access_key,
                )
