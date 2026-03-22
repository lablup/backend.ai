"""
Common types for prometheus_query_preset DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    # Enums
    "OrderDirection",
    "QueryDefinitionOrderField",
    # Sub-models
    "QueryDefinitionOptionsInfo",
    "MetricLabelEntryInfo",
    "MetricValueInfo",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class QueryDefinitionOrderField(StrEnum):
    """Fields available for ordering prometheus query definitions."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class QueryDefinitionOptionsInfo(BaseResponseModel):
    """Options embedded in a query definition response."""

    filter_labels: list[str] = Field(description="Allowed filter label keys")
    group_labels: list[str] = Field(description="Allowed group-by label keys")


class MetricLabelEntryInfo(BaseResponseModel):
    """A key-value label entry in an execute response."""

    key: str = Field(description="Label key")
    value: str = Field(description="Label value")


class MetricValueInfo(BaseResponseModel):
    """A single (timestamp, value) data point from Prometheus."""

    timestamp: float = Field(description="Unix timestamp of the data point")
    value: str = Field(description="Metric value as a string to preserve precision")
