import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Final, Protocol

from aiohttp import web
from aiohttp.typedefs import Handler, Middleware

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

SYSTEM_METRIC_UPDATE_INTERVAL: Final = 10.0


class APIMetricObserverProtocol(Protocol):
    def observe_request(
        self,
        *,
        method: str,
        endpoint: str,
        error_code: ErrorCode | None,
        status_code: int,
        duration: float,
    ) -> None: ...


class PrometheusAPIMetric(Protocol):
    def to_prometheus(self) -> str: ...


class SystemMetricObserverProtocol(Protocol):
    def observe(self) -> None: ...


class PrometheusMetricsGenerator:
    """
    Runs `to_prometheus()` in a thread so the event loop keeps serving requests.
    Callers arriving during a generation share its result.
    """

    _metric: PrometheusAPIMetric
    _in_flight: asyncio.Future[str] | None

    def __init__(self, metric: PrometheusAPIMetric) -> None:
        self._metric = metric
        self._in_flight = None

    async def generate(self) -> str:
        if self._in_flight is None:
            in_flight = asyncio.ensure_future(asyncio.to_thread(self._metric.to_prometheus))
            in_flight.add_done_callback(self._clear_in_flight)
            self._in_flight = in_flight
        return await asyncio.shield(self._in_flight)

    def _clear_in_flight(self, _in_flight: asyncio.Future[str]) -> None:
        self._in_flight = None


class SystemMetricUpdater:
    """Updates the system metrics of this process periodically on the event loop."""

    _observer: SystemMetricObserverProtocol
    _interval: float
    _task: asyncio.Task[None] | None

    def __init__(
        self,
        observer: SystemMetricObserverProtocol,
        interval: float = SYSTEM_METRIC_UPDATE_INTERVAL,
    ) -> None:
        self._observer = observer
        self._interval = interval
        self._task = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._update_periodically())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def cleanup_ctx(self, _app: web.Application) -> AsyncIterator[None]:
        self.start()
        yield
        await self.stop()

    async def _update_periodically(self) -> None:
        while True:
            try:
                self._observer.observe()
            except Exception:
                log.warning("failed to update system metrics", exc_info=True)
            await asyncio.sleep(self._interval)


def build_api_metric_middleware(metric: APIMetricObserverProtocol) -> Middleware:
    @web.middleware
    async def metric_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        # normalize path
        method = request.method
        endpoint = getattr(request.match_info.route.resource, "canonical", request.path)
        status_code = -1
        start = time.perf_counter()
        error_code: ErrorCode | None = None
        try:
            resp = await handler(request)
            status_code = resp.status
        except BackendAIError as e:
            status_code = e.status_code
            error_code = e.error_code()
            raise
        except web.HTTPError as e:
            status_code = e.status_code
            error_code = ErrorCode.default()
            raise
        except Exception:
            status_code = 500
            error_code = ErrorCode.default()
            raise
        else:
            return resp
        finally:
            end = time.perf_counter()
            elapsed = end - start
            try:
                metric.observe_request(
                    method=method,
                    endpoint=endpoint,
                    error_code=error_code,
                    status_code=status_code,
                    duration=elapsed,
                )
            except Exception:
                # Defense-in-depth: safe metric types handle mmap errors
                # internally, but this ensures metric failures never mask
                # the original request exception in the finally block.
                pass

    return metric_middleware


def build_prometheus_metrics_handler(prometheus_metric: PrometheusAPIMetric) -> Handler:
    generator = PrometheusMetricsGenerator(prometheus_metric)

    async def prometheus_metrics_handler(_request: web.Request) -> web.Response:
        """
        Returns the Prometheus metrics.
        """
        metrics = await generator.generate()
        return web.Response(text=metrics, content_type="text/plain")

    return prometheus_metrics_handler
