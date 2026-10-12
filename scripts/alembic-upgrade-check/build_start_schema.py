"""Build a release's head schema with its fixtures, as that release's install does.

Runs under the release's own interpreter with the release's ``src`` on ``PYTHONPATH``.
Usage: build_start_schema.py <asyncpg-url> [<fixture.json> ...]
"""

import asyncio
import importlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine


def _optional_attr(module: str, name: str) -> object | None:
    try:
        return getattr(importlib.import_module(module), name, None)
    except ImportError:
        return None


def _create_all(conn: Connection, head: str) -> None:
    importlib.import_module("ai.backend.manager.models")
    base = importlib.import_module("ai.backend.manager.models.base")
    if hasattr(base, "ensure_all_tables_registered"):
        base.ensure_all_tables_registered()
    conn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    uuid7_ddl = _optional_attr("ai.backend.manager.models.uuid7", "UUID_GENERATE_V7_DDL")
    if uuid7_ddl:
        conn.exec_driver_sql(str(uuid7_ddl))
    base.metadata.create_all(conn, checkfirst=False)
    _record_column_values(conn, base.metadata)
    seed = _optional_attr(
        "ai.backend.manager.models.global_entity.seed", "SEED_GLOBAL_ENTITIES_SQL"
    )
    for statement in cast(Sequence[str], seed or ()):
        conn.exec_driver_sql(statement)
    conn.exec_driver_sql(
        "CREATE TABLE alembic_version (version_num varchar(32) NOT NULL PRIMARY KEY)"
    )
    conn.exec_driver_sql(f"INSERT INTO alembic_version VALUES ('{head}')")


def _record_column_values(conn: Connection, metadata: MetaData) -> None:
    """Keep the values a varchar column's Python enum allows in ``upgrade_check.column_values``.

    The schema is outside ``public``, which the migrations work on.
    """
    conn.exec_driver_sql("CREATE SCHEMA upgrade_check")
    conn.exec_driver_sql(
        "CREATE TABLE upgrade_check.column_values"
        " (table_name text, column_name text, allowed text[], PRIMARY KEY (table_name, column_name))"
    )
    for table in metadata.tables.values():
        for column in table.columns:
            enum_cls = getattr(column.type, "_enum_cls", None)
            if enum_cls is None:
                continue
            use_name = getattr(column.type, "_use_name", False)
            allowed = [str(m.name if use_name else m.value) for m in enum_cls]
            conn.execute(
                text("INSERT INTO upgrade_check.column_values VALUES (:t, :c, :v)"),
                {"t": table.name, "c": column.name, "v": allowed},
            )


async def main(url: str, fixtures: list[dict[str, object]]) -> None:
    cfg = Config()
    cfg.set_main_option("script_location", "ai.backend.manager.models:alembic")
    heads = ScriptDirectory.from_config(cfg).get_heads()
    if len(heads) != 1:
        raise SystemExit(f"expected one alembic head, got {heads}")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(_create_all, heads[0])
    populate_fixture = importlib.import_module("ai.backend.manager.models.base").populate_fixture
    for fixture in fixtures:
        await populate_fixture(engine, fixture)
    await engine.dispose()
    sys.stdout.write(f"{heads[0]}\n")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], [json.loads(Path(p).read_text()) for p in sys.argv[2:]]))
