import enum
import logging
import uuid
from collections.abc import (
    Mapping,
    Sequence,
)
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Self,
    TypeVar,
    cast,
)

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.orm import registry
from sqlalchemy.types import CHAR, VARCHAR, TypeDecorator

from ai.backend.common.logging import BraceStyleAdapter

from ..utils import hash_password

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

# The common shared metadata instance
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()

pgsql_connect_opts = {
    "server_settings": {
        "jit": "off",
        # 'deadlock_timeout': '10000',  # FIXME: AWS RDS forbids settings this via connection arguments
        "lock_timeout": "60000",  # 60 secs
        "idle_in_transaction_session_timeout": "60000",  # 60 secs
    },
}

UUID_SubType = TypeVar("UUID_SubType", bound=uuid.UUID)


class GUID(TypeDecorator, Generic[UUID_SubType]):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(16) storing as raw bytes.
    """

    impl = CHAR
    uuid_subtype_func: ClassVar[Callable[[Any], Any]] = lambda v: v
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(16))

    def process_bind_param(self, value: UUID_SubType | uuid.UUID | None, dialect):
        # NOTE: EndpointId, SessionId, KernelId are *not* actual types defined as classes,
        #       but a "virtual" type that is an identity function at runtime.
        #       The type checker treats them as distinct derivatives of uuid.UUID.
        #       Therefore, we just do isinstance on uuid.UUID only below.
        if value is None:
            return value
        elif dialect.name == "postgresql":
            match value:
                case uuid.UUID():
                    return str(value)
                case _:
                    return str(uuid.UUID(value))
        else:
            match value:
                case uuid.UUID():
                    return value.bytes
                case _:
                    return uuid.UUID(value).bytes

    def process_result_value(self, value: Any, dialect) -> UUID_SubType | None:
        if value is None:
            return value
        else:
            cls = type(self)
            match value:
                case bytes():
                    return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(bytes=value)))
                case _:
                    return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(value)))


T_StrEnum = TypeVar("T_StrEnum", bound=enum.Enum, covariant=True)


class StrEnumType(TypeDecorator, Generic[T_StrEnum]):
    """
    Maps Postgres VARCHAR(64) column with a Python enum.StrEnum type.
    """

    impl = sa.VARCHAR
    cache_ok = True

    def __init__(self, enum_cls: type[T_StrEnum], **opts) -> None:
        self._opts = opts
        super().__init__(length=64, **opts)
        self._enum_cls = enum_cls

    def process_bind_param(
        self,
        value: T_StrEnum | None,
        dialect: Dialect,
    ) -> str | None:
        return value.value if value is not None else None

    def process_result_value(
        self,
        value: str,
        dialect: Dialect,
    ) -> T_StrEnum | None:
        return self._enum_cls(value) if value is not None else None

    def copy(self, **kw) -> type[Self]:
        return StrEnumType(self._enum_cls, **self._opts)

    @property
    def python_type(self) -> T_StrEnum:
        return self._enum_class


class PasswordColumn(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        return hash_password(value)


def IDColumn(name="id"):
    return sa.Column(name, GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()"))


class FixtureOpModes(enum.StrEnum):
    INSERT = "insert"
    UPDATE = "update"


async def populate_fixture(
    engine: SAEngine,
    fixture_data: Mapping[str, str | Sequence[dict[str, Any]]],
) -> None:
    op_mode = FixtureOpModes(cast(str, fixture_data.get("__mode", "insert")))
    for table_name, rows in fixture_data.items():
        if table_name.startswith("__"):
            # skip reserved names like "__mode"
            continue
        assert not isinstance(rows, str)

        table: sa.Table = metadata.tables.get(table_name)

        assert isinstance(table, sa.Table)
        if not rows:
            return
        log.debug("Loading the fixture table {0} (mode:{1})", table_name, op_mode.name)
        async with engine.begin() as conn:
            # Apply typedecorator manually for required columns
            for col in table.columns:
                if isinstance(col.type, StrEnumType):
                    for row in rows:
                        if col.name in row:
                            row[col.name] = col.type._enum_cls(row[col.name])

            match op_mode:
                case FixtureOpModes.INSERT:
                    stmt = sa.dialects.postgresql.insert(table, rows).on_conflict_do_nothing()
                    await conn.execute(stmt)
                case FixtureOpModes.UPDATE:
                    stmt = sa.update(table)
                    pkcols = []
                    for pkidx, pkcol in enumerate(table.primary_key):
                        stmt = stmt.where(pkcol == sa.bindparam(f"_pk_{pkidx}"))
                        pkcols.append(pkcol)
                    update_data = []
                    # Extract the data column names from the FIRST row
                    # (Therefore a fixture dataset for a single table in the udpate mode should
                    # have consistent set of attributes!)
                    try:
                        datacols: list[sa.Column] = [
                            getattr(table.columns, name)
                            for name in set(rows[0].keys()) - {pkcol.name for pkcol in pkcols}
                        ]
                    except AttributeError as e:
                        raise ValueError(
                            f"fixture for table {table_name!r} has an invalid column name: "
                            f"{e.args[0]!r}"
                        )
                    stmt = stmt.values({
                        datacol.name: sa.bindparam(datacol.name) for datacol in datacols
                    })
                    for row in rows:
                        update_row = {}
                        for pkidx, pkcol in enumerate(pkcols):
                            try:
                                update_row[f"_pk_{pkidx}"] = row[pkcol.name]
                            except KeyError:
                                raise ValueError(
                                    f"fixture for table {table_name!r} has a missing primary key column for update"
                                    f"query: {pkcol.name!r}"
                                )
                        for datacol in datacols:
                            try:
                                update_row[datacol.name] = row[datacol.name]
                            except KeyError:
                                raise ValueError(
                                    f"fixture for table {table_name!r} has a missing data column for update"
                                    f"query: {datacol.name!r}"
                                )
                        update_data.append(update_row)
                    await conn.execute(stmt, update_data)
