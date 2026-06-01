"""Component tests for the v2 prometheus query preset preview endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.clients.prometheus.response import (
    PrometheusQueryData,
    PrometheusResponse,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    PreviewQueryDefinitionInput,
)
from ai.backend.common.exception import FailedToGetMetric, PrometheusQueryEvaluationFailed


class TestPrometheusQueryPresetPreview:
    @pytest.mark.parametrize(
        ("query_template", "result_type"),
        [
            # Instant vector wrapping a range vector (typical preset shape).
            ("sum(rate(metric{{{labels}}}[{window}]))", "vector"),
            # Plain instant vector.
            ("metric{{{labels}}}", "vector"),
            # Raw range vector — accepted by query_instant, returns matrix.
            ("metric{{{labels}}}[{window}]", "matrix"),
        ],
    )
    async def test_returns_prometheus_response(
        self,
        admin_v2_registry: V2ClientRegistry,
        prometheus_client_mock: MagicMock,
        query_template: str,
        result_type: str,
    ) -> None:
        prometheus_client_mock.preview_query_template = AsyncMock(
            return_value=PrometheusResponse(
                status="success",
                data=PrometheusQueryData(result_type=result_type, result=[]),
            )
        )

        result = await admin_v2_registry.prometheus_query_preset.admin_preview(
            PreviewQueryDefinitionInput(query_template=query_template),
        )

        assert result.status == "success"
        assert result.data.result_type == result_type
        prometheus_client_mock.preview_query_template.assert_called_once()

    async def test_propagates_prometheus_error(
        self,
        admin_v2_registry: V2ClientRegistry,
        prometheus_client_mock: MagicMock,
    ) -> None:
        prometheus_client_mock.preview_query_template = AsyncMock(
            side_effect=FailedToGetMetric('parse error: unexpected "}" (status=400, path=query)'),
        )

        with pytest.raises(BackendAPIError) as exc_info:
            await admin_v2_registry.prometheus_query_preset.admin_preview(
                PreviewQueryDefinitionInput(query_template="sum({invalid_placeholder})"),
            )
        assert exc_info.value.data["type"] == PrometheusQueryEvaluationFailed.error_type
