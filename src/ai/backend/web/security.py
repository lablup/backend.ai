import secrets
from typing import Callable, Iterable, Mapping, Optional, Self

from aiohttp import web
from aiohttp.typedefs import Handler

type RequestPolicy = Callable[[web.Request], None]

type ResponsePolicy = Callable[[web.Request, web.StreamResponse], web.StreamResponse]


@web.middleware
async def security_policy_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    security_policy: SecurityPolicy = request.app["security_policy"]
    security_policy.check_request_policies(request)
    response = await handler(request)
    return security_policy.apply_response_policies(request, response)


class SecurityPolicy:
    _request_policies: Iterable[RequestPolicy]
    _response_policies: Iterable[ResponsePolicy]

    def __init__(
        self,
        request_policies: Iterable[RequestPolicy],
        response_policies: Iterable[ResponsePolicy],
    ) -> None:
        self._request_policies = request_policies
        self._response_policies = response_policies

    @classmethod
    def from_config(
        cls,
        request_policy_config: list[str],
        response_policy_config: list[str],
        csp_config: Optional[Mapping[str, Optional[list[str]]]] = None,
    ) -> Self:
        request_policy_map = {
            "reject_metadata_local_link_policy": reject_metadata_local_link_policy,
            "reject_access_for_unsafe_file_policy": reject_access_for_unsafe_file_policy,
        }
        response_policy_map = {
            "set_content_type_nosniff_policy": set_content_type_nosniff_policy,
        }
        try:
            request_policies = [
                request_policy_map[policy_name] for policy_name in request_policy_config
            ]
            response_policies: list[ResponsePolicy] = []
            for policy_name in response_policy_config:
                response_policies.append(response_policy_map[policy_name])
        except KeyError as e:
            raise ValueError(f"Unknown security policy name: {e}")
        if csp_config is not None:
            request_policies.append(add_nonce_policy)
            response_policies.append(csp_policy_builder(csp_config))
        return cls(request_policies, response_policies)

    def check_request_policies(self, request: web.Request) -> None:
        for policy in self._request_policies:
            policy(request)

    def apply_response_policies(
        self, request: web.Request, response: web.StreamResponse
    ) -> web.StreamResponse:
        for policy in self._response_policies:
            response = policy(request, response)
        return response


def reject_metadata_local_link_policy(request: web.Request) -> None:
    metadata_local_link_map = {
        "metadata.google.internal": True,
        "169.254.169.254": True,
        "100.100.100.200": True,
        "alibaba.zaproxy.org": True,
        "metadata.oraclecloud.com": True,
    }
    if metadata_local_link_map.get(request.host):
        raise web.HTTPForbidden()


def reject_access_for_unsafe_file_policy(request: web.Request) -> None:
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


def add_nonce_policy(request: web.Request) -> None:
    nonce = secrets.token_urlsafe(16)
    request["request_nonce"] = nonce


def csp_policy_builder(csp_config: Mapping[str, Optional[list[str]]]) -> ResponsePolicy:
    nonce_targets_map: dict[str, bool] = {}
    if "nonce-targets" in csp_config:
        nonce_targets = csp_config["nonce-targets"]
        if nonce_targets is None:
            nonce_targets = []
        for target in nonce_targets:
            nonce_targets_map[target] = True
    csp_config = {key: value for key, value in csp_config.items() if key != "nonce-targets"}

    def generate_csp(request: web.Request) -> Optional[str]:
        csp = []
        nonce = request.get("request_nonce")
        for key, value in csp_config.items():
            csp_fields: list[str] = []
            if value is not None:
                csp_fields.extend(value)
            if nonce is not None and nonce_targets_map.get(key):
                csp_fields.append(f"'nonce-{nonce}'")
            if len(csp_fields) > 0:
                csp.append(key + " " + " ".join(csp_fields))
        if len(csp) == 0:
            return None
        csp_str = "; ".join(csp)
        if csp_str:
            csp_str = csp_str + ";"
        return csp_str

    def policy(request: web.Request, response: web.StreamResponse) -> web.StreamResponse:
        csp_str = generate_csp(request)
        if csp_str is None:
            return response
        response.headers["Content-Security-Policy"] = csp_str
        return response

    return policy


def set_content_type_nosniff_policy(
    _: web.Request, response: web.StreamResponse
) -> web.StreamResponse:
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
