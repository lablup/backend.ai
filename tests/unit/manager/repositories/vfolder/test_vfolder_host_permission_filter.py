"""
Tests for VFolderConditions.by_host_permission() filter.

Verifies that the host_permission filter correctly filters vfolders by storage host
accessibility based on the user's allowed_vfolder_hosts from domains, groups, and
keypair_resource_policies.

Design reference: docs/superpowers/my-vfolder-filter-design.md section 7.2
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    VFolderHostPermission,
    VFolderUsageMode,
)
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderPermissionRow, VFolderRow
from ai.backend.manager.models.vfolder.conditions import VFolderConditions
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfolder.types import UserVFolderSearchScope
from ai.backend.testutils.db import with_tables


@dataclass
class HostPermissionTestData:
    """Test data IDs for host_permission filter tests."""

    # Users
    user_a_id: uuid.UUID  # domain=alpha, groups=[alpha-proj-1, alpha-proj-3]
    user_b_id: uuid.UUID  # domain=beta, groups=[beta-proj-1]
    user_c_id: uuid.UUID  # domain=alpha, groups=[alpha-proj-2]

    # VFolders owned by User A
    vf_alpha_shared_id: uuid.UUID  # host="host-shared"
    vf_alpha_a_id: uuid.UUID  # host="host-a"
    vf_alpha_b_id: uuid.UUID  # host="host-b"
    vf_alpha_c_id: uuid.UUID  # host="host-c" (inaccessible to A)
    vf_alpha_orphan_id: uuid.UUID  # host="host-nowhere" (inaccessible to A)

    # VFolders owned by User B
    vf_beta_shared_id: uuid.UUID  # host="host-shared"
    vf_beta_x_id: uuid.UUID  # host="host-x"
    vf_beta_y_id: uuid.UUID  # host="host-y"
    vf_beta_a_id: uuid.UUID  # host="host-a" (inaccessible to B)

    # VFolder owned by User C
    vf_alpha_c2_id: uuid.UUID  # host="host-c"

    # VFolder on keypair resource policy host
    vf_alpha_krp_id: uuid.UUID  # host="host-krp" (from keypair resource policy)

    # Shared vfolders (owned by B/C, shared to A via VFolderPermissionRow)
    vf_shared_to_a_id: uuid.UUID  # owned by B, host="host-shared", shared to A
    vf_shared_on_c_id: uuid.UUID  # owned by C, host="host-c", shared to A

    def resolve_ids(self, field_names: set[str]) -> set[uuid.UUID]:
        """Resolve a set of field names to their UUID values."""
        return {getattr(self, name) for name in field_names}


@dataclass(frozen=True)
class HostPermFilterCase:
    """Parametrized test case for host_permission filter."""

    description: str
    user_id_field: str  # field name in HostPermissionTestData (e.g. "user_a_id")
    domain_name: str
    permissions: list[VFolderHostPermission]
    negate: bool
    expected_vf_keys: set[str] = field(default_factory=set)
    excluded_vf_keys: set[str] = field(default_factory=set)


class TestVFolderHostPermissionFilter:
    """Tests for VFolderConditions.by_host_permission() integrated with repository search."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssocGroupUserRow,
                VFolderRow,
                VFolderPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        return VfolderRepository(db=db_with_cleanup)

    @pytest.fixture
    async def test_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[HostPermissionTestData, None]:
        """Set up the 2-domain, multi-group test scenario from design doc section 7.2.

        Domain "alpha":
          allowed_vfolder_hosts: {"host-shared": ["create-vfolder", "mount-in-session"],
                                   "host-a": ["create-vfolder"]}
          Group "alpha-proj-1" (User A member):
            allowed_vfolder_hosts: {"host-b": ["create-vfolder", "mount-in-session"]}
          Group "alpha-proj-2" (User C member, User A NOT member):
            allowed_vfolder_hosts: {"host-c": ["mount-in-session"]}  (no CREATE!)
          Group "alpha-proj-3" (User A member):
            allowed_vfolder_hosts: {"host-a": ["mount-in-session"]}
            (cross-source: host-a gets CREATE from domain + MOUNT from this group)

        Domain "beta":
          allowed_vfolder_hosts: {"host-shared": ["create-vfolder"],
                                   "host-x": ["mount-in-session"]}  (no CREATE on host-x!)
          Group "beta-proj-1" (User B member):
            allowed_vfolder_hosts: {"host-y": ["create-vfolder"]}

        User A accessible hosts (CREATE): host-shared, host-a, host-b
        User B accessible hosts (CREATE): host-shared, host-y
        User C accessible hosts (CREATE): host-shared, host-a (domain only, host-c has no CREATE)
        """
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()
        user_c_id = uuid.uuid4()

        alpha_proj_1_id = uuid.uuid4()
        alpha_proj_2_id = uuid.uuid4()
        alpha_proj_3_id = uuid.uuid4()
        beta_proj_1_id = uuid.uuid4()

        vf_alpha_shared_id = uuid.uuid4()
        vf_alpha_a_id = uuid.uuid4()
        vf_alpha_b_id = uuid.uuid4()
        vf_alpha_c_id = uuid.uuid4()
        vf_alpha_orphan_id = uuid.uuid4()
        vf_beta_shared_id = uuid.uuid4()
        vf_beta_x_id = uuid.uuid4()
        vf_beta_y_id = uuid.uuid4()
        vf_beta_a_id = uuid.uuid4()
        vf_alpha_c2_id = uuid.uuid4()
        vf_shared_to_a_id = uuid.uuid4()
        vf_alpha_krp_id = uuid.uuid4()
        vf_shared_on_c_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # --- Domains ---
            db_sess.add(
                DomainRow(
                    name="alpha",
                    description="Alpha domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={
                        "host-shared": ["create-vfolder", "mount-in-session"],
                        "host-a": ["create-vfolder"],
                    },
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                DomainRow(
                    name="beta",
                    description="Beta domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={
                        "host-shared": ["create-vfolder"],
                        "host-x": ["mount-in-session"],
                    },
                    allowed_docker_registries=[],
                )
            )

            # --- Resource Policies ---
            db_sess.add(
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=3,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="default",
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                    allowed_vfolder_hosts={
                        "host-krp": ["create-vfolder", "mount-in-session"],
                    },
                )
            )
            await db_sess.flush()

            # --- Users ---
            for uid, uname, email, domain in [
                (user_a_id, "usera", "usera@example.com", "alpha"),
                (user_b_id, "userb", "userb@example.com", "beta"),
                (user_c_id, "userc", "userc@example.com", "alpha"),
            ]:
                db_sess.add(
                    UserRow(
                        uuid=uid,
                        username=uname,
                        email=email,
                        password=None,
                        need_password_change=False,
                        status=UserStatus.ACTIVE,
                        status_info="active",
                        domain_name=domain,
                        role=UserRole.USER,
                        resource_policy="default",
                    )
                )
            await db_sess.flush()

            # --- KeyPairs ---
            for uid_str, uid, ak in [
                ("usera@example.com", user_a_id, "TESTHOSTPERM000A"),
                ("userb@example.com", user_b_id, "TESTHOSTPERM000B"),
                ("userc@example.com", user_c_id, "TESTHOSTPERM000C"),
            ]:
                db_sess.add(
                    KeyPairRow(
                        user_id=uid_str,
                        user=uid,
                        access_key=ak,
                        secret_key=f"secret-{ak}",
                        is_active=True,
                        is_admin=False,
                        resource_policy="default",
                        rate_limit=1000,
                    )
                )
            await db_sess.flush()

            # --- Groups ---
            for gid, gname, domain, hosts in [
                (
                    alpha_proj_1_id,
                    "alpha-proj-1",
                    "alpha",
                    {"host-b": ["create-vfolder", "mount-in-session"]},
                ),
                (
                    alpha_proj_2_id,
                    "alpha-proj-2",
                    "alpha",
                    {"host-c": ["mount-in-session"]},
                ),
                (
                    alpha_proj_3_id,
                    "alpha-proj-3",
                    "alpha",
                    {"host-a": ["mount-in-session"]},
                ),
                (beta_proj_1_id, "beta-proj-1", "beta", {"host-y": ["create-vfolder"]}),
            ]:
                db_sess.add(
                    GroupRow(
                        id=gid,
                        name=gname,
                        domain_name=domain,
                        description=f"Test {gname}",
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts=hosts,
                        resource_policy="default",
                        type=ProjectType.GENERAL,
                    )
                )
            await db_sess.flush()

            # --- Group Memberships ---
            for uid, gid in [
                (user_a_id, alpha_proj_1_id),
                (user_a_id, alpha_proj_3_id),
                (user_b_id, beta_proj_1_id),
                (user_c_id, alpha_proj_2_id),
            ]:
                db_sess.add(AssocGroupUserRow(user_id=uid, group_id=gid))
            await db_sess.flush()

            # --- VFolders ---
            def _make_vfolder(
                vid: uuid.UUID,
                name: str,
                host: str,
                domain: str,
                owner: uuid.UUID,
                group: uuid.UUID | None = None,
            ) -> VFolderRow:
                return VFolderRow(
                    id=vid,
                    name=name,
                    host=host,
                    domain_name=domain,
                    quota_scope_id=f"user:{owner}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator=f"{name}@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=owner,
                    group=group,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )

            # User A's vfolders
            for vid, name, host in [
                (vf_alpha_shared_id, "vf-alpha-shared", "host-shared"),
                (vf_alpha_a_id, "vf-alpha-a", "host-a"),
                (vf_alpha_b_id, "vf-alpha-b", "host-b"),
                (vf_alpha_c_id, "vf-alpha-c", "host-c"),
                (vf_alpha_orphan_id, "vf-alpha-orphan", "host-nowhere"),
                (vf_alpha_krp_id, "vf-alpha-krp", "host-krp"),
            ]:
                db_sess.add(_make_vfolder(vid, name, host, "alpha", user_a_id))

            # User B's vfolders
            for vid, name, host in [
                (vf_beta_shared_id, "vf-beta-shared", "host-shared"),
                (vf_beta_x_id, "vf-beta-x", "host-x"),
                (vf_beta_y_id, "vf-beta-y", "host-y"),
                (vf_beta_a_id, "vf-beta-a", "host-a"),
            ]:
                db_sess.add(_make_vfolder(vid, name, host, "beta", user_b_id))

            # User C's vfolder
            db_sess.add(_make_vfolder(vf_alpha_c2_id, "vf-alpha-c2", "host-c", "alpha", user_c_id))

            # Shared vfolders (owned by B/C, shared to A)
            db_sess.add(
                _make_vfolder(vf_shared_to_a_id, "vf-shared-to-a", "host-shared", "beta", user_b_id)
            )
            db_sess.add(
                _make_vfolder(vf_shared_on_c_id, "vf-shared-on-c", "host-c", "alpha", user_c_id)
            )
            await db_sess.flush()

            # Share vfolders to User A via VFolderPermissionRow
            db_sess.add(
                VFolderPermissionRow(
                    permission=VFolderMountPermission.READ_ONLY,
                    vfolder=vf_shared_to_a_id,
                    user=user_a_id,
                )
            )
            db_sess.add(
                VFolderPermissionRow(
                    permission=VFolderMountPermission.READ_ONLY,
                    vfolder=vf_shared_on_c_id,
                    user=user_a_id,
                )
            )
            await db_sess.flush()

        yield HostPermissionTestData(
            user_a_id=user_a_id,
            user_b_id=user_b_id,
            user_c_id=user_c_id,
            vf_alpha_shared_id=vf_alpha_shared_id,
            vf_alpha_a_id=vf_alpha_a_id,
            vf_alpha_b_id=vf_alpha_b_id,
            vf_alpha_c_id=vf_alpha_c_id,
            vf_alpha_orphan_id=vf_alpha_orphan_id,
            vf_alpha_krp_id=vf_alpha_krp_id,
            vf_beta_shared_id=vf_beta_shared_id,
            vf_beta_x_id=vf_beta_x_id,
            vf_beta_y_id=vf_beta_y_id,
            vf_beta_a_id=vf_beta_a_id,
            vf_alpha_c2_id=vf_alpha_c2_id,
            vf_shared_to_a_id=vf_shared_to_a_id,
            vf_shared_on_c_id=vf_shared_on_c_id,
        )

    # ── Parametrized host_permission filter tests ──

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                HostPermFilterCase(
                    description="in CREATE returns accessible host vfolders for user A",
                    user_id_field="user_a_id",
                    domain_name="alpha",
                    permissions=[VFolderHostPermission.CREATE],
                    negate=False,
                    expected_vf_keys={
                        "vf_alpha_shared_id",
                        "vf_alpha_a_id",
                        "vf_alpha_b_id",
                        "vf_alpha_krp_id",
                        "vf_shared_to_a_id",
                    },
                ),
                id="H-1",
            ),
            pytest.param(
                HostPermFilterCase(
                    description="not_in CREATE returns inaccessible host vfolders for user A",
                    user_id_field="user_a_id",
                    domain_name="alpha",
                    permissions=[VFolderHostPermission.CREATE],
                    negate=True,
                    expected_vf_keys={
                        "vf_alpha_c_id",
                        "vf_alpha_orphan_id",
                        "vf_shared_on_c_id",
                    },
                ),
                id="H-3",
            ),
            pytest.param(
                HostPermFilterCase(
                    description="domain isolation — user B sees only beta CREATE hosts",
                    user_id_field="user_b_id",
                    domain_name="beta",
                    permissions=[VFolderHostPermission.CREATE],
                    negate=False,
                    expected_vf_keys={
                        "vf_beta_shared_id",
                        "vf_beta_y_id",
                        "vf_shared_to_a_id",
                    },
                ),
                id="H-4",
            ),
            pytest.param(
                HostPermFilterCase(
                    description="cross-domain host exclusion — host-a not in beta",
                    user_id_field="user_b_id",
                    domain_name="beta",
                    permissions=[VFolderHostPermission.CREATE],
                    negate=False,
                    expected_vf_keys={
                        "vf_beta_shared_id",
                        "vf_beta_y_id",
                        "vf_shared_to_a_id",
                    },
                    excluded_vf_keys={"vf_beta_a_id"},
                ),
                id="H-6",
            ),
            pytest.param(
                HostPermFilterCase(
                    description="mount-only host excluded from CREATE filter for user C",
                    user_id_field="user_c_id",
                    domain_name="alpha",
                    permissions=[VFolderHostPermission.CREATE],
                    negate=False,
                    excluded_vf_keys={"vf_alpha_c2_id"},
                ),
                id="H-9",
            ),
            pytest.param(
                HostPermFilterCase(
                    description="shared vfolder filtered by requester permissions, not owner",
                    user_id_field="user_a_id",
                    domain_name="alpha",
                    permissions=[VFolderHostPermission.CREATE],
                    negate=False,
                    expected_vf_keys={
                        "vf_alpha_shared_id",
                        "vf_alpha_a_id",
                        "vf_alpha_b_id",
                        "vf_alpha_krp_id",
                        "vf_shared_to_a_id",
                    },
                    excluded_vf_keys={"vf_shared_on_c_id"},
                ),
                id="H-10",
            ),
            pytest.param(
                HostPermFilterCase(
                    description="multiple permissions requires ALL (CREATE + MOUNT_IN_SESSION)",
                    user_id_field="user_a_id",
                    domain_name="alpha",
                    permissions=[
                        VFolderHostPermission.CREATE,
                        VFolderHostPermission.MOUNT_IN_SESSION,
                    ],
                    negate=False,
                    expected_vf_keys={
                        "vf_alpha_shared_id",
                        "vf_alpha_a_id",  # CREATE from domain + MOUNT from group (cross-source)
                        "vf_alpha_b_id",
                        "vf_alpha_krp_id",  # both CREATE + MOUNT from keypair policy
                        "vf_shared_to_a_id",
                    },
                ),
                id="multi-perm",
            ),
            pytest.param(
                HostPermFilterCase(
                    description="cross-source permission union — host-a gets CREATE from domain, MOUNT from group",
                    user_id_field="user_a_id",
                    domain_name="alpha",
                    permissions=[
                        VFolderHostPermission.CREATE,
                        VFolderHostPermission.MOUNT_IN_SESSION,
                    ],
                    negate=False,
                    expected_vf_keys={
                        "vf_alpha_shared_id",
                        "vf_alpha_a_id",
                        "vf_alpha_b_id",
                        "vf_alpha_krp_id",
                        "vf_shared_to_a_id",
                    },
                    excluded_vf_keys={
                        "vf_alpha_c_id",
                        "vf_alpha_orphan_id",
                    },
                ),
                id="cross-source-union",
            ),
            pytest.param(
                HostPermFilterCase(
                    description="keypair resource policy host included in filter results",
                    user_id_field="user_a_id",
                    domain_name="alpha",
                    permissions=[VFolderHostPermission.CREATE],
                    negate=False,
                    expected_vf_keys={
                        "vf_alpha_shared_id",
                        "vf_alpha_a_id",
                        "vf_alpha_b_id",
                        "vf_alpha_krp_id",  # from keypair resource policy
                        "vf_shared_to_a_id",
                    },
                ),
                id="keypair-source",
            ),
        ],
    )
    async def test_host_permission_filter(
        self,
        vfolder_repository: VfolderRepository,
        test_data: HostPermissionTestData,
        case: HostPermFilterCase,
    ) -> None:
        user_id = getattr(test_data, case.user_id_field)
        requester = UserData(
            user_id=user_id,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name=case.domain_name,
        )

        scope = UserVFolderSearchScope(user_id=user_id)
        condition = VFolderConditions.by_host_permission(
            requester, permissions=case.permissions, negate=case.negate
        )
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[condition],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = {item.id for item in result.items}
        expected_ids = test_data.resolve_ids(case.expected_vf_keys)
        excluded_ids = test_data.resolve_ids(case.excluded_vf_keys)
        assert returned_ids == expected_ids
        assert not (excluded_ids & returned_ids)

    # ── H-2: no filter returns all user vfolders ──

    async def test_no_filter_returns_all_user_vfolders(
        self,
        vfolder_repository: VfolderRepository,
        test_data: HostPermissionTestData,
    ) -> None:
        """Without host_permission filter, all User A's vfolders are returned."""
        scope = UserVFolderSearchScope(user_id=test_data.user_a_id)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        # User A owns 6 vfolders + 2 shared = 8
        assert result.total_count == 8

    # ── H-12: pagination compatibility ──

    async def test_pagination_with_host_permission_filter(
        self,
        vfolder_repository: VfolderRepository,
        test_data: HostPermissionTestData,
    ) -> None:
        """host_permission filter works correctly with pagination."""
        requester = UserData(
            user_id=test_data.user_a_id,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="alpha",
        )
        scope = UserVFolderSearchScope(user_id=test_data.user_a_id)
        condition = VFolderConditions.by_host_permission(
            requester,
            permissions=[VFolderHostPermission.CREATE],
            negate=False,
        )
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[condition],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        assert result.total_count == 5
        assert len(result.items) == 2
        assert result.has_next_page is True

    # ── H-13: combination with other filters ──

    async def test_combined_with_host_string_filter(
        self,
        vfolder_repository: VfolderRepository,
        test_data: HostPermissionTestData,
    ) -> None:
        """host_permission filter combines correctly with host string filter."""
        requester = UserData(
            user_id=test_data.user_a_id,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="alpha",
        )
        scope = UserVFolderSearchScope(user_id=test_data.user_a_id)
        host_perm_condition = VFolderConditions.by_host_permission(
            requester,
            permissions=[VFolderHostPermission.CREATE],
            negate=False,
        )
        host_string_condition = VFolderConditions.by_host_contains(
            StringMatchSpec(value="shared", case_insensitive=False, negated=False)
        )
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[host_perm_condition, host_string_condition],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            test_data.vf_alpha_shared_id,
            test_data.vf_shared_to_a_id,
        }


class TestVFolderHostPermissionFilterEmptyHosts:
    """Test edge case: empty allowed_vfolder_hosts."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                VFolderPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        return VfolderRepository(db=db_with_cleanup)

    @pytest.fixture
    async def empty_hosts_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Domain and groups all have empty allowed_vfolder_hosts."""
        user_id = uuid.uuid4()
        vf_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name="empty-domain",
                    description="Domain with no hosts",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=3,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="default",
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username="emptyuser",
                    email="empty@example.com",
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name="empty-domain",
                    role=UserRole.USER,
                    resource_policy="default",
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user_id="empty@example.com",
                    user=user_id,
                    access_key="TESTHOSTPERM0EMP",
                    secret_key="secret-empty",
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            db_sess.add(
                VFolderRow(
                    id=vf_id,
                    name="vf-on-some-host",
                    host="some-host",
                    domain_name="empty-domain",
                    quota_scope_id=f"user:{user_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator="empty@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=user_id,
                    group=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            await db_sess.flush()

        yield {"user_id": user_id, "vf_id": vf_id}

    @pytest.fixture
    def requester(self, empty_hosts_data: dict[str, uuid.UUID]) -> UserData:
        return UserData(
            user_id=empty_hosts_data["user_id"],
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="empty-domain",
        )

    async def test_empty_allowed_hosts_returns_empty_for_in_filter(
        self,
        vfolder_repository: VfolderRepository,
        empty_hosts_data: dict[str, uuid.UUID],
        requester: UserData,
    ) -> None:
        """H-11: When all allowed_vfolder_hosts are empty, in_ filter returns no results."""
        user_id = empty_hosts_data["user_id"]
        scope = UserVFolderSearchScope(user_id=user_id)
        condition = VFolderConditions.by_host_permission(
            requester,
            permissions=[VFolderHostPermission.CREATE],
            negate=False,
        )
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[condition],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        assert result.total_count == 0
        assert len(result.items) == 0
