import time
from typing import Protocol

from aiohttp import web
from aiohttp.typedefs import Handler, Middleware


class APIMetricObserverProtocol(Protocol):
    def observe_request(
        self, *, method: str, endpoint: str, status_code: int, duration: float
    ) -> None: ...


class PrometheusAPIMetric(Protocol):
    def to_prometheus(self) -> str: ...


def build_api_metric_middleware(metric: APIMetricObserverProtocol) -> Middleware:
    @web.middleware
    async def metric_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        # normalize path
        method = request.method
        endpoint = getattr(request.match_info.route.resource, "canonical", request.path)
        status_code = -1
        start = time.perf_counter()
        try:
            resp = await handler(request)
            status_code = resp.status
        except web.HTTPError as e:
            status_code = e.status_code
            raise
        except Exception:
            status_code = 500
            raise
        else:
            return resp
        finally:
            end = time.perf_counter()
            elapsed = end - start
            metric.observe_request(
                method=method, endpoint=endpoint, status_code=status_code, duration=elapsed
            )

    return metric_middleware


def build_prometheus_metrics_handler(prometheus_metric: PrometheusAPIMetric) -> Handler:
    async def prometheus_metrics_handler(request: web.Request) -> web.Response:
        """
        Returns the Prometheus metrics.
        """
        metrics = prometheus_metric.to_prometheus()
        return web.Response(text=metrics, content_type="text/plain")

    return prometheus_metrics_handler
