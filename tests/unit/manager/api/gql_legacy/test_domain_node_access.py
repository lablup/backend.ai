from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from unittest.mock import MagicMock

import graphene
import pytest

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.api.gql_legacy.domain import DomainNode
from ai.backend.manager.api.gql_legacy.scaling_group import ScalingGroupNode
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.rbac.permission_defs import DomainPermission
from ai.backend.manager.models.resource_slot.row import DeploymentRevisionResourceSlotRow
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, create_async_engine
from ai.backend.testutils.db import with_tables

# Reachable only through string relationships of the rows the legacy GQL modules import.
_ORM_CLUSTER = (
    AgentRow,
    DeploymentRevisionResourceSlotRow,
)

_CALLER_DOMAIN_NAME = "caller-domain"
_OTHER_DOMAIN_NAME = "other-domain"


@dataclass(frozen=True)
class _DomainNodeReadCase:
    role: UserRole
    requested_domain_name: str


class TestDomainNodeGetNodeByName:
    @pytest.fixture
    async def database_connection(
        self,
        postgres_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        _, addr = postgres_container
        url = f"postgresql+asyncpg://postgres:develove@{addr.host}:{addr.port}/testing"
        engine = create_async_engine(url, pool_size=8, pool_pre_ping=False, max_overflow=64)
        yield engine
        await engine.dispose()

    @pytest.fixture
    async def db_holding_caller_and_other_domains(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [DomainRow]):
            async with database_connection.begin_session() as db_session:
                db_session.add_all([
                    DomainRow(
                        name=domain_name,
                        description=domain_name,
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts=VFolderHostPermissionMap(),
                        allowed_docker_registries=[],
                    )
                    for domain_name in (_CALLER_DOMAIN_NAME, _OTHER_DOMAIN_NAME)
                ])
            yield database_connection

    @pytest.fixture
    def resolve_info_of_caller(
        self,
        db_holding_caller_and_other_domains: ExtendedAsyncSAEngine,
        case: _DomainNodeReadCase,
    ) -> MagicMock:
        graph_ctx = MagicMock()
        graph_ctx.db = db_holding_caller_and_other_domains
        graph_ctx.user = {
            "role": case.role,
            "domain_name": _CALLER_DOMAIN_NAME,
            "uuid": uuid.uuid4(),
        }
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = graph_ctx
        return info

    @pytest.mark.parametrize(
        "case",
        [
            _DomainNodeReadCase(role=UserRole.USER, requested_domain_name=_CALLER_DOMAIN_NAME),
            _DomainNodeReadCase(role=UserRole.ADMIN, requested_domain_name=_CALLER_DOMAIN_NAME),
            _DomainNodeReadCase(role=UserRole.MONITOR, requested_domain_name=_OTHER_DOMAIN_NAME),
            _DomainNodeReadCase(role=UserRole.SUPERADMIN, requested_domain_name=_OTHER_DOMAIN_NAME),
        ],
        ids=lambda case: f"{case.role.value}-{case.requested_domain_name}",
    )
    async def test_returns_domain_within_caller_permission(
        self,
        resolve_info_of_caller: MagicMock,
        case: _DomainNodeReadCase,
    ) -> None:
        domain_node = await DomainNode.get_node_by_name(
            resolve_info_of_caller,
            case.requested_domain_name,
            DomainPermission.READ_ATTRIBUTE,
        )

        assert domain_node is not None
        assert domain_node.name == case.requested_domain_name

    @pytest.mark.parametrize(
        "case",
        [
            _DomainNodeReadCase(role=UserRole.USER, requested_domain_name=_OTHER_DOMAIN_NAME),
            _DomainNodeReadCase(role=UserRole.ADMIN, requested_domain_name=_OTHER_DOMAIN_NAME),
            _DomainNodeReadCase(role=UserRole.SUPERADMIN, requested_domain_name="no-such-domain"),
        ],
        ids=lambda case: f"{case.role.value}-{case.requested_domain_name}",
    )
    async def test_returns_none_for_domain_outside_caller_permission(
        self,
        resolve_info_of_caller: MagicMock,
        case: _DomainNodeReadCase,
    ) -> None:
        domain_node = await DomainNode.get_node_by_name(
            resolve_info_of_caller,
            case.requested_domain_name,
            DomainPermission.READ_ATTRIBUTE,
        )

        assert domain_node is None


class TestScalingGroupNodeFromRow:
    @pytest.fixture
    def scaling_group_row_holding_wsproxy_token(self) -> MagicMock:
        return MagicMock(spec=ScalingGroupRow, wsproxy_api_token="wsproxy-secret")

    def test_does_not_expose_wsproxy_api_token(
        self,
        scaling_group_row_holding_wsproxy_token: MagicMock,
    ) -> None:
        scaling_group_node = ScalingGroupNode.from_row(
            MagicMock(),
            scaling_group_row_holding_wsproxy_token,
        )

        assert "wsproxy_api_token" not in ScalingGroupNode._meta.fields
        assert not hasattr(scaling_group_node, "wsproxy_api_token")
