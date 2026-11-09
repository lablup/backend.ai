"""ComputeSessionNode reads the sessions linked by dependencies (graph, dependents, dependees),
against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from unittest.mock import MagicMock

import graphene
import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import (
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.session.row import SessionDependencyRow, SessionRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables

# Reachable only through string relationships of the session row's eager loads.
_ORM_CLUSTER = (EndpointRow,)

_DOMAIN_NAME = "graph-domain"
_OTHER_DOMAIN_NAME = "other-domain"
_RESOURCE_GROUP_NAME = "graph-rg"
_PROJECT_POLICY_NAME = "graph-project-policy"
_USER_POLICY_NAME = "graph-user-policy"

type _AddDependency = Callable[[SessionId, SessionId], Awaitable[None]]


class _AddSession(Protocol):
    async def __call__(self, *, owner: UserID | None = None) -> SessionId: ...


@dataclass(frozen=True)
class _Project:
    domain_id: DomainID
    resource_group_id: ResourceGroupID
    project_id: uuid.UUID


@dataclass(frozen=True)
class _Requester:
    role: UserRole
    domain_name: str
    owns_the_sessions: bool
    reads_the_sessions: bool


_REQUESTERS = [
    _Requester(UserRole.SUPERADMIN, _OTHER_DOMAIN_NAME, False, True),
    _Requester(UserRole.ADMIN, _DOMAIN_NAME, False, True),
    _Requester(UserRole.ADMIN, _OTHER_DOMAIN_NAME, False, False),
    _Requester(UserRole.USER, _DOMAIN_NAME, True, True),
    _Requester(UserRole.USER, _DOMAIN_NAME, False, False),
]
_REQUESTER_IDS = [
    "superadmin",
    "admin-of-the-domain",
    "admin-of-another-domain",
    "user-owning-the-sessions",
    "another-user",
]


@pytest.fixture
async def db_with_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            # FK dependency order: parents before children
            DomainRow,
            ResourceGroupRow,
            ResourceSlotTypeRow,
            AgentRow,
            AgentResourceRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            ProjectRow,
            KeyPairRow,
            ResourceGroupForDomainRow,
            ResourceGroupForProjectRow,
            ResourceGroupForKeypairsRow,
            ContainerRegistryRow,
            AssociationContainerRegistriesGroupsRow,
            ImageRow,
            ImageAliasRow,
            SessionRow,
            KernelRow,
            SessionDependencyRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def project(db_with_tables: ExtendedAsyncSAEngine) -> _Project:
    """A domain, a resource group and one project of the domain."""
    domain_id = DomainID(uuid.uuid4())
    resource_group_id = ResourceGroupID(uuid.uuid4())
    project_id = uuid.uuid4()
    async with db_with_tables.begin_session() as db_sess:
        db_sess.add(
            DomainRow(
                id=domain_id,
                name=_DOMAIN_NAME,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                integration_id=None,
            )
        )
        db_sess.add(
            ResourceGroupRow(
                id=resource_group_id,
                name=_RESOURCE_GROUP_NAME,
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
            )
        )
        db_sess.add(
            ProjectResourcePolicyRow(
                name=_PROJECT_POLICY_NAME,
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
        )
        await db_sess.flush()
        db_sess.add(
            ProjectRow(
                id=project_id,
                name="graph-project",
                description="",
                is_active=True,
                domain_name=_DOMAIN_NAME,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=_PROJECT_POLICY_NAME,
                type=ProjectType.GENERAL,
            )
        )
    return _Project(domain_id=domain_id, resource_group_id=resource_group_id, project_id=project_id)


@pytest.fixture
async def session_owner(db_with_tables: ExtendedAsyncSAEngine, project: _Project) -> UserID:
    """A user of the domain."""
    user_id = UserID(uuid.uuid4())
    async with db_with_tables.begin_session() as db_sess:
        db_sess.add(
            UserResourcePolicyRow(
                name=_USER_POLICY_NAME,
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await db_sess.flush()
        db_sess.add(
            UserRow(
                uuid=user_id,
                username="graph-owner",
                email="graph-owner@example.com",
                password=None,
                need_password_change=False,
                full_name="graph-owner",
                description="",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=_DOMAIN_NAME,
                role=UserRole.USER,
                resource_policy=_USER_POLICY_NAME,
                allowed_client_ip=None,
                totp_key=None,
                domain_id=project.domain_id,
            )
        )
    return user_id


@pytest.fixture
def add_session(db_with_tables: ExtendedAsyncSAEngine, project: _Project) -> _AddSession:
    """Insert a session of the project with its main kernel."""

    async def _add(*, owner: UserID | None = None) -> SessionId:
        session_id = SessionId(uuid.uuid4())
        name = f"graph-{session_id.hex[:8]}"
        created = datetime.now(tzutc())
        async with db_with_tables.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=session_id.hex[:32],
                    name=name,
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_id=project.domain_id,
                    domain_name=_DOMAIN_NAME,
                    group_id=project.project_id,
                    user_uuid=owner,
                    access_key=None,
                    tag=None,
                    status=SessionStatus.RUNNING,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    result=SessionResult.UNDEFINED,
                    created_at=created,
                    terminated_at=None,
                    starts_at=None,
                    startup_command=None,
                    callback_url=None,
                    vfolder_mounts=[],
                    environ=None,
                    bootstrap_script=None,
                    use_host_network=False,
                    resource_group_id=project.resource_group_id,
                    scaling_group_name=_RESOURCE_GROUP_NAME,
                )
            )
            await db_sess.flush()
            # The node reads the service ports of the main kernel.
            db_sess.add(
                KernelRow(
                    id=KernelId(uuid.uuid4()),
                    session_id=session_id,
                    session_name=name,
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=_DOMAIN_NAME,
                    group_id=project.project_id,
                    user_uuid=owner,
                    access_key=None,
                    cluster_mode=ClusterMode.SINGLE_NODE.value,
                    cluster_size=1,
                    cluster_role=DEFAULT_ROLE,
                    cluster_idx=0,
                    local_rank=0,
                    cluster_hostname="main",
                    scaling_group=_RESOURCE_GROUP_NAME,
                    resource_group_id=project.resource_group_id,
                    image="cr.backend.ai/stable/python:latest",
                    architecture="x86_64",
                    registry="cr.backend.ai",
                    agent=None,
                    agent_addr=None,
                    container_id=None,
                    repl_in_port=2000,
                    repl_out_port=2001,
                    stdin_port=2002,
                    stdout_port=2003,
                    use_host_network=False,
                    status=KernelStatus.RUNNING,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    status_changed=created,
                    result=SessionResult.UNDEFINED,
                    created_at=created,
                    terminated_at=None,
                    starts_at=None,
                    occupied_shares={},
                    environ=None,
                    vfolder_mounts=[],
                    attached_devices={},
                    resource_opts=None,
                    preopen_ports=None,
                    bootstrap_script=None,
                    startup_command=None,
                )
            )
        return session_id

    return _add


@pytest.fixture
def add_dependency(db_with_tables: ExtendedAsyncSAEngine) -> _AddDependency:
    async def _add(session_id: SessionId, depends_on: SessionId) -> None:
        async with db_with_tables.begin_session() as db_sess:
            db_sess.add(
                SessionDependencyRow(
                    session_id=SessionID(session_id), depends_on=SessionID(depends_on)
                )
            )

    return _add


def _context(
    db: ExtendedAsyncSAEngine, role: UserRole, domain_name: str, user_id: uuid.UUID
) -> MagicMock:
    ctx = MagicMock()
    ctx.db = db
    ctx.user = {"role": role, "domain_name": domain_name, "uuid": user_id}
    return ctx


class TestComputeSessionNodeGraphTraversal:
    async def _graph_of(
        self, db_with_tables: ExtendedAsyncSAEngine, session_id: SessionId
    ) -> list[uuid.UUID]:
        """The session ids a superadmin reads from the graph of the session."""
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = _context(db_with_tables, UserRole.SUPERADMIN, _DOMAIN_NAME, uuid.uuid4())
        result = await ComputeSessionNode(row_id=session_id).resolve_graph(info)
        assert isinstance(result.node_list, list)
        return [node.row_id for node in result.node_list]

    async def test_a_session_without_dependencies_is_its_whole_graph(
        self, db_with_tables: ExtendedAsyncSAEngine, add_session: _AddSession
    ) -> None:
        alone = await add_session()
        await add_session()

        assert await self._graph_of(db_with_tables, alone) == [alone]

    async def test_the_graph_follows_dependencies_in_both_directions(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        add_session: _AddSession,
        add_dependency: _AddDependency,
    ) -> None:
        first, second, third, fourth = [await add_session() for _ in range(4)]
        unrelated = await add_session()
        # second depends on first; third and fourth depend on second
        await add_dependency(second, first)
        await add_dependency(third, second)
        await add_dependency(fourth, second)

        for start in (first, second, fourth):
            graph = await self._graph_of(db_with_tables, start)
            assert sorted(graph) == sorted([first, second, third, fourth])
            assert unrelated not in graph

    async def test_sessions_depending_on_each_other_are_read_once(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        add_session: _AddSession,
        add_dependency: _AddDependency,
    ) -> None:
        first, second = await add_session(), await add_session()
        await add_dependency(first, second)
        await add_dependency(second, first)

        graph = await self._graph_of(db_with_tables, first)
        assert sorted(graph) == sorted([first, second])


class TestComputeSessionNodeDependencyLoaders:
    """The dependents and dependees loaders answer only the sessions the requester may read."""

    @pytest.fixture
    async def dependee(self, add_session: _AddSession, session_owner: UserID) -> SessionId:
        return await add_session(owner=session_owner)

    @pytest.fixture
    async def dependent(
        self,
        add_session: _AddSession,
        add_dependency: _AddDependency,
        session_owner: UserID,
        dependee: SessionId,
    ) -> SessionId:
        """A session of the same owner that depends on ``dependee``."""
        session_id = await add_session(owner=session_owner)
        await add_dependency(session_id, dependee)
        return session_id

    def _context_of(
        self, db: ExtendedAsyncSAEngine, requester: _Requester, session_owner: UserID
    ) -> MagicMock:
        user_id = session_owner if requester.owns_the_sessions else uuid.uuid4()
        return _context(db, requester.role, requester.domain_name, user_id)

    @pytest.mark.parametrize("requester", _REQUESTERS, ids=_REQUESTER_IDS)
    async def test_the_dependents_of_a_session_are_bounded_by_the_requester(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        session_owner: UserID,
        dependee: SessionId,
        dependent: SessionId,
        requester: _Requester,
    ) -> None:
        ctx = self._context_of(db_with_tables, requester, session_owner)

        (loaded,) = await ComputeSessionNode.batch_load_by_dependee_id(ctx, [dependee])

        expected = [dependent] if requester.reads_the_sessions else []
        assert [node.row_id for node in loaded] == expected

    @pytest.mark.parametrize("requester", _REQUESTERS, ids=_REQUESTER_IDS)
    async def test_the_dependees_of_a_session_are_bounded_by_the_requester(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        session_owner: UserID,
        dependee: SessionId,
        dependent: SessionId,
        requester: _Requester,
    ) -> None:
        ctx = self._context_of(db_with_tables, requester, session_owner)

        (loaded,) = await ComputeSessionNode.batch_load_by_dependent_id(ctx, [dependent])

        expected = [dependee] if requester.reads_the_sessions else []
        assert [node.row_id for node in loaded] == expected
