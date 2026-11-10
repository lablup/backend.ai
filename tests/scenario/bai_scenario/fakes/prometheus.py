"""Stand-in for the Prometheus a query preset is run against.

Implements ``PrometheusClient`` without HTTP. Every query is answered with one series
holding one sample, and the sample's value is the PromQL the query asked, so a scenario
reads what reached Prometheus off the answer. The result type is what Prometheus
answers: a matrix for a range query, a vector for an instant one. An empty query is
refused as Prometheus refuses it. The renderer is the real one, so a template the
client could not render is refused here as it is there.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import override

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import (
    MetricResponse,
    MetricResponseInfo,
    PrometheusQueryData,
    PrometheusResponse,
)
from ai.backend.common.exception import FailedToGetMetric
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.clients.prometheus.preset import MetricPreset, PromQLTemplateRenderer

ANSWERED_AT = 1000.0
INSTANT = "vector"
RANGE = "matrix"


@dataclass(frozen=True)
class PrometheusCall:
    method: str
    query: str
    window: str
    labels: Mapping[str, str]
    group_by: frozenset[str]
    time_range: QueryTimeRange | None


def one_sample_of(query: str, result_type: str) -> PrometheusResponse:
    """What the stand-in answers: one series whose one sample carries the query."""
    return PrometheusResponse(
        status="success",
        data=PrometheusQueryData(
            result_type=result_type,
            result=[MetricResponse(metric=MetricResponseInfo(), values=[(ANSWERED_AT, query)])],
        ),
    )


class FakePrometheusClient(PrometheusClient):
    calls: list[PrometheusCall]

    def __init__(self) -> None:
        # The real constructor binds an HTTP client pool; this one holds state instead.
        self.calls = []
        self._template_renderer = PromQLTemplateRenderer()

    @override
    async def execute_preset(
        self,
        preset: MetricPreset,
        *,
        time_range: QueryTimeRange | None,
        time: str | None = None,
    ) -> PrometheusResponse:
        query = self._asked("execute_preset", preset, time_range)
        return one_sample_of(query, RANGE if time_range is not None else INSTANT)

    @override
    async def preview_query_template(
        self,
        query_template: str,
        default_window: str,
    ) -> PrometheusResponse:
        preset = MetricPreset(template=query_template, window=default_window)
        query = self._asked("preview_query_template", preset, None)
        return one_sample_of(query, INSTANT)

    def asked(self) -> tuple[PrometheusCall, ...]:
        """What was queried, in the order it was asked."""
        return tuple(self.calls)

    def _asked(self, method: str, preset: MetricPreset, time_range: QueryTimeRange | None) -> str:
        query = self._template_renderer.render(preset)
        if not query.strip():
            raise FailedToGetMetric(
                'invalid parameter "query": 1:1: parse error: no expression found in input '
                f"(status=400, path={'query_range' if time_range is not None else 'query'})"
            )
        self.calls.append(
            PrometheusCall(
                method=method,
                query=query,
                window=preset.window,
                labels={name: matcher.value for name, matcher in preset.labels.items()},
                group_by=frozenset(preset.group_by),
                time_range=time_range,
            )
        )
        return query
