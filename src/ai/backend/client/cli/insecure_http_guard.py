from __future__ import annotations

import ipaddress
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, override

import click
from yarl import URL

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
            f"This command can send a password, key or token to {', '.join(insecure_endpoints)}: "
            "it is neither https nor loopback, so the value can be read on the network. "
            "Use an https endpoint, or pass --allow-insecure-http to run it anyway."
        )


class SecureEndpointCommand(click.Command, ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.params.append(_ALLOW_INSECURE_HTTP_OPTION)

    @abstractmethod
    def _load_endpoints(self) -> Iterable[URL]:
        raise NotImplementedError

    @override
    def invoke(self, ctx: click.Context) -> Any:
        allow_insecure_http = ctx.params.pop("allow_insecure_http")
        reject_insecure_secret_endpoints(self._load_endpoints(), allow_insecure_http)
        return super().invoke(ctx)


class LegacySecureEndpointCommand(SecureEndpointCommand):
    @override
    def _load_endpoints(self) -> Iterable[URL]:
        return get_config().endpoints


class V2SecureEndpointCommand(SecureEndpointCommand):
    @override
    def _load_endpoints(self) -> Iterable[URL]:
        # Imported here because the v2 package imports this module while it loads.
        from ai.backend.client.cli.v2.helpers import load_v2_config

        return [load_v2_config().endpoint]
