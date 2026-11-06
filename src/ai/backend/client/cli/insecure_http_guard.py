from __future__ import annotations

import ipaddress
from collections.abc import Iterable

import click
from yarl import URL

allow_insecure_http_option = click.option(
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
