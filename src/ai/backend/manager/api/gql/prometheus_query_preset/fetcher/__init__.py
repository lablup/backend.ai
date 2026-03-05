"""Prometheus query preset GQL fetcher functions."""

from .preset import (
    fetch_admin_prometheus_query_preset,
    fetch_admin_prometheus_query_presets,
    fetch_prometheus_query_preset_result,
)

__all__ = [
    "fetch_admin_prometheus_query_preset",
    "fetch_admin_prometheus_query_presets",
    "fetch_prometheus_query_preset_result",
]
