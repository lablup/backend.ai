"""Regression integration test for the OBSERVE_HEALTH route lifecycle cycle.

BA-6093: ``RouteCoordinator._process_observer`` previously fetched only
``RouteStatus.RUNNING`` rows, so ``PROVISIONING + sub_status=WARMING_UP``
routes never received a health probe — ``WarmingUpRouteHandler`` then
timed them out into ``TERMINATING``. This test inserts one route per
lifecycle bucket, runs one observer cycle, and asserts which rows the
observer actually receives.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
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
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.deployment.route.handlers.observer import (
    RouteObservationResult,
    RouteObserver,
)
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.testutils.db import with_tables

# Tables `RoutingRow` transitively requires for its FK constraints to be
# created. We do NOT populate most of these — only the rows the routes
# themselves need (one domain, scaling group, two policies, one user,
# one project, one endpoint).
_REQUIRED_TABLES = [
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
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    EndpointRow,
    ResourcePresetRow,
    ReplicaGroupRow,
    RoutingRow,
]


@dataclass(frozen=True)
class _Environment:
    """The pre-existing world the routes live in."""

    domain: str
    user_id: UUID
    project_id: UUID
    endpoint_id: DeploymentID
    revision_id: UUID


@dataclass(frozen=True)
class _Routes:
    """IDs of the routes inserted by the fixture, one per lifecycle bucket."""

    running_id: ReplicaID
    warming_up_id: ReplicaID
    starting_id: ReplicaID
    terminating_id: ReplicaID


class TestObserverCycleRouteScope:
    """Regression test for BA-6093.

    Runs the OBSERVE_HEALTH cycle against a real database and asserts
    which routes the observer actually receives.
    """

    # ------------------------------------------------------------------
    # Schema + per-row fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, _REQUIRED_TABLES):
            yield database_connection

    @pytest.fixture
    def suffix(self) -> str:
        return uuid.uuid4().hex[:8]

    @pytest.fixture
    async def domain(self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str) -> str:
        name = f"d-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(DomainRow(name=name, total_resource_slots=ResourceSlot()))
        return name

    @pytest.fixture
    async def scaling_group(self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str) -> str:
        name = f"sg-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
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
        domain: str,
        user_resource_policy: str,
    ) -> UUID:
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
                    domain_name=domain,
                    resource_policy=user_resource_policy,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
        return user_id

    @pytest.fixture
    async def project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
        domain: str,
        project_resource_policy: str,
    ) -> UUID:
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=f"g-{suffix}",
                    domain_name=domain,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_resource_policy,
                )
            )
        return project_id

    @pytest.fixture
    def revision_id(self) -> UUID:
        return uuid.uuid4()

    @pytest.fixture
    async def endpoint(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
        domain: str,
        scaling_group: str,
        user: UUID,
        project: UUID,
        revision_id: UUID,
    ) -> DeploymentID:
        endpoint_id = DeploymentID(uuid.uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"ep-{suffix}",
                    created_user=user,
                    session_owner=user,
                    domain=domain,
                    project=project,
                    resource_group=scaling_group,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                    replicas=4,
                )
            )
        return endpoint_id

    @pytest.fixture
    def environment(
        self,
        domain: str,
        user: UUID,
        project: UUID,
        endpoint: DeploymentID,
        revision_id: UUID,
    ) -> _Environment:
        return _Environment(
            domain=domain,
            user_id=user,
            project_id=project,
            endpoint_id=endpoint,
            revision_id=revision_id,
        )

    @pytest.fixture
    async def routes(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        environment: _Environment,
    ) -> _Routes:
        """Insert four routes into the environment's endpoint, one per
        lifecycle bucket:

        - ``RUNNING`` (any health status): observer's existing scope.
        - ``PROVISIONING + WARMING_UP``: the regression target.
        - ``PROVISIONING + STARTING``: still waiting for replica host/port;
          must NOT be observed.
        - ``TERMINATING``: shutting down; must NOT be observed.
        """
        running_id = ReplicaID(uuid.uuid4())
        warming_up_id = ReplicaID(uuid.uuid4())
        starting_id = ReplicaID(uuid.uuid4())
        terminating_id = ReplicaID(uuid.uuid4())

        def _route(
            route_id: ReplicaID,
            status: RouteStatus,
            sub_status: RouteSubStatus | None,
            health_status: RouteHealthStatus = RouteHealthStatus.NOT_CHECKED,
        ) -> RoutingRow:
            return RoutingRow(
                id=route_id,
                endpoint=environment.endpoint_id,
                session=None,
                session_owner=environment.user_id,
                domain=environment.domain,
                project=environment.project_id,
                status=status,
                sub_status=sub_status,
                health_status=health_status,
                traffic_status=RouteTrafficStatus.INACTIVE,
                traffic_ratio=1.0,
                revision=environment.revision_id,
            )

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add_all([
                _route(running_id, RouteStatus.RUNNING, None, RouteHealthStatus.HEALTHY),
                _route(warming_up_id, RouteStatus.PROVISIONING, RouteSubStatus.WARMING_UP),
                _route(starting_id, RouteStatus.PROVISIONING, RouteSubStatus.STARTING),
                _route(terminating_id, RouteStatus.TERMINATING, None),
            ])

        return _Routes(
            running_id=running_id,
            warming_up_id=warming_up_id,
            starting_id=starting_id,
            terminating_id=terminating_id,
        )

    # ------------------------------------------------------------------
    # Coordinator + observer wiring
    # ------------------------------------------------------------------

    @pytest.fixture
    def mock_observer(self) -> MagicMock:
        observer = MagicMock(spec=RouteObserver)
        observer.name = MagicMock(return_value="route-health-observer")
        observer.observe = AsyncMock(return_value=RouteObservationResult(observed_count=0))
        return observer

    @pytest.fixture
    def coordinator(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_observer: MagicMock,
    ) -> RouteCoordinator:
        repository = DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=AsyncMock(),
            valkey_stat=AsyncMock(),
            valkey_live=AsyncMock(),
            valkey_schedule=AsyncMock(),
        )
        coord = RouteCoordinator(
            valkey_schedule=AsyncMock(),
            deployment_repository=repository,
            event_producer=AsyncMock(),
            lock_factory=MagicMock(),
            config_provider=MagicMock(),
            scheduling_controller=MagicMock(),
            client_pool=MagicMock(),
            service_discovery=MagicMock(),
            appproxy_client_pool=MagicMock(),
        )
        coord._route_observers = {RouteLifecycleType.OBSERVE_HEALTH: mock_observer}
        return coord

    # ------------------------------------------------------------------
    # Test
    # ------------------------------------------------------------------

    async def test_observer_scope_covers_running_and_warming_up_only(
        self,
        coordinator: RouteCoordinator,
        environment: _Environment,
        routes: _Routes,
        mock_observer: MagicMock,
    ) -> None:
        """The OBSERVE_HEALTH cycle must hand both ``RUNNING`` and
        ``PROVISIONING+WARMING_UP`` routes to the observer, but exclude
        routes in other lifecycle states.
        """
        await coordinator.process_route_lifecycle(RouteLifecycleType.OBSERVE_HEALTH)

        mock_observer.observe.assert_awaited_once()
        (observed,) = mock_observer.observe.await_args.args
        observed_ids = {r.route_id for r in observed}

        assert routes.running_id in observed_ids, "RUNNING route must be observed"
        assert routes.warming_up_id in observed_ids, (
            "PROVISIONING+WARMING_UP route must be observed (BA-6093)"
        )
        assert routes.starting_id not in observed_ids, (
            "PROVISIONING+STARTING route must NOT be observed"
        )
        assert routes.terminating_id not in observed_ids, "TERMINATING route must NOT be observed"
