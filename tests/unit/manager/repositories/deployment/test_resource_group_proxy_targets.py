from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment.db_source.db_source import DeploymentDBSource
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.testutils.db import with_tables

PROXY_GROUP = "proxy-group"
BARE_GROUP = "bare-group"


class TestFetchResourceGroupProxyTargets:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [ResourceGroupRow]):
            async with database_connection.begin_session() as sess:
                for name, addr, token in (
                    (PROXY_GROUP, "http://appproxy:5000", "token"),
                    (BARE_GROUP, None, None),
                ):
                    sess.add(
                        ResourceGroupRow(
                            id=uuid.uuid4(),
                            name=name,
                            description=None,
                            is_active=True,
                            is_public=True,
                            driver="static",
                            driver_opts={},
                            scheduler="fifo",
                            use_host_network=False,
                            wsproxy_addr=addr,
                            wsproxy_api_token=token,
                        )
                    )
            yield database_connection

    @pytest.fixture
    def db_source(self, db: ExtendedAsyncSAEngine) -> DeploymentDBSource:
        return DeploymentDBSource(
            db=db,
            reconcile_ops_provider=ReconcileOpsProvider(db),
            storage_manager=MagicMock(spec=StorageSessionManager),
        )

    async def test_empty_set_returns_empty_mapping(self, db_source: DeploymentDBSource) -> None:
        assert await db_source.fetch_resource_group_proxy_targets(set()) == {}

    async def test_returns_target_with_proxy_configured(
        self, db_source: DeploymentDBSource
    ) -> None:
        targets = await db_source.fetch_resource_group_proxy_targets({PROXY_GROUP, BARE_GROUP})

        target = targets[PROXY_GROUP]
        assert target is not None
        assert (target.addr, target.api_token) == ("http://appproxy:5000", "token")
        assert targets.get(BARE_GROUP) is None

    async def test_unknown_resource_group_raises(self, db_source: DeploymentDBSource) -> None:
        with pytest.raises(ResourceGroupNotFound):
            await db_source.fetch_resource_group_proxy_targets({"missing-group"})
