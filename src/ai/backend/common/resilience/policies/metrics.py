from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar

from ai.backend.common.metrics.metric import DomainType, LayerMetricObserver, LayerType
from ai.backend.logging import BraceStyleAdapter

from ..policy import Policy

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class MetricArgs:
    """Arguments for MetricPolicy."""

    domain: DomainType
    layer: LayerType
    operation: str


class MetricPolicy(Policy):
    """
    Metric policy that collects execution metrics.

    Integrates with LayerMetricObserver to track:
    - Operation triggers
    - Success/failure counts
    - Execution duration
    """

    _domain: DomainType
    _layer: LayerType
    _operation: str
    _observer: LayerMetricObserver

    def __init__(self, args: MetricArgs) -> None:
        """
        Initialize MetricPolicy.

        Args:
            args: Metric arguments
        """
        self._domain = args.domain
        self._layer = args.layer
        self._operation = args.operation
        self._observer = LayerMetricObserver.instance()

    async def execute(
        self,
        next_call: Callable[P, Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        """
        Execute with metric collection.

        Tracks operation trigger, success/failure, and duration.
        """
        log.trace("Metric tracking for operation: {}", self._operation)
        start = time.perf_counter()

        # Record operation triggered
        self._observer.observe_layer_operation_triggered(
            domain=self._domain,
            layer=self._layer,
            operation=self._operation,
        )

        try:
            result = await next_call(*args, **kwargs)
            # Record success
            self._observer.observe_layer_operation(
                domain=self._domain,
                layer=self._layer,
                operation=self._operation,
                success=True,
                duration=time.perf_counter() - start,
            )
            return result
        except Exception:
            # Record failure
            self._observer.observe_layer_operation(
                domain=self._domain,
                layer=self._layer,
                operation=self._operation,
                success=False,
                duration=time.perf_counter() - start,
            )
            raise
