from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironValueSource
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ArchName,
    ClusterMode,
    KernelId,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.sokovan.scheduler.launcher.session_environ import build_session_environ
from ai.backend.manager.views.sokovan.lifecycle import KernelBindingData, SessionDataForStart

_SESSION_ID = SessionId(UUID("6f1c2a0e-0000-4000-8000-000000000001"))
_USER_UUID = UUID("6f1c2a0e-0000-4000-8000-000000000002")
_DOMAIN_ID = DomainID(UUID("6f1c2a0e-0000-4000-8000-000000000003"))
_PROJECT_ID = ProjectID(UUID("6f1c2a0e-0000-4000-8000-000000000004"))
_OTHER_DOMAIN_ID = DomainID(UUID("6f1c2a0e-0000-4000-8000-000000000005"))
_OTHER_PROJECT_ID = ProjectID(UUID("6f1c2a0e-0000-4000-8000-000000000006"))


@dataclass(frozen=True)
class _Binding:
    key: str
    value_source: SystemSessionEnvironValueSource
    scope_id: EntityIdentifier | None = None


@dataclass(frozen=True)
class _EnvironCase:
    name: str
    bindings: list[_Binding]
    expected: dict[str, str]
    user_environ: dict[str, str] = field(default_factory=dict)


def _kernel(cluster_role: str, cluster_idx: int, cluster_hostname: str | None) -> KernelBindingData:
    return KernelBindingData(
        kernel_id=KernelId(uuid4()),
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
def session(case: _EnvironCase) -> SessionDataForStart:
    return SessionDataForStart(
        session_id=_SESSION_ID,
        creation_id="creation-1",
        access_key=AccessKey("AKTESTACCESSKEY"),
        session_type=SessionTypes.INTERACTIVE,
        name="test-session",
        cluster_mode=ClusterMode.MULTI_NODE,
        kernels=[_kernel("main", 1, "main1"), _kernel("sub", 1, None), _kernel("sub", 2, None)],
        user_uuid=_USER_UUID,
        user_email="user@example.com",
        user_name="test-user",
        domain_id=_DOMAIN_ID,
        project_id=_PROJECT_ID,
        environ=case.user_environ,
    )


@pytest.fixture
def rows(case: _EnvironCase) -> list[SystemSessionEnvironData]:
    now = datetime.now(UTC)
    return [
        SystemSessionEnvironData(
            id=SystemSessionEnvironID(uuid4()),
            value_source=binding.value_source,
            key=binding.key,
            scope_id=binding.scope_id,
            created_at=now,
            updated_at=now,
        )
        for binding in case.bindings
    ]


class TestValueSources:
    @pytest.mark.parametrize(
        "case",
        [
            _EnvironCase(
                name="session_id",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.SESSION_ID)],
                expected={"K": str(_SESSION_ID)},
            ),
            _EnvironCase(
                name="session_name",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.SESSION_NAME)],
                expected={"K": "test-session"},
            ),
            _EnvironCase(
                name="cluster_size",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.CLUSTER_SIZE)],
                expected={"K": "3"},
            ),
            _EnvironCase(
                name="cluster_replicas",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.CLUSTER_REPLICAS)],
                expected={"K": "main:1,sub:2"},
            ),
            _EnvironCase(
                name="cluster_hosts",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.CLUSTER_HOSTS)],
                expected={"K": "main1,sub1,sub2"},
            ),
            _EnvironCase(
                name="preopen_ports",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.PREOPEN_PORTS)],
                expected={"K": "8080,8081"},
            ),
            _EnvironCase(
                name="user_uuid",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.USER_UUID)],
                expected={"K": str(_USER_UUID)},
            ),
            _EnvironCase(
                name="user_email",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.USER_EMAIL)],
                expected={"K": "user@example.com"},
            ),
            _EnvironCase(
                name="user_name",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.USER_NAME)],
                expected={"K": "test-user"},
            ),
            _EnvironCase(
                name="access_key",
                bindings=[_Binding("K", SystemSessionEnvironValueSource.ACCESS_KEY)],
                expected={"K": "AKTESTACCESSKEY"},
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_injects_the_value_of_the_source(
        self,
        case: _EnvironCase,
        session: SessionDataForStart,
        rows: list[SystemSessionEnvironData],
    ) -> None:
        assert build_session_environ(session, rows) == case.expected


class TestScopeSelection:
    @pytest.mark.parametrize(
        "case",
        [
            _EnvironCase(
                name="other_domain_and_project_ignored",
                bindings=[
                    _Binding("K", SystemSessionEnvironValueSource.USER_NAME, _OTHER_DOMAIN_ID),
                    _Binding("L", SystemSessionEnvironValueSource.USER_EMAIL, _OTHER_PROJECT_ID),
                ],
                expected={},
            ),
            _EnvironCase(
                name="other_domain_does_not_shadow_global",
                bindings=[
                    _Binding("K", SystemSessionEnvironValueSource.SESSION_NAME),
                    _Binding("K", SystemSessionEnvironValueSource.USER_NAME, _OTHER_DOMAIN_ID),
                ],
                expected={"K": "test-session"},
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_injects_only_the_rows_at_the_sessions_scopes(
        self,
        case: _EnvironCase,
        session: SessionDataForStart,
        rows: list[SystemSessionEnvironData],
    ) -> None:
        assert build_session_environ(session, rows) == case.expected


class TestScopePrecedence:
    @pytest.mark.parametrize(
        "case",
        [
            _EnvironCase(
                name="domain_over_global",
                bindings=[
                    _Binding("K", SystemSessionEnvironValueSource.USER_NAME, _DOMAIN_ID),
                    _Binding("K", SystemSessionEnvironValueSource.SESSION_NAME),
                ],
                expected={"K": "test-user"},
            ),
            _EnvironCase(
                name="project_over_global",
                bindings=[
                    _Binding("K", SystemSessionEnvironValueSource.SESSION_NAME),
                    _Binding("K", SystemSessionEnvironValueSource.USER_EMAIL, _PROJECT_ID),
                ],
                expected={"K": "user@example.com"},
            ),
            _EnvironCase(
                name="project_over_domain",
                bindings=[
                    _Binding("K", SystemSessionEnvironValueSource.USER_EMAIL, _PROJECT_ID),
                    _Binding("K", SystemSessionEnvironValueSource.USER_NAME, _DOMAIN_ID),
                ],
                expected={"K": "user@example.com"},
            ),
            _EnvironCase(
                name="project_over_domain_and_global",
                bindings=[
                    _Binding("K", SystemSessionEnvironValueSource.USER_NAME, _DOMAIN_ID),
                    _Binding("K", SystemSessionEnvironValueSource.USER_EMAIL, _PROJECT_ID),
                    _Binding("K", SystemSessionEnvironValueSource.SESSION_NAME),
                ],
                expected={"K": "user@example.com"},
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_the_most_specific_scope_wins(
        self,
        case: _EnvironCase,
        session: SessionDataForStart,
        rows: list[SystemSessionEnvironData],
    ) -> None:
        assert build_session_environ(session, rows) == case.expected


class TestUserEnvironMerge:
    @pytest.mark.parametrize(
        "case",
        [
            _EnvironCase(
                name="nothing_bound",
                bindings=[],
                user_environ={"A": "mine"},
                expected={"A": "mine"},
            ),
            _EnvironCase(
                name="system_overrides_user",
                bindings=[_Binding("A", SystemSessionEnvironValueSource.SESSION_NAME)],
                user_environ={"A": "mine"},
                expected={"A": "test-session"},
            ),
            _EnvironCase(
                name="user_overrides_optional",
                bindings=[_Binding("A", SystemSessionEnvironValueSource.USER_EMAIL)],
                user_environ={"A": "mine"},
                expected={"A": "mine"},
            ),
            _EnvironCase(
                name="distinct_keys_all_kept",
                bindings=[
                    _Binding("S", SystemSessionEnvironValueSource.SESSION_NAME),
                    _Binding("O", SystemSessionEnvironValueSource.USER_NAME),
                ],
                user_environ={"U": "mine"},
                expected={"S": "test-session", "O": "test-user", "U": "mine"},
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_merges_with_the_session_environ(
        self,
        case: _EnvironCase,
        session: SessionDataForStart,
        rows: list[SystemSessionEnvironData],
    ) -> None:
        assert build_session_environ(session, rows) == case.expected
