from __future__ import annotations

import enum
import logging
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Final, cast

import sqlalchemy as sa
from dateutil.parser import isoparse
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.errors.resource import DataTransformationFailed
from ai.backend.manager.models.base import (
    EnumType,
    EnumValueType,
    PydanticColumn,
    ResourceSlotColumn,
    SecretColumn,
    StrEnumType,
    StructuredJSONObjectColumn,
    StructuredJSONObjectListColumn,
    VFolderHostPermissionColumn,
    ensure_all_tables_registered,
    metadata,
)
from ai.backend.manager.secret.types import SecretValue

log = StructuredLogger(logging.getLogger(__spec__.name))


class FixtureOpModes(enum.StrEnum):
    INSERT = "insert"
    UPDATE = "update"


@dataclass(frozen=True)
class FixtureReferenceSpec:
    """Declarative spec for resolving a human-friendly alias in a fixture row
    into a value looked up from another table.

    For each matching fixture row, the value in `fixture_alias_column` is
    looked up against `lookup_table.lookup_match_column`, and the resulting
    `lookup_table.lookup_referenced_column` is written into `fixture_fk_column`.
    In SQL terms, the fixture's FK column ends up referencing
    `lookup_table(lookup_referenced_column)`.
    """

    fixture_alias_column: str
    fixture_fk_column: str
    lookup_table: str
    lookup_match_column: str
    lookup_referenced_column: str


FIXTURE_REFERENCE_SPECS: Final[Mapping[str, Sequence[FixtureReferenceSpec]]] = {
    "runtime_variant_presets": (
        FixtureReferenceSpec(
            fixture_alias_column="runtime_variant_name",
            fixture_fk_column="runtime_variant",
            lookup_table="runtime_variants",
            lookup_match_column="name",
            lookup_referenced_column="id",
        ),
    ),
    "prometheus_query_presets": (
        FixtureReferenceSpec(
            fixture_alias_column="category_name",
            fixture_fk_column="category_id",
            lookup_table="prometheus_query_preset_categories",
            lookup_match_column="name",
            lookup_referenced_column="id",
        ),
    ),
}


async def populate_fixture(
    engine: SAEngine,
    fixture_data: Mapping[str, str | Sequence[dict[str, Any]]],
) -> None:
    """Deprecated: write seed files with `mgr seed apply` instead. Removed in the next LTS.

    A fixture without the RBAC rows of the entities it writes may leave them unreachable through
    permission checks."""
    warnings.warn(
        "populate_fixture() is deprecated and will be removed in the next LTS; use"
        " `mgr seed apply`. A fixture without the RBAC rows (virtual_entities,"
        " entity_memberships, scope_bindings) of the entities it writes may leave them"
        " unreachable through permission checks.",
        DeprecationWarning,
        stacklevel=2,
    )
    ensure_all_tables_registered()
    op_mode = FixtureOpModes(cast(str, fixture_data.get("__mode", "insert")))
    for table_name, rows in fixture_data.items():
        if table_name.startswith("__"):
            # skip reserved names like "__mode"
            continue
        if isinstance(rows, str):
            raise DataTransformationFailed(
                f"Invalid fixture data for table {table_name}: expected sequence, got string"
            )

        table = metadata.tables.get(table_name)

        if not isinstance(table, sa.Table):
            raise DataTransformationFailed(f"Table {table_name} not found in metadata")
        if not rows:
            continue
        log.debug("fixture table loading", table_name=table_name, op_mode=op_mode.name)
        from .hasher.types import PasswordColumn

        async with engine.begin() as conn:
            await _resolve_fixture_references(conn, table, rows)
            # Apply typedecorator manually for required columns
            for col in table.columns:
                if isinstance(col.type, sa.sql.sqltypes.DateTime):
                    for row in rows:
                        if col.name in row:
                            if row[col.name] is not None:
                                row[col.name] = isoparse(row[col.name])
                            elif not col.nullable and col.server_default is not None:
                                # Remove the key so PostgreSQL applies the server default
                                # instead of explicitly inserting NULL into a NOT NULL column.
                                del row[col.name]
                            else:
                                row[col.name] = None
                if isinstance(col.type, sa.Interval):
                    # asyncpg encodes intervals only from datetime.timedelta.
                    # Accept a kwargs dict (e.g. {"days": 365}) or a number of
                    # seconds in the fixture JSON.
                    for row in rows:
                        if col.name in row and row[col.name] is not None:
                            value = row[col.name]
                            if isinstance(value, timedelta):
                                continue
                            if isinstance(value, Mapping):
                                row[col.name] = timedelta(**value)
                            else:
                                row[col.name] = timedelta(seconds=value)
                if isinstance(col.type, EnumType):
                    for row in rows:
                        if col.name in row:
                            row[col.name] = col.type._enum_cls[row[col.name]]
                elif isinstance(col.type, (StrEnumType, EnumValueType)):
                    for row in rows:
                        if col.name in row:
                            row[col.name] = col.type._enum_cls(row[col.name])
                elif isinstance(col.type, (StructuredJSONObjectColumn)):
                    for row in rows:
                        if col.name in row:
                            row[col.name] = col.type._schema.from_json(row[col.name])
                elif isinstance(col.type, (StructuredJSONObjectListColumn)):
                    for row in rows:
                        if col.name in row and row[col.name] is not None:
                            row[col.name] = [
                                item
                                if isinstance(item, col.type._schema)
                                else col.type._schema.from_json(item)
                                for item in row[col.name]
                            ]
                elif isinstance(col.type, PasswordColumn):
                    for row in rows:
                        if col.name in row and row[col.name] is not None:
                            # Convert raw password string to PasswordInfo
                            # Using default algorithm and parameters for fixtures
                            row[col.name] = PasswordInfo(
                                password=row[col.name],
                                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                                rounds=600_000,
                                salt_size=32,
                            )
                elif isinstance(col.type, SecretColumn):
                    for row in rows:
                        if col.name in row and row[col.name] is not None:
                            # Fixtures carry plaintext, which needs no key provider.
                            row[col.name] = SecretValue(row[col.name])
                elif isinstance(col.type, ResourceSlotColumn):
                    from ai.backend.common.types import ResourceSlot

                    for row in rows:
                        if col.name in row and row[col.name] is not None:
                            if not isinstance(row[col.name], ResourceSlot):
                                row[col.name] = ResourceSlot.from_json(row[col.name])
                elif isinstance(col.type, VFolderHostPermissionColumn):
                    from ai.backend.common.types import VFolderHostPermissionMap

                    for row in rows:
                        if col.name in row and row[col.name] is not None:
                            if not isinstance(row[col.name], VFolderHostPermissionMap):
                                row[col.name] = VFolderHostPermissionMap(row[col.name])
                elif isinstance(col.type, PydanticColumn):
                    for row in rows:
                        if col.name in row and row[col.name] is not None:
                            if not isinstance(row[col.name], col.type._schema):
                                row[col.name] = col.type._schema.model_validate(row[col.name])

            match op_mode:
                case FixtureOpModes.INSERT:
                    # A multi-row INSERT takes its column list from the FIRST row, silently
                    # dropping keys that only later rows carry. Group the rows by attribute
                    # set so every row's own columns reach the server.
                    row_groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
                    for row in rows:
                        row_groups.setdefault(tuple(sorted(row)), []).append(row)
                    for row_group in row_groups.values():
                        insert_stmt = (
                            sa.dialects.postgresql.insert(table)
                            .values(row_group)
                            .on_conflict_do_nothing()
                        )
                        await conn.execute(insert_stmt)
                case FixtureOpModes.UPDATE:
                    update_stmt = sa.update(table)
                    pkcols = []
                    for pkidx, pkcol in enumerate(table.primary_key):
                        update_stmt = update_stmt.where(pkcol == sa.bindparam(f"_pk_{pkidx}"))
                        pkcols.append(pkcol)
                    update_data = []
                    # Extract the data column names from the FIRST row
                    # (Therefore a fixture dataset for a single table in the udpate mode should
                    # have consistent set of attributes!)
                    try:
                        datacols: list[sa.Column[Any]] = [
                            getattr(table.columns, name)
                            for name in set(rows[0].keys()) - {pkcol.name for pkcol in pkcols}
                        ]
                    except AttributeError as e:
                        raise ValueError(
                            f"fixture for table {table_name!r} has an invalid column name: "
                            f"{e.args[0]!r}"
                        ) from e
                    update_stmt = update_stmt.values({
                        datacol.name: sa.bindparam(datacol.name) for datacol in datacols
                    })
                    for row in rows:
                        update_row = {}
                        for pkidx, pkcol in enumerate(pkcols):
                            try:
                                update_row[f"_pk_{pkidx}"] = row[pkcol.name]
                            except KeyError as e:
                                raise ValueError(
                                    f"fixture for table {table_name!r} has a missing primary key column for update"
                                    f"query: {pkcol.name!r}"
                                ) from e
                        for datacol in datacols:
                            try:
                                update_row[datacol.name] = row[datacol.name]
                            except KeyError as e:
                                raise ValueError(
                                    f"fixture for table {table_name!r} has a missing data column for update"
                                    f"query: {datacol.name!r}"
                                ) from e
                        update_data.append(update_row)
                    await conn.execute(update_stmt, update_data)

    # After every table, so a node this fixture wrote itself is already there and the
    # edges naming it stand. Imported here: the module is declared over this one's rows.
    from .virtual_entity.fixture import provision_fixture_entities

    async with engine.begin() as conn:
        await provision_fixture_entities(conn, fixture_data.keys())


async def _resolve_fixture_references(
    conn: AsyncConnection,
    table: sa.Table,
    rows: Sequence[dict[str, Any]],
) -> None:
    reference_specs = FIXTURE_REFERENCE_SPECS.get(table.name, ())
    for reference_spec in reference_specs:
        await _resolve_fixture_reference(conn, table, rows, reference_spec)


async def _resolve_fixture_reference(
    conn: AsyncConnection,
    table: sa.Table,
    rows: Sequence[dict[str, Any]],
    reference_spec: FixtureReferenceSpec,
) -> None:
    # Pop alias column from every row, collecting rows that still need a resolved FK.
    rows_to_resolve: list[tuple[dict[str, Any], str]] = []
    for row in rows:
        alias_value = row.pop(reference_spec.fixture_alias_column, None)
        if alias_value is not None and reference_spec.fixture_fk_column not in row:
            rows_to_resolve.append((row, cast(str, alias_value)))

    if not rows_to_resolve:
        return

    alias_values = {alias for _, alias in rows_to_resolve}

    lookup_table = metadata.tables.get(reference_spec.lookup_table)
    if lookup_table is None:
        raise DataTransformationFailed(f"Table {reference_spec.lookup_table} not found in metadata")

    match_column = lookup_table.columns.get(reference_spec.lookup_match_column)
    if match_column is None:
        raise DataTransformationFailed(
            f"Column {reference_spec.lookup_table}.{reference_spec.lookup_match_column} "
            "not found in metadata"
        )
    referenced_column = lookup_table.columns.get(reference_spec.lookup_referenced_column)
    if referenced_column is None:
        raise DataTransformationFailed(
            f"Column {reference_spec.lookup_table}.{reference_spec.lookup_referenced_column} "
            "not found in metadata"
        )

    result = await conn.execute(
        sa.select(match_column, referenced_column).where(match_column.in_(alias_values))
    )
    # Access via `_mapping` with column objects so that match/referenced being the same
    # column still yields the expected identity mapping.
    resolved_values: dict[str, Any] = {
        row._mapping[match_column]: row._mapping[referenced_column] for row in result
    }
    missing_values = sorted(alias_values - resolved_values.keys())
    if missing_values:
        raise DataTransformationFailed(
            f"Unknown {reference_spec.fixture_alias_column} in fixture for {table.name}: "
            + ", ".join(missing_values)
        )

    for row, alias_value in rows_to_resolve:
        row[reference_spec.fixture_fk_column] = resolved_values[alias_value]
