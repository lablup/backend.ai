from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import uuid4

import pytest

from ai.backend.manager.data.resource.types import ResourceGroupProxyTarget
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import ResourceAllocationRow, ResourceSlotTypeRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.testutils.db import with_tables

_RESOURCE_GROUP_NAME = "default"
_WSPROXY_ADDR = "http://127.0.0.1:5050"
_WSPROXY_API_TOKEN = "coordinator-api-token"


@dataclass(frozen=True)
class _ProxyTargetCase:
    description: str
    wsproxy_addr: str | None
    wsproxy_api_token: str | None
    expected_target: ResourceGroupProxyTarget | None


class TestResourceGroupProxyTarget:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                AgentRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                ProjectRow,
                KeyPairRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> SessionRepository:
        return SessionRepository(
            db_with_cleanup,
            V2DBOpsProvider(db_with_cleanup),
            registry_db_source=ContainerRegistryDBSource(V2DBOpsProvider(db_with_cleanup)),
        )

    @pytest.fixture
    async def resource_group_configured_by_case(
        self, db_with_cleanup: ExtendedAsyncSAEngine, case: _ProxyTargetCase
    ) -> str:
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ResourceGroupRow(
                    id=uuid4(),
                    name=_RESOURCE_GROUP_NAME,
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                    wsproxy_addr=case.wsproxy_addr,
                    wsproxy_api_token=case.wsproxy_api_token,
                )
            )
        return _RESOURCE_GROUP_NAME

    @pytest.mark.parametrize(
        "case",
        [
            _ProxyTargetCase(
                description="address_and_token",
                wsproxy_addr=_WSPROXY_ADDR,
                wsproxy_api_token=_WSPROXY_API_TOKEN,
                expected_target=ResourceGroupProxyTarget(
                    addr=_WSPROXY_ADDR,
                    api_token=_WSPROXY_API_TOKEN,
                ),
            ),
            _ProxyTargetCase(
                description="no_address",
                wsproxy_addr=None,
                wsproxy_api_token=_WSPROXY_API_TOKEN,
                expected_target=None,
            ),
            _ProxyTargetCase(
                description="no_token",
                wsproxy_addr=_WSPROXY_ADDR,
                wsproxy_api_token=None,
                expected_target=ResourceGroupProxyTarget(addr=_WSPROXY_ADDR, api_token=""),
            ),
            _ProxyTargetCase(
                description="empty_token",
                wsproxy_addr=_WSPROXY_ADDR,
                wsproxy_api_token="",
                expected_target=ResourceGroupProxyTarget(addr=_WSPROXY_ADDR, api_token=""),
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_returns_target_only_when_address_is_set(
        self,
        repository: SessionRepository,
        resource_group_configured_by_case: str,
        case: _ProxyTargetCase,
    ) -> None:
        target = await repository.resource_group_proxy_target(resource_group_configured_by_case)

        assert target == case.expected_target

    async def test_returns_none_for_unknown_resource_group(
        self, repository: SessionRepository
    ) -> None:
        target = await repository.resource_group_proxy_target("unknown")

        assert target is None
