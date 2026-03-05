"""Client SDK functions for prometheus query preset system."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from ai.backend.client.request import Request
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import PrometheusQueryRangeResponse

from .base import BaseFunction, api_function

__all__ = ("PrometheusQueryPreset",)


class PrometheusQueryPreset(BaseFunction):
    """
    Provides functions to interact with prometheus query presets.
    Admin CRUD requires superadmin privileges.
    Execute is available to all authenticated users.
    """

    @api_function
    @classmethod
    async def create(
        cls,
        name: str,
        metric_name: str,
        query_template: str,
        *,
        time_window: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new prometheus query preset."""
        body: dict[str, Any] = {
            "name": name,
            "metric_name": metric_name,
            "query_template": query_template,
        }
        if time_window is not None:
            body["time_window"] = time_window
        if options is not None:
            body["options"] = options
        rqst = Request("POST", "/resource/prometheus-query-presets")
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return data

    @api_function
    @classmethod
    async def list_presets(cls) -> list[dict[str, Any]]:
        """List all prometheus query presets."""
        rqst = Request("GET", "/resource/prometheus-query-presets")
        async with rqst.fetch() as resp:
            data: list[dict[str, Any]] = await resp.json()
            return data

    @api_function
    @classmethod
    async def get(cls, preset_id: UUID) -> dict[str, Any]:
        """Get a prometheus query preset by ID."""
        rqst = Request("GET", f"/resource/prometheus-query-presets/{preset_id}")
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return data

    @api_function
    @classmethod
    async def modify(
        cls,
        preset_id: UUID,
        *,
        name: str | None = None,
        metric_name: str | None = None,
        query_template: str | None = None,
        time_window: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Modify an existing prometheus query preset."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if metric_name is not None:
            body["metric_name"] = metric_name
        if query_template is not None:
            body["query_template"] = query_template
        if time_window is not None:
            body["time_window"] = time_window
        if options is not None:
            body["options"] = options
        rqst = Request("PATCH", f"/resource/prometheus-query-presets/{preset_id}")
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return data

    @api_function
    @classmethod
    async def delete(cls, preset_id: UUID) -> dict[str, Any]:
        """Delete a prometheus query preset."""
        rqst = Request("DELETE", f"/resource/prometheus-query-presets/{preset_id}")
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return data

    @api_function
    @classmethod
    async def execute(
        cls,
        preset_id: UUID,
        *,
        start: str,
        end: str,
        step: str,
        labels: list[dict[str, str]] | None = None,
        group_labels: list[str] | None = None,
        window: str | None = None,
    ) -> PrometheusQueryRangeResponse:
        """Execute a prometheus query preset."""
        body: dict[str, Any] = {
            "time_range": QueryTimeRange(start=start, end=end, step=step).model_dump(mode="json"),
        }
        if labels is not None:
            body["labels"] = labels
        if group_labels is not None:
            body["group_labels"] = group_labels
        if window is not None:
            body["window"] = window
        rqst = Request("POST", f"/resource/prometheus-query-presets/{preset_id}/execute")
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data = await resp.json()
            return PrometheusQueryRangeResponse.model_validate(data)
