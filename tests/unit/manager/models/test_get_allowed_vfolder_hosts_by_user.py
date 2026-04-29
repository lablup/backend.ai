"""Tests for `get_allowed_vfolder_hosts_by_user` project-membership behavior.

Only the membership filter (powered by `association_scopes_entities`) is verified.
The function's domain-level and resource-policy-level merge behavior is not the
focus of this test module.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest

from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.permission.types import (
    EntityType as PermissionEntityType,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as PermissionScopeType,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import get_allowed_vfolder_hosts_by_user
from ai.backend.testutils.db import with_tables

HOST_A = "host-a"
HOST_B = "host-b"
HOST_C = "host-c"
HOSTS_A: VFolderHostPermissionMap = VFolderHostPermissionMap({
    HOST_A: {VFolderHostPermission.CREATE}
})
HOSTS_B: VFolderHostPermissionMap = VFolderHostPermissionMap({
    HOST_B: {VFolderHostPermission.CREATE}
})
HOSTS_C: VFolderHostPermissionMap = VFolderHostPermissionMap({
    HOST_C: {VFolderHostPermission.CREATE}
})


def _password() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=600_000,
        salt_size=32,
    )


class TestGetAllowedVFolderHostsByUserMembership:
    """Project-membership filter for `get_allowed_vfolder_hosts_by_user`.

    Each test seeds a domain, two groups in that domain, and a regular user.
    Membership is granted by inserting the corresponding ASE row.
    """

    @pytest.fixture
    async def db_with_cleanup(
        self,
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
                AgentRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def domain_name(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        name = f"test-domain-{uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                )
            )
            await sess.flush()
        yield name

    @pytest.fixture
    async def project_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-proj-policy-{uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=5,
                )
            )
            await sess.flush()
        yield policy_name

    @pytest.fixture
    async def user_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-user-policy-{uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await sess.flush()
        yield policy_name

    @pytest.fixture
    async def regular_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        user_resource_policy: str,
    ) -> AsyncGenerator[UUID, None]:
        user_uuid = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"user_{user_uuid.hex[:8]}",
                    email=f"user-{user_uuid.hex[:8]}@example.com",
                    password=_password(),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_resource_policy,
                )
            )
            await sess.flush()
        yield user_uuid

    @pytest.fixture
    async def group_a(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_resource_policy: str,
    ) -> AsyncGenerator[UUID, None]:
        gid = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                GroupRow(
                    id=gid,
                    name=f"group-a-{gid.hex[:8]}",
                    domain_name=domain_name,
                    resource_policy=project_resource_policy,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=HOSTS_A,
                    type=ProjectType.GENERAL,
                )
            )
            await sess.flush()
        yield gid

    @pytest.fixture
    async def group_b(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_resource_policy: str,
    ) -> AsyncGenerator[UUID, None]:
        gid = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                GroupRow(
                    id=gid,
                    name=f"group-b-{gid.hex[:8]}",
                    domain_name=domain_name,
                    resource_policy=project_resource_policy,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=HOSTS_B,
                    type=ProjectType.GENERAL,
                )
            )
            await sess.flush()
        yield gid

    @pytest.fixture
    async def membership_in_group_a(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        regular_user: UUID,
        group_a: UUID,
    ) -> AsyncGenerator[None, None]:
        """Insert ASE row binding regular_user to group_a."""
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(group_a),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(regular_user),
                )
            )
            await sess.flush()
        yield

    @pytest.fixture
    async def membership_in_group_b(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        regular_user: UUID,
        group_b: UUID,
    ) -> AsyncGenerator[None, None]:
        """Insert ASE row binding regular_user to group_b."""
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(group_b),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(regular_user),
                )
            )
            await sess.flush()
        yield

    async def test_member_groups_contribute_their_hosts(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        regular_user: UUID,
        group_a: UUID,
        group_b: UUID,
        membership_in_group_a: None,
        membership_in_group_b: None,
    ) -> None:
        """Without `group_id`, hosts from every group the user is a member of are merged."""
        async with db_with_cleanup.begin_readonly() as conn:
            result = await get_allowed_vfolder_hosts_by_user(
                conn,
                resource_policy={},
                domain_name=domain_name,
                user_uuid=regular_user,
            )

        assert HOST_A in result
        assert HOST_B in result

    async def test_non_member_groups_do_not_contribute(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        regular_user: UUID,
        group_a: UUID,
        group_b: UUID,
        membership_in_group_a: None,
    ) -> None:
        """Only groups with an ASE membership row are merged into the result."""
        async with db_with_cleanup.begin_readonly() as conn:
            result = await get_allowed_vfolder_hosts_by_user(
                conn,
                resource_policy={},
                domain_name=domain_name,
                user_uuid=regular_user,
            )

        assert HOST_A in result
        assert HOST_B not in result

    async def test_group_id_filter_with_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        regular_user: UUID,
        group_a: UUID,
        group_b: UUID,
        membership_in_group_a: None,
        membership_in_group_b: None,
    ) -> None:
        """`group_id` restricts merging to that single group when the user is a member."""
        async with db_with_cleanup.begin_readonly() as conn:
            result = await get_allowed_vfolder_hosts_by_user(
                conn,
                resource_policy={},
                domain_name=domain_name,
                user_uuid=regular_user,
                group_id=group_a,
            )

        assert HOST_A in result
        assert HOST_B not in result

    async def test_group_id_filter_without_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        regular_user: UUID,
        group_a: UUID,
    ) -> None:
        """`group_id` for a group the user is not a member of yields no group hosts."""
        async with db_with_cleanup.begin_readonly() as conn:
            result = await get_allowed_vfolder_hosts_by_user(
                conn,
                resource_policy={},
                domain_name=domain_name,
                user_uuid=regular_user,
                group_id=group_a,
            )

        assert HOST_A not in result

    async def test_resource_policy_hosts_merge_independent_of_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        regular_user: UUID,
    ) -> None:
        """Hosts from `resource_policy` are merged regardless of project membership.

        Sanity check that the membership filter does not gate non-membership inputs.
        """
        async with db_with_cleanup.begin_readonly() as conn:
            result = await get_allowed_vfolder_hosts_by_user(
                conn,
                resource_policy={"allowed_vfolder_hosts": HOSTS_C},
                domain_name=domain_name,
                user_uuid=regular_user,
            )

        assert HOST_C in result
