"""Tests for StrategyResultApplier."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    RuntimeVariant,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import (
    DeploymentSubStep,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
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
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.strategy.applier import StrategyResultApplier
from ai.backend.manager.sokovan.deployment.strategy.types import (
    RouteChanges,
    StrategyEvaluationSummary,
)
from ai.backend.testutils.db import with_tables


def _create_test_password_info(password: str = "test_password") -> PasswordInfo:
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestStrategyResultApplier:
    """Tests for StrategyResultApplier.apply() with real database."""

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
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                SessionRow,
                EndpointRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
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
            await db_sess.commit()
        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
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
            await db_sess.commit()
        return sgroup_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"testuser-{user_uuid.hex[:8]}",
                    email=f"test-{user_uuid.hex[:8]}@example.com",
                    password=_create_test_password_info("test_password"),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=test_domain_name,
                    role=UserRole.USER,
                    resource_policy=policy_name,
                )
            )
            await db_sess.commit()
        return user_uuid

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> uuid.UUID:
        group_id = uuid.uuid4()
        policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"
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
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=test_domain_name,
                    resource_policy=policy_name,
                )
            )
            await db_sess.commit()
        return group_id

    @pytest.fixture
    async def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=MagicMock(),
            valkey_stat=MagicMock(),
            valkey_live=MagicMock(),
            valkey_schedule=MagicMock(),
        )

    @pytest.fixture
    def applier(self, deployment_repository: DeploymentRepository) -> StrategyResultApplier:
        return StrategyResultApplier(deployment_repo=deployment_repository)

    async def _create_endpoint(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain: str,
        scaling_group: str,
        user_uuid: uuid.UUID,
        group_id: uuid.UUID,
        deploying_revision: uuid.UUID | None = None,
        current_revision: uuid.UUID | None = None,
        sub_step: DeploymentSubStep | None = None,
    ) -> uuid.UUID:
        endpoint_id = uuid.uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                    created_user=user_uuid,
                    session_owner=user_uuid,
                    domain=domain,
                    project=group_id,
                    resource_group=scaling_group,
                    model=None,
                    desired_replicas=1,
                    image=uuid.uuid4(),
                    runtime_variant=RuntimeVariant.VLLM,
                    url="http://test.example.com",
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.DEPLOYING,
                    resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
                    deploying_revision=deploying_revision,
                    current_revision=current_revision,
                    sub_step=sub_step,
                )
            )
            await db_sess.commit()
        return endpoint_id

    async def _create_route(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        endpoint_id: uuid.UUID,
        user_uuid: uuid.UUID,
        domain: str,
        group_id: uuid.UUID,
        traffic_ratio: float = 1.0,
    ) -> uuid.UUID:
        route_id = uuid.uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                RoutingRow(
                    id=route_id,
                    endpoint=endpoint_id,
                    session=None,
                    session_owner=user_uuid,
                    domain=domain,
                    project=group_id,
                    traffic_ratio=traffic_ratio,
                )
            )
            await db_sess.commit()
        return route_id

    async def test_completed_assignment_swaps_revision(
        self,
        applier: StrategyResultApplier,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> None:
        """COMPLETED assignment should swap deploying_revision to current_revision."""
        deploying_rev = uuid.uuid4()
        old_current_rev = uuid.uuid4()
        endpoint_id = await self._create_endpoint(
            db_with_cleanup,
            domain=test_domain_name,
            scaling_group=test_scaling_group_name,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
            deploying_revision=deploying_rev,
            current_revision=old_current_rev,
        )

        summary = StrategyEvaluationSummary(
            assignments={endpoint_id: DeploymentSubStep.COMPLETED},
        )
        result = await applier.apply(summary)

        assert result.completed_ids == {endpoint_id}
        async with db_with_cleanup.begin_session() as db_sess:
            row = await db_sess.get(EndpointRow, endpoint_id)
            assert row is not None
            assert row.current_revision == deploying_rev
            assert row.deploying_revision is None

    async def test_rolled_back_assignment_clears_deploying_revision(
        self,
        applier: StrategyResultApplier,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> None:
        """ROLLED_BACK assignment should clear deploying_revision without touching current_revision."""
        deploying_rev = uuid.uuid4()
        current_rev = uuid.uuid4()
        endpoint_id = await self._create_endpoint(
            db_with_cleanup,
            domain=test_domain_name,
            scaling_group=test_scaling_group_name,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
            deploying_revision=deploying_rev,
            current_revision=current_rev,
        )

        summary = StrategyEvaluationSummary(
            assignments={endpoint_id: DeploymentSubStep.ROLLED_BACK},
        )
        result = await applier.apply(summary)

        assert result.rolled_back_ids == {endpoint_id}
        async with db_with_cleanup.begin_session() as db_sess:
            row = await db_sess.get(EndpointRow, endpoint_id)
            assert row is not None
            assert row.current_revision == current_rev
            assert row.deploying_revision is None

    async def test_sub_step_assignment_updates_db_column(
        self,
        applier: StrategyResultApplier,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> None:
        """Assignments should update the sub_step column in the database."""
        endpoint_id = await self._create_endpoint(
            db_with_cleanup,
            domain=test_domain_name,
            scaling_group=test_scaling_group_name,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
            sub_step=DeploymentSubStep.PROVISIONING,
        )

        summary = StrategyEvaluationSummary(
            assignments={endpoint_id: DeploymentSubStep.PROGRESSING},
        )
        await applier.apply(summary)

        async with db_with_cleanup.begin_session() as db_sess:
            row = await db_sess.get(EndpointRow, endpoint_id)
            assert row is not None
            assert row.sub_step == DeploymentSubStep.PROGRESSING

    async def test_drain_routes_sets_terminating_status(
        self,
        applier: StrategyResultApplier,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> None:
        """Draining routes should set status=TERMINATING, traffic_ratio=0, traffic_status=INACTIVE."""
        endpoint_id = await self._create_endpoint(
            db_with_cleanup,
            domain=test_domain_name,
            scaling_group=test_scaling_group_name,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
        )
        route_id = await self._create_route(
            db_with_cleanup,
            endpoint_id=endpoint_id,
            user_uuid=test_user_uuid,
            domain=test_domain_name,
            group_id=test_group_id,
        )

        summary = StrategyEvaluationSummary(
            assignments={endpoint_id: DeploymentSubStep.PROGRESSING},
            route_changes=RouteChanges(drain_route_ids=[route_id]),
        )
        result = await applier.apply(summary)

        assert result.routes_drained == 1
        async with db_with_cleanup.begin_session() as db_sess:
            row = await db_sess.get(RoutingRow, route_id)
            assert row is not None
            assert row.status == RouteStatus.TERMINATING
            assert row.traffic_ratio == 0.0
            assert row.traffic_status == RouteTrafficStatus.INACTIVE

    async def test_rollout_creates_new_routes(
        self,
        applier: StrategyResultApplier,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> None:
        """Rollout specs should create new route rows in the database."""
        endpoint_id = await self._create_endpoint(
            db_with_cleanup,
            domain=test_domain_name,
            scaling_group=test_scaling_group_name,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
        )
        rollout_spec: Creator[RoutingRow] = Creator(
            spec=RouteCreatorSpec(
                endpoint_id=endpoint_id,
                session_owner_id=test_user_uuid,
                domain=test_domain_name,
                project_id=test_group_id,
                traffic_ratio=1.0,
            ),
        )

        summary = StrategyEvaluationSummary(
            assignments={endpoint_id: DeploymentSubStep.PROVISIONING},
            route_changes=RouteChanges(rollout_specs=[rollout_spec]),
        )
        result = await applier.apply(summary)

        assert result.routes_created == 1
        async with db_with_cleanup.begin_session() as db_sess:
            routes = (
                (
                    await db_sess.execute(
                        sa.select(RoutingRow).where(RoutingRow.endpoint == endpoint_id)
                    )
                )
                .scalars()
                .all()
            )
            assert len(routes) == 1
            assert routes[0].traffic_ratio == 1.0

    async def test_mixed_assignments_handles_all_categories(
        self,
        applier: StrategyResultApplier,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> None:
        """Mixed PROVISIONING/COMPLETED/ROLLED_BACK assignments are classified correctly."""
        deploying_rev = uuid.uuid4()
        provisioning_id = await self._create_endpoint(
            db_with_cleanup,
            domain=test_domain_name,
            scaling_group=test_scaling_group_name,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
        )
        completed_id = await self._create_endpoint(
            db_with_cleanup,
            domain=test_domain_name,
            scaling_group=test_scaling_group_name,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
            deploying_revision=deploying_rev,
        )
        rolled_back_id = await self._create_endpoint(
            db_with_cleanup,
            domain=test_domain_name,
            scaling_group=test_scaling_group_name,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
            deploying_revision=uuid.uuid4(),
            current_revision=uuid.uuid4(),
        )

        summary = StrategyEvaluationSummary(
            assignments={
                provisioning_id: DeploymentSubStep.PROVISIONING,
                completed_id: DeploymentSubStep.COMPLETED,
                rolled_back_id: DeploymentSubStep.ROLLED_BACK,
            },
        )
        result = await applier.apply(summary)

        assert result.completed_ids == {completed_id}
        assert result.rolled_back_ids == {rolled_back_id}

        async with db_with_cleanup.begin_session() as db_sess:
            provisioning_row = await db_sess.get(EndpointRow, provisioning_id)
            assert provisioning_row is not None
            assert provisioning_row.sub_step == DeploymentSubStep.PROVISIONING

            completed_row = await db_sess.get(EndpointRow, completed_id)
            assert completed_row is not None
            assert completed_row.current_revision == deploying_rev
            assert completed_row.deploying_revision is None

            rolled_back_row = await db_sess.get(EndpointRow, rolled_back_id)
            assert rolled_back_row is not None
            assert rolled_back_row.deploying_revision is None
