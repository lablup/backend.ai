from __future__ import annotations

import ipaddress
from collections.abc import Iterable
from typing import Any, override

import click
from yarl import URL

from ai.backend.cli.extensions import ExtendedCommandGroup
from ai.backend.client.config import get_config

_ALLOW_INSECURE_HTTP_OPTION = click.Option(
    ["--allow-insecure-http"],
    is_flag=True,
    default=False,
    help=(
        "Run a command that can send a password, key or token against an endpoint that is "
        "neither https nor loopback. Anyone on the network path can read the value."
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


def reject_insecure_endpoints(
    endpoints: Iterable[URL],
    allow_insecure_http: bool,
    how_to_allow: str,
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
            f"Refusing to send a request to {', '.join(insecure_endpoints)}: "
            "it is neither https nor loopback, so passwords, keys, tokens and session cookies "
            f"can be read on the network. Use an https endpoint, or {how_to_allow}."
        )


class SecureEndpointCommand(click.Command):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.params.append(_ALLOW_INSECURE_HTTP_OPTION)

    def _load_endpoints(self) -> Iterable[URL]:
        return get_config().endpoints

    @override
    def invoke(self, ctx: click.Context) -> Any:
        allow_insecure_http = ctx.params.pop("allow_insecure_http")
        reject_insecure_endpoints(
            self._load_endpoints(),
            allow_insecure_http,
            how_to_allow="pass --allow-insecure-http to run it anyway",
        )
        return super().invoke(ctx)


class SecureEndpointGroup(ExtendedCommandGroup):
    command_class = SecureEndpointCommand
