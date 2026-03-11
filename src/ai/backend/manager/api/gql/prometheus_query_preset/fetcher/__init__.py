"""Prometheus query preset GQL fetcher functions."""

from .preset import (
    fetch_prometheus_query_preset,
    fetch_prometheus_query_preset_result,
    fetch_prometheus_query_presets,
)

__all__ = [
    "fetch_prometheus_query_preset",
    "fetch_prometheus_query_presets",
    "fetch_prometheus_query_preset_result",
]
