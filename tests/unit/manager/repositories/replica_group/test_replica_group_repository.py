"""DB-backed tests for ReplicaGroupRepository search/update."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
    RouteHealthStatus,
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group.conditions import ReplicaGroupConditions
from ai.backend.manager.models.replica_group_history import ReplicaGroupHistoryRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment.updaters import (
    ReplicaGroupDeployUpdaterSpec,
    ReplicaGroupScalingUpdaterSpec,
)
from ai.backend.manager.repositories.replica_group import ReplicaGroupRepository
from ai.backend.manager.repositories.replica_group.types import (
    GroupRouteDrainInstruction,
    ReplicaGroupScalingReconcileApply,
)
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


def _running_route(
    endpoint_row: EndpointRow,
    group_id: ReplicaGroupID,
    revision_id: DeploymentRevisionID,
    *,
    route_id: uuid.UUID,
    health_status: RouteHealthStatus,
    created_at: datetime,
) -> RoutingRow:
    return RoutingRow(
        id=route_id,
        endpoint=endpoint_row.id,
        session=None,
        session_owner=endpoint_row.session_owner,
        domain=endpoint_row.domain,
        project=endpoint_row.project,
        traffic_ratio=1.0,
        revision=revision_id,
        replica_group_id=group_id,
        status=RouteStatus.RUNNING,
        traffic_status=RouteTrafficStatus.ACTIVE,
        health_status=health_status,
        created_at=created_at,
    )


def _provisioning_route(
    endpoint_row: EndpointRow,
    group_id: ReplicaGroupID,
    revision_id: DeploymentRevisionID,
    *,
    route_id: uuid.UUID,
    created_at: datetime,
) -> RoutingRow:
    return RoutingRow(
        id=route_id,
        endpoint=endpoint_row.id,
        session=None,
        session_owner=endpoint_row.session_owner,
        domain=endpoint_row.domain,
        project=endpoint_row.project,
        traffic_ratio=1.0,
        revision=revision_id,
        replica_group_id=group_id,
        status=RouteStatus.PROVISIONING,
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_status=RouteHealthStatus.NOT_CHECKED,
        created_at=created_at,
    )


def _password_info(password: str) -> PasswordInfo:
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestReplicaGroupRepository:
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
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentID:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        endpoint_id = DeploymentID(uuid.uuid4())

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
                    password=_password_info("test_password"),
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
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    resource_policy=project_policy_name,
                )
            )
            await db_sess.flush()
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                    created_user=user_uuid,
                    session_owner=user_uuid,
                    domain=domain_name,
                    project=group_id,
                    resource_group=sgroup_name,
                    desired_replicas=1,
                    url=f"http://test-{uuid.uuid4().hex[:8]}.example.com",
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.DESTROYED,
                )
            )
            await db_sess.commit()

        return endpoint_id

    @pytest.fixture
    async def two_group_ids(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: DeploymentID,
    ) -> tuple[ReplicaGroupID, ReplicaGroupID]:
        first = ReplicaGroupID(uuid.uuid4())
        second = ReplicaGroupID(uuid.uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ReplicaGroupRow(
                    id=first,
                    deployment_id=test_endpoint_id,
                    desired_current_replica_count=1,
                    desired_target_replica_count=0,
                    lifecycle=ReplicaGroupLifecycle.ROLLING,
                    scaling_status=ReplicaGroupScalingStatus.SCALING,
                )
            )
            db_sess.add(
                ReplicaGroupRow(
                    id=second,
                    deployment_id=test_endpoint_id,
                    desired_current_replica_count=2,
                    desired_target_replica_count=0,
                    lifecycle=ReplicaGroupLifecycle.STABLE,
                    scaling_status=ReplicaGroupScalingStatus.STABLE,
                )
            )
            await db_sess.commit()
        return first, second

    @pytest.fixture
    def replica_group_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ReplicaGroupRepository:
        return ReplicaGroupRepository(db=db_with_cleanup)

    async def test_search_deploy_scheduling_views_filters_by_lifecycle(
        self,
        replica_group_repository: ReplicaGroupRepository,
        two_group_ids: tuple[ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        rolling_group_id, _ = two_group_ids
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10),
            conditions=[ReplicaGroupConditions.by_lifecycles([ReplicaGroupLifecycle.ROLLING])],
        )

        result = await replica_group_repository.search_deploy_scheduling_views(querier)

        assert len(result) == 1
        assert result[0].group_id == rolling_group_id
        assert result[0].lifecycle is ReplicaGroupLifecycle.ROLLING

    async def test_search_scaling_scheduling_views_filters_by_scaling_status(
        self,
        replica_group_repository: ReplicaGroupRepository,
        two_group_ids: tuple[ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        scaling_group_id, _ = two_group_ids
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10),
            conditions=[
                ReplicaGroupConditions.by_scaling_statuses([ReplicaGroupScalingStatus.SCALING])
            ],
        )

        result = await replica_group_repository.search_scaling_scheduling_views(querier)

        assert len(result) == 1
        assert result[0].group_id == scaling_group_id
        assert result[0].desired_current_replica_count == 1
        assert result[0].scaling_status is ReplicaGroupScalingStatus.SCALING

    async def test_update_replica_groups_applies_per_id_deploy_values(
        self,
        replica_group_repository: ReplicaGroupRepository,
        two_group_ids: tuple[ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        first_id, second_id = two_group_ids
        updaters: list[Updater[ReplicaGroupRow]] = [
            Updater(
                spec=ReplicaGroupDeployUpdaterSpec(
                    lifecycle=OptionalState.update(ReplicaGroupLifecycle.DRAINING),
                ),
                pk_value=first_id,
            ),
            Updater(
                spec=ReplicaGroupDeployUpdaterSpec(
                    lifecycle=OptionalState.update(ReplicaGroupLifecycle.DRAINED),
                ),
                pk_value=second_id,
            ),
        ]

        result = await replica_group_repository.update_replica_groups(updaters)

        assert result.success_count() == 2
        assert result.has_failures() is False

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10),
            conditions=[ReplicaGroupConditions.by_ids([first_id, second_id])],
        )
        groups = await replica_group_repository.search_deploy_scheduling_views(querier)
        lifecycle_by_id = {group.group_id: group.lifecycle for group in groups}
        assert lifecycle_by_id[first_id] is ReplicaGroupLifecycle.DRAINING
        assert lifecycle_by_id[second_id] is ReplicaGroupLifecycle.DRAINED

    async def test_fetch_autoscale_reconcile_views_counts_live_and_serving_routes(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        replica_group_repository: ReplicaGroupRepository,
        test_endpoint_id: DeploymentID,
    ) -> None:
        group_id = ReplicaGroupID(uuid.uuid4())
        current_revision_id = DeploymentRevisionID(uuid.uuid4())
        other_revision_id = DeploymentRevisionID(uuid.uuid4())
        route_specs = [
            (current_revision_id, RouteStatus.RUNNING, RouteTrafficStatus.ACTIVE),
            (current_revision_id, RouteStatus.RUNNING, RouteTrafficStatus.ACTIVE),
            (current_revision_id, RouteStatus.PROVISIONING, RouteTrafficStatus.INACTIVE),
            (current_revision_id, RouteStatus.RUNNING, RouteTrafficStatus.INACTIVE),
            (current_revision_id, RouteStatus.TERMINATED, RouteTrafficStatus.INACTIVE),
            (other_revision_id, RouteStatus.RUNNING, RouteTrafficStatus.ACTIVE),
        ]
        async with db_with_cleanup.begin_session() as db_sess:
            endpoint_row = (
                await db_sess.execute(
                    sa.select(EndpointRow).where(EndpointRow.id == test_endpoint_id)
                )
            ).scalar_one()
            db_sess.add(
                ReplicaGroupRow(
                    id=group_id,
                    deployment_id=test_endpoint_id,
                    current_revision_id=current_revision_id,
                    desired_current_replica_count=3,
                    desired_target_replica_count=0,
                    lifecycle=ReplicaGroupLifecycle.STABLE,
                    scaling_status=ReplicaGroupScalingStatus.STABLE,
                )
            )
            for revision_id, route_status, route_traffic_status in route_specs:
                db_sess.add(
                    RoutingRow(
                        id=uuid.uuid4(),
                        endpoint=test_endpoint_id,
                        session=None,
                        session_owner=endpoint_row.session_owner,
                        domain=endpoint_row.domain,
                        project=endpoint_row.project,
                        traffic_ratio=1.0,
                        revision=revision_id,
                        replica_group_id=group_id,
                        status=route_status,
                        traffic_status=route_traffic_status,
                    )
                )
            await db_sess.commit()

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10),
            conditions=[ReplicaGroupConditions.by_ids([group_id])],
        )
        fetch = await replica_group_repository.fetch_autoscale_reconcile_views(
            querier, ReplicaGroupHandlerCategory.LIFECYCLE
        )

        assert len(fetch.views) == 1
        view = fetch.views[0]
        assert view.group_id == group_id
        assert view.desired_current_replica_count == 3
        assert view.deployment_desired_replica_count == 1
        # live = PROVISIONING or (RUNNING & ACTIVE); RUNNING+INACTIVE and TERMINATED are
        # excluded, and so are routes of revisions other than the group's current one.
        assert view.current_live_replica_count == 3
        assert view.current_serving_replica_count == 2

    async def test_update_replica_groups_applies_per_id_scaling_values(
        self,
        replica_group_repository: ReplicaGroupRepository,
        two_group_ids: tuple[ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        first_id, second_id = two_group_ids
        updaters: list[Updater[ReplicaGroupRow]] = [
            Updater(
                spec=ReplicaGroupScalingUpdaterSpec(
                    desired_current_replica_count=OptionalState.update(5),
                ),
                pk_value=first_id,
            ),
            Updater(
                spec=ReplicaGroupScalingUpdaterSpec(
                    desired_current_replica_count=OptionalState.update(7),
                ),
                pk_value=second_id,
            ),
        ]

        result = await replica_group_repository.update_replica_groups(updaters)

        assert result.success_count() == 2
        assert result.has_failures() is False

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10),
            conditions=[ReplicaGroupConditions.by_ids([first_id, second_id])],
        )
        groups = await replica_group_repository.search_scaling_scheduling_views(querier)
        count_by_id = {group.group_id: group.desired_current_replica_count for group in groups}
        assert count_by_id[first_id] == 5
        assert count_by_id[second_id] == 7

    async def test_apply_scaling_reconcile_drains_least_healthy_routes_first(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        replica_group_repository: ReplicaGroupRepository,
        test_endpoint_id: DeploymentID,
    ) -> None:
        group_id = ReplicaGroupID(uuid.uuid4())
        revision_id = DeploymentRevisionID(uuid.uuid4())
        base = datetime(2026, 1, 1, tzinfo=UTC)
        healthy_old_id = uuid.uuid4()
        healthy_new_id = uuid.uuid4()
        unhealthy_id = uuid.uuid4()
        degraded_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            endpoint_row = (
                await db_sess.execute(
                    sa.select(EndpointRow).where(EndpointRow.id == test_endpoint_id)
                )
            ).scalar_one()
            db_sess.add(
                ReplicaGroupRow(
                    id=group_id,
                    deployment_id=test_endpoint_id,
                    current_revision_id=revision_id,
                    desired_current_replica_count=2,
                    desired_target_replica_count=0,
                    lifecycle=ReplicaGroupLifecycle.STABLE,
                    scaling_status=ReplicaGroupScalingStatus.SCALING,
                )
            )
            # Oldest routes are HEALTHY; newer routes are UNHEALTHY/DEGRADED.
            # Priority must win over created_at, so the unhealthy ones drain first.
            db_sess.add(
                _running_route(
                    endpoint_row,
                    group_id,
                    revision_id,
                    route_id=healthy_old_id,
                    health_status=RouteHealthStatus.HEALTHY,
                    created_at=base,
                )
            )
            db_sess.add(
                _running_route(
                    endpoint_row,
                    group_id,
                    revision_id,
                    route_id=unhealthy_id,
                    health_status=RouteHealthStatus.UNHEALTHY,
                    created_at=base + timedelta(minutes=1),
                )
            )
            db_sess.add(
                _running_route(
                    endpoint_row,
                    group_id,
                    revision_id,
                    route_id=degraded_id,
                    health_status=RouteHealthStatus.DEGRADED,
                    created_at=base + timedelta(minutes=2),
                )
            )
            db_sess.add(
                _running_route(
                    endpoint_row,
                    group_id,
                    revision_id,
                    route_id=healthy_new_id,
                    health_status=RouteHealthStatus.HEALTHY,
                    created_at=base + timedelta(minutes=3),
                )
            )
            await db_sess.commit()

        await replica_group_repository.apply_scaling_reconcile(
            ReplicaGroupScalingReconcileApply(
                drain_instructions=[
                    GroupRouteDrainInstruction(
                        replica_group_id=group_id,
                        revision_id=revision_id,
                        count=2,
                    )
                ],
            )
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = (
                await db_sess.execute(
                    sa.select(RoutingRow.id, RoutingRow.status, RoutingRow.sub_status).where(
                        RoutingRow.replica_group_id == group_id
                    )
                )
            ).all()
        status_by_id = {row.id: row.status for row in rows}
        sub_status_by_id = {row.id: row.sub_status for row in rows}
        assert status_by_id[unhealthy_id] is RouteStatus.TERMINATING
        assert status_by_id[degraded_id] is RouteStatus.TERMINATING
        assert sub_status_by_id[unhealthy_id] is RouteSubStatus.DRAINING
        assert sub_status_by_id[degraded_id] is RouteSubStatus.DRAINING
        assert status_by_id[healthy_old_id] is RouteStatus.RUNNING
        assert status_by_id[healthy_new_id] is RouteStatus.RUNNING

    async def test_apply_scaling_reconcile_breaks_ties_by_oldest_first(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        replica_group_repository: ReplicaGroupRepository,
        test_endpoint_id: DeploymentID,
    ) -> None:
        group_id = ReplicaGroupID(uuid.uuid4())
        revision_id = DeploymentRevisionID(uuid.uuid4())
        base = datetime(2026, 1, 1, tzinfo=UTC)
        oldest_id = uuid.uuid4()
        middle_id = uuid.uuid4()
        newest_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            endpoint_row = (
                await db_sess.execute(
                    sa.select(EndpointRow).where(EndpointRow.id == test_endpoint_id)
                )
            ).scalar_one()
            db_sess.add(
                ReplicaGroupRow(
                    id=group_id,
                    deployment_id=test_endpoint_id,
                    current_revision_id=revision_id,
                    desired_current_replica_count=1,
                    desired_target_replica_count=0,
                    lifecycle=ReplicaGroupLifecycle.STABLE,
                    scaling_status=ReplicaGroupScalingStatus.SCALING,
                )
            )
            # All equally healthy -> created_at ascending decides: oldest drains first.
            for route_id, offset in (
                (oldest_id, 0),
                (middle_id, 1),
                (newest_id, 2),
            ):
                db_sess.add(
                    _running_route(
                        endpoint_row,
                        group_id,
                        revision_id,
                        route_id=route_id,
                        health_status=RouteHealthStatus.HEALTHY,
                        created_at=base + timedelta(minutes=offset),
                    )
                )
            await db_sess.commit()

        await replica_group_repository.apply_scaling_reconcile(
            ReplicaGroupScalingReconcileApply(
                drain_instructions=[
                    GroupRouteDrainInstruction(
                        replica_group_id=group_id,
                        revision_id=revision_id,
                        count=2,
                    )
                ],
            )
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = (
                await db_sess.execute(
                    sa.select(RoutingRow.id, RoutingRow.status).where(
                        RoutingRow.replica_group_id == group_id
                    )
                )
            ).all()
        status_by_id = {row.id: row.status for row in rows}
        assert status_by_id[oldest_id] is RouteStatus.TERMINATING
        assert status_by_id[middle_id] is RouteStatus.TERMINATING
        assert status_by_id[newest_id] is RouteStatus.RUNNING

    async def test_apply_scaling_reconcile_drains_not_yet_serving_routes_first(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        replica_group_repository: ReplicaGroupRepository,
        test_endpoint_id: DeploymentID,
    ) -> None:
        group_id = ReplicaGroupID(uuid.uuid4())
        revision_id = DeploymentRevisionID(uuid.uuid4())
        base = datetime(2026, 1, 1, tzinfo=UTC)
        provisioning_old_id = uuid.uuid4()
        provisioning_new_id = uuid.uuid4()
        running_healthy_id = uuid.uuid4()
        running_unhealthy_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            endpoint_row = (
                await db_sess.execute(
                    sa.select(EndpointRow).where(EndpointRow.id == test_endpoint_id)
                )
            ).scalar_one()
            db_sess.add(
                ReplicaGroupRow(
                    id=group_id,
                    deployment_id=test_endpoint_id,
                    current_revision_id=revision_id,
                    desired_current_replica_count=2,
                    desired_target_replica_count=0,
                    lifecycle=ReplicaGroupLifecycle.STABLE,
                    scaling_status=ReplicaGroupScalingStatus.SCALING,
                )
            )
            # Not-yet-serving PROVISIONING routes must drain before serving RUNNING ones,
            # even an UNHEALTHY RUNNING route, since they are not receiving traffic yet.
            db_sess.add(
                _provisioning_route(
                    endpoint_row,
                    group_id,
                    revision_id,
                    route_id=provisioning_old_id,
                    created_at=base,
                )
            )
            db_sess.add(
                _running_route(
                    endpoint_row,
                    group_id,
                    revision_id,
                    route_id=running_healthy_id,
                    health_status=RouteHealthStatus.HEALTHY,
                    created_at=base + timedelta(minutes=1),
                )
            )
            db_sess.add(
                _provisioning_route(
                    endpoint_row,
                    group_id,
                    revision_id,
                    route_id=provisioning_new_id,
                    created_at=base + timedelta(minutes=2),
                )
            )
            db_sess.add(
                _running_route(
                    endpoint_row,
                    group_id,
                    revision_id,
                    route_id=running_unhealthy_id,
                    health_status=RouteHealthStatus.UNHEALTHY,
                    created_at=base + timedelta(minutes=3),
                )
            )
            await db_sess.commit()

        await replica_group_repository.apply_scaling_reconcile(
            ReplicaGroupScalingReconcileApply(
                drain_instructions=[
                    GroupRouteDrainInstruction(
                        replica_group_id=group_id,
                        revision_id=revision_id,
                        count=2,
                    )
                ],
            )
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = (
                await db_sess.execute(
                    sa.select(RoutingRow.id, RoutingRow.status).where(
                        RoutingRow.replica_group_id == group_id
                    )
                )
            ).all()
        status_by_id = {row.id: row.status for row in rows}
        assert status_by_id[provisioning_old_id] is RouteStatus.TERMINATING
        assert status_by_id[provisioning_new_id] is RouteStatus.TERMINATING
        assert status_by_id[running_healthy_id] is RouteStatus.RUNNING
        assert status_by_id[running_unhealthy_id] is RouteStatus.RUNNING
