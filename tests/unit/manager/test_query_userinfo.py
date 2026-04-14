"""
Tests for query_userinfo() and query_userinfo_from_session() in manager/utils.py.

These functions validate user/domain/group ownership when creating sessions.
They raise BackendAIError subclasses for invalid parameters (previously ValueError → 500).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from dataclasses import dataclass
from uuid import UUID

import pytest

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import AccessKeyNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, create_async_engine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.utils import query_userinfo, query_userinfo_from_session
from ai.backend.testutils.db import with_tables

ALL_ROWS = [
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
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    RoutingRow,
    ResourcePresetRow,
]


@dataclass
class SeedData:
    domain_name: str
    group_id: UUID
    group_name: str
    user_uuid: UUID
    access_key: AccessKey
    kp_policy_name: str
    user_policy_name: str
    proj_policy_name: str


@dataclass
class ExtraUserData:
    user_uuid: UUID
    access_key: AccessKey


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def database_connection(
    postgres_container: tuple[str, HostPortPairModel],
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    _, addr = postgres_container
    url = f"postgresql+asyncpg://postgres:develove@{addr.host}:{addr.port}/testing"
    engine = create_async_engine(url, pool_size=8, pool_pre_ping=False, max_overflow=64)
    yield engine
    await engine.dispose()


# ---------------------------------------------------------------------------
# TestQueryUserinfo — SAConnection path
# ---------------------------------------------------------------------------


class TestQueryUserinfo:
    """Tests for query_userinfo() using SAConnection."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, ALL_ROWS):
            yield database_connection

    @pytest.fixture
    async def seed(self, db: ExtendedAsyncSAEngine) -> AsyncGenerator[SeedData, None]:
        """Create a normal user who is a member of a group."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        group_id = uuid.uuid4()
        group_name = f"test-group-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        access_key = AccessKey(f"AK{uuid.uuid4().hex[:16]}")
        kp_policy = f"kp-policy-{uuid.uuid4().hex[:8]}"
        user_policy = f"user-policy-{uuid.uuid4().hex[:8]}"
        proj_policy = f"proj-policy-{uuid.uuid4().hex[:8]}"

        async with db.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=user_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=proj_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name=kp_policy,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"user-{uuid.uuid4().hex[:8]}",
                    email=f"test-{uuid.uuid4().hex[:8]}@test.io",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    access_key=access_key,
                    secret_key="secret",
                    user=user_uuid,
                    is_active=True,
                    resource_policy=kp_policy,
                )
            )
            sess.add(
                GroupRow(
                    id=group_id,
                    name=group_name,
                    domain_name=domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=proj_policy,
                )
            )
            await sess.flush()
            sess.add(AssocGroupUserRow(user_id=user_uuid, group_id=group_id))
            await sess.commit()

        yield SeedData(
            domain_name=domain_name,
            group_id=group_id,
            group_name=group_name,
            user_uuid=user_uuid,
            access_key=access_key,
            kp_policy_name=kp_policy,
            user_policy_name=user_policy,
            proj_policy_name=proj_policy,
        )

    @pytest.fixture
    async def non_member_group(
        self, db: ExtendedAsyncSAEngine, seed: SeedData
    ) -> AsyncGenerator[str, None]:
        """A group in the same domain that the seed user is NOT a member of."""
        name = f"other-group-{uuid.uuid4().hex[:8]}"
        async with db.begin_session() as sess:
            sess.add(
                GroupRow(
                    id=uuid.uuid4(),
                    name=name,
                    domain_name=seed.domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=seed.proj_policy_name,
                )
            )
            await sess.commit()
        yield name

    @pytest.fixture
    async def inactive_domain_user(
        self, db: ExtendedAsyncSAEngine, seed: SeedData
    ) -> AsyncGenerator[ExtraUserData, None]:
        """A user belonging to an inactive domain."""
        domain = f"inactive-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        ak = AccessKey(f"AK{uuid.uuid4().hex[:16]}")
        user_policy = f"inactive-up-{uuid.uuid4().hex[:8]}"

        async with db.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=domain,
                    is_active=False,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=user_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"inactive-{uuid.uuid4().hex[:8]}",
                    email=f"inactive-{uuid.uuid4().hex[:8]}@test.io",
                    domain_name=domain,
                    role=UserRole.USER,
                    resource_policy=user_policy,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    access_key=ak,
                    secret_key="secret",
                    user=user_uuid,
                    is_active=True,
                    resource_policy=seed.kp_policy_name,
                )
            )
            await sess.commit()
        yield ExtraUserData(user_uuid=user_uuid, access_key=ak)

    @pytest.fixture
    async def superadmin(
        self, db: ExtendedAsyncSAEngine, seed: SeedData
    ) -> AsyncGenerator[ExtraUserData, None]:
        """A superadmin in the same domain as seed."""
        admin_uuid = uuid.uuid4()
        admin_ak = AccessKey(f"AK{uuid.uuid4().hex[:16]}")
        async with db.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=admin_uuid,
                    username=f"admin-{uuid.uuid4().hex[:8]}",
                    email=f"admin-{uuid.uuid4().hex[:8]}@test.io",
                    domain_name=seed.domain_name,
                    role=UserRole.SUPERADMIN,
                    resource_policy=seed.user_policy_name,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    access_key=admin_ak,
                    secret_key="secret",
                    user=admin_uuid,
                    is_active=True,
                    resource_policy=seed.kp_policy_name,
                )
            )
            await sess.commit()
        yield ExtraUserData(user_uuid=admin_uuid, access_key=admin_ak)

    # -- success cases --

    async def test_success_with_group_name(self, db: ExtendedAsyncSAEngine, seed: SeedData) -> None:
        async with db.begin() as conn:
            result = await query_userinfo(
                conn,
                seed.user_uuid,
                seed.access_key,
                UserRole.USER,
                seed.domain_name,
                {"some": "policy"},
                seed.domain_name,
                seed.group_name,
            )
        assert result.owner_uuid == seed.user_uuid
        assert result.group_id == seed.group_id
        assert result.owner_role == UserRole.USER

    async def test_success_with_group_id(self, db: ExtendedAsyncSAEngine, seed: SeedData) -> None:
        async with db.begin() as conn:
            result = await query_userinfo(
                conn,
                seed.user_uuid,
                seed.access_key,
                UserRole.USER,
                seed.domain_name,
                {"some": "policy"},
                seed.domain_name,
                seed.group_id,
            )
        assert result.group_id == seed.group_id

    async def test_superadmin_delegation_resolves_group(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
        superadmin: ExtraUserData,
    ) -> None:
        """Superadmin creating session on behalf of user uses owner's role for group resolution."""
        async with db.begin() as conn:
            result = await query_userinfo(
                conn,
                superadmin.user_uuid,
                superadmin.access_key,
                UserRole.SUPERADMIN,
                seed.domain_name,
                None,
                seed.domain_name,
                seed.group_name,
                query_on_behalf_of=seed.access_key,
            )
        assert result.owner_uuid == seed.user_uuid
        assert result.group_id == seed.group_id

    # -- error cases --

    async def test_invalid_group_raises_bad_request(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match="Invalid group"):
            async with db.begin() as conn:
                await query_userinfo(
                    conn,
                    seed.user_uuid,
                    seed.access_key,
                    UserRole.USER,
                    seed.domain_name,
                    {"some": "policy"},
                    seed.domain_name,
                    "nonexistent-group",
                )

    async def test_non_member_group_raises_bad_request(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
        non_member_group: str,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match="Invalid group"):
            async with db.begin() as conn:
                await query_userinfo(
                    conn,
                    seed.user_uuid,
                    seed.access_key,
                    UserRole.USER,
                    seed.domain_name,
                    {"some": "policy"},
                    seed.domain_name,
                    non_member_group,
                )

    async def test_inactive_domain_raises_bad_request(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
        inactive_domain_user: ExtraUserData,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match="Invalid or inactive domain"):
            async with db.begin() as conn:
                await query_userinfo(
                    conn,
                    inactive_domain_user.user_uuid,
                    inactive_domain_user.access_key,
                    UserRole.USER,
                    "inactive",  # will match the user's own domain
                    {"some": "policy"},
                    "inactive",
                    seed.group_name,
                )

    async def test_unknown_access_key_raises_not_found(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
    ) -> None:
        with pytest.raises(AccessKeyNotFound):
            async with db.begin() as conn:
                await query_userinfo(
                    conn,
                    seed.user_uuid,
                    seed.access_key,
                    UserRole.USER,
                    seed.domain_name,
                    None,
                    seed.domain_name,
                    seed.group_name,
                    query_on_behalf_of=AccessKey("BOGUS_KEY"),
                )

    async def test_domain_mismatch_raises_bad_request(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match="domain"):
            async with db.begin() as conn:
                await query_userinfo(
                    conn,
                    seed.user_uuid,
                    seed.access_key,
                    UserRole.USER,
                    seed.domain_name,
                    {"some": "policy"},
                    "wrong-domain",
                    seed.group_name,
                )


# ---------------------------------------------------------------------------
# TestQueryUserinfoFromSession — SASession path
# ---------------------------------------------------------------------------


class TestQueryUserinfoFromSession:
    """Tests for query_userinfo_from_session() using SASession."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, ALL_ROWS):
            yield database_connection

    @pytest.fixture
    async def seed(self, db: ExtendedAsyncSAEngine) -> AsyncGenerator[SeedData, None]:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        group_id = uuid.uuid4()
        group_name = f"test-group-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        access_key = AccessKey(f"AK{uuid.uuid4().hex[:16]}")
        kp_policy = f"kp-policy-{uuid.uuid4().hex[:8]}"
        user_policy = f"user-policy-{uuid.uuid4().hex[:8]}"
        proj_policy = f"proj-policy-{uuid.uuid4().hex[:8]}"

        async with db.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=user_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=proj_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name=kp_policy,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"user-{uuid.uuid4().hex[:8]}",
                    email=f"test-{uuid.uuid4().hex[:8]}@test.io",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    access_key=access_key,
                    secret_key="secret",
                    user=user_uuid,
                    is_active=True,
                    resource_policy=kp_policy,
                )
            )
            sess.add(
                GroupRow(
                    id=group_id,
                    name=group_name,
                    domain_name=domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=proj_policy,
                )
            )
            await sess.flush()
            sess.add(AssocGroupUserRow(user_id=user_uuid, group_id=group_id))
            await sess.commit()

        yield SeedData(
            domain_name=domain_name,
            group_id=group_id,
            group_name=group_name,
            user_uuid=user_uuid,
            access_key=access_key,
            kp_policy_name=kp_policy,
            user_policy_name=user_policy,
            proj_policy_name=proj_policy,
        )

    async def test_success(self, db: ExtendedAsyncSAEngine, seed: SeedData) -> None:
        async with db.begin_session() as sess:
            result = await query_userinfo_from_session(
                sess,
                seed.user_uuid,
                seed.access_key,
                UserRole.USER,
                seed.domain_name,
                {"some": "policy"},
                seed.domain_name,
                seed.group_name,
            )
        assert result.owner_uuid == seed.user_uuid
        assert result.group_id == seed.group_id

    async def test_invalid_group_raises_bad_request(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match="Invalid group"):
            async with db.begin_session() as sess:
                await query_userinfo_from_session(
                    sess,
                    seed.user_uuid,
                    seed.access_key,
                    UserRole.USER,
                    seed.domain_name,
                    {"some": "policy"},
                    seed.domain_name,
                    "nonexistent-group",
                )

    async def test_unknown_access_key_raises_not_found(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
    ) -> None:
        with pytest.raises(AccessKeyNotFound):
            async with db.begin_session() as sess:
                await query_userinfo_from_session(
                    sess,
                    seed.user_uuid,
                    seed.access_key,
                    UserRole.USER,
                    seed.domain_name,
                    None,
                    seed.domain_name,
                    seed.group_name,
                    query_on_behalf_of=AccessKey("BOGUS_KEY"),
                )

    async def test_domain_mismatch_raises_bad_request(
        self,
        db: ExtendedAsyncSAEngine,
        seed: SeedData,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match="domain"):
            async with db.begin_session() as sess:
                await query_userinfo_from_session(
                    sess,
                    seed.user_uuid,
                    seed.access_key,
                    UserRole.USER,
                    seed.domain_name,
                    {"some": "policy"},
                    "wrong-domain",
                    seed.group_name,
                )
