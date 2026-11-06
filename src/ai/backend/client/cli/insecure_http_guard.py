from __future__ import annotations

import ipaddress
from collections.abc import Callable, Iterable, Mapping
from functools import wraps
from typing import Any

import click
from yarl import URL

from ai.backend.cli.types import undefined
from ai.backend.client.config import get_config

_allow_insecure_http_option = click.option(
    "--allow-insecure-http",
    is_flag=True,
    default=False,
    help=(
        "Send a password, key or token to an endpoint that is neither https nor loopback. "
        "Anyone on the network path can read it."
    ),
)


def _is_loopback_host(host: str | None) -> bool:
    if host is None:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def reject_insecure_secret_endpoints(
    endpoints: Iterable[URL],
    allow_insecure_http: bool,
) -> None:
    if allow_insecure_http:
        return
    insecure_endpoints = [
        str(endpoint)
        for endpoint in endpoints
        if endpoint.scheme != "https" and not _is_loopback_host(endpoint.host)
    ]
    if insecure_endpoints:
        raise click.ClickException(
            f"Refusing to send a password, key or token to {', '.join(insecure_endpoints)}: "
            "it is neither https nor loopback, so the value can be read on the network. "
            "Use an https endpoint, or pass --allow-insecure-http to send it anyway."
        )


def legacy_endpoints() -> Iterable[URL]:
    return get_config().endpoints


def v2_endpoints() -> Iterable[URL]:
    # Imported here because the v2 package imports this module while it loads.
    from ai.backend.client.cli.v2.helpers import load_v2_config

    return [load_v2_config().endpoint]


def option_given(option_name: str) -> Callable[[Mapping[str, Any]], bool]:
    def is_option_given(params: Mapping[str, Any]) -> bool:
        value = params[option_name]
        return value is not None and value is not undefined

    return is_option_given


def refuse_secret_over_insecure_http[T](
    load_endpoints: Callable[[], Iterable[URL]],
    sends_secret: Callable[[Mapping[str, Any]], bool] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Add ``--allow-insecure-http`` and check the endpoint before the command runs.

    Place it directly above ``def``. Without ``sends_secret`` the command always sends a secret.
    """

    def decorate(command: Callable[..., T]) -> Callable[..., T]:
        @_allow_insecure_http_option
        @wraps(command)
        def check_endpoint_then_run(
            *args: Any,
            allow_insecure_http: bool,
            **params: Any,
        ) -> T:
            if sends_secret is None or sends_secret(params):
                reject_insecure_secret_endpoints(load_endpoints(), allow_insecure_http)
            return command(*args, **params)

        return check_endpoint_then_run

    return decorate
