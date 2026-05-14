"""Tests for ``prepare_vfolder_mounts`` subpath handling."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.types import (
    BinarySize,
    QuotaScopeID,
    ResourceSlot,
    VFolderMountOptions,
    VFolderMountRequest,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.agent import AgentRow
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
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import (
    VFolderPermissionRow,
    VFolderRow,
    prepare_vfolder_mounts,
)
from ai.backend.manager.types import UserScope
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


def _password_info() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestPrepareVFolderMountsSubpathValidation:
    """Subpath escape validation happens before any DB query, so we can
    drive it with bare mocks. These cases lock in that ``..``, absolute
    paths, and otherwise-escaping inputs raise ``InvalidAPIParameters``
    regardless of vfolder availability."""

    @pytest.mark.parametrize(
        "bad_subpath",
        [
            pytest.param("..", id="parent-traversal"),
            pytest.param("/etc/passwd", id="absolute-path"),
            pytest.param("a/../../b", id="normalizes-above-root"),
        ],
    )
    async def test_root_escaping_subpath_is_rejected(self, bad_subpath: str) -> None:
        vfolder_uuid = uuid4()
        with pytest.raises(InvalidAPIParameters, match="must not escape"):
            await prepare_vfolder_mounts(
                conn=AsyncMock(),
                storage_manager=MagicMock(),
                allowed_vfolder_types=["user"],
                user_scope=UserScope(
                    domain_name="default",
                    group_id=uuid4(),
                    user_uuid=uuid4(),
                    user_role=UserRole.USER,
                ),
                resource_policy={},
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_uuid,
                        dst_path="/home/work/extra",
                        options=VFolderMountOptions(subpath=bad_subpath),
                    ),
                ],
            )


class TestPrepareVFolderMountsSubpathFlow:
    """End-to-end test of subpath plumbing — a request carrying ``subpath``
    must surface as ``VFolderMount.vfsubpath`` (and join correctly into
    ``host_path``) on the resolved mount."""

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
                VFolderRow,
                VFolderPermissionRow,
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
    async def fixture_vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[tuple[UUID, str, UUID, UUID], None]:
        """Provision the minimum row chain (domain → policies → user → group → vfolder)
        with a host name whose volume part matches ``NOOP_STORAGE_VOLUME_NAME``
        so ``ensure_host_permission_allowed`` short-circuits.

        Yields ``(user_uuid, domain_name, group_id, vfolder_id)``.
        """
        domain_name = f"test-domain-{uuid4().hex[:8]}"
        user_policy_name = f"test-user-pol-{uuid4().hex[:8]}"
        project_policy_name = f"test-proj-pol-{uuid4().hex[:8]}"
        user_uuid = uuid4()
        group_id = uuid4()
        vfolder_id = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={"proxy:noop": ["mount-in-session"]},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("10GiB")),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_network_count=5,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"u-{user_uuid.hex[:6]}",
                    email=f"{user_uuid.hex[:6]}@example.com",
                    password=_password_info(),
                    need_password_change=False,
                    full_name="Test User",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    resource_policy=user_policy_name,
                )
            )
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"g-{group_id.hex[:6]}",
                    description="",
                    is_active=True,
                    domain_name=domain_name,
                    resource_policy=project_policy_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={"proxy:noop": ["mount-in-session"]},
                )
            )
            await db_sess.flush()
            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    host="proxy:noop",
                    domain_name=domain_name,
                    quota_scope_id=QuotaScopeID.parse(
                        f"user:{user_uuid}",
                    ),
                    name=f"vf-{vfolder_id.hex[:6]}",
                    creator=f"{user_uuid.hex[:6]}@example.com",
                    user=user_uuid,
                )
            )
            await db_sess.flush()

        yield user_uuid, domain_name, group_id, vfolder_id

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        """``get_proxy_and_volume`` returns a dummy pair; the manager-facing
        client returns a deterministic mount base path. The host path that
        ``prepare_vfolder_mounts`` constructs joins this base with the
        subpath, so we can assert subpath wiring through ``host_path`` too.
        """
        client = MagicMock()
        client.get_mount_path = AsyncMock(return_value={"path": "/data/mount-base"})
        sm = MagicMock()
        sm.get_proxy_and_volume = MagicMock(return_value=("proxy", "volume"))
        sm.get_manager_facing_client = MagicMock(return_value=client)
        return sm

    async def test_subpath_propagates_to_vfsubpath_and_host_path(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        user_uuid, domain_name, group_id, vfolder_id = fixture_vfolder
        async with db_with_cleanup.connect() as conn:
            mounts = await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=mock_storage_manager,
                allowed_vfolder_types=["user"],
                user_scope=UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    user_role=UserRole.USER,
                ),
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path="/home/work/dataset",
                        options=VFolderMountOptions(subpath="train/v2"),
                    ),
                ],
            )

        assert len(mounts) == 1
        mount = mounts[0]
        assert mount.vfsubpath == PurePosixPath("train/v2")
        # Host path joins the storage-side base with the requested subpath.
        assert mount.host_path == PurePosixPath("/data/mount-base/train/v2")
        # And the storage proxy was asked to resolve the subpath, not "."
        client = mock_storage_manager.get_manager_facing_client.return_value
        client.get_mount_path.assert_awaited_once()
        assert client.get_mount_path.call_args.args[-1] == "train/v2"

    async def test_subpath_omitted_falls_back_to_vfolder_root(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        """No subpath in options → ``vfsubpath == PurePosixPath('.')`` —
        the storage-proxy-facing default."""
        user_uuid, domain_name, group_id, vfolder_id = fixture_vfolder
        async with db_with_cleanup.connect() as conn:
            mounts = await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=mock_storage_manager,
                allowed_vfolder_types=["user"],
                user_scope=UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    user_role=UserRole.USER,
                ),
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path="/home/work/dataset",
                        options=VFolderMountOptions(),
                    ),
                ],
            )

        assert len(mounts) == 1
        assert mounts[0].vfsubpath == PurePosixPath(".")
