"""Tests for DeploymentRepository.update_endpoint_route_info_for_termination."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository


def _make_repository(
    *,
    connection_info: dict[str, Any] | None = None,
    health_check_config: ModelHealthCheck | None = None,
    health_check_side_effect: Exception | None = None,
) -> tuple[DeploymentRepository, AsyncMock, AsyncMock]:
    mock_db_source = AsyncMock()
    mock_db_source.generate_route_connection_info = AsyncMock(
        return_value=connection_info or {"routes": []}
    )
    if health_check_side_effect is not None:
        mock_db_source.get_endpoint_health_check_config = AsyncMock(
            side_effect=health_check_side_effect
        )
    else:
        mock_db_source.get_endpoint_health_check_config = AsyncMock(
            return_value=health_check_config
        )

    mock_valkey_live = AsyncMock()

    repo = DeploymentRepository.__new__(DeploymentRepository)
    repo._db_source = mock_db_source
    repo._valkey_live = mock_valkey_live
    return repo, mock_db_source, mock_valkey_live


class TestUpdateEndpointRouteInfoForTermination:
    async def test_passes_health_check_config_when_available(self) -> None:
        health_check = ModelHealthCheck(path="/health")
        endpoint_id = uuid4()
        repo, db_source, valkey_live = _make_repository(
            connection_info={"routes": [{"id": str(endpoint_id)}]},
            health_check_config=health_check,
        )

        await repo.update_endpoint_route_info_for_termination(endpoint_id)

        valkey_live.update_appproxy_redis_info.assert_awaited_once_with(
            endpoint_id,
            {"routes": [{"id": str(endpoint_id)}]},
            health_check,
        )

    async def test_proceeds_with_none_when_health_check_lookup_fails(self) -> None:
        endpoint_id = uuid4()
        repo, db_source, valkey_live = _make_repository(
            connection_info={"routes": []},
            health_check_side_effect=InvalidAPIParameters(
                "Model definition YAML file model-definition.yaml not found"
            ),
        )

        await repo.update_endpoint_route_info_for_termination(endpoint_id)

        valkey_live.update_appproxy_redis_info.assert_awaited_once_with(
            endpoint_id,
            {"routes": []},
            None,
        )

    async def test_proceeds_with_none_on_unexpected_error(self) -> None:
        endpoint_id = uuid4()
        repo, db_source, valkey_live = _make_repository(
            health_check_side_effect=RuntimeError("storage unreachable"),
        )

        await repo.update_endpoint_route_info_for_termination(endpoint_id)

        valkey_live.update_appproxy_redis_info.assert_awaited_once()
        call_args = valkey_live.update_appproxy_redis_info.await_args
        assert call_args[0][2] is None  # health_check_config

    async def test_logs_warning_on_health_check_failure(self) -> None:
        endpoint_id = uuid4()
        repo, db_source, valkey_live = _make_repository(
            health_check_side_effect=InvalidAPIParameters("file not found"),
        )

        with patch("ai.backend.manager.repositories.deployment.repository.log") as mock_log:
            await repo.update_endpoint_route_info_for_termination(endpoint_id)

            mock_log.warning.assert_called_once()
            assert "termination" in mock_log.warning.call_args[0][0].lower()
