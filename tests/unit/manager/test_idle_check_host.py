"""
Tests for ``IdleCheckerHost.do_idle_check()`` against a real database.

The idle policy is resolved through the user's main keypair — the one marked
``keypairs.is_default`` — instead of the kernel's own ``access_key``, which a
keypair deletion can leave orphaned. A kernel whose policy cannot be resolved,
or whose checker raises, must not stop the remaining kernels of the same cycle
from being checked.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar, override
from unittest.mock import MagicMock

import pytest
from dateutil.tz import tzutc
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SecretKey,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.idle import (
    BaseIdleChecker,
    IdleCheckerError,
    IdleCheckerHost,
    RemainingTimeType,
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
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.db.engine import create_async_engine
from ai.backend.testutils.db import with_tables

IDLE_LOGGER_NAME = "ai.backend.manager.idle"

_IDLE_ROWS = [
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
    AssociationScopesEntitiesRow,
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
]


class _RecordingChecker(BaseIdleChecker):
    """Records which kernels were checked and with which policy."""

    name: ClassVar[str] = "recording"
    remaining_time_type: RemainingTimeType = RemainingTimeType.EXPIRE_AFTER

    checked_kernel_ids: list[uuid.UUID]
    seen_idle_timeouts: dict[uuid.UUID, int | None]
    _failing_kernel_ids: frozenset[uuid.UUID]

    def __init__(self, failing_kernel_ids: frozenset[uuid.UUID] = frozenset()) -> None:
        self.checked_kernel_ids = []
        self.seen_idle_timeouts = {}
        self._failing_kernel_ids = failing_kernel_ids

    @override
    async def populate_config(self, config: Mapping[str, Any]) -> None:
        return None

    @override
    async def get_extra_info(
        self, redis_obj: ValkeyLiveClient, session_id: SessionId
    ) -> dict[str, Any] | None:
        return None

    @override
    async def get_checker_result(
        self, redis_obj: ValkeyLiveClient, session_id: SessionId
    ) -> float | None:
        return None

    @override
    def terminate_reason(self) -> KernelLifecycleEventReason:
        return KernelLifecycleEventReason.IDLE_TIMEOUT

    @override
    async def check_idleness(
        self,
        kernel: Row[Any],
        dbconn: SAConnection,
        policy: Row[Any],
        *,
        grace_period_end: datetime | None = None,
    ) -> bool:
        self.checked_kernel_ids.append(kernel.id)
        self.seen_idle_timeouts[kernel.id] = policy.idle_timeout
        if kernel.id in self._failing_kernel_ids:
            raise RuntimeError("checker failed for this kernel")
        return True

    @override
    async def callback_idle_session(self, session_id: SessionId) -> None:
        return None


@pytest.fixture
async def database_connection(
    postgres_container: tuple[str, HostPortPairModel],
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    _, addr = postgres_container
    url = f"postgresql+asyncpg://postgres:develove@{addr.host}:{addr.port}/testing"
    engine = create_async_engine(url, pool_size=8, pool_pre_ping=False, max_overflow=64)
    yield engine
    await engine.dispose()


class TestDoIdleCheck:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, _IDLE_ROWS):
            yield database_connection

    @pytest.fixture
    async def domain(self, db: ExtendedAsyncSAEngine) -> tuple[DomainID, str]:
        domain_id = DomainID(uuid.uuid4())
        name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("1000"),
                        "mem": Decimal("1048576"),
                    }),
                )
            )
            await db_sess.flush()
        return domain_id, name

    @pytest.fixture
    async def scaling_group(self, db: ExtendedAsyncSAEngine) -> tuple[ResourceGroupID, str]:
        sg_id = ResourceGroupID(uuid.uuid4())
        name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with db.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    id=sg_id,
                    name=name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(
                        allowed_session_types=[],
                        config={},
                    ),
                    driver_opts={},
                    is_active=True,
                )
            )
            await db_sess.flush()
        return sg_id, name

    @pytest.fixture
    async def group_id(self, db: ExtendedAsyncSAEngine, domain: tuple[DomainID, str]) -> uuid.UUID:
        _, domain_name = domain
        project_policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"
        gid = uuid.uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
            db_sess.add(
                GroupRow(
                    id=gid,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("500"),
                        "mem": Decimal("524288"),
                    }),
                    resource_policy=project_policy_name,
                    integration_id=None,
                )
            )
            await db_sess.flush()
        return gid

    @pytest.fixture
    async def user_resource_policy_name(self, db: ExtendedAsyncSAEngine) -> str:
        name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        async with db.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
        return name

    async def _create_keypair_policy(self, db: ExtendedAsyncSAEngine, idle_timeout: int) -> str:
        name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"
        async with db.begin_session() as db_sess:
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=name,
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("100"),
                        "mem": Decimal("102400"),
                    }),
                    max_concurrent_sessions=10,
                    max_containers_per_session=1,
                    idle_timeout=idle_timeout,
                    max_session_lifetime=0,
                    allowed_vfolder_hosts={},
                )
            )
            await db_sess.flush()
        return name

    async def _create_user(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        user_resource_policy_name: str,
        main_keypair_idle_timeout: int | None,
    ) -> tuple[uuid.UUID, AccessKey | None]:
        """Create a user; ``None`` idle timeout leaves the user without a main keypair."""
        user_uuid = uuid.uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                    username=f"test-user-{uuid.uuid4().hex[:8]}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_name=domain_name,
                    resource_policy=user_resource_policy_name,
                )
            )
            await db_sess.flush()
        if main_keypair_idle_timeout is None:
            return user_uuid, None
        access_key = await self._create_keypair(
            db, user_uuid=user_uuid, idle_timeout=main_keypair_idle_timeout, is_default=True
        )
        return user_uuid, access_key

    async def _create_keypair(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        user_uuid: uuid.UUID,
        idle_timeout: int,
        is_default: bool = False,
    ) -> AccessKey:
        policy_name = await self._create_keypair_policy(db, idle_timeout)
        access_key = AccessKey(f"AKTEST{uuid.uuid4().hex[:14]}")
        async with db.begin_session() as db_sess:
            db_sess.add(
                KeyPairRow(
                    access_key=access_key,
                    secret_key=SecretKey(f"SK{uuid.uuid4().hex[:38]}"),
                    user=user_uuid,
                    user_id=str(user_uuid),
                    is_active=True,
                    is_admin=False,
                    is_default=is_default,
                    resource_policy=policy_name,
                )
            )
            await db_sess.flush()
        return access_key

    async def _create_running_kernel(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain: tuple[DomainID, str],
        scaling_group: tuple[ResourceGroupID, str],
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
    ) -> KernelId:
        domain_id, domain_name = domain
        sg_id, sg_name = scaling_group
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())
        now = datetime.now(tzutc())
        slots = ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("2048")})
        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    access_key=access_key,
                    resource_group_id=sg_id,
                    scaling_group_name=sg_name,
                    status=SessionStatus.RUNNING,
                    status_info="test",
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=slots,
                    created_at=now,
                    starts_at=now,
                    images=["python:3.8"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    scaling_group=sg_name,
                    resource_group_id=sg_id,
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    status=KernelStatus.RUNNING,
                    status_changed=now,
                    session_type=SessionTypes.INTERACTIVE,
                    occupied_slots=slots,
                    requested_slots=slots,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    access_key=access_key,
                    created_at=now,
                    starts_at=now,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001,
                    repl_out_port=2002,
                    stdin_port=2003,
                    stdout_port=2004,
                )
            )
            await db_sess.flush()
        return kernel_id

    def _make_host(self, db: ExtendedAsyncSAEngine, checker: BaseIdleChecker) -> IdleCheckerHost:
        host = IdleCheckerHost(
            db,
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )
        host.add_checker(checker)
        return host

    async def test_policy_resolved_via_main_keypair(
        self,
        db: ExtendedAsyncSAEngine,
        domain: tuple[DomainID, str],
        scaling_group: tuple[ResourceGroupID, str],
        group_id: uuid.UUID,
        user_resource_policy_name: str,
    ) -> None:
        """A kernel created with a secondary keypair uses the main keypair's policy."""
        user_uuid, main_access_key = await self._create_user(
            db,
            domain_name=domain[1],
            user_resource_policy_name=user_resource_policy_name,
            main_keypair_idle_timeout=600,
        )
        assert main_access_key is not None
        secondary_access_key = await self._create_keypair(db, user_uuid=user_uuid, idle_timeout=30)
        kernel_id = await self._create_running_kernel(
            db,
            domain=domain,
            scaling_group=scaling_group,
            group_id=group_id,
            user_uuid=user_uuid,
            access_key=secondary_access_key,
        )

        checker = _RecordingChecker()
        await self._make_host(db, checker).do_idle_check()

        assert checker.checked_kernel_ids == [kernel_id]
        assert checker.seen_idle_timeouts[kernel_id] == 600

    async def test_orphaned_kernel_access_key_is_still_checked(
        self,
        db: ExtendedAsyncSAEngine,
        domain: tuple[DomainID, str],
        scaling_group: tuple[ResourceGroupID, str],
        group_id: uuid.UUID,
        user_resource_policy_name: str,
    ) -> None:
        """A kernel whose own access key has no keypair row is checked all the same."""
        user_uuid, _ = await self._create_user(
            db,
            domain_name=domain[1],
            user_resource_policy_name=user_resource_policy_name,
            main_keypair_idle_timeout=600,
        )
        kernel_id = await self._create_running_kernel(
            db,
            domain=domain,
            scaling_group=scaling_group,
            group_id=group_id,
            user_uuid=user_uuid,
            access_key=AccessKey(f"AKDELETED{uuid.uuid4().hex[:11]}"),
        )

        checker = _RecordingChecker()
        await self._make_host(db, checker).do_idle_check()

        assert checker.checked_kernel_ids == [kernel_id]
        assert checker.seen_idle_timeouts[kernel_id] == 600

    async def test_unresolvable_policy_skips_only_its_own_kernels(
        self,
        db: ExtendedAsyncSAEngine,
        domain: tuple[DomainID, str],
        scaling_group: tuple[ResourceGroupID, str],
        group_id: uuid.UUID,
        user_resource_policy_name: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A user without a main access key never blocks the rest of the cycle,
        and its missing policy is warned about only once."""
        policyless_uuid, _ = await self._create_user(
            db,
            domain_name=domain[1],
            user_resource_policy_name=user_resource_policy_name,
            main_keypair_idle_timeout=None,
        )
        normal_uuid, normal_access_key = await self._create_user(
            db,
            domain_name=domain[1],
            user_resource_policy_name=user_resource_policy_name,
            main_keypair_idle_timeout=600,
        )
        assert normal_access_key is not None
        orphan_access_key = AccessKey(f"AKDELETED{uuid.uuid4().hex[:11]}")
        for _ in range(2):
            await self._create_running_kernel(
                db,
                domain=domain,
                scaling_group=scaling_group,
                group_id=group_id,
                user_uuid=policyless_uuid,
                access_key=orphan_access_key,
            )
        normal_kernel_ids = [
            await self._create_running_kernel(
                db,
                domain=domain,
                scaling_group=scaling_group,
                group_id=group_id,
                user_uuid=normal_uuid,
                access_key=normal_access_key,
            )
            for _ in range(2)
        ]

        checker = _RecordingChecker()
        with caplog.at_level(logging.WARNING, logger=IDLE_LOGGER_NAME):
            await self._make_host(db, checker).do_idle_check()

        assert sorted(checker.checked_kernel_ids) == sorted(normal_kernel_ids)
        warnings = [
            record
            for record in caplog.records
            if record.name == IDLE_LOGGER_NAME and "idle policy not found" in record.getMessage()
        ]
        assert len(warnings) == 1

    async def test_checker_error_does_not_skip_remaining_kernels(
        self,
        db: ExtendedAsyncSAEngine,
        domain: tuple[DomainID, str],
        scaling_group: tuple[ResourceGroupID, str],
        group_id: uuid.UUID,
        user_resource_policy_name: str,
    ) -> None:
        """A checker failing on one kernel still lets the others be checked."""
        user_uuid, access_key = await self._create_user(
            db,
            domain_name=domain[1],
            user_resource_policy_name=user_resource_policy_name,
            main_keypair_idle_timeout=600,
        )
        assert access_key is not None
        kernel_ids = [
            await self._create_running_kernel(
                db,
                domain=domain,
                scaling_group=scaling_group,
                group_id=group_id,
                user_uuid=user_uuid,
                access_key=access_key,
            )
            for _ in range(3)
        ]

        checker = _RecordingChecker(failing_kernel_ids=frozenset({kernel_ids[0]}))
        with pytest.raises(IdleCheckerError):
            await self._make_host(db, checker).do_idle_check()

        assert sorted(checker.checked_kernel_ids) == sorted(kernel_ids)
