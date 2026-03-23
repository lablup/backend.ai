from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar

from ai.backend.common.metrics.metric import DomainType, LayerMetricObserver, LayerType
from ai.backend.common.resilience.policy import Policy
from ai.backend.common.resilience.resilience import get_current_operation
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class MetricArgs:
    """Arguments for MetricPolicy."""

    domain: DomainType
    layer: LayerType


class MetricPolicy(Policy):
    """
    Metric policy that collects execution metrics.

    Integrates with LayerMetricObserver to track:
    - Operation triggers
    - Success/failure counts
    - Execution duration

    The operation name is automatically retrieved from the resilience context
    set by the Resilience.apply() decorator.

    All metric recording is best-effort: failures (e.g., corrupted prometheus
    mmap files after OS sleep/wake) are logged and suppressed so they never
    interfere with the actual operation or trigger retries.
    """

    _domain: DomainType
    _layer: LayerType
    _observer: LayerMetricObserver

    def __init__(self, args: MetricArgs) -> None:
        """
        Initialize MetricPolicy.

        Args:
            args: Metric arguments (domain and layer)

        Notes:
            The operation name is not specified here. Instead, it is automatically
            retrieved from the resilience context when the policy executes.
        """
        self._domain = args.domain
        self._layer = args.layer
        self._observer = LayerMetricObserver.instance()
        self._metric_error_logged = False

    def _safe_observe(self, fn: Callable[[], None]) -> bool:
        """Call a metric-recording function, suppressing any errors.

        Returns True if the function executed successfully, False otherwise.
        """
        try:
            fn()
            return True
        except Exception:
            if not self._metric_error_logged:
                log.warning(
                    "Failed to record metric (domain={}, layer={})",
                    self._domain,
                    self._layer,
                    exc_info=True,
                )
                self._metric_error_logged = True
            return False

    async def execute(
        self,
        next_call: Callable[P, Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        """
        Execute with metric collection.

        Tracks operation trigger, success/failure, and duration.
        The operation name is retrieved from the resilience context.
        """
        # Get operation name from context
        operation = get_current_operation()
        if not operation:
            log.warning("No operation name found in resilience context, using 'unknown'")
            operation = "unknown"

        log.trace("Metric tracking for operation: {}", operation)
        start = time.perf_counter()

        triggered = self._safe_observe(
            lambda: self._observer.observe_layer_operation_triggered(
                domain=self._domain,
                layer=self._layer,
                operation=operation,
            )
        )

        try:
            result = await next_call(*args, **kwargs)
            # Only record completion if the trigger was recorded, to avoid
            # decrementing the in-flight gauge below zero.
            if triggered:
                self._safe_observe(
                    lambda: self._observer.observe_layer_operation(
                        domain=self._domain,
                        layer=self._layer,
                        operation=operation,
                        duration=time.perf_counter() - start,
                        exception=None,
                    )
                )
            return result
        except BaseException as exc:
            caught = exc
            if triggered:
                self._safe_observe(
                    lambda: self._observer.observe_layer_operation(
                        domain=self._domain,
                        layer=self._layer,
                        operation=operation,
                        duration=time.perf_counter() - start,
                        exception=caught,
                    )
                )
            raise
