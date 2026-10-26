from __future__ import annotations

import enum
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, replace
from datetime import UTC, datetime

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ArchName,
    ClusterMode,
    KernelId,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.system_session_environ.repository import (
    SystemSessionEnvironRepository,
)
from ai.backend.manager.repositories.system_session_environ.value_resolver import (
    AccessKeyValueResolver,
    ClusterHostsValueResolver,
    ClusterReplicasValueResolver,
    ClusterSizeValueResolver,
    PreopenPortsValueResolver,
    SessionIdValueResolver,
    SessionNameValueResolver,
    SystemSessionEnvironValueResolverRegistry,
    UserEmailValueResolver,
    UserNameValueResolver,
    UserUuidValueResolver,
)
from ai.backend.manager.views.sokovan.lifecycle import KernelBindingData, SessionDataForStart
from ai.backend.testutils.db import with_tables

_DOMAIN_ID = DomainID(uuid.UUID("5c8e1d2a-0000-4000-8000-000000000001"))
_PROJECT_ID = ProjectID(uuid.UUID("5c8e1d2a-0000-4000-8000-000000000002"))
_OTHER_DOMAIN_ID = DomainID(uuid.UUID("5c8e1d2a-0000-4000-8000-000000000003"))
_OTHER_PROJECT_ID = ProjectID(uuid.UUID("5c8e1d2a-0000-4000-8000-000000000004"))
_SESSION_ID = SessionId(uuid.UUID("5c8e1d2a-0000-4000-8000-000000000005"))
_USER_UUID = uuid.UUID("5c8e1d2a-0000-4000-8000-000000000006")
_OTHER_SESSION_ID = SessionId(uuid.UUID("5c8e1d2a-0000-4000-8000-000000000007"))


class _RowOwner(enum.Enum):
    PUBLIC = enum.auto()
    DOMAIN = enum.auto()
    PROJECT = enum.auto()
    OTHER_DOMAIN = enum.auto()
    OTHER_PROJECT = enum.auto()


@dataclass(frozen=True)
class _RowScope:
    scope_type: SystemSessionEnvironScopeType
    scope_id: uuid.UUID


@dataclass(frozen=True)
class _RowAtOwner:
    key: str
    value_source: SystemSessionEnvironValueSource
    owner: _RowOwner
    deleted: bool = False


@dataclass(frozen=True)
class _EffectiveRowsCase:
    name: str
    rows: list[_RowAtOwner]
    expected_environ: dict[str, str]


@dataclass(frozen=True)
class _ValueSourceCase:
    value_source: SystemSessionEnvironValueSource
    expected_value: str


def _kernel_binding(
    cluster_role: str, cluster_idx: int, cluster_hostname: str | None
) -> KernelBindingData:
    return KernelBindingData(
        kernel_id=KernelId(uuid.uuid4()),
        agent_id=AgentId("agent-1"),
        agent_addr="tcp://agent-1:6001",
        resource_group="default",
        image="cr.backend.ai/stable/python:3.9-ubuntu20.04",
        image_id=None,
        architecture=ArchName("x86_64"),
        cluster_role=cluster_role,
        cluster_idx=cluster_idx,
        cluster_hostname=cluster_hostname,
        preopen_ports=[8080, 8081] if cluster_role == "main" else [],
    )


@pytest.fixture
async def database(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, [SystemSessionEnvironRow]):
        yield global_entity_ids


@pytest.fixture
def value_resolver_registry() -> SystemSessionEnvironValueResolverRegistry:
    return SystemSessionEnvironValueResolverRegistry([
        SessionIdValueResolver(),
        SessionNameValueResolver(),
        ClusterSizeValueResolver(),
        ClusterReplicasValueResolver(),
        ClusterHostsValueResolver(),
        PreopenPortsValueResolver(),
        UserUuidValueResolver(),
        UserEmailValueResolver(),
        UserNameValueResolver(),
        AccessKeyValueResolver(),
    ])


@pytest.fixture
def repository(
    database: ExtendedAsyncSAEngine,
    value_resolver_registry: SystemSessionEnvironValueResolverRegistry,
) -> SystemSessionEnvironRepository:
    return SystemSessionEnvironRepository(V2DBOpsProvider(database), value_resolver_registry)


@pytest.fixture
def row_scope_by_owner(database: ExtendedAsyncSAEngine) -> dict[_RowOwner, _RowScope]:
    return {
        _RowOwner.PUBLIC: _RowScope(
            SystemSessionEnvironScopeType.PUBLIC, global_entity_id(GlobalEntityName.PUBLIC)
        ),
        _RowOwner.DOMAIN: _RowScope(SystemSessionEnvironScopeType.DOMAIN, _DOMAIN_ID),
        _RowOwner.PROJECT: _RowScope(SystemSessionEnvironScopeType.PROJECT, _PROJECT_ID),
        _RowOwner.OTHER_DOMAIN: _RowScope(SystemSessionEnvironScopeType.DOMAIN, _OTHER_DOMAIN_ID),
        _RowOwner.OTHER_PROJECT: _RowScope(
            SystemSessionEnvironScopeType.PROJECT, _OTHER_PROJECT_ID
        ),
    }


@pytest.fixture
async def case_rows(
    database: ExtendedAsyncSAEngine,
    row_scope_by_owner: dict[_RowOwner, _RowScope],
    case: _EffectiveRowsCase,
) -> None:
    async with database.begin_session() as db_sess:
        db_sess.add_all([
            SystemSessionEnvironRow(
                value_source=row.value_source,
                key=row.key,
                scope_type=row_scope_by_owner[row.owner].scope_type,
                scope_id=SystemSessionEnvironScopeID(row_scope_by_owner[row.owner].scope_id),
                deleted_at=datetime.now(UTC) if row.deleted else None,
            )
            for row in case.rows
        ])


@pytest.fixture
async def rows_at_two_projects(
    database: ExtendedAsyncSAEngine,
    row_scope_by_owner: dict[_RowOwner, _RowScope],
) -> None:
    async with database.begin_session() as db_sess:
        db_sess.add_all([
            SystemSessionEnvironRow(
                value_source=SystemSessionEnvironValueSource.SESSION_NAME,
                key="K",
                scope_type=SystemSessionEnvironScopeType.PUBLIC,
                scope_id=SystemSessionEnvironScopeID(row_scope_by_owner[_RowOwner.PUBLIC].scope_id),
            ),
            SystemSessionEnvironRow(
                value_source=SystemSessionEnvironValueSource.USER_NAME,
                key="K",
                scope_type=SystemSessionEnvironScopeType.PROJECT,
                scope_id=SystemSessionEnvironScopeID(_PROJECT_ID),
            ),
            SystemSessionEnvironRow(
                value_source=SystemSessionEnvironValueSource.USER_EMAIL,
                key="K",
                scope_type=SystemSessionEnvironScopeType.PROJECT,
                scope_id=SystemSessionEnvironScopeID(_OTHER_PROJECT_ID),
            ),
        ])


@pytest.fixture
def starting_session() -> SessionDataForStart:
    return SessionDataForStart(
        session_id=_SESSION_ID,
        creation_id="creation-1",
        access_key=AccessKey("AKTESTACCESSKEY"),
        session_type=SessionTypes.INTERACTIVE,
        name="test-session",
        cluster_mode=ClusterMode.MULTI_NODE,
        kernels=[
            _kernel_binding("main", 1, "main1"),
            _kernel_binding("sub", 1, None),
            _kernel_binding("sub", 2, None),
        ],
        user_uuid=_USER_UUID,
        user_email="user@example.com",
        user_name="test-user",
        domain_id=_DOMAIN_ID,
        project_id=_PROJECT_ID,
        environ={},
    )


@pytest.fixture
def session_in_other_project(starting_session: SessionDataForStart) -> SessionDataForStart:
    return replace(starting_session, session_id=_OTHER_SESSION_ID, project_id=_OTHER_PROJECT_ID)


@pytest.fixture
async def value_source_bound_to_key_k(
    database: ExtendedAsyncSAEngine,
    row_scope_by_owner: dict[_RowOwner, _RowScope],
    case: _ValueSourceCase,
) -> None:
    async with database.begin_session() as db_sess:
        db_sess.add(
            SystemSessionEnvironRow(
                value_source=case.value_source,
                key="K",
                scope_type=SystemSessionEnvironScopeType.PUBLIC,
                scope_id=SystemSessionEnvironScopeID(row_scope_by_owner[_RowOwner.PUBLIC].scope_id),
            )
        )


class TestResolve:
    @pytest.mark.parametrize(
        "case",
        [
            _EffectiveRowsCase(
                name="other_domain_and_project_ignored",
                rows=[
                    _RowAtOwner(
                        "K", SystemSessionEnvironValueSource.USER_NAME, _RowOwner.OTHER_DOMAIN
                    ),
                    _RowAtOwner(
                        "L", SystemSessionEnvironValueSource.USER_EMAIL, _RowOwner.OTHER_PROJECT
                    ),
                ],
                expected_environ={},
            ),
            _EffectiveRowsCase(
                name="other_domain_does_not_shadow_public",
                rows=[
                    _RowAtOwner(
                        "K", SystemSessionEnvironValueSource.SESSION_NAME, _RowOwner.PUBLIC
                    ),
                    _RowAtOwner(
                        "K", SystemSessionEnvironValueSource.USER_NAME, _RowOwner.OTHER_DOMAIN
                    ),
                ],
                expected_environ={"K": "test-session"},
            ),
            _EffectiveRowsCase(
                name="domain_over_public",
                rows=[
                    _RowAtOwner("K", SystemSessionEnvironValueSource.USER_NAME, _RowOwner.DOMAIN),
                    _RowAtOwner(
                        "K", SystemSessionEnvironValueSource.SESSION_NAME, _RowOwner.PUBLIC
                    ),
                ],
                expected_environ={"K": "test-user"},
            ),
            _EffectiveRowsCase(
                name="project_over_public",
                rows=[
                    _RowAtOwner(
                        "K", SystemSessionEnvironValueSource.SESSION_NAME, _RowOwner.PUBLIC
                    ),
                    _RowAtOwner("K", SystemSessionEnvironValueSource.USER_EMAIL, _RowOwner.PROJECT),
                ],
                expected_environ={"K": "user@example.com"},
            ),
            _EffectiveRowsCase(
                name="project_over_domain",
                rows=[
                    _RowAtOwner("K", SystemSessionEnvironValueSource.USER_EMAIL, _RowOwner.PROJECT),
                    _RowAtOwner("K", SystemSessionEnvironValueSource.USER_NAME, _RowOwner.DOMAIN),
                ],
                expected_environ={"K": "user@example.com"},
            ),
            _EffectiveRowsCase(
                name="project_over_domain_and_public",
                rows=[
                    _RowAtOwner("K", SystemSessionEnvironValueSource.USER_NAME, _RowOwner.DOMAIN),
                    _RowAtOwner("K", SystemSessionEnvironValueSource.USER_EMAIL, _RowOwner.PROJECT),
                    _RowAtOwner(
                        "K", SystemSessionEnvironValueSource.SESSION_NAME, _RowOwner.PUBLIC
                    ),
                ],
                expected_environ={"K": "user@example.com"},
            ),
            _EffectiveRowsCase(
                name="deleted_row_left_out",
                rows=[
                    _RowAtOwner(
                        "K",
                        SystemSessionEnvironValueSource.SESSION_NAME,
                        _RowOwner.PUBLIC,
                        deleted=True,
                    ),
                ],
                expected_environ={},
            ),
            _EffectiveRowsCase(
                name="deleted_project_row_leaves_the_public_key",
                rows=[
                    _RowAtOwner("K", SystemSessionEnvironValueSource.USER_NAME, _RowOwner.PUBLIC),
                    _RowAtOwner(
                        "K",
                        SystemSessionEnvironValueSource.USER_EMAIL,
                        _RowOwner.PROJECT,
                        deleted=True,
                    ),
                ],
                expected_environ={"K": "test-user"},
            ),
            _EffectiveRowsCase(
                name="live_project_row_over_a_deleted_public_key",
                rows=[
                    _RowAtOwner(
                        "K",
                        SystemSessionEnvironValueSource.USER_NAME,
                        _RowOwner.PUBLIC,
                        deleted=True,
                    ),
                    _RowAtOwner("K", SystemSessionEnvironValueSource.USER_EMAIL, _RowOwner.PROJECT),
                ],
                expected_environ={"K": "user@example.com"},
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_injects_the_effective_row_of_each_key(
        self,
        case: _EffectiveRowsCase,
        repository: SystemSessionEnvironRepository,
        starting_session: SessionDataForStart,
        case_rows: None,
    ) -> None:
        resolved_environ_by_session = await repository.resolve([starting_session])

        assert resolved_environ_by_session[starting_session.session_id] == case.expected_environ

    async def test_resolves_each_session_of_one_call_on_its_own(
        self,
        repository: SystemSessionEnvironRepository,
        starting_session: SessionDataForStart,
        session_in_other_project: SessionDataForStart,
        rows_at_two_projects: None,
    ) -> None:
        resolved_environ_by_session = await repository.resolve([
            starting_session,
            session_in_other_project,
        ])

        assert resolved_environ_by_session[starting_session.session_id] == {"K": "test-user"}
        assert resolved_environ_by_session[session_in_other_project.session_id] == {
            "K": "user@example.com"
        }

    @pytest.mark.parametrize(
        "case",
        [
            _ValueSourceCase(SystemSessionEnvironValueSource.SESSION_ID, str(_SESSION_ID)),
            _ValueSourceCase(SystemSessionEnvironValueSource.SESSION_NAME, "test-session"),
            _ValueSourceCase(SystemSessionEnvironValueSource.CLUSTER_SIZE, "3"),
            _ValueSourceCase(SystemSessionEnvironValueSource.CLUSTER_REPLICAS, "main:1,sub:2"),
            _ValueSourceCase(SystemSessionEnvironValueSource.CLUSTER_HOSTS, "main1,sub1,sub2"),
            _ValueSourceCase(SystemSessionEnvironValueSource.PREOPEN_PORTS, "8080,8081"),
            _ValueSourceCase(SystemSessionEnvironValueSource.USER_UUID, str(_USER_UUID)),
            _ValueSourceCase(SystemSessionEnvironValueSource.USER_EMAIL, "user@example.com"),
            _ValueSourceCase(SystemSessionEnvironValueSource.USER_NAME, "test-user"),
            _ValueSourceCase(SystemSessionEnvironValueSource.ACCESS_KEY, "AKTESTACCESSKEY"),
        ],
        ids=lambda case: case.value_source.value,
    )
    async def test_injects_the_session_value_of_the_source(
        self,
        case: _ValueSourceCase,
        repository: SystemSessionEnvironRepository,
        starting_session: SessionDataForStart,
        value_source_bound_to_key_k: None,
    ) -> None:
        resolved_environ_by_session = await repository.resolve([starting_session])

        assert resolved_environ_by_session[starting_session.session_id] == {
            "K": case.expected_value
        }
