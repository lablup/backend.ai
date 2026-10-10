from __future__ import annotations

import enum
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.auto_scaling_rule import AutoScalingRuleID
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import AutoScalingMetricSource, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.scale import AutoScalingRule
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointAutoScalingRuleRow, EndpointRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.deployment.repository import (
    AutoScalingMetricsData,
    DeploymentRepository,
)
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData

_SCALE_UP_THRESHOLD = Decimal("80")
_SCALE_DOWN_THRESHOLD = Decimal("20")


class _Load(enum.Enum):
    HIGH = Decimal("90")
    LOW = Decimal("10")


@dataclass(frozen=True)
class _RuleLimits:
    step_size: int
    min_replicas: int | None
    max_replicas: int | None


@dataclass(frozen=True)
class _DesiredReplicasCase:
    current_replicas: int
    load: _Load
    rules: list[_RuleLimits]
    expected_replicas: int | None


class TestCalculateDesiredReplicasForDeployment:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                ResourcePresetRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                ProjectRow,
                VFolderRow,
                EndpointRow,
                ReplicaGroupRow,
                DeploymentPolicyRow,
                PrometheusQueryPresetCategoryRow,
                PrometheusQueryPresetRow,
                EndpointAutoScalingRuleRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def suffix(self) -> str:
        return uuid.uuid4().hex[:8]

    @pytest.fixture
    async def domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
    ) -> DomainFixtureData:
        domain_id = DomainID(uuid.uuid4())
        name = f"d-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(DomainRow(id=domain_id, name=name, total_resource_slots=ResourceSlot()))
        return DomainFixtureData(domain_name=DomainName(name), domain_id=domain_id)

    @pytest.fixture
    async def resource_group(self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str) -> str:
        name = f"sg-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ResourceGroupRow(
                    name=name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
        return name

    @pytest.fixture
    async def user_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str
    ) -> str:
        name = f"up-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
        return name

    @pytest.fixture
    async def project_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str
    ) -> str:
        name = f"pp-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
        return name

    @pytest.fixture
    async def user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
        domain: DomainFixtureData,
        user_resource_policy: str,
    ) -> uuid.UUID:
        user_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_id,
                    email=f"{suffix}@test.com",
                    username=f"u-{suffix}",
                    password=PasswordInfo(
                        password="x",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_name=domain.domain_name,
                    resource_policy=user_resource_policy,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_id=domain.domain_id,
                )
            )
        return user_id

    @pytest.fixture
    async def project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
        domain: DomainFixtureData,
        project_resource_policy: str,
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"g-{suffix}",
                    domain_name=domain.domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_resource_policy,
                )
            )
        return project_id

    @pytest.fixture
    async def deployment(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
        domain: DomainFixtureData,
        resource_group: str,
        user: uuid.UUID,
        project: uuid.UUID,
        case: _DesiredReplicasCase,
    ) -> DeploymentInfo:
        async with db_with_cleanup.begin_session() as db_sess:
            row = EndpointRow(
                name=f"ep-{suffix}",
                created_user=user,
                session_owner=user,
                domain=domain.domain_name,
                project=project,
                resource_group=resource_group,
                lifecycle_stage=EndpointLifecycle.CREATED,
                replicas=case.current_replicas,
                desired_replicas=case.current_replicas,
            )
            db_sess.add(row)
            await db_sess.flush()
            await db_sess.refresh(row)
            return row.to_bare_deployment_info()

    @pytest.fixture
    async def rules(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        deployment: DeploymentInfo,
        case: _DesiredReplicasCase,
    ) -> list[AutoScalingRule]:
        rows = [
            EndpointAutoScalingRuleRow(
                id=AutoScalingRuleID(uuid.uuid4()),
                endpoint=deployment.id,
                metric_source=AutoScalingMetricSource.PROMETHEUS,
                metric_name="requests",
                min_threshold=_SCALE_DOWN_THRESHOLD,
                max_threshold=_SCALE_UP_THRESHOLD,
                step_size=limits.step_size,
                cooldown_seconds=0,
                min_replicas=limits.min_replicas,
                max_replicas=limits.max_replicas,
                prometheus_query_preset_id=None,
                created_at=datetime.now(UTC),
                last_triggered_at=None,
            )
            for limits in case.rules
        ]
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add_all(rows)
            await db_sess.flush()
            return [row.to_autoscaling_rule() for row in rows]

    @pytest.fixture
    def metrics_data(
        self,
        rules: list[AutoScalingRule],
        case: _DesiredReplicasCase,
    ) -> AutoScalingMetricsData:
        return AutoScalingMetricsData(
            prometheus_metrics={rule.id: case.load.value for rule in rules},
        )

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        return DeploymentRepository(
            db=db_with_cleanup,
            reconcile_ops_provider=ReconcileOpsProvider(db_with_cleanup),
            storage_manager=MagicMock(),
            valkey_stat=MagicMock(),
            valkey_live=MagicMock(),
            valkey_schedule=MagicMock(),
            permission_check=MagicMock(),
        )

    @pytest.mark.parametrize(
        "case",
        [
            _DesiredReplicasCase(
                current_replicas=1,
                load=_Load.LOW,
                rules=[_RuleLimits(step_size=2, min_replicas=2, max_replicas=3)],
                expected_replicas=2,
            ),
            _DesiredReplicasCase(
                current_replicas=2,
                load=_Load.HIGH,
                rules=[_RuleLimits(step_size=2, min_replicas=None, max_replicas=3)],
                expected_replicas=3,
            ),
            _DesiredReplicasCase(
                current_replicas=3,
                load=_Load.LOW,
                rules=[_RuleLimits(step_size=5, min_replicas=1, max_replicas=None)],
                expected_replicas=1,
            ),
            _DesiredReplicasCase(
                current_replicas=3,
                load=_Load.HIGH,
                rules=[_RuleLimits(step_size=1, min_replicas=None, max_replicas=3)],
                expected_replicas=None,
            ),
            _DesiredReplicasCase(
                current_replicas=1,
                load=_Load.LOW,
                rules=[_RuleLimits(step_size=1, min_replicas=1, max_replicas=None)],
                expected_replicas=None,
            ),
            _DesiredReplicasCase(
                current_replicas=1,
                load=_Load.HIGH,
                rules=[_RuleLimits(step_size=1, min_replicas=1, max_replicas=3)],
                expected_replicas=2,
            ),
            _DesiredReplicasCase(
                current_replicas=3,
                load=_Load.HIGH,
                rules=[
                    _RuleLimits(step_size=1, min_replicas=None, max_replicas=3),
                    _RuleLimits(step_size=1, min_replicas=None, max_replicas=5),
                ],
                expected_replicas=4,
            ),
        ],
        ids=lambda case: (
            f"{case.load.name.lower()}-{len(case.rules)}rule"
            f"-{case.current_replicas}-to-{case.expected_replicas}"
        ),
    )
    async def test_desired_replicas_clamped_to_rule_limits(
        self,
        deployment_repository: DeploymentRepository,
        deployment: DeploymentInfo,
        rules: list[AutoScalingRule],
        metrics_data: AutoScalingMetricsData,
        case: _DesiredReplicasCase,
    ) -> None:
        result = await deployment_repository.calculate_desired_replicas_for_deployment(
            deployment, rules, metrics_data
        )

        assert result == case.expected_replicas

    @pytest.mark.parametrize(
        "case",
        [
            _DesiredReplicasCase(
                current_replicas=3,
                load=_Load.HIGH,
                rules=[_RuleLimits(step_size=1, min_replicas=None, max_replicas=3)],
                expected_replicas=None,
            ),
            _DesiredReplicasCase(
                current_replicas=1,
                load=_Load.LOW,
                rules=[_RuleLimits(step_size=1, min_replicas=1, max_replicas=None)],
                expected_replicas=None,
            ),
        ],
        ids=lambda case: f"{case.load.name.lower()}-at-{case.current_replicas}",
    )
    async def test_rule_at_limit_is_not_triggered(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        deployment_repository: DeploymentRepository,
        deployment: DeploymentInfo,
        rules: list[AutoScalingRule],
        metrics_data: AutoScalingMetricsData,
        case: _DesiredReplicasCase,
    ) -> None:
        await deployment_repository.calculate_desired_replicas_for_deployment(
            deployment, rules, metrics_data
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            last_triggered = (
                await db_sess.scalars(
                    sa.select(EndpointAutoScalingRuleRow.last_triggered_at).where(
                        EndpointAutoScalingRuleRow.endpoint == deployment.id
                    )
                )
            ).all()
        assert list(last_triggered) == [None]
