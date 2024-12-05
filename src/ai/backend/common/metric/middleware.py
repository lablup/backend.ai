import time
from typing import Protocol

from aiohttp import web
from aiohttp.typedefs import Handler


class APIMetricProtocol(Protocol):
    def update_request_metric(
        self, *, method: str, endpoint: str, status_code: int, duration: float
    ) -> None: ...


def build_metric_middleware(metric: APIMetricProtocol):
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
            raise e
        except Exception as e:
            status_code = 500
            raise e
        else:
            return resp
        finally:
            end = time.perf_counter()
            elapsed = end - start
            metric.update_request_metric(
                method=method, endpoint=endpoint, status_code=status_code, duration=elapsed
            )

    return metric_middleware
