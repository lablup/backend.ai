import inspect
from typing import Callable, Iterable

from aiohttp import web


@web.middleware
async def security_policy_middleware(request: web.Request, handler) -> web.StreamResponse:
    security_policy: SecurityPolicy = request.app["security_policy"]
    security_policy.check_request(request)
    if inspect.iscoroutinefunction(handler):
        response = await handler(request)
    else:
        response = handler(request)
    return security_policy.apply_response_policies(response)


class SecurityPolicy:
    def __init__(
        self,
        request_policies: Iterable[Callable[[web.Request], None]],
        response_policies: Iterable[Callable[[web.Response], web.Response]],
    ):
        self.request_policies = request_policies
        self.response_policies = response_policies

    @classmethod
    def default_policy(cls) -> "SecurityPolicy":
        request_policies = [reject_metadata_local_link]
        response_policies = [add_self_content_security_policy, set_content_type_nosniff]
        return cls(request_policies, response_policies)

    def check_request(self, request: web.Request):
        for policy in self.request_policies:
            policy(request)

    def apply_response_policies(self, response: web.Response) -> web.Response:
        for policy in self.response_policies:
            response = policy(response)
        return response


def reject_metadata_local_link(request: web.Request):
    if request.host == "169.254.169.254":
        raise web.HTTPForbidden()


def add_self_content_security_policy(response: web.Response) -> web.Response:
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    return response


def set_content_type_nosniff(response: web.Response) -> web.Response:
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
