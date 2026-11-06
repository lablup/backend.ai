from __future__ import annotations

import ipaddress

import click
from yarl import URL

ALLOW_INSECURE_HTTP_ENV = "BACKEND_ALLOW_INSECURE_HTTP"


def _is_loopback_host(host: str | None) -> bool:
    if host is None:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def reject_insecure_endpoint(endpoint: URL, allow_insecure_http: bool) -> None:
    if allow_insecure_http:
        return
    if endpoint.scheme != "https" and not _is_loopback_host(endpoint.host):
        raise click.ClickException(
            f"Refusing to send a request to {endpoint}: it is neither https nor loopback, "
            "so passwords, keys, tokens and session cookies can be read on the network. "
            f"Use an https endpoint, set {ALLOW_INSECURE_HTTP_ENV}=1, "
            "or run `./bai config set allow-insecure-http true`."
        )
