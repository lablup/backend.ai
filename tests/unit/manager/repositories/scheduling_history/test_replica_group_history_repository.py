"""
Tests for the replica-group history search paths on SchedulingHistoryRepository.

The scoped search checks that the replica group exists, so these tests insert a
real endpoint and replica groups rather than history rows alone.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    OrderDirection,
    ReplicaGroupHistoryOrderField,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.errors.deployment import EndpointNotFound, ReplicaGroupNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group_history import ReplicaGroupHistoryRow
from ai.backend.manager.models.replica_group_history.conditions import (
    ReplicaGroupHistoryConditions,
)
from ai.backend.manager.models.replica_group_history.orders import resolve_replica_group_order
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.scheduling_history import SchedulingHistoryRepository
from ai.backend.manager.repositories.scheduling_history.types import (
    DeploymentReplicaGroupHistorySearchScope,
    ReplicaGroupReplicaGroupHistorySearchScope,
)
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class _ReplicaGroupHistorySeed:
    """A seeded deployment, its two replica groups, and their history rows."""

    deployment_id: DeploymentID
    replica_group_id: ReplicaGroupID
    sibling_replica_group_id: ReplicaGroupID
    target_lifecycle_attempts: tuple[int, ...]
    target_scaling_count: int
    sibling_count: int

    @property
    def target_count(self) -> int:
        return len(self.target_lifecycle_attempts) + self.target_scaling_count

    @property
    def deployment_count(self) -> int:
        return self.target_count + self.sibling_count


@dataclass(frozen=True)
class _ScopedSearchCase:
    """A scope dimension the scoped search accepts, plus what it should return."""

    label: str
    scope: Callable[[_ReplicaGroupHistorySeed], SearchScope]
    expected_count: Callable[[_ReplicaGroupHistorySeed], int]
    row_belongs: Callable[[ReplicaGroupHistoryData, _ReplicaGroupHistorySeed], bool]


@dataclass(frozen=True)
class _UnknownScopeCase:
    """A scope dimension pointed at a non-existent target, and the error it raises."""

    label: str
    scope: SearchScope
    error: type[Exception]


class TestReplicaGroupHistoryRepository:
    """Test cases for the replica-group history searches (read-only)"""

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
                ResourcePresetRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                EndpointRow,
                ReplicaGroupRow,
                ReplicaGroupHistoryRow,
                SessionRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scheduling_history_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[SchedulingHistoryRepository, None]:
        """Create SchedulingHistoryRepository instance with database"""
        repo = SchedulingHistoryRepository(db=db_with_cleanup)
        yield repo

    @pytest.fixture
    async def replica_group_history_seed(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> _ReplicaGroupHistorySeed:
        """Seed a deployment, two replica groups, and a fixed set of history rows.

        The scoped search checks the replica group exists, so the rows and the
        endpoint they hang off must be real; that in turn needs the domain,
        project, scaling group and user the endpoint points at.
        """
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        project_id = uuid.uuid4()
        deployment_id = DeploymentID(uuid.uuid4())
        target_group_id = ReplicaGroupID(uuid.uuid4())
        sibling_group_id = ReplicaGroupID(uuid.uuid4())
        # The target group gets a LIFECYCLE row per attempt plus this many SCALING
        # rows; the sibling group gets this many LIFECYCLE rows. Every test asserts
        # against these counts.
        target_lifecycle_attempts = (1, 2, 3)
        target_scaling_count = 2
        sibling_count = 2

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                ScalingGroupRow(
                    name=sgroup_name,
                    description="Test scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
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
                    username=f"testuser-{user_uuid.hex[:8]}",
                    email=f"test-{user_uuid.hex[:8]}@example.com",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy_name,
                )
            )
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    resource_policy=project_policy_name,
                )
            )
            await db_sess.flush()
            db_sess.add(
                EndpointRow(
                    id=deployment_id,
                    name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                    created_user=user_uuid,
                    session_owner=user_uuid,
                    domain=domain_name,
                    project=project_id,
                    resource_group=sgroup_name,
                    desired_replicas=1,
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                )
            )
            await db_sess.flush()
            for group_id in (target_group_id, sibling_group_id):
                db_sess.add(
                    ReplicaGroupRow(
                        id=group_id,
                        deployment_id=deployment_id,
                        desired_current_replica_count=1,
                        desired_target_replica_count=0,
                        lifecycle=ReplicaGroupLifecycle.STABLE,
                        scaling_status=ReplicaGroupScalingStatus.STABLE,
                        rollout=ReplicaGroupRolloutSpec(
                            max_surge=IntOrPercent(count=1),
                            max_unavailable=IntOrPercent(count=0),
                        ),
                    )
                )
            await db_sess.flush()
            for attempts in target_lifecycle_attempts:
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=target_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.LIFECYCLE,
                        phase="DEPLOYING",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"target lifecycle {attempts}",
                        attempts=attempts,
                    )
                )
            for i in range(target_scaling_count):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=target_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.SCALING,
                        phase=f"SCALING_{i}",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"target scaling {i}",
                        attempts=1,
                    )
                )
            for i in range(sibling_count):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=sibling_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.LIFECYCLE,
                        phase=f"PHASE_{i}",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"sibling {i}",
                        attempts=1,
                    )
                )
            await db_sess.commit()

        return _ReplicaGroupHistorySeed(
            deployment_id=deployment_id,
            replica_group_id=target_group_id,
            sibling_replica_group_id=sibling_group_id,
            target_lifecycle_attempts=target_lifecycle_attempts,
            target_scaling_count=target_scaling_count,
            sibling_count=sibling_count,
        )

    async def test_admin_search_replica_group_history_spans_every_group(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_history_seed: _ReplicaGroupHistorySeed,
    ) -> None:
        """Test that the unscoped admin search returns rows from every replica group"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scheduling_history_repository.admin_search_replica_group_history(querier)

        assert result.total_count == replica_group_history_seed.deployment_count
        assert {item.replica_group_id for item in result.items} == {
            replica_group_history_seed.replica_group_id,
            replica_group_history_seed.sibling_replica_group_id,
        }

    async def test_admin_search_replica_group_history_pagination(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_history_seed: _ReplicaGroupHistorySeed,
    ) -> None:
        """Test searching replica-group history with pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scheduling_history_repository.admin_search_replica_group_history(querier)

        assert len(result.items) == 2
        assert result.total_count == replica_group_history_seed.deployment_count
        assert result.has_next_page is True
        assert result.has_previous_page is False

    async def test_admin_search_replica_group_history_by_category(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_history_seed: _ReplicaGroupHistorySeed,
    ) -> None:
        """Test searching replica-group history filtered by handler category"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                ReplicaGroupHistoryConditions.by_category(ReplicaGroupHandlerCategory.SCALING)
            ],
            orders=[],
        )
        result = await scheduling_history_repository.admin_search_replica_group_history(querier)

        assert result.total_count == replica_group_history_seed.target_scaling_count
        assert all(item.category == ReplicaGroupHandlerCategory.SCALING for item in result.items)

    @pytest.mark.parametrize(
        "case",
        [
            _ScopedSearchCase(
                label="replica-group",
                scope=lambda seed: ReplicaGroupReplicaGroupHistorySearchScope(
                    replica_group_id=seed.replica_group_id
                ),
                expected_count=lambda seed: seed.target_count,
                row_belongs=lambda item, seed: item.replica_group_id == seed.replica_group_id,
            ),
            _ScopedSearchCase(
                label="deployment",
                scope=lambda seed: DeploymentReplicaGroupHistorySearchScope(
                    deployment_id=seed.deployment_id
                ),
                expected_count=lambda seed: seed.deployment_count,
                row_belongs=lambda item, seed: item.deployment_id == seed.deployment_id,
            ),
        ],
        ids=lambda case: case.label,
    )
    async def test_scoped_search_returns_the_rows_within_the_scope(
        self,
        case: _ScopedSearchCase,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_history_seed: _ReplicaGroupHistorySeed,
    ) -> None:
        """Test that the scoped search returns exactly the rows under the scope"""
        seed = replica_group_history_seed
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            querier, [case.scope(seed)]
        )

        assert result.total_count == case.expected_count(seed)
        assert all(case.row_belongs(item, seed) for item in result.items)

    async def test_scoped_search_replica_group_history_narrows_within_the_scope(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_history_seed: _ReplicaGroupHistorySeed,
    ) -> None:
        """Test that a querier condition narrows further, still bounded by the scope"""
        target_group_id = replica_group_history_seed.replica_group_id

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                ReplicaGroupHistoryConditions.by_category(ReplicaGroupHandlerCategory.SCALING)
            ],
            orders=[],
        )
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            querier,
            [ReplicaGroupReplicaGroupHistorySearchScope(replica_group_id=target_group_id)],
        )

        # Bounded by the scope (target only) and narrowed by the category condition.
        assert result.total_count == replica_group_history_seed.target_scaling_count
        assert all(
            item.replica_group_id == target_group_id
            and item.category == ReplicaGroupHandlerCategory.SCALING
            for item in result.items
        )

    async def test_scoped_search_replica_group_history_ordering(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_history_seed: _ReplicaGroupHistorySeed,
    ) -> None:
        """Test that the requested order reaches the query"""
        target_group_id = replica_group_history_seed.replica_group_id

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[
                resolve_replica_group_order(
                    ReplicaGroupHistoryOrderField.ATTEMPTS, OrderDirection.ASC
                )
            ],
        )
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            querier,
            [ReplicaGroupReplicaGroupHistorySearchScope(replica_group_id=target_group_id)],
        )

        returned_attempts = [item.attempts for item in result.items]
        assert returned_attempts == sorted(returned_attempts)
        assert returned_attempts[0] == min(replica_group_history_seed.target_lifecycle_attempts)
        assert returned_attempts[-1] == max(replica_group_history_seed.target_lifecycle_attempts)

    @pytest.mark.parametrize(
        "case",
        [
            _UnknownScopeCase(
                label="replica-group",
                scope=ReplicaGroupReplicaGroupHistorySearchScope(
                    replica_group_id=ReplicaGroupID(
                        uuid.UUID("00000000-0000-0000-0000-0000000000aa")
                    )
                ),
                error=ReplicaGroupNotFound,
            ),
            _UnknownScopeCase(
                label="deployment",
                scope=DeploymentReplicaGroupHistorySearchScope(
                    deployment_id=DeploymentID(uuid.UUID("00000000-0000-0000-0000-0000000000bb"))
                ),
                error=EndpointNotFound,
            ),
        ],
        ids=lambda case: case.label,
    )
    async def test_scoped_search_rejects_an_unknown_scope(
        self,
        case: _UnknownScopeCase,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that the scope's existence check rejects a non-existent target"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        with pytest.raises(case.error):
            await scheduling_history_repository.scoped_search_replica_group_history(
                querier, [case.scope]
            )

    async def test_resolve_replica_group_deployment(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_history_seed: _ReplicaGroupHistorySeed,
    ) -> None:
        """Test resolving the deployment owning a replica group"""
        resolved = await scheduling_history_repository.resolve_replica_group_deployment(
            replica_group_history_seed.replica_group_id
        )

        assert resolved == replica_group_history_seed.deployment_id

    async def test_resolve_replica_group_deployment_unknown_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that resolving an unknown replica group raises"""
        with pytest.raises(ReplicaGroupNotFound):
            await scheduling_history_repository.resolve_replica_group_deployment(
                ReplicaGroupID(uuid.uuid4())
            )
