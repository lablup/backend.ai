from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
    UtilizationSpec,
)
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.idle_checker.types import ScopeType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class ScopeFixture:
    domain_name: str
    domain_id: DomainID
    project_id: uuid.UUID
    scaling_group_name: str
    scaling_group_id: ResourceGroupID


@dataclass(frozen=True)
class SeededIdleCheckData:
    resource_group_session_id: SessionId
    project_session_id: SessionId
    domain_session_id: SessionId
    inference_session_id: SessionId
    resource_group_checker_id: IdleCheckerID
    project_checker_id: IdleCheckerID
    domain_checker_id: IdleCheckerID


@dataclass(frozen=True)
class PerTypeCheckerData:
    interactive_session_id: SessionId
    batch_session_id: SessionId
    interactive_checker_id: IdleCheckerID
    batch_checker_id: IdleCheckerID


class TestFetchIdleCheckBatch:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ProjectResourcePolicyRow,
                DomainRow,
                GroupRow,
                ScalingGroupRow,
                SessionRow,
                IdleCheckerRow,
                IdleCheckerBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
        return IdleCheckerRepository(DBOpsProvider(database))

    @pytest.fixture
    async def running_session_without_bindings(
        self,
        database: ExtendedAsyncSAEngine,
        request: pytest.FixtureRequest,
    ) -> SessionId:
        prefix = str(request.param)
        scope = ScopeFixture(
            domain_name=f"{prefix}-domain",
            domain_id=DomainID(uuid.uuid4()),
            project_id=uuid.uuid4(),
            scaling_group_name=f"{prefix}-sgroup",
            scaling_group_id=ResourceGroupID(uuid.uuid4()),
        )
        session_id = SessionId(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"{scope.domain_name}-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=1024,
                    max_network_count=10,
                )
            )
            db_sess.add(
                DomainRow(
                    id=scope.domain_id,
                    name=scope.domain_name,
                    description=None,
                    is_active=True,
                )
            )
            db_sess.add(
                GroupRow(
                    id=scope.project_id,
                    name=f"{scope.domain_name}-project",
                    description=None,
                    is_active=True,
                    domain_name=scope.domain_name,
                    resource_policy=f"{scope.domain_name}-policy",
                )
            )
            db_sess.add(
                ScalingGroupRow(
                    id=scope.scaling_group_id,
                    name=scope.scaling_group_name,
                    description=None,
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    use_host_network=False,
                )
            )
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=str(session_id)[:32],
                    name=f"session-{session_id}",
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_name=scope.domain_name,
                    domain_id=scope.domain_id,
                    resource_group_id=scope.scaling_group_id,
                    group_id=scope.project_id,
                    user_uuid=uuid.uuid4(),
                    access_key=None,
                    tag=None,
                    status=SessionStatus.RUNNING,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    result=SessionResult.UNDEFINED,
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                    terminated_at=None,
                    starts_at=datetime(2026, 1, 1, tzinfo=UTC),
                    startup_command=None,
                    callback_url=None,
                    occupying_slots=ResourceSlot({"cpu": "1"}),
                    requested_slots=ResourceSlot({"cpu": "1"}),
                    vfolder_mounts=[],
                    environ=None,
                    bootstrap_script=None,
                    use_host_network=False,
                    scaling_group_name=scope.scaling_group_name,
                )
            )
        return session_id

    @pytest.fixture
    async def running_session_with_disabled_binding(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> SessionId:
        scope = ScopeFixture(
            domain_name="disabled-binding-domain",
            domain_id=DomainID(uuid.uuid4()),
            project_id=uuid.uuid4(),
            scaling_group_name="disabled-binding-sgroup",
            scaling_group_id=ResourceGroupID(uuid.uuid4()),
        )
        session_id = SessionId(uuid.uuid4())
        checker_id = IdleCheckerID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"{scope.domain_name}-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=1024,
                    max_network_count=10,
                )
            )
            db_sess.add(
                DomainRow(
                    id=scope.domain_id,
                    name=scope.domain_name,
                    description=None,
                    is_active=True,
                )
            )
            db_sess.add(
                GroupRow(
                    id=scope.project_id,
                    name=f"{scope.domain_name}-project",
                    description=None,
                    is_active=True,
                    domain_name=scope.domain_name,
                    resource_policy=f"{scope.domain_name}-policy",
                )
            )
            db_sess.add(
                ScalingGroupRow(
                    id=scope.scaling_group_id,
                    name=scope.scaling_group_name,
                    description=None,
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    use_host_network=False,
                )
            )
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=str(session_id)[:32],
                    name=f"session-{session_id}",
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_name=scope.domain_name,
                    domain_id=scope.domain_id,
                    resource_group_id=scope.scaling_group_id,
                    group_id=scope.project_id,
                    user_uuid=uuid.uuid4(),
                    access_key=None,
                    tag=None,
                    status=SessionStatus.RUNNING,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    result=SessionResult.UNDEFINED,
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                    terminated_at=None,
                    starts_at=datetime(2026, 1, 1, tzinfo=UTC),
                    startup_command=None,
                    callback_url=None,
                    occupying_slots=ResourceSlot({"cpu": "1"}),
                    requested_slots=ResourceSlot({"cpu": "1"}),
                    vfolder_mounts=[],
                    environ=None,
                    bootstrap_script=None,
                    use_host_network=False,
                    scaling_group_name=scope.scaling_group_name,
                )
            )
            db_sess.add(
                IdleCheckerRow(
                    id=checker_id,
                    name=f"checker-{checker_id}",
                    description=None,
                    checker_type=CheckerType.SESSION_LIFETIME,
                    spec=IdleCheckerSpec(
                        type=CheckerType.SESSION_LIFETIME,
                        session_lifetime=SessionLifetimeSpec(),
                    ),
                )
            )
            await db_sess.flush()
            db_sess.add(
                IdleCheckerBindingRow(
                    scope_type=ScopeType.DOMAIN.value,
                    scope_id=scope.domain_id,
                    idle_checker_id=checker_id,
                    enabled=False,
                )
            )
        return session_id

    @pytest.fixture
    async def seeded_idle_check_data(
        self,
        database: ExtendedAsyncSAEngine,
        request: pytest.FixtureRequest,
    ) -> SeededIdleCheckData:
        resource_group_prefix, project_prefix, domain_prefix = request.param
        resource_group_scope = ScopeFixture(
            domain_name=f"{resource_group_prefix}-domain",
            domain_id=DomainID(uuid.uuid4()),
            project_id=uuid.uuid4(),
            scaling_group_name=f"{resource_group_prefix}-sgroup",
            scaling_group_id=ResourceGroupID(uuid.uuid4()),
        )
        project_scope = ScopeFixture(
            domain_name=f"{project_prefix}-domain",
            domain_id=DomainID(uuid.uuid4()),
            project_id=uuid.uuid4(),
            scaling_group_name=f"{project_prefix}-sgroup",
            scaling_group_id=ResourceGroupID(uuid.uuid4()),
        )
        domain_scope = ScopeFixture(
            domain_name=f"{domain_prefix}-domain",
            domain_id=DomainID(uuid.uuid4()),
            project_id=uuid.uuid4(),
            scaling_group_name=f"{domain_prefix}-sgroup",
            scaling_group_id=ResourceGroupID(uuid.uuid4()),
        )
        scopes = (resource_group_scope, project_scope, domain_scope)
        resource_group_session_id = SessionId(uuid.uuid4())
        project_session_id = SessionId(uuid.uuid4())
        domain_session_id = SessionId(uuid.uuid4())
        inference_session_id = SessionId(uuid.uuid4())
        session_specs = (
            (
                resource_group_scope,
                resource_group_session_id,
                datetime(2026, 1, 1, tzinfo=UTC),
                SessionTypes.INTERACTIVE,
            ),
            (
                project_scope,
                project_session_id,
                datetime(2026, 1, 2, tzinfo=UTC),
                SessionTypes.INTERACTIVE,
            ),
            (
                domain_scope,
                domain_session_id,
                datetime(2026, 1, 3, tzinfo=UTC),
                SessionTypes.INTERACTIVE,
            ),
            (
                resource_group_scope,
                inference_session_id,
                datetime(2026, 1, 4, tzinfo=UTC),
                SessionTypes.INFERENCE,
            ),
        )
        resource_group_checker_id = IdleCheckerID(uuid.uuid4())
        project_checker_id = IdleCheckerID(uuid.uuid4())
        domain_checker_id = IdleCheckerID(uuid.uuid4())
        binding_specs = (
            (
                resource_group_checker_id,
                CheckerType.SESSION_LIFETIME,
                IdleCheckerSpec(
                    type=CheckerType.SESSION_LIFETIME,
                    session_lifetime=SessionLifetimeSpec(),
                ),
                ScopeType.RESOURCE_GROUP,
                resource_group_scope.scaling_group_id,
            ),
            (
                project_checker_id,
                CheckerType.NETWORK_TIMEOUT,
                IdleCheckerSpec(
                    type=CheckerType.NETWORK_TIMEOUT,
                    network=NetworkTimeoutSpec(),
                ),
                ScopeType.PROJECT,
                project_scope.project_id,
            ),
            (
                domain_checker_id,
                CheckerType.UTILIZATION,
                IdleCheckerSpec(
                    type=CheckerType.UTILIZATION,
                    utilization=UtilizationSpec(),
                ),
                ScopeType.DOMAIN,
                domain_scope.domain_id,
            ),
        )
        async with database.begin_session() as db_sess:
            for scope in scopes:
                db_sess.add(
                    ProjectResourcePolicyRow(
                        name=f"{scope.domain_name}-policy",
                        max_vfolder_count=10,
                        max_quota_scope_size=1024,
                        max_network_count=10,
                    )
                )
                db_sess.add(
                    DomainRow(
                        id=scope.domain_id,
                        name=scope.domain_name,
                        description=None,
                        is_active=True,
                    )
                )
                db_sess.add(
                    GroupRow(
                        id=scope.project_id,
                        name=f"{scope.domain_name}-project",
                        description=None,
                        is_active=True,
                        domain_name=scope.domain_name,
                        resource_policy=f"{scope.domain_name}-policy",
                    )
                )
                db_sess.add(
                    ScalingGroupRow(
                        id=scope.scaling_group_id,
                        name=scope.scaling_group_name,
                        description=None,
                        is_active=True,
                        is_public=True,
                        driver="static",
                        driver_opts={},
                        scheduler="fifo",
                        use_host_network=False,
                    )
                )
            for scope, session_id, created_at, session_type in session_specs:
                db_sess.add(
                    SessionRow(
                        id=session_id,
                        creation_id=str(session_id)[:32],
                        name=f"session-{session_id}",
                        session_type=session_type,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        cluster_size=1,
                        domain_name=scope.domain_name,
                        domain_id=scope.domain_id,
                        resource_group_id=scope.scaling_group_id,
                        group_id=scope.project_id,
                        user_uuid=uuid.uuid4(),
                        access_key=None,
                        tag=None,
                        status=SessionStatus.RUNNING,
                        status_info=None,
                        status_data=None,
                        status_history={},
                        result=SessionResult.UNDEFINED,
                        created_at=created_at,
                        terminated_at=None,
                        starts_at=created_at,
                        startup_command=None,
                        callback_url=None,
                        occupying_slots=ResourceSlot({"cpu": "1"}),
                        requested_slots=ResourceSlot({"cpu": "1"}),
                        vfolder_mounts=[],
                        environ=None,
                        bootstrap_script=None,
                        use_host_network=False,
                        scaling_group_name=scope.scaling_group_name,
                    )
                )
            for checker_id, checker_type, spec, _, _ in binding_specs:
                db_sess.add(
                    IdleCheckerRow(
                        id=checker_id,
                        name=f"{checker_type.value}-{checker_id}",
                        description=None,
                        checker_type=checker_type,
                        spec=spec,
                    )
                )
            await db_sess.flush()
            for checker_id, _, _, scope_type, scope_id in binding_specs:
                db_sess.add(
                    IdleCheckerBindingRow(
                        scope_type=scope_type.value,
                        scope_id=scope_id,
                        idle_checker_id=checker_id,
                        enabled=True,
                    )
                )

        return SeededIdleCheckData(
            resource_group_session_id=resource_group_session_id,
            project_session_id=project_session_id,
            domain_session_id=domain_session_id,
            inference_session_id=inference_session_id,
            resource_group_checker_id=resource_group_checker_id,
            project_checker_id=project_checker_id,
            domain_checker_id=domain_checker_id,
        )

    @pytest.mark.parametrize("running_session_without_bindings", ["empty"], indirect=True)
    @pytest.mark.usefixtures("running_session_without_bindings")
    async def test_returns_empty_batch_without_enabled_bindings(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        batch = await repository.fetch_idle_check_batch([SessionStatus.RUNNING])

        assert batch.targets == ()

    async def test_ignores_disabled_bindings(
        self,
        repository: IdleCheckerRepository,
        running_session_with_disabled_binding: SessionId,
    ) -> None:
        batch = await repository.fetch_idle_check_batch([SessionStatus.RUNNING])
        target_session_ids = {target.session.session_id for target in batch.targets}

        assert batch.targets == ()
        assert running_session_with_disabled_binding not in target_session_ids

    @pytest.mark.parametrize(
        "seeded_idle_check_data",
        [("resource-group", "project", "domain")],
        indirect=True,
    )
    async def test_fetches_resource_group_scope_bound_checker(
        self,
        repository: IdleCheckerRepository,
        seeded_idle_check_data: SeededIdleCheckData,
    ) -> None:
        batch = await repository.fetch_idle_check_batch([SessionStatus.RUNNING])
        targets_by_session_id = {target.session.session_id: target for target in batch.targets}
        resource_group_target = targets_by_session_id[
            seeded_idle_check_data.resource_group_session_id
        ]
        checkers = resource_group_target.checkers

        assert len(checkers) == 1
        assert checkers[0].checker.checker_id == seeded_idle_check_data.resource_group_checker_id
        assert checkers[0].scope.scope_type is ScopeType.RESOURCE_GROUP

    @pytest.mark.parametrize(
        "seeded_idle_check_data",
        [("resource-group", "project", "domain")],
        indirect=True,
    )
    async def test_fetches_project_scope_bound_checker(
        self,
        repository: IdleCheckerRepository,
        seeded_idle_check_data: SeededIdleCheckData,
    ) -> None:
        batch = await repository.fetch_idle_check_batch([SessionStatus.RUNNING])
        targets_by_session_id = {target.session.session_id: target for target in batch.targets}
        project_target = targets_by_session_id[seeded_idle_check_data.project_session_id]
        checkers = project_target.checkers

        assert len(checkers) == 1
        assert checkers[0].checker.checker_id == seeded_idle_check_data.project_checker_id
        assert checkers[0].scope.scope_type is ScopeType.PROJECT

    @pytest.mark.parametrize(
        "seeded_idle_check_data",
        [("resource-group", "project", "domain")],
        indirect=True,
    )
    async def test_fetches_domain_scope_bound_checker(
        self,
        repository: IdleCheckerRepository,
        seeded_idle_check_data: SeededIdleCheckData,
    ) -> None:
        batch = await repository.fetch_idle_check_batch([SessionStatus.RUNNING])
        targets_by_session_id = {target.session.session_id: target for target in batch.targets}
        domain_target = targets_by_session_id[seeded_idle_check_data.domain_session_id]
        checkers = domain_target.checkers

        assert len(checkers) == 1
        assert checkers[0].checker.checker_id == seeded_idle_check_data.domain_checker_id
        assert checkers[0].scope.scope_type is ScopeType.DOMAIN

    @pytest.mark.parametrize(
        "seeded_idle_check_data",
        [("resource-group", "project", "domain")],
        indirect=True,
    )
    async def test_excludes_inference_sessions(
        self,
        repository: IdleCheckerRepository,
        seeded_idle_check_data: SeededIdleCheckData,
    ) -> None:
        batch = await repository.fetch_idle_check_batch([SessionStatus.RUNNING])
        targets_by_session_id = {target.session.session_id: target for target in batch.targets}

        assert set(targets_by_session_id) == {
            seeded_idle_check_data.resource_group_session_id,
            seeded_idle_check_data.project_session_id,
            seeded_idle_check_data.domain_session_id,
        }
        assert seeded_idle_check_data.inference_session_id not in targets_by_session_id

    @pytest.fixture
    async def per_type_checker_data(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> PerTypeCheckerData:
        scope = ScopeFixture(
            domain_name="per-type-domain",
            domain_id=DomainID(uuid.uuid4()),
            project_id=uuid.uuid4(),
            scaling_group_name="per-type-sgroup",
            scaling_group_id=ResourceGroupID(uuid.uuid4()),
        )
        interactive_session_id = SessionId(uuid.uuid4())
        batch_session_id = SessionId(uuid.uuid4())
        interactive_checker_id = IdleCheckerID(uuid.uuid4())
        batch_checker_id = IdleCheckerID(uuid.uuid4())
        session_specs = (
            (interactive_session_id, SessionTypes.INTERACTIVE, datetime(2026, 1, 1, tzinfo=UTC)),
            (batch_session_id, SessionTypes.BATCH, datetime(2026, 1, 2, tzinfo=UTC)),
        )
        checker_specs = (
            (interactive_checker_id, frozenset({SessionTypes.INTERACTIVE})),
            (batch_checker_id, frozenset({SessionTypes.BATCH})),
        )
        async with database.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"{scope.domain_name}-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=1024,
                    max_network_count=10,
                )
            )
            db_sess.add(
                DomainRow(
                    id=scope.domain_id,
                    name=scope.domain_name,
                    description=None,
                    is_active=True,
                )
            )
            db_sess.add(
                GroupRow(
                    id=scope.project_id,
                    name=f"{scope.domain_name}-project",
                    description=None,
                    is_active=True,
                    domain_name=scope.domain_name,
                    resource_policy=f"{scope.domain_name}-policy",
                )
            )
            db_sess.add(
                ScalingGroupRow(
                    id=scope.scaling_group_id,
                    name=scope.scaling_group_name,
                    description=None,
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    use_host_network=False,
                )
            )
            for session_id, session_type, created_at in session_specs:
                db_sess.add(
                    SessionRow(
                        id=session_id,
                        creation_id=str(session_id)[:32],
                        name=f"session-{session_id}",
                        session_type=session_type,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        cluster_size=1,
                        domain_name=scope.domain_name,
                        domain_id=scope.domain_id,
                        resource_group_id=scope.scaling_group_id,
                        group_id=scope.project_id,
                        user_uuid=uuid.uuid4(),
                        access_key=None,
                        tag=None,
                        status=SessionStatus.RUNNING,
                        status_info=None,
                        status_data=None,
                        status_history={},
                        result=SessionResult.UNDEFINED,
                        created_at=created_at,
                        terminated_at=None,
                        starts_at=created_at,
                        startup_command=None,
                        callback_url=None,
                        occupying_slots=ResourceSlot({"cpu": "1"}),
                        requested_slots=ResourceSlot({"cpu": "1"}),
                        vfolder_mounts=[],
                        environ=None,
                        bootstrap_script=None,
                        use_host_network=False,
                        scaling_group_name=scope.scaling_group_name,
                    )
                )
            for checker_id, target_types in checker_specs:
                db_sess.add(
                    IdleCheckerRow(
                        id=checker_id,
                        name=f"checker-{checker_id}",
                        description=None,
                        checker_type=CheckerType.SESSION_LIFETIME,
                        spec=IdleCheckerSpec(
                            type=CheckerType.SESSION_LIFETIME,
                            target_session_types=target_types,
                            session_lifetime=SessionLifetimeSpec(),
                        ),
                    )
                )
            await db_sess.flush()
            for checker_id, _ in checker_specs:
                db_sess.add(
                    IdleCheckerBindingRow(
                        scope_type=ScopeType.DOMAIN.value,
                        scope_id=scope.domain_id,
                        idle_checker_id=checker_id,
                        enabled=True,
                    )
                )
        return PerTypeCheckerData(
            interactive_session_id=interactive_session_id,
            batch_session_id=batch_session_id,
            interactive_checker_id=interactive_checker_id,
            batch_checker_id=batch_checker_id,
        )

    async def test_applies_only_checkers_targeting_session_type(
        self,
        repository: IdleCheckerRepository,
        per_type_checker_data: PerTypeCheckerData,
    ) -> None:
        batch = await repository.fetch_idle_check_batch([SessionStatus.RUNNING])
        targets_by_session_id = {target.session.session_id: target for target in batch.targets}

        interactive_target = targets_by_session_id[per_type_checker_data.interactive_session_id]
        interactive_checker_ids = [
            bound.checker.checker_id for bound in interactive_target.checkers
        ]
        assert interactive_checker_ids == [per_type_checker_data.interactive_checker_id]

        batch_target = targets_by_session_id[per_type_checker_data.batch_session_id]
        batch_checker_ids = [bound.checker.checker_id for bound in batch_target.checkers]
        assert batch_checker_ids == [per_type_checker_data.batch_checker_id]
