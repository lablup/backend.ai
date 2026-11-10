"""ComputeSessionNode.graph reads the sessions linked by dependencies, against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import datetime
from unittest.mock import MagicMock

import graphene
import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session import SessionID
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
from ai.backend.manager.models.user.row import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables

# Reachable only through string relationships of the session row's eager loads.
_ORM_CLUSTER = (EndpointRow,)

_DOMAIN_NAME = "graph-domain"
_RESOURCE_GROUP_NAME = "graph-rg"
_PROJECT_POLICY_NAME = "graph-project-policy"

type _AddSession = Callable[[], Awaitable[SessionId]]
type _AddDependency = Callable[[SessionId, SessionId], Awaitable[None]]


class TestComputeSessionNodeGraphTraversal:
    @pytest.fixture
    async def db_with_tables(
        self,
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
    async def add_session(self, db_with_tables: ExtendedAsyncSAEngine) -> _AddSession:
        """Insert a session of one project; the domain, resource group and project come first."""
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

        async def _add() -> SessionId:
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
                        domain_id=domain_id,
                        domain_name=_DOMAIN_NAME,
                        group_id=project_id,
                        user_uuid=None,
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
                        resource_group_id=resource_group_id,
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
                        group_id=project_id,
                        user_uuid=None,
                        access_key=None,
                        cluster_mode=ClusterMode.SINGLE_NODE.value,
                        cluster_size=1,
                        cluster_role=DEFAULT_ROLE,
                        cluster_idx=0,
                        local_rank=0,
                        cluster_hostname="main",
                        scaling_group=_RESOURCE_GROUP_NAME,
                        resource_group_id=resource_group_id,
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
    def add_dependency(self, db_with_tables: ExtendedAsyncSAEngine) -> _AddDependency:
        async def _add(session_id: SessionId, depends_on: SessionId) -> None:
            async with db_with_tables.begin_session() as db_sess:
                db_sess.add(
                    SessionDependencyRow(
                        session_id=SessionID(session_id), depends_on=SessionID(depends_on)
                    )
                )

        return _add

    async def _graph_of(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        session_id: SessionId,
        role: UserRole = UserRole.SUPERADMIN,
        domain_name: str = _DOMAIN_NAME,
    ) -> list[uuid.UUID]:
        """The session ids the requester reads from the graph of the session."""
        ctx = MagicMock()
        ctx.db = db_with_tables
        ctx.user = {
            "role": role,
            "domain_name": domain_name,
            "uuid": uuid.uuid4(),
        }
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
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

    @pytest.mark.parametrize(
        ("role", "domain_name"),
        [(UserRole.ADMIN, "other-domain"), (UserRole.USER, _DOMAIN_NAME)],
        ids=["admin-of-another-domain", "user-not-owning-the-sessions"],
    )
    async def test_the_graph_holds_only_the_sessions_the_requester_may_read(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        add_session: _AddSession,
        add_dependency: _AddDependency,
        role: UserRole,
        domain_name: str,
    ) -> None:
        first, second = await add_session(), await add_session()
        await add_dependency(second, first)

        assert await self._graph_of(db_with_tables, first, role, domain_name) == []

    async def test_an_admin_of_the_domain_reads_the_whole_graph(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        add_session: _AddSession,
        add_dependency: _AddDependency,
    ) -> None:
        first, second = await add_session(), await add_session()
        await add_dependency(second, first)

        graph = await self._graph_of(db_with_tables, first, UserRole.ADMIN)
        assert sorted(graph) == sorted([first, second])
