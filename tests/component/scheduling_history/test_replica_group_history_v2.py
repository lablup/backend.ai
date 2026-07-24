"""Component tests for the replica-group scheduling-history REST v2 endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchReplicaGroupHistoriesInput,
    ScopedSearchReplicaGroupHistoriesInput,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    SearchReplicaGroupHistoriesPayload,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    ReplicaGroupHistoryScopeDTO,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID

if TYPE_CHECKING:
    from tests.component.scheduling_history.conftest import ReplicaGroupHistorySeed


class TestAdminSearchReplicaGroupHistories:
    """``/replica-groups/admin/search``."""

    async def test_returns_seeded_rows(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        result = await admin_v2_registry.scheduling_history.admin_search_replica_group_history(
            AdminSearchReplicaGroupHistoriesInput()
        )

        assert isinstance(result, SearchReplicaGroupHistoriesPayload)
        found = {item.id for item in result.items}
        assert set(replica_group_history_seed.lifecycle_history_ids) <= found
        assert replica_group_history_seed.scaling_history_id in found
        assert replica_group_history_seed.other_group_history_id in found

    async def test_regular_user_is_rejected(
        self,
        user_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.scheduling_history.admin_search_replica_group_history(
                AdminSearchReplicaGroupHistoriesInput()
            )


class TestScopedSearchReplicaGroupHistories:
    """``/replica-groups/scoped/search``."""

    async def test_returns_only_the_scoped_replica_group(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        result = await admin_v2_registry.scheduling_history.scoped_search_replica_group_history(
            ScopedSearchReplicaGroupHistoriesInput(
                scope=ReplicaGroupHistoryScopeDTO(
                    replica_group=[UUIDScope(value=replica_group_history_seed.replica_group_id)]
                ),
            )
        )

        assert isinstance(result, SearchReplicaGroupHistoriesPayload)
        returned = {item.id for item in result.items}
        assert returned == {
            *replica_group_history_seed.lifecycle_history_ids,
            replica_group_history_seed.scaling_history_id,
        }
        assert replica_group_history_seed.other_group_history_id not in returned

    async def test_unknown_replica_group_is_rejected(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_v2_registry.scheduling_history.scoped_search_replica_group_history(
                ScopedSearchReplicaGroupHistoriesInput(
                    scope=ReplicaGroupHistoryScopeDTO(
                        replica_group=[UUIDScope(value=ReplicaGroupID(uuid.uuid4()))]
                    ),
                )
            )

    async def test_returns_every_replica_group_under_the_deployment(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        result = await admin_v2_registry.scheduling_history.scoped_search_replica_group_history(
            ScopedSearchReplicaGroupHistoriesInput(
                scope=ReplicaGroupHistoryScopeDTO(
                    deployment=[UUIDScope(value=replica_group_history_seed.deployment_id)]
                ),
            )
        )

        assert isinstance(result, SearchReplicaGroupHistoriesPayload)
        returned = {item.id for item in result.items}
        assert returned == {
            *replica_group_history_seed.lifecycle_history_ids,
            replica_group_history_seed.scaling_history_id,
            replica_group_history_seed.other_group_history_id,
        }

    async def test_unknown_deployment_is_rejected(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_v2_registry.scheduling_history.scoped_search_replica_group_history(
                ScopedSearchReplicaGroupHistoriesInput(
                    scope=ReplicaGroupHistoryScopeDTO(
                        deployment=[UUIDScope(value=DeploymentID(uuid.uuid4()))]
                    ),
                )
            )

    async def test_cursor_pagination_is_applied(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        result = await admin_v2_registry.scheduling_history.scoped_search_replica_group_history(
            ScopedSearchReplicaGroupHistoriesInput(
                scope=ReplicaGroupHistoryScopeDTO(
                    replica_group=[UUIDScope(value=replica_group_history_seed.replica_group_id)]
                ),
                first=2,
            )
        )

        assert len(result.items) == 2
        assert result.has_next_page is True
