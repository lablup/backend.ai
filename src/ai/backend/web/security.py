from __future__ import annotations

import logging
import secrets
from collections.abc import Callable, Iterable, Mapping
from contextvars import ContextVar
from typing import Self

from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

type RequestPolicy = Callable[[web.Request], None]

type ResponsePolicy = Callable[[web.StreamResponse], web.StreamResponse]

# Per-request CSP nonce shared between the response policies (which set the
# Content-Security-Policy header) and the handler that renders index.html.
csp_nonce_var: ContextVar[str] = ContextVar("csp_nonce", default="")

# Opt-in placeholder a directive lists to request the per-request nonce.
_CSP_NONCE_KEYWORD = "nonce"

# The only CSP keyword a nonce overrides: a browser ignores 'unsafe-inline' once
# a nonce-source is present, so the two cannot take effect together. Other
# unsafe-* keywords (unsafe-eval, unsafe-hashes, wasm-unsafe-eval) are
# orthogonal to nonces and may coexist.
_CSP_UNSAFE_INLINE_KEYWORD = "unsafe-inline"


def _is_nonce_keyword(source: str) -> bool:
    return source.strip("'") == _CSP_NONCE_KEYWORD


def _is_unsafe_inline_keyword(source: str) -> bool:
    return source.strip("'") == _CSP_UNSAFE_INLINE_KEYWORD


@web.middleware
async def security_policy_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    security_policy: SecurityPolicy = request.app["security_policy"]
    token = csp_nonce_var.set(secrets.token_urlsafe(16))
    try:
        security_policy.check_request_policies(request)
        response = await handler(request)
        return security_policy.apply_response_policies(response)
    finally:
        csp_nonce_var.reset(token)


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
        csp_config: Mapping[str, list[str] | None] | None = None,
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
            raise ValueError(f"Unknown security policy name: {e}") from e
        if csp_config is not None:
            response_policies.append(csp_policy_builder(csp_config))
        return cls(request_policies, response_policies)

    def check_request_policies(self, request: web.Request) -> None:
        for policy in self._request_policies:
            policy(request)

    def apply_response_policies(self, response: web.StreamResponse) -> web.StreamResponse:
        for policy in self._response_policies:
            response = policy(response)
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


def add_self_content_security_policy(response: web.StreamResponse) -> web.StreamResponse:
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; form-action 'self';"
    )
    return response


def csp_policy_builder(csp_config: Mapping[str, list[str] | None]) -> ResponsePolicy:
    def policy(response: web.StreamResponse) -> web.StreamResponse:
        nonce = csp_nonce_var.get()
        directives = []
        for key, value in csp_config.items():
            if not value:
                continue
            sources = _resolve_csp_sources(key, list(value), nonce)
            directives.append(key + " " + " ".join(sources))
        csp_str = "; ".join(directives)
        if csp_str:
            csp_str = csp_str + ";"
        response.headers["Content-Security-Policy"] = csp_str
        return response

    return policy


def _resolve_csp_sources(directive: str, sources: list[str], nonce: str) -> list[str]:
    if not any(_is_nonce_keyword(source) for source in sources):
        return sources
    has_unsafe_inline = any(_is_unsafe_inline_keyword(source) for source in sources)
    if has_unsafe_inline:
        log.warning(
            "CSP directive {} lists both the nonce keyword and 'unsafe-inline'; "
            "dropping the nonce so 'unsafe-inline' keeps effect.",
            directive,
        )
    if has_unsafe_inline or not nonce:
        return [source for source in sources if not _is_nonce_keyword(source)]
    return [f"'nonce-{nonce}'" if _is_nonce_keyword(source) else source for source in sources]


def set_content_type_nosniff_policy(response: web.StreamResponse) -> web.StreamResponse:
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
