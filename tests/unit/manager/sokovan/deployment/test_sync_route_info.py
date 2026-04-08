"""Tests for DeploymentCoordinator.sync_route_info_to_appproxy."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from ai.backend.common.events.event_types.model_serving.anycast import (
    EndpointRouteListUpdatedEvent,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator


def _make_coordinator(
    *, active_endpoint_ids: list[UUID], update_side_effect: object = None
) -> tuple[DeploymentCoordinator, AsyncMock, AsyncMock]:
    mock_repo = AsyncMock(spec=DeploymentRepository)
    mock_repo.list_active_endpoint_ids = AsyncMock(return_value=active_endpoint_ids)
    if update_side_effect is not None:
        mock_repo.update_endpoint_route_info = AsyncMock(side_effect=update_side_effect)
    else:
        mock_repo.update_endpoint_route_info = AsyncMock()

    mock_event_producer = AsyncMock()

    # DeploymentCoordinator.sync_route_info_to_appproxy only touches
    # _deployment_repository and _event_producer, so we build an instance
    # directly with MagicMock for every other field to avoid DI overhead.
    coordinator = DeploymentCoordinator.__new__(DeploymentCoordinator)
    coordinator._deployment_repository = mock_repo
    coordinator._event_producer = mock_event_producer
    return coordinator, mock_repo, mock_event_producer


class TestSyncRouteInfoToAppproxy:
    async def test_noop_when_no_active_endpoints(self) -> None:
        coordinator, repo, producer = _make_coordinator(active_endpoint_ids=[])

        await coordinator.sync_route_info_to_appproxy()

        repo.update_endpoint_route_info.assert_not_called()
        producer.anycast_event.assert_not_called()

    async def test_pushes_each_active_endpoint(self) -> None:
        endpoint_ids = [uuid4(), uuid4(), uuid4()]
        coordinator, repo, producer = _make_coordinator(active_endpoint_ids=endpoint_ids)

        await coordinator.sync_route_info_to_appproxy()

        assert repo.update_endpoint_route_info.await_count == len(endpoint_ids)
        assert producer.anycast_event.await_count == len(endpoint_ids)

        published_ids = {
            call.args[0].endpoint_id for call in producer.anycast_event.await_args_list
        }
        assert published_ids == set(endpoint_ids)

        for call in producer.anycast_event.await_args_list:
            assert isinstance(call.args[0], EndpointRouteListUpdatedEvent)

    async def test_continues_after_per_endpoint_failure(self) -> None:
        endpoint_ids = [uuid4(), uuid4(), uuid4()]

        # First update raises, second/third succeed. The loop must not bail.
        call_log: list[UUID] = []

        async def update_side_effect(endpoint_id: UUID) -> None:
            call_log.append(endpoint_id)
            if endpoint_id == endpoint_ids[0]:
                raise RuntimeError("redis down")

        coordinator, repo, producer = _make_coordinator(
            active_endpoint_ids=endpoint_ids, update_side_effect=update_side_effect
        )

        await coordinator.sync_route_info_to_appproxy()

        assert call_log == endpoint_ids  # every endpoint was attempted
        # Only the 2 successful endpoints emit anycast events.
        assert producer.anycast_event.await_count == len(endpoint_ids) - 1
        published_ids = {
            call.args[0].endpoint_id for call in producer.anycast_event.await_args_list
        }
        assert published_ids == set(endpoint_ids[1:])
