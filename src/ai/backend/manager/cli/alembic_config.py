"""Resolve the Alembic config and database URL for the manager CLI.

Resolution precedence (first match wins):

1. ``-f PATH`` given: load that file.
2. No ``-f`` and ``./alembic.ini`` exists: load it (the historical default).
3. Otherwise: build a config in memory that points at the migration scripts
   packaged with the manager, so no operator-supplied file is needed.

A ``sqlalchemy.url`` in a loaded file always wins. When the file has none, or
no file is used at all, the URL is built from the ``[db]`` section of the
manager bootstrap config (``manager.toml``), the same source the server uses.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from alembic.config import Config
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.errors.resource import ConfigurationLoadFailed

if TYPE_CHECKING:
    from ai.backend.manager.config.unified import DatabaseConfig

    from .context import CLIContext

log = StructuredLogger(logging.getLogger(__spec__.name))

DEFAULT_ALEMBIC_CONFIG_PATH = Path("alembic.ini")
MANAGER_SCRIPT_LOCATION = "ai.backend.manager.models:alembic"
ASYNC_DRIVERNAME = "postgresql+asyncpg"

ALEMBIC_CONFIG_HELP = (
    "The path to an Alembic config file. "
    "[default: ./alembic.ini if present, otherwise the migrations packaged with the manager] "
    "A sqlalchemy.url in the file wins; without one, the DB URL comes from the [db] section of manager.toml."
)

type DatabaseConfigLoader = Callable[[], Awaitable[DatabaseConfig]]


@dataclass(frozen=True)
class ResolvedAlembicConfig:
    config: Config
    """The Alembic config, with ``sqlalchemy.url`` set to :attr:`db_url`."""
    db_url: URL
    """The asyncpg SQLAlchemy URL of the manager database."""


def build_db_url(db_config: DatabaseConfig) -> URL:
    """Build the asyncpg SQLAlchemy URL from the manager ``[db]`` config.

    ``URL.create`` escapes the credentials, so passwords with URL-special
    characters survive the round trip.
    """
    return URL.create(
        ASYNC_DRIVERNAME,
        username=db_config.user,
        password=db_config.password,
        host=db_config.addr.host,
        port=db_config.addr.port,
        database=db_config.name,
    )


def load_alembic_config(alembic_config: Path | None) -> Config:
    """Load the Alembic config without resolving the database URL.

    Enough for commands that only walk the migration scripts.
    """
    path = alembic_config
    if path is None and DEFAULT_ALEMBIC_CONFIG_PATH.is_file():
        path = DEFAULT_ALEMBIC_CONFIG_PATH
    if path is None:
        log.debug("no alembic config file; using the packaged migration scripts")
        config = Config()
    else:
        log.debug("loading the alembic config file", path=str(path))
        config = Config(str(path))
    if config.get_main_option("script_location") is None:
        config.set_main_option("script_location", MANAGER_SCRIPT_LOCATION)
    return config


def _normalize_driver(url: URL) -> URL:
    if url.drivername == "postgresql":
        return url.set(drivername=ASYNC_DRIVERNAME)
    return url


async def resolve_alembic_config(
    alembic_config: Path | None,
    load_db_config: DatabaseConfigLoader,
) -> ResolvedAlembicConfig:
    """Load the Alembic config and resolve the manager database URL.

    ``load_db_config`` is awaited only when the config carries no
    ``sqlalchemy.url``, so a file-supplied URL never requires ``manager.toml``.
    """
    config = load_alembic_config(alembic_config)
    raw_url = config.get_main_option("sqlalchemy.url")
    if raw_url:
        try:
            db_url = _normalize_driver(make_url(raw_url))
        except ArgumentError as e:
            raise ConfigurationLoadFailed(
                "sqlalchemy.url in the alembic config is not a valid database URL"
            ) from e
    else:
        db_url = build_db_url(await load_db_config())
        log.debug(
            "built the database URL from the manager config",
            url=db_url.render_as_string(hide_password=True),
        )
    # ConfigParser interpolates '%', which the escaped credentials may contain.
    config.set_main_option(
        "sqlalchemy.url",
        db_url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    return ResolvedAlembicConfig(config=config, db_url=db_url)


def db_config_loader(cli_ctx: CLIContext) -> DatabaseConfigLoader:
    """Return a loader reading the ``[db]`` section from the CLI's bootstrap config."""

    async def _load() -> DatabaseConfig:
        bootstrap_config = await cli_ctx.get_bootstrap_config()
        return bootstrap_config.db

    return _load
