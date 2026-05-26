"""Regression test for auto-mount (dot-prefixed) vfolder resolution.

Reproduces the 26.4.4rc6 regression where
``ScheduleDBSource.fetch_session_spec_contexts`` short-circuited a kernel
group with no explicit mount requests::

    if not per_group_requests:
        continue

That early ``continue`` skipped ``prepare_vfolder_mounts`` entirely, but
that resolver injects dot-prefixed auto-mount vfolders regardless of the
request list — so sessions created without an explicit mount silently
lost their ``.config``/``.local``/... auto-mounts. The legacy pre-#11250
path always invoked the resolver unconditionally; this test pins that
behavior so the optimization cannot creep back in.

The invariant under test: a kernel group whose ``execution_spec.mounts``
is empty STILL resolves the user's accessible auto-mount vfolders into
``vfolder_mounts_by_role``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.identifier.domain import DomainName
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.types import BinarySize, QuotaScopeID, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.session.draft import (
    KernelGroupDraft,
    SessionIdentityDraft,
    SessionOptionsDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
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
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import ResourceSlotTypeRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# Volume part matches ``NOOP_STORAGE_VOLUME_NAME`` so
# ``ensure_host_permission_allowed`` short-circuits and the auto-mount is not
# silently skipped on a permission failure.
NOOP_VFOLDER_HOST = "proxy:noop"
# A dot prefix is what marks a vfolder for automatic mounting.
AUTOMOUNT_VFOLDER_NAME = ".config"


def _password_info() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestAutoMountVFolderResolution:
    """Auto-mount vfolders must resolve even without explicit mount requests."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ResourceSlotTypeRow,
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
                VFolderRow,
                VFolderPermissionRow,
                ContainerRegistryRow,
                ImageRow,
                ResourcePresetRow,
                RuntimeVariantRow,
                EndpointRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentPolicyRow,
                SessionRow,
                KernelRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a test domain that allows mounting on the noop host."""
        domain_name = f"test-domain-{uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={NOOP_VFOLDER_HOST: ["mount-in-session"]},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()
        return domain_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a test user resource policy."""
        policy_name = f"test-user-pol-{uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("10GiB")),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a test project resource policy."""
        policy_name = f"test-proj-pol-{uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_network_count=5,
                )
            )
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> UUID:
        """Create a test user that owns the auto-mount vfolder."""
        user_uuid = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"u-{user_uuid.hex[:6]}",
                    email=f"{user_uuid.hex[:6]}@example.com",
                    password=_password_info(),
                    need_password_change=False,
                    full_name="Test User",
                    domain_name=test_domain_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    resource_policy=test_user_resource_policy_name,
                )
            )
            await db_sess.flush()
        return user_uuid

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> UUID:
        """Create a test group used as the session's project scope."""
        group_id = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"g-{group_id.hex[:6]}",
                    description="",
                    is_active=True,
                    domain_name=test_domain_name,
                    resource_policy=test_project_resource_policy_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={NOOP_VFOLDER_HOST: ["mount-in-session"]},
                )
            )
            await db_sess.flush()
        return group_id

    @pytest.fixture
    async def automount_vfolder_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user: UUID,
    ) -> UUID:
        """Create a dot-prefixed (auto-mount) vfolder owned by ``test_user``."""
        vfolder_id = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    host=NOOP_VFOLDER_HOST,
                    domain_name=test_domain_name,
                    quota_scope_id=QuotaScopeID.parse(f"user:{test_user}"),
                    name=AUTOMOUNT_VFOLDER_NAME,
                    creator=f"{test_user.hex[:6]}@example.com",
                    user=test_user,
                )
            )
            await db_sess.flush()
        return vfolder_id

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        """A storage manager that resolves any vfolder to a deterministic
        mount base. ``prepare_vfolder_mounts`` calls these to materialize the
        host path for each resolved mount.
        """
        client = MagicMock()
        client.get_mount_path = AsyncMock(return_value={"path": "/data/mount-base"})
        sm = MagicMock()
        sm.get_proxy_and_volume = MagicMock(return_value=("proxy", "volume"))
        sm.get_manager_facing_client = MagicMock(return_value=client)
        return sm

    async def test_automount_resolved_without_explicit_mount_requests(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user: UUID,
        test_group: UUID,
        automount_vfolder_id: UUID,
        mock_storage_manager: MagicMock,
    ) -> None:
        # A session with a single kernel group and NO explicit mounts —
        # exactly the case the regression dropped auto-mounts for.
        draft = SessionSpecDraft(
            identity=SessionIdentityDraft(
                creation_id="automount-regression",
                session_name="automount-regression",
                user_uuid=test_user,
            ),
            scope=SessionScopeDraft(
                domain_name=DomainName(test_domain_name),
                project_id=ProjectID(test_group),
                resource_group_name=None,
            ),
            options=SessionOptionsDraft(
                kernel_groups=(KernelGroupDraft(role="main", replica_count=1),),
            ),
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.fetch_session_spec_contexts(
            draft,
            storage_manager=mock_storage_manager,
            allowed_vfolder_types=["user"],
        )

        # The "main" role must carry the auto-mount vfolder even though the
        # group requested no mounts explicitly.
        assert "main" in result.vfolder_mounts_by_role
        mounted_names = {mount.name for mount in result.vfolder_mounts_by_role["main"]}
        assert AUTOMOUNT_VFOLDER_NAME in mounted_names, (
            f"auto-mount vfolder {AUTOMOUNT_VFOLDER_NAME!r} must be resolved for a group "
            f"with no explicit mounts; got {mounted_names!r}"
        )
        mounted_ids = {mount.vfid.folder_id for mount in result.vfolder_mounts_by_role["main"]}
        assert automount_vfolder_id in mounted_ids
