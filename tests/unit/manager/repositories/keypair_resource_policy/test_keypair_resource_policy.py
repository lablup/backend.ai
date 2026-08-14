from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermission,
)
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_policy.creators import (
    KeyPairResourcePolicyCreator,
)
from ai.backend.manager.models.resource_policy.purgers import (
    KeyPairResourcePolicyPurger,
)
from ai.backend.manager.models.resource_policy.updaters import (
    KeyPairResourcePolicyUpdater,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables


class TestKeypairResourcePolicyRepository:
    """Test cases for KeypairResourcePolicyRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
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
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def sample_resource_slots(self) -> ResourceSlot:
        """Sample resource slots for testing"""
        return ResourceSlot({"cpu": "4", "mem": "8g", "gpu": "1"})

    @pytest.fixture
    async def sample_allowed_vfolder_hosts(self) -> dict[str, Any]:
        """Fixture for sample allowed_vfolder_hosts"""
        return {
            "s3": {
                VFolderHostPermission.CREATE,
                VFolderHostPermission.UPLOAD_FILE,
                VFolderHostPermission.DOWNLOAD_FILE,
            },
            "azure": {
                VFolderHostPermission.CREATE,
                VFolderHostPermission.MOUNT_IN_SESSION,
            },
            "local": {
                VFolderHostPermission.CREATE,
                VFolderHostPermission.UPLOAD_FILE,
                VFolderHostPermission.DOWNLOAD_FILE,
                VFolderHostPermission.MOUNT_IN_SESSION,
            },
        }

    @pytest.fixture
    def sample_creator(
        self,
        sample_resource_slots: ResourceSlot,
        sample_allowed_vfolder_hosts: dict[str, Any],
    ) -> KeyPairResourcePolicyCreator:
        """Create a sample KeyPairResourcePolicyCreator for testing"""
        return KeyPairResourcePolicyCreator(
            name=str(uuid4()),
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=sample_resource_slots,
            max_session_lifetime=86400,
            max_concurrent_sessions=10,
            max_containers_per_session=3,
            idle_timeout=3600,
            allowed_vfolder_hosts=sample_allowed_vfolder_hosts,
            max_concurrent_sftp_sessions=5,
            max_pending_session_count=5,
            max_pending_session_resource_slots=ResourceSlot({"cpu": "1", "mem": "1g"}),
            max_priority=None,
        )

    @pytest.fixture
    async def sample_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_creator: KeyPairResourcePolicyCreator,
    ) -> str:
        """Create sample keypair resource policy directly in DB and return its name"""
        async with db_with_cleanup.begin_session() as db_sess:
            policy_row = sample_creator.build_row()
            db_sess.add(policy_row)
            await db_sess.commit()

        assert sample_creator.name is not None
        return sample_creator.name

    @pytest.fixture
    async def multiple_policies(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_resource_slots: ResourceSlot,
        sample_allowed_vfolder_hosts: dict[str, Any],
    ) -> list[str]:
        """Create multiple sample policies for testing"""
        policy_names: list[str] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(3):
                spec = KeyPairResourcePolicyCreator(
                    name=str(uuid4()),
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=sample_resource_slots,
                    max_session_lifetime=86400,
                    max_concurrent_sessions=10 + i,
                    max_containers_per_session=3,
                    idle_timeout=3600,
                    allowed_vfolder_hosts=sample_allowed_vfolder_hosts,
                    max_concurrent_sftp_sessions=5,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_priority=None,
                )
                policy_row = spec.build_row()
                db_sess.add(policy_row)
                assert spec.name is not None
                policy_names.append(spec.name)
            await db_sess.commit()

        return policy_names

    @pytest.fixture
    def repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> KeypairResourcePolicyRepository:
        """Create KeypairResourcePolicyRepository instance with database"""
        return KeypairResourcePolicyRepository(db=db_with_cleanup)

    @pytest.fixture
    def ops(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> OpsRepository[KeyPairResourcePolicyData]:
        """Writes go through the generic ops repository the v2 specs are wired to."""
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    @pytest.mark.parametrize(
        "policy_creator",
        [
            pytest.param(
                KeyPairResourcePolicyCreator(
                    name=f"unlimited-policy-{uuid4()}",
                    default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                    total_resource_slots=ResourceSlot({"cpu": "4", "mem": "8g", "gpu": "1"}),
                    max_session_lifetime=0,
                    max_concurrent_sessions=100,
                    max_containers_per_session=10,
                    idle_timeout=0,
                    allowed_vfolder_hosts={
                        "local": {
                            VFolderHostPermission.CREATE,
                            VFolderHostPermission.UPLOAD_FILE,
                            VFolderHostPermission.DOWNLOAD_FILE,
                            VFolderHostPermission.MOUNT_IN_SESSION,
                        },
                        "nfs": {
                            VFolderHostPermission.CREATE,
                            VFolderHostPermission.MOUNT_IN_SESSION,
                        },
                    },
                    max_concurrent_sftp_sessions=10,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_priority=None,
                ),
                id="unlimited",
            ),
            pytest.param(
                KeyPairResourcePolicyCreator(
                    name=f"complex-resource-policy-{uuid4()}",
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot({
                        "cpu": "16",
                        "mem": "64g",
                        "gpu": "4",
                        "tpu": "2",
                        "cuda.shares": "8",
                    }),
                    max_session_lifetime=172800,
                    max_concurrent_sessions=50,
                    max_containers_per_session=5,
                    idle_timeout=7200,
                    allowed_vfolder_hosts={
                        "local": {
                            VFolderHostPermission.CREATE,
                            VFolderHostPermission.MODIFY,
                            VFolderHostPermission.DELETE,
                            VFolderHostPermission.UPLOAD_FILE,
                            VFolderHostPermission.DOWNLOAD_FILE,
                            VFolderHostPermission.MOUNT_IN_SESSION,
                        },
                        "nfs": {
                            VFolderHostPermission.CREATE,
                            VFolderHostPermission.MOUNT_IN_SESSION,
                        },
                    },
                    max_concurrent_sftp_sessions=10,
                    max_pending_session_count=10,
                    max_pending_session_resource_slots=ResourceSlot({"cpu": "2", "mem": "4g"}),
                    max_priority=None,
                ),
                id="complex_resource",
            ),
            pytest.param(
                KeyPairResourcePolicyCreator(
                    name=f"minimal-policy-{uuid4()}",
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot({"cpu": "4", "mem": "8g", "gpu": "1"}),
                    max_session_lifetime=0,
                    max_concurrent_sessions=1,
                    max_containers_per_session=1,
                    idle_timeout=0,
                    allowed_vfolder_hosts={
                        "local": {VFolderHostPermission.MOUNT_IN_SESSION},
                        "nfs": set(),
                    },
                    max_concurrent_sftp_sessions=1,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_priority=None,
                ),
                id="minimal",
            ),
        ],
    )
    async def test_create_keypair_resource_policy(
        self,
        ops: OpsRepository[KeyPairResourcePolicyData],
        policy_creator: KeyPairResourcePolicyCreator,
    ) -> None:
        """Test creating a new keypair resource policy with various configurations"""
        result = await ops.create_global_entity(policy_creator)

        assert result.name == policy_creator.name
        assert result.default_for_unspecified == policy_creator.default_for_unspecified
        assert result.total_resource_slots == policy_creator.total_resource_slots
        assert result.max_session_lifetime == policy_creator.max_session_lifetime
        assert result.max_concurrent_sessions == policy_creator.max_concurrent_sessions
        assert result.max_containers_per_session == policy_creator.max_containers_per_session
        assert result.idle_timeout == policy_creator.idle_timeout
        assert result.allowed_vfolder_hosts == policy_creator.allowed_vfolder_hosts
        assert result.max_concurrent_sftp_sessions == policy_creator.max_concurrent_sftp_sessions
        assert result.max_pending_session_count == policy_creator.max_pending_session_count
        assert (
            result.max_pending_session_resource_slots
            == policy_creator.max_pending_session_resource_slots
        )

    @pytest.mark.parametrize(
        "update_spec,expected_values",
        [
            pytest.param(
                KeyPairResourcePolicyUpdater(
                    name="",
                    default_for_unspecified=OptionalState.update(DefaultForUnspecified.UNLIMITED),
                    total_resource_slots=OptionalState.update(
                        ResourceSlot({"cpu": "8", "mem": "16g", "gpu": "2"})
                    ),
                    max_concurrent_sessions=OptionalState.update(20),
                    idle_timeout=OptionalState.update(7200),
                ),
                {
                    "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
                    "total_resource_slots": ResourceSlot({"cpu": "8", "mem": "16g", "gpu": "2"}),
                    "max_concurrent_sessions": 20,
                    "idle_timeout": 7200,
                },
                id="full_update",
            ),
            pytest.param(
                KeyPairResourcePolicyUpdater(
                    name="",
                    max_concurrent_sessions=OptionalState.update(15),
                ),
                {"max_concurrent_sessions": 15},
                id="partial_update",
            ),
            pytest.param(
                KeyPairResourcePolicyUpdater(
                    name="",
                    max_pending_session_count=TriState.nullify(),
                    max_pending_session_resource_slots=TriState.nullify(),
                ),
                {
                    "max_pending_session_count": None,
                    "max_pending_session_resource_slots": None,
                },
                id="nullify",
            ),
            pytest.param(
                KeyPairResourcePolicyUpdater(
                    name="",
                    max_pending_session_count=TriState.update(15),
                ),
                {"max_pending_session_count": 15},
                id="tristate_update",
            ),
        ],
    )
    async def test_update_keypair_resource_policy(
        self,
        ops: OpsRepository[KeyPairResourcePolicyData],
        sample_policy_name: str,
        update_spec: KeyPairResourcePolicyUpdater,
        expected_values: dict[str, Any],
    ) -> None:
        """Test updating an existing keypair resource policy with various updaters"""
        result = await ops.update(replace(update_spec, name=sample_policy_name))

        assert result.name == sample_policy_name

        for field_name, expected_value in expected_values.items():
            actual_value = getattr(result, field_name)
            assert actual_value == expected_value, (
                f"Field {field_name}: expected {expected_value}, got {actual_value}"
            )

    async def test_update_nonexistent_policy_raises_error(
        self,
        ops: OpsRepository[KeyPairResourcePolicyData],
    ) -> None:
        """Test that updating a non-existent policy raises EntityNotFoundError"""
        updater = KeyPairResourcePolicyUpdater(
            name="nonexistent-policy",
            max_concurrent_sessions=OptionalState.update(99),
        )

        with pytest.raises(EntityNotFoundError):
            await ops.update(updater)

    async def test_remove_keypair_resource_policy(
        self,
        ops: OpsRepository[KeyPairResourcePolicyData],
        sample_policy_name: str,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test removing a keypair resource policy"""
        result = await ops.purge_global_entity(KeyPairResourcePolicyPurger(name=sample_policy_name))

        assert result.name == sample_policy_name

        # Verify policy is deleted
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(
                KeyPairResourcePolicyRow.name == sample_policy_name
            )
            deleted_policy = await db_sess.scalar(query)
            assert deleted_policy is None

    async def test_remove_nonexistent_policy_raises_error(
        self,
        ops: OpsRepository[KeyPairResourcePolicyData],
    ) -> None:
        """Test that removing a non-existent policy raises EntityNotFoundError"""
        with pytest.raises(EntityNotFoundError):
            await ops.purge_global_entity(KeyPairResourcePolicyPurger(name="nonexistent-policy"))

    @pytest.fixture
    async def allowed_vfolder_updater_spec(
        self,
        sample_allowed_vfolder_hosts: dict[str, Any],
    ) -> KeyPairResourcePolicyUpdater:
        """Fixture for allowed_vfolder_hosts updater spec"""
        return KeyPairResourcePolicyUpdater(
            name="",
            allowed_vfolder_hosts=OptionalState.update(sample_allowed_vfolder_hosts),
        )

    async def test_update_allowed_vfolder_hosts(
        self,
        ops: OpsRepository[KeyPairResourcePolicyData],
        sample_policy_name: str,
        allowed_vfolder_updater_spec: KeyPairResourcePolicyUpdater,
        sample_allowed_vfolder_hosts: dict[str, Any],
    ) -> None:
        """Test updating allowed_vfolder_hosts configuration"""
        result = await ops.update(replace(allowed_vfolder_updater_spec, name=sample_policy_name))
        assert result.allowed_vfolder_hosts == sample_allowed_vfolder_hosts

    @pytest.mark.parametrize("max_priority", [None, 0, 10, 100])
    async def test_max_priority_accepts_values_within_range(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_creator: KeyPairResourcePolicyCreator,
        max_priority: int | None,
    ) -> None:
        row = sample_creator.build_row()
        row.max_priority = max_priority
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(row)
            await db_sess.commit()

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            stored = await db_sess.scalar(
                sa.select(KeyPairResourcePolicyRow.max_priority).where(
                    KeyPairResourcePolicyRow.name == sample_creator.name
                )
            )
        assert stored == max_priority

    @pytest.mark.parametrize("max_priority", [-1, 101])
    async def test_max_priority_outside_range_is_rejected(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_creator: KeyPairResourcePolicyCreator,
        max_priority: int,
    ) -> None:
        # A cap outside the requestable priority range is unsatisfiable —
        # a negative one would reject every session create for the keypair.
        row = sample_creator.build_row()
        row.max_priority = max_priority
        with pytest.raises(IntegrityError):
            async with db_with_cleanup.begin_session() as db_sess:
                db_sess.add(row)
                await db_sess.commit()
