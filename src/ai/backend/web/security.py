import inspect
from typing import Callable, Iterable, Self

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
    ) -> None:
        self.request_policies = request_policies
        self.response_policies = response_policies

    @classmethod
    def default_policy(cls) -> Self:
        request_policies = [reject_metadata_local_link, reject_access_for_unsafe_file]
        response_policies = [add_self_content_security_policy, set_content_type_nosniff]
        return cls(request_policies, response_policies)

    def check_request(self, request: web.Request) -> None:
        for policy in self.request_policies:
            policy(request)

    def apply_response_policies(self, response: web.Response) -> web.Response:
        for policy in self.response_policies:
            response = policy(response)
        return response


def reject_metadata_local_link(request: web.Request) -> None:
    metadata_local_link_map = {
        "metadata.google.internal": True,
        "169.254.169.254": True,
        "100.100.100.200": True,
        "alibaba.zaproxy.org": True,
        "metadata.oraclecloud.com": True,
    }
    if metadata_local_link_map.get(request.host):
        raise web.HTTPForbidden()


def reject_access_for_unsafe_file(request: web.Request) -> None:
    unsafe_file_map = {
        "._darcs": True,
        ".bzr": True,
        ".hg": True,
        "BitKeeper": True,
        ".bak": True,
        ".log": True,
        ".git": True,
        ".svn": True,
    }
    file_name = request.path.split("/")[-1]
    if unsafe_file_map.get(file_name):
        raise web.HTTPForbidden()


def add_self_content_security_policy(response: web.Response) -> web.Response:
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'; form-action 'self';"
    )
    return response


def set_content_type_nosniff(response: web.Response) -> web.Response:
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
