"""Stand-in for the Prometheus a query preset is run against.

Implements ``PrometheusClient`` without HTTP: every query is answered with the one
sample below, and what each query asked — the rendered PromQL, the window, the label
matchers, the range — is kept so a scenario can read it back. The renderer is the real
one, so a template the client could not render is refused here as it is there.
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
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.clients.prometheus.preset import MetricPreset, PromQLTemplateRenderer

ANSWERED_AT = 1000.0
ANSWERED_VALUE = "1"
ANSWERED_RESULT_TYPE = "vector"


@dataclass(frozen=True)
class PrometheusCall:
    method: str
    query: str
    window: str
    labels: Mapping[str, str]
    group_by: frozenset[str]
    time_range: QueryTimeRange | None


def one_sample() -> PrometheusResponse:
    """What the stand-in answers for every query: one series with one sample."""
    return PrometheusResponse(
        status="success",
        data=PrometheusQueryData(
            result_type=ANSWERED_RESULT_TYPE,
            result=[
                MetricResponse(metric=MetricResponseInfo(), values=[(ANSWERED_AT, ANSWERED_VALUE)])
            ],
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
        self._note("execute_preset", preset, time_range)
        return one_sample()

    @override
    async def preview_query_template(
        self,
        query_template: str,
        default_window: str,
    ) -> PrometheusResponse:
        preset = MetricPreset(template=query_template, window=default_window)
        self._note("preview_query_template", preset, None)
        return one_sample()

    def asked(self) -> tuple[PrometheusCall, ...]:
        """What was queried, in the order it was asked."""
        return tuple(self.calls)

    def _note(self, method: str, preset: MetricPreset, time_range: QueryTimeRange | None) -> None:
        self.calls.append(
            PrometheusCall(
                method=method,
                query=self._template_renderer.render(preset),
                window=preset.window,
                labels={name: matcher.value for name, matcher in preset.labels.items()},
                group_by=frozenset(preset.group_by),
                time_range=time_range,
            )
        )
