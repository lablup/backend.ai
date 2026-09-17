"""Shared helpers for v2 CLI commands."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp
import click
from pydantic import TypeAdapter, ValidationError
from yarl import URL

from ai.backend.common.tristate.unset import UNSET, Unset

if TYPE_CHECKING:
    from ai.backend.client.v2.v2_registry import V2ClientRegistry
    from ai.backend.common.dto.manager.v2.entity_label.request import EntityLabelNestedFilter

CONFIG_DIR = Path.home() / ".backend.ai"

PROFILE_ENV = "BACKEND_PROFILE"
PROFILE_META_KEY = "ai.backend.client.cli.v2.profile"
_PROFILE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

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
    cookie_file: Path | None = field(default=None)


@dataclass(frozen=True)
class ProfilePaths:
    """File locations of one profile. ``name`` is ``None`` for ``~/.backend.ai/`` itself."""

    name: str | None
    base_dir: Path

    @property
    def config_file(self) -> Path:
        return self.base_dir / "config.toml"

    @property
    def credentials_file(self) -> Path:
        return self.base_dir / "credentials.toml"

    @property
    def session_dir(self) -> Path:
        return self.base_dir / "session"

    @property
    def cookie_file(self) -> Path:
        return self.session_dir / "cookie.dat"

    def read_config(self) -> dict[str, Any]:
        """``config.toml`` values laid over the built-in defaults."""
        import tomllib

        cfg: dict[str, Any] = dict(DEFAULTS)
        if self.config_file.exists():
            with self.config_file.open("rb") as f:
                file_cfg = tomllib.load(f).get("backend-ai", {})
            cfg.update({k: v for k, v in file_cfg.items() if v is not None})
        return cfg


class ProfileStore:
    """Profiles under ``~/.backend.ai/profiles/`` and the ``current-profile`` file."""

    _root: Path

    def __init__(self) -> None:
        self._root = Path.home() / ".backend.ai"

    @property
    def _profiles_dir(self) -> Path:
        return self._root / "profiles"

    @property
    def _current_file(self) -> Path:
        return self._root / "current-profile"

    def paths(self, name: str | None) -> ProfilePaths:
        if name is None:
            return ProfilePaths(name=None, base_dir=self._root)
        if not _PROFILE_NAME_PATTERN.match(name):
            raise click.ClickException(f"Invalid profile name: {name!r}")
        return ProfilePaths(name=name, base_dir=self._profiles_dir / name)

    def existing(self, name: str) -> ProfilePaths:
        paths = self.paths(name)
        if not paths.base_dir.is_dir():
            raise click.ClickException(f"Profile {name!r} does not exist.")
        return paths

    def names(self) -> list[str]:
        if not self._profiles_dir.is_dir():
            return []
        return sorted(p.name for p in self._profiles_dir.iterdir() if p.is_dir())

    def current(self) -> str | None:
        if not self._current_file.exists():
            return None
        return self._current_file.read_text().strip() or None

    def set_current(self, name: str | None) -> None:
        if name is None:
            self._current_file.unlink(missing_ok=True)
            return
        self._root.mkdir(parents=True, exist_ok=True)
        self._current_file.write_text(name + "\n")

    def selected_name(self) -> str | None:
        """``--profile`` > ``BACKEND_PROFILE`` > ``current-profile`` > none."""
        ctx = click.get_current_context(silent=True)
        if ctx is not None and (name := ctx.meta.get(PROFILE_META_KEY)):
            return str(name)
        if name := os.environ.get(PROFILE_ENV):
            return name
        return self.current()

    def selected(self) -> ProfilePaths:
        name = self.selected_name()
        if name is None:
            return self.paths(None)
        return self.existing(name)


def load_v2_config() -> V2ConnectionConfig:
    """Load v2 connection config from the selected profile.

    Precedence (highest to lowest):
    1. Environment variables (``BACKEND_ENDPOINT``, ``BACKEND_ACCESS_KEY``, etc.)
    2. ``credentials.toml`` of the profile
    3. ``config.toml`` of the profile
    4. Built-in defaults
    """
    import tomllib

    paths = ProfileStore().selected()
    cfg = paths.read_config()

    access_key: str | None = None
    secret_key: str | None = None

    if paths.credentials_file.exists():
        with paths.credentials_file.open("rb") as f:
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

    # Defer cookie jar creation to async context (aiohttp >=3.13 requires event loop)
    cookie_file = None
    endpoint_type = str(cfg["endpoint_type"])
    if endpoint_type == "session" and paths.cookie_file.exists():
        cookie_file = paths.cookie_file

    return V2ConnectionConfig(
        endpoint=URL(str(cfg["endpoint"])),
        endpoint_type=endpoint_type,
        access_key=access_key,
        secret_key=secret_key,
        api_version=str(cfg["api_version"]),
        skip_ssl_verification=bool(cfg.get("skip_ssl_verification", False)),
        cookie_file=cookie_file,
    )


async def create_v2_registry(config: V2ConnectionConfig) -> V2ClientRegistry:
    """Build a ``V2ClientRegistry`` from a ``V2ConnectionConfig``."""
    from ai.backend.client.v2.auth import HMACAuth, NoAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.v2_registry import V2ClientRegistry

    cookie_jar: aiohttp.CookieJar | None = None
    if config.cookie_file is not None:
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        cookie_jar.load(config.cookie_file)

    client_config = ClientConfig(
        endpoint=config.endpoint,
        endpoint_type=config.endpoint_type,
        api_version=config.api_version,
        skip_ssl_verification=config.skip_ssl_verification,
        cookie_jar=cookie_jar,
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


def load_model[T](payload: str, model: type[T]) -> T:
    """Parse a JSON string or ``@file`` path and validate it against *model*.

    *payload* is either a raw JSON string or ``@<path>`` pointing to a JSON file.
    *model* is any type usable with Pydantic ``TypeAdapter`` — a model class or a
    parametrized form such as ``list[Entry]``. Exits with an error message on
    malformed JSON or validation failure.
    """
    if payload.startswith("@"):
        path = payload[1:]
        try:
            raw = Path(path).read_text()
        except OSError as e:
            click.echo(f"Cannot read file {path}: {e}", err=True)
            sys.exit(1)
    else:
        raw = payload

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    try:
        return TypeAdapter(model).validate_python(data)
    except ValidationError as e:
        click.echo(f"Invalid input: {e}", err=True)
        sys.exit(1)


def run_async(coro_fn: Callable[[], Awaitable[None]]) -> None:
    """Run an async function, translating SDK errors into clean CLI output.

    On ``BackendAPIError`` the gateway's error detail is printed to stderr and
    the process exits with code 1, instead of leaking a traceback.
    """
    from ai.backend.client.exceptions import BackendAPIError

    try:
        asyncio.run(coro_fn())
    except BackendAPIError as e:
        data = e.args[2] if len(e.args) > 2 else {}
        title = data.get("title", "") if isinstance(data, dict) else ""
        msg = data.get("msg", "") if isinstance(data, dict) else ""
        status = e.args[0] if e.args else "?"
        detail = title or msg or str(e)
        click.echo(f"Error ({status}): {detail}", err=True)
        sys.exit(1)


def nullable_option[T](value: T | None, set_null: bool, *, option: str) -> T | None | Unset:
    """Resolve a ``--<option>`` / ``--set-null-<option>`` pair for a nullable field.

    Omitted stays ``UNSET`` (unchanged); the flag clears with ``None``.
    """
    if value is not None and set_null:
        raise click.UsageError(f"--{option} and --set-null-{option} are mutually exclusive.")
    if set_null:
        return None
    if value is None:
        return UNSET
    return value


def print_result(data: Any) -> None:
    """Print a Pydantic model or dict as formatted JSON."""
    if hasattr(data, "model_dump"):
        dumped = data.model_dump(mode="json")
    else:
        dumped = data
    json_str = json.dumps(dumped, indent=2, ensure_ascii=False, default=str)
    sys.stdout.write(json_str + "\n")


@dataclass(frozen=True)
class EntityLabelTerm:
    """One ``KEY`` or ``KEY=VALUE`` a search was narrowed by."""

    key: str
    value: str | None


def entity_label_relations(
    terms: Sequence[EntityLabelTerm],
) -> list[EntityLabelNestedFilter]:
    """One relation per term, since a relation matches a single label.

    Requiring every term is the entity filter's own ``AND`` over these, which the
    command building that filter writes itself.
    """
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.entity_label.request import (
        EntityLabelFilter,
        EntityLabelNestedFilter,
    )

    return [
        EntityLabelNestedFilter(
            some=EntityLabelFilter(
                key=StringFilter(equals=term.key),
                value=StringFilter(equals=term.value) if term.value is not None else None,
            )
        )
        for term in terms
    ]


def _parse_entity_label_terms(
    _ctx: click.Context, _param: click.Parameter, value: tuple[str, ...]
) -> tuple[EntityLabelTerm, ...]:
    """Split each ``KEY=VALUE``; a bare ``KEY`` leaves the value unconstrained."""

    def to_term(term: str) -> EntityLabelTerm:
        key, sep, val = term.partition("=")
        if not key:
            raise click.BadParameter(f"{term!r} names no label key")
        return EntityLabelTerm(key=key, value=val if sep else None)

    return tuple(to_term(term) for term in value)


def entity_label_filter_options(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Add ``--label`` to a search command, parsed into :class:`EntityLabelTerm` values.

    Takes ``KEY=VALUE``, or ``KEY`` alone to match the key whatever its value.
    Repeating it narrows further: an entity must carry every label given.
    """
    return click.option(
        "--label",
        multiple=True,
        metavar="KEY[=VALUE]",
        callback=_parse_entity_label_terms,
        help="Only entities carrying this label. Repeatable (all must match).",
    )(fn)
