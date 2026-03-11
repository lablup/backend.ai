"""Client SDK functions for prometheus query preset system."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from ai.backend.client.request import Request

from .base import BaseFunction, api_function

__all__ = ("PrometheusQueryPreset",)

_BASE_PATH = "/resource/prometheus-query-definitions"


class PrometheusQueryPreset(BaseFunction):
    """
    Provides functions to interact with prometheus query presets.
    All operations require superadmin privileges.
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
        filter_labels: list[str] | None = None,
        group_labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new prometheus query preset."""
        body: dict[str, Any] = {
            "name": name,
            "metric_name": metric_name,
            "query_template": query_template,
            "options": {
                "filter_labels": filter_labels or [],
                "group_labels": group_labels or [],
            },
        }
        if time_window is not None:
            body["time_window"] = time_window
        rqst = Request("POST", _BASE_PATH)
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return cast(dict[str, Any], data["item"])

    @api_function
    @classmethod
    async def search(
        cls,
        *,
        filter_name: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search prometheus query presets with optional filters and pagination."""
        body: dict[str, Any] = {
            "offset": offset,
            "limit": limit,
        }
        if filter_name is not None:
            body["filter"] = {"name": {"contains": filter_name}}
        rqst = Request("POST", f"{_BASE_PATH}/search")
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return data

    @api_function
    @classmethod
    async def get(cls, preset_id: UUID) -> dict[str, Any]:
        """Get a prometheus query preset by ID."""
        rqst = Request("GET", f"{_BASE_PATH}/{preset_id}")
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return cast(dict[str, Any], data["item"])

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
        filter_labels: list[str] | None = None,
        group_labels: list[str] | None = None,
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
        options: dict[str, Any] = {}
        if filter_labels is not None:
            options["filter_labels"] = filter_labels
        if group_labels is not None:
            options["group_labels"] = group_labels
        if options:
            body["options"] = options
        rqst = Request("PATCH", f"{_BASE_PATH}/{preset_id}")
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return cast(dict[str, Any], data["item"])

    @api_function
    @classmethod
    async def delete(cls, preset_id: UUID) -> dict[str, Any]:
        """Delete a prometheus query preset."""
        rqst = Request("DELETE", f"{_BASE_PATH}/{preset_id}")
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return data

    @api_function
    @classmethod
    async def execute(
        cls,
        preset_id: UUID,
        *,
        filter_labels: list[dict[str, str]] | None = None,
        group_labels: list[str] | None = None,
        time_window: str | None = None,
        time_range: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute a prometheus query preset.

        If *time_range* is ``None``, an instant query is executed.
        """
        body: dict[str, Any] = {}
        options: dict[str, Any] = {}
        if filter_labels is not None:
            options["filter_labels"] = filter_labels
        if group_labels is not None:
            options["group_labels"] = group_labels
        if options:
            body["options"] = options
        if time_window is not None:
            body["time_window"] = time_window
        if time_range is not None:
            body["time_range"] = time_range
        rqst = Request("POST", f"{_BASE_PATH}/{preset_id}/execute")
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data: dict[str, Any] = await resp.json()
            return data
