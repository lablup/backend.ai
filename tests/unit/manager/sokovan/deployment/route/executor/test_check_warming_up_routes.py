"""Unit tests for ``RouteExecutor.check_warming_up_routes``.

Covers the WARMING_UP graduation pipeline:
- WU-001: health check disabled → ready immediately
- WU-002: health check enabled & probe passed → ready
- WU-003: health check enabled & probe missing/not yet passed → stays in WARMING_UP
- WU-004: dead session → in errors (handler maps to FAILED_TO_START)
- WU-005: revision row vanished → not promoted (left for route_eviction)
- WU-006: empty route list → empty result
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule import RouteHealthRecord
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import RouteHealthStatus, RouteStatus
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.recorder.context import RouteRecorderContext


def _warming_up_route(
    *,
    revision_id: DeploymentRevisionID | None = None,
) -> RouteData:
    """WARMING_UP route with replica info pre-populated."""
    return RouteData(
        route_id=uuid4(),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.WARMING_UP,
        health_status=RouteHealthStatus.NOT_CHECKED,
        traffic_ratio=1.0,
        created_at=datetime.now(tzutc()),
        revision_id=revision_id or DeploymentRevisionID(uuid4()),
        replica_host="10.0.0.1",
        replica_port=8000,
    )


def _live_session_status() -> MagicMock:
    status = MagicMock()
    status.is_terminal = MagicMock(return_value=False)
    status.value = "RUNNING"
    return status


def _terminal_session_status() -> MagicMock:
    status = MagicMock()
    status.is_terminal = MagicMock(return_value=True)
    status.value = "TERMINATED"
    return status


def _stub_health_record(
    route: RouteData,
    *,
    agent_healthy: bool = False,
    agent_last_check: int = 0,
) -> RouteHealthRecord:
    """Stub RouteHealthRecord so _ensure_health_records sees the record as present and skips re-init."""
    return RouteHealthRecord(
        route_id=str(route.route_id),
        created_at=4900,
        initial_delay_until=4960,
        health_path="/health",
        inference_port=8000,
        replica_host="10.0.0.1",
        agent_healthy=agent_healthy,
        agent_last_check=agent_last_check,
    )


def _wire_live_session(
    mock_deployment_repo: AsyncMock,
    routes: list[RouteData],
) -> None:
    mock_deployment_repo.fetch_session_statuses_by_route_ids.return_value = {
        r.route_id: _live_session_status() for r in routes
    }


class TestCheckWarmingUpRoutes:
    """Tests for the WARMING_UP graduation pipeline."""

    async def test_empty_input_returns_empty_result(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """WU-006: Empty route list short-circuits without touching the repo."""
        result = await route_executor.check_warming_up_routes([])

        assert result.successes == []
        assert result.errors == []
        mock_deployment_repo.fetch_session_statuses_by_route_ids.assert_not_awaited()

    async def test_health_check_disabled_promotes_immediately(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """WU-001: Endpoint with no health_check config → ready in the first cycle."""
        route = _warming_up_route()
        _wire_live_session(mock_deployment_repo, [route])
        mock_valkey_schedule.get_route_health_records_batch.return_value = {
            str(route.route_id): _stub_health_record(route),
        }
        mock_deployment_repo.fetch_health_check_configs_by_revision_ids.return_value = {
            route.revision_id: None,
        }

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_warming_up_routes([route])

        assert [r.route_id for r in result.successes] == [route.route_id]
        assert result.errors == []

    async def test_health_enabled_and_probe_passed_promotes(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """WU-002: Health enabled and a passing probe is recorded → ready."""
        route = _warming_up_route()
        _wire_live_session(mock_deployment_repo, [route])
        mock_deployment_repo.fetch_health_check_configs_by_revision_ids.return_value = {
            route.revision_id: ModelHealthCheck(path="/health", initial_delay=60.0),
        }

        current_time = 5000
        passing_record = _stub_health_record(
            route,
            agent_healthy=True,
            agent_last_check=current_time - 5,
        )
        mock_valkey_schedule.get_route_health_records_batch.return_value = {
            str(route.route_id): passing_record,
        }
        mock_valkey_schedule.get_redis_time.return_value = current_time

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_warming_up_routes([route])

        assert [r.route_id for r in result.successes] == [route.route_id]
        assert result.errors == []

    async def test_health_enabled_but_probe_missing_stays_in_warming_up(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """WU-003: Health enabled but no probe yet → not promoted, no error."""
        route = _warming_up_route()
        _wire_live_session(mock_deployment_repo, [route])
        mock_deployment_repo.fetch_health_check_configs_by_revision_ids.return_value = {
            route.revision_id: ModelHealthCheck(path="/health", initial_delay=60.0),
        }
        # Health record exists but no probe has run (last_check=0).
        mock_valkey_schedule.get_route_health_records_batch.return_value = {
            str(route.route_id): _stub_health_record(route),
        }
        mock_valkey_schedule.get_redis_time.return_value = 5000

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_warming_up_routes([route])

        assert result.successes == []
        assert result.errors == []

    async def test_dead_session_goes_to_errors(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """WU-004: Terminal session yields an error so the handler can fail to FAILED_TO_START."""
        route = _warming_up_route()
        mock_deployment_repo.fetch_session_statuses_by_route_ids.return_value = {
            route.route_id: _terminal_session_status(),
        }

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_warming_up_routes([route])

        assert result.successes == []
        assert len(result.errors) == 1
        assert result.errors[0].route_info.route_id == route.route_id

    async def test_missing_revision_is_skipped_not_promoted(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """WU-005: Revision row missing from health-config map → leave for route_eviction."""
        route = _warming_up_route()
        _wire_live_session(mock_deployment_repo, [route])
        mock_valkey_schedule.get_route_health_records_batch.return_value = {
            str(route.route_id): _stub_health_record(route),
        }
        # Repo returns an empty map (revision row vanished between fetch and classify).
        mock_deployment_repo.fetch_health_check_configs_by_revision_ids.return_value = {}

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_warming_up_routes([route])

        assert result.successes == []
        assert result.errors == []

    async def test_mixed_routes_classified_correctly(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """A live + a dead route are classified into successes / errors respectively."""
        live_route = _warming_up_route()
        dead_route = _warming_up_route()
        mock_deployment_repo.fetch_session_statuses_by_route_ids.return_value = {
            live_route.route_id: _live_session_status(),
            dead_route.route_id: _terminal_session_status(),
        }
        mock_valkey_schedule.get_route_health_records_batch.return_value = {
            str(live_route.route_id): _stub_health_record(live_route),
        }
        mock_deployment_repo.fetch_health_check_configs_by_revision_ids.return_value = {
            live_route.revision_id: None,  # disabled → live route promotes
        }

        with RouteRecorderContext.scope(
            "test", entity_ids=[live_route.route_id, dead_route.route_id]
        ):
            result = await route_executor.check_warming_up_routes([live_route, dead_route])

        assert [r.route_id for r in result.successes] == [live_route.route_id]
        assert [e.route_info.route_id for e in result.errors] == [dead_route.route_id]
