"""Shared helpers for v2 CLI commands."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp
from yarl import URL

if TYPE_CHECKING:
    from ai.backend.client.v2.v2_registry import V2ClientRegistry

CONFIG_DIR = Path.home() / ".backend.ai"
CONFIG_FILE = CONFIG_DIR / "config.toml"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.toml"
SESSION_DIR = CONFIG_DIR / "session"
COOKIE_FILE = SESSION_DIR / "cookie.dat"

DEFAULTS = {
    "endpoint": "https://api.cloud.backend.ai",
    "endpoint_type": "api",
    "api_version": "v9.20250722",
    "skip_ssl_verification": False,
}


@dataclass(frozen=True)
class V2ConnectionConfig:
    """Configuration for connecting to a Backend.AI endpoint."""

    endpoint: URL
    endpoint_type: str
    access_key: str | None
    secret_key: str | None
    api_version: str
    skip_ssl_verification: bool = False
    cookie_jar: aiohttp.CookieJar | None = field(default=None)


def load_v2_config() -> V2ConnectionConfig:
    """Load v2 connection config from ``~/.backend.ai/``.

    Precedence (highest to lowest):
    1. Environment variables (``BACKEND_ENDPOINT``, ``BACKEND_ACCESS_KEY``, etc.)
    2. ``~/.backend.ai/credentials.toml``
    3. ``~/.backend.ai/config.toml``
    4. Built-in defaults
    """
    import tomllib

    cfg: dict[str, Any] = dict(DEFAULTS)

    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("rb") as f:
            file_cfg = tomllib.load(f).get("backend-ai", {})
        cfg.update({k: v for k, v in file_cfg.items() if v is not None})

    access_key: str | None = None
    secret_key: str | None = None

    if CREDENTIALS_FILE.exists():
        with CREDENTIALS_FILE.open("rb") as f:
            creds = tomllib.load(f).get("backend-ai", {})
        access_key = creds.get("access_key")
        secret_key = creds.get("secret_key")

    # Environment variables override file settings
    if env_endpoint := os.environ.get("BACKEND_ENDPOINT"):
        cfg["endpoint"] = env_endpoint
    if env_type := os.environ.get("BACKEND_ENDPOINT_TYPE"):
        cfg["endpoint_type"] = env_type
    if env_ak := os.environ.get("BACKEND_ACCESS_KEY"):
        access_key = env_ak
    if env_sk := os.environ.get("BACKEND_SECRET_KEY"):
        secret_key = env_sk

    # Load session cookie if endpoint_type is "session"
    cookie_jar = None
    endpoint_type = str(cfg["endpoint_type"])
    if endpoint_type == "session" and COOKIE_FILE.exists():
        import aiohttp

        cookie_jar = aiohttp.CookieJar()
        cookie_jar.load(COOKIE_FILE)

    return V2ConnectionConfig(
        endpoint=URL(str(cfg["endpoint"])),
        endpoint_type=endpoint_type,
        access_key=access_key,
        secret_key=secret_key,
        api_version=str(cfg["api_version"]),
        skip_ssl_verification=bool(cfg.get("skip_ssl_verification", False)),
        cookie_jar=cookie_jar,
    )


async def create_v2_registry(config: V2ConnectionConfig) -> V2ClientRegistry:
    """Build a ``V2ClientRegistry`` from a ``V2ConnectionConfig``."""
    from ai.backend.client.v2.auth import HMACAuth, NoAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.v2_registry import V2ClientRegistry

    client_config = ClientConfig(
        endpoint=config.endpoint,
        endpoint_type=config.endpoint_type,
        api_version=config.api_version,
        skip_ssl_verification=config.skip_ssl_verification,
        cookie_jar=config.cookie_jar,
    )

    if config.endpoint_type == "session":
        auth = NoAuth()
    else:
        auth = HMACAuth(
            access_key=config.access_key or "",
            secret_key=config.secret_key or "",
        )

    return await V2ClientRegistry.create(client_config, auth)


def parse_order_options(
    order_by: tuple[str, ...],
    order_field_enum: type,
    order_class: type,
) -> list[Any]:
    """Parse ``--order-by field:direction`` options into Order DTO instances.

    Each element in *order_by* is ``"field"`` (defaults to ASC) or
    ``"field:asc"`` / ``"field:desc"``.

    *order_field_enum* is the domain-specific ``OrderField`` enum,
    *order_class* is the corresponding ``Order`` dataclass/model that
    takes ``field`` and ``direction`` keyword arguments.
    """
    from ai.backend.common.dto.manager.v2.common import OrderDirection

    orders: list[Any] = []
    for spec in order_by:
        parts = spec.split(":", 1)
        field_name = parts[0]
        direction_str = parts[1].upper() if len(parts) > 1 else "ASC"
        orders.append(
            order_class(
                field=order_field_enum(field_name),
                direction=OrderDirection(direction_str),
            )
        )
    return orders


def print_result(data: Any) -> None:
    """Print a Pydantic model or dict as formatted JSON."""
    if hasattr(data, "model_dump"):
        dumped = data.model_dump(mode="json")
    else:
        dumped = data
    json_str = json.dumps(dumped, indent=2, ensure_ascii=False, default=str)
    sys.stdout.write(json_str + "\n")
