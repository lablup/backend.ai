from __future__ import annotations

import enum
import json
import logging
import uuid
from collections.abc import (
    Callable,
    Mapping,
    Sequence,
)
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Final,
    Optional,
    Self,
    TypeVar,
    cast,
    overload,
)

import sqlalchemy as sa
import trafaret as t
import yarl
from dateutil.parser import isoparse
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import ARRAY, CIDR, ENUM, JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.orm import registry
from sqlalchemy.types import CHAR, SchemaType, TypeDecorator, TypeEngine, Unicode, UnicodeText

from ai.backend.common import validators as tx
from ai.backend.common.auth import PublicKey
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.types import (
    AbstractPermission,
    EndpointId,
    JSONSerializableMixin,
    KernelId,
    QuotaScopeID,
    ReadableCIDR,
    ResourceSlot,
    SessionId,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.resource import DataTransformationFailed
from ai.backend.manager.models.hasher.types import PasswordInfo

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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
Base: Any = mapper_registry.generate_base()  # TODO: remove Any after #422 is merged

# Subpackages to skip when dynamically importing model modules
_SKIP_SUBPACKAGES: Final[frozenset[str]] = frozenset({"alembic", "hasher", "minilang", "rbac"})


def ensure_all_tables_registered() -> None:
    """
    Import all model modules to register their tables with the shared metadata.

    Call this function before using `metadata` for operations that require
    all tables to be registered (e.g., schema creation, fixture population).
    """
    import importlib
    import pkgutil

    import ai.backend.manager.models

    for module_info in pkgutil.iter_modules(ai.backend.manager.models.__path__):
        if module_info.name in _SKIP_SUBPACKAGES:
            continue
        importlib.import_module(f"ai.backend.manager.models.{module_info.name}")


pgsql_connect_opts = {
    "server_settings": {
        "jit": "off",
        # 'deadlock_timeout': '10000',  # FIXME: AWS RDS forbids settings this via connection arguments
        "lock_timeout": "60000",  # 60 secs
        "idle_in_transaction_session_timeout": "60000",  # 60 secs
    },
}

DEFAULT_PAGE_SIZE: Final[int] = 10


# helper functions
def zero_if_none(val) -> int:
    return 0 if val is None else val


class FixtureOpModes(enum.StrEnum):
    INSERT = "insert"
    UPDATE = "update"


T_Enum = TypeVar("T_Enum", bound=enum.Enum, covariant=True)
T_StrEnum = TypeVar("T_StrEnum", bound=enum.Enum, covariant=True)
TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


class EnumType[T_Enum: enum.Enum](TypeDecorator, SchemaType):
    """
    A stripped-down version of Spoqa's sqlalchemy-enum34.
    It also handles postgres-specific enum type creation.

    The actual postgres enum choices are taken from the Python enum names.
    """

    impl = ENUM
    cache_ok = True

    def __init__(self, enum_cls: type[T_Enum], **opts) -> None:
        if "name" not in opts:
            opts["name"] = enum_cls.__name__.lower()
        self._opts = opts
        enums = (m.name for m in enum_cls)
        super().__init__(*enums, **opts)
        self._enum_cls = enum_cls

    def process_bind_param(
        self,
        value: Optional[T_Enum],
        dialect: Dialect,
    ) -> Optional[str]:
        return value.name if value else None

    def process_result_value(
        self,
        value: Any | None,
        dialect: Dialect,
    ) -> Optional[T_Enum]:
        return self._enum_cls[value] if value else None

    def copy(self, **kw) -> Self:
        return EnumType(self._enum_cls, **self._opts)  # type: ignore[return-value]

    @property
    def python_type(self) -> type[T_Enum]:
        return self._enum_cls


class EnumValueType[T_Enum: enum.Enum](TypeDecorator, SchemaType):
    """
    A stripped-down version of Spoqa's sqlalchemy-enum34.
    It also handles postgres-specific enum type creation.

    The actual postgres enum choices are taken from the Python enum values.
    """

    impl = ENUM
    cache_ok = True

    def __init__(self, enum_cls: type[T_Enum], **opts) -> None:
        if "name" not in opts:
            opts["name"] = enum_cls.__name__.lower()
        self._opts = opts
        enums = (m.value for m in enum_cls)
        super().__init__(*enums, **opts)
        self._enum_cls = enum_cls

    def process_bind_param(
        self,
        value: Optional[T_Enum],
        dialect: Dialect,
    ) -> Optional[str]:
        return value.value if value else None

    def process_result_value(
        self,
        value: Any | None,
        dialect: Dialect,
    ) -> Optional[T_Enum]:
        return self._enum_cls(value) if value else None

    def copy(self, **kw) -> Self:
        return EnumValueType(self._enum_cls, **self._opts)  # type: ignore[return-value]

    @property
    def python_type(self) -> type[T_Enum]:
        return self._enum_cls


class StrEnumType[T_StrEnum: enum.Enum](TypeDecorator):
    """
    Maps Postgres VARCHAR(64) column with a Python enum.StrEnum type.
    """

    impl = sa.VARCHAR
    cache_ok = True

    def __init__(
        self, enum_cls: type[T_StrEnum], use_name: bool = False, length: int = 64, **opts
    ) -> None:
        self._opts = opts
        super().__init__(length=length, **opts)
        self._use_name = use_name
        self._enum_cls = enum_cls

    def process_bind_param(
        self,
        value: Optional[T_StrEnum],
        dialect: Dialect,
    ) -> Optional[str]:
        if value is None:
            return None
        if self._use_name:
            return value.name
        return value.value

    def process_result_value(
        self,
        value: Optional[str],
        dialect: Dialect,
    ) -> Optional[T_StrEnum]:
        if value is None:
            return None
        if self._use_name:
            return self._enum_cls[value]
        return self._enum_cls(value)

    def copy(self, **kw) -> Self:
        return StrEnumType(self._enum_cls, self._use_name, **self._opts)  # type: ignore[return-value]

    @property
    def python_type(self) -> type[T_StrEnum]:
        return self._enum_cls


class CurvePublicKeyColumn(TypeDecorator):
    """
    A column type wrapper for string-based Z85-encoded CURVE public key.

    In the database, it resides as a string but it's safe to just convert them to PublicKey (bytes)
    because zmq uses Z85 encoding to use printable characters only in the key while the pyzmq API
    treats them as bytes.

    The pure binary representation of a public key is 32 bytes and its Z85-encoded form used in the
    pyzmq APIs is 40 ASCII characters.
    """

    impl = sa.String
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeEngine:
        return dialect.type_descriptor(sa.String(40))

    def process_bind_param(
        self,
        value: Optional[PublicKey],
        dialect: Dialect,
    ) -> Optional[str]:
        return value.decode("ascii") if value else None

    def process_result_value(
        self,
        value: str | None,
        dialect: Dialect,
    ) -> Optional[PublicKey]:
        if value is None:
            return None
        return PublicKey(value.encode("ascii"))


class QuotaScopeIDType(TypeDecorator):
    """
    A column type wrapper for string-based quota scope ID.
    """

    impl = sa.String
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeEngine:
        return dialect.type_descriptor(sa.String(64))

    def process_bind_param(
        self,
        value: Optional[QuotaScopeID],
        dialect: Dialect,
    ) -> Optional[str]:
        return str(value) if value else None

    def process_result_value(
        self,
        value: Optional[str],
        dialect: Dialect,
    ) -> Optional[QuotaScopeID]:
        return QuotaScopeID.parse(value) if value else None


class ResourceSlotColumn(TypeDecorator):
    """
    A column type wrapper for ResourceSlot from JSONB.
    """

    impl = JSONB
    cache_ok = True

    def process_bind_param(
        self,
        value: Optional[ResourceSlot],
        dialect: Dialect,
    ) -> Optional[Mapping[str, str]]:
        if value is None:
            return None
        if isinstance(value, ResourceSlot):
            return value.to_json()
        return value

    def process_result_value(
        self,
        value: Optional[dict[str, str]],
        dialect: Dialect,
    ) -> Optional[ResourceSlot]:
        if value is None:
            return None
        try:
            return ResourceSlot.from_json(value)
        except ArithmeticError:
            # for legacy-compat scenario
            return ResourceSlot.from_user_input(value, None)


class StructuredJSONColumn(TypeDecorator):
    """
    A column type to convert JSON values back and forth using a Trafaret.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: t.Trafaret) -> None:
        super().__init__()
        self._schema = schema

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(sa.JSON())
        return super().load_dialect_impl(dialect)

    def process_bind_param(
        self,
        value: Optional[Any],
        dialect: Dialect,
    ) -> Optional[Any]:
        if value is None:
            return self._schema.check({})
        try:
            self._schema.check(value)
        except t.DataError as e:
            raise ValueError(
                "The given value does not conform with the structured json column format.",
                e.as_dict(),
            ) from e
        return value

    def process_result_value(
        self,
        value: Optional[Any],
        dialect: Dialect,
    ) -> Optional[Any]:
        if value is None:
            return self._schema.check({})
        return self._schema.check(value)

    def copy(self, **kw) -> Self:
        return StructuredJSONColumn(self._schema)  # type: ignore[return-value]


class StructuredJSONObjectColumn(TypeDecorator):
    """
    A column type to convert JSON values back and forth using JSONSerializableMixin.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: type[JSONSerializableMixin]) -> None:
        super().__init__()
        self._schema = schema

    def process_bind_param(self, value, dialect) -> Optional[dict]:
        return self._schema.to_json(value)

    def process_result_value(self, value, dialect) -> Optional[JSONSerializableMixin]:
        return self._schema.from_json(value)

    def copy(self, **kw) -> Self:
        return StructuredJSONObjectColumn(self._schema)  # type: ignore[return-value]


class StructuredJSONObjectListColumn(TypeDecorator):
    """
    A column type to convert JSON values back and forth using JSONSerializableMixin,
    but store and load a list of the objects.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: type[JSONSerializableMixin]) -> None:
        super().__init__()
        self._schema = schema

    def coerce_compared_value(self, op, value) -> JSONB:
        return JSONB()

    def process_bind_param(self, value, dialect) -> list[dict]:
        return [self._schema.to_json(item) for item in value]

    def process_result_value(self, value, dialect) -> list[JSONSerializableMixin]:
        if value is None:
            return []
        return [self._schema.from_json(item) for item in value]

    def copy(self, **kw) -> Self:
        return StructuredJSONObjectListColumn(self._schema)  # type: ignore[return-value]


class PydanticColumn[TBaseModel: BaseModel](TypeDecorator):
    """
    A column type for storing a single Pydantic model in JSONB.
    Handles nullable columns - returns None for null values.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: type[TBaseModel]) -> None:
        super().__init__()
        self._schema = schema

    def process_bind_param(
        self,
        value: TBaseModel | None,
        dialect: Dialect,
    ) -> dict[str, Any] | None:
        # JSONB accepts Python objects directly, not JSON strings
        if value is not None:
            return value.model_dump(mode="json")
        return None

    def process_result_value(
        self,
        value: dict[str, Any] | None,
        dialect: Dialect,
    ) -> TBaseModel | None:
        # JSONB returns already parsed Python objects, not strings
        if value is not None:
            return self._schema.model_validate(value)
        return None

    def copy(self, **kw) -> Self:
        return PydanticColumn(self._schema)  # type: ignore[return-value]


class PydanticListColumn[TBaseModel: BaseModel](TypeDecorator):
    """
    A column type for storing a list of Pydantic models in JSONB.
    Always returns empty list instead of None for null values.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: type[TBaseModel]) -> None:
        super().__init__()
        self._schema = schema

    def coerce_compared_value(self, op, value) -> JSONB:
        return JSONB()

    def process_bind_param(self, value: list[TBaseModel] | None, dialect) -> list:
        # JSONB accepts Python objects directly, not JSON strings
        if value is not None:
            return [item.model_dump(mode="json") for item in value]
        return []

    def process_result_value(self, value: list | str | None, dialect) -> list[TBaseModel]:
        # JSONB returns already parsed Python objects, not strings
        # Handle case where value is stored as JSON string (legacy data)
        if value is not None:
            if isinstance(value, str):
                value = json.loads(value)
            return [self._schema.model_validate(item) for item in value]
        return []

    def copy(self, **kw) -> Self:
        return PydanticListColumn(self._schema)  # type: ignore[return-value]


class URLColumn(TypeDecorator):
    """
    A column type for URL strings
    """

    impl = UnicodeText
    cache_ok = True

    def process_bind_param(self, value: Optional[yarl.URL], dialect: Dialect) -> Optional[str]:
        return str(value)

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[yarl.URL]:
        if value is None:
            return None
        return yarl.URL(value)


class IPColumn(TypeDecorator):
    """
    A column type to convert IP string values back and forth to CIDR.
    """

    impl = CIDR
    cache_ok = True

    def process_bind_param(self, value, dialect) -> Optional[str]:
        if value is None:
            return value
        try:
            cidr = ReadableCIDR(value).address
        except InvalidIpAddressValue as e:
            raise InvalidAPIParameters(f"{value} is invalid IP address value") from e
        return cidr

    def process_result_value(self, value, dialect) -> Optional[ReadableCIDR]:
        if value is None:
            return None
        return ReadableCIDR(value)


class PermissionListColumn(TypeDecorator):
    """
    A column type to convert Permission values back and forth.
    """

    impl = ARRAY
    cache_ok = True

    def __init__(self, perm_type: type[AbstractPermission]) -> None:
        super().__init__(sa.String)
        self._perm_type = perm_type

    @overload
    def process_bind_param(
        self, value: Sequence[AbstractPermission], dialect: Dialect
    ) -> list[str]: ...

    @overload
    def process_bind_param(self, value: Sequence[str], dialect: Dialect) -> list[str]: ...

    @overload
    def process_bind_param(self, value: None, dialect: Dialect) -> list[str]: ...

    def process_bind_param(
        self,
        value: Sequence[AbstractPermission] | Sequence[str] | None,
        dialect: Dialect,
    ) -> list[str]:
        if value is None:
            return []
        try:
            return [self._perm_type(perm).value for perm in value]
        except ValueError as e:
            raise InvalidAPIParameters(f"Invalid value for binding to {self._perm_type}") from e

    def process_result_value(
        self,
        value: Sequence[str] | None,
        dialect: Dialect,
    ) -> set[AbstractPermission]:
        if value is None:
            return set()
        return {self._perm_type(perm) for perm in value}


class VFolderHostPermissionColumn(TypeDecorator):
    """
    A column type to convert vfolder host permission back and forth.
    """

    impl = JSONB
    cache_ok = True
    perm_col = PermissionListColumn(VFolderHostPermission)

    def process_bind_param(
        self,
        value: Mapping[str, Any] | None,
        dialect: Dialect,
    ) -> Mapping[str, Any]:
        if value is None:
            return {}
        return {
            host: self.perm_col.process_bind_param(perms, dialect) for host, perms in value.items()
        }

    def process_result_value(
        self,
        value: Mapping[str, Any] | None,
        dialect: Dialect,
    ) -> VFolderHostPermissionMap:
        if value is None:
            return VFolderHostPermissionMap()
        return VFolderHostPermissionMap({
            host: self.perm_col.process_result_value(perms, dialect)
            for host, perms in value.items()
        })


class CurrencyTypes(enum.Enum):
    KRW = "KRW"
    USD = "USD"


TUUIDSubType = TypeVar("TUUIDSubType", bound=uuid.UUID)


class GUID[TUUIDSubType: uuid.UUID](TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(16) storing as raw bytes.
    """

    impl = CHAR
    uuid_subtype_func: ClassVar[Callable[[Any], uuid.UUID]] = lambda v: v
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        return dialect.type_descriptor(CHAR(16))

    def process_bind_param(self, value: Any | None, dialect) -> str | bytes | None:
        # NOTE: EndpointId, SessionId, KernelId are *not* actual types defined as classes,
        #       but a "virtual" type that is an identity function at runtime.
        #       The type checker treats them as distinct derivatives of uuid.UUID.
        #       Therefore, we just do isinstance on uuid.UUID only below.
        if value is None:
            return value
        if dialect.name == "postgresql":
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(uuid.UUID(value))
        if isinstance(value, uuid.UUID):
            return value.bytes
        return uuid.UUID(value).bytes

    def process_result_value(self, value: Any, dialect) -> Optional[TUUIDSubType]:
        if value is None:
            return value
        cls = type(self)
        if isinstance(value, bytes):
            return cast(TUUIDSubType, cls.uuid_subtype_func(uuid.UUID(bytes=value)))
        # Handle asyncpg's UUID type (asyncpg.pgproto.pgproto.UUID) and standard uuid.UUID
        # Both have a 'bytes' attribute, so we can use it to construct a standard uuid.UUID
        if hasattr(value, "bytes"):
            return cast(TUUIDSubType, cls.uuid_subtype_func(uuid.UUID(bytes=value.bytes)))
        return cast(TUUIDSubType, cls.uuid_subtype_func(uuid.UUID(value)))


class SlugType(TypeDecorator):
    """
    A type wrapper for slug type string
    """

    impl = Unicode
    cache_ok = True

    def __init__(
        self,
        *,
        length: int | None = None,
        allow_dot: bool = False,
        allow_space: bool = False,
        allow_unicode: bool = False,
    ) -> None:
        super().__init__(length=length)
        self._tx_slug = tx.Slug(
            max_length=length,
            allow_dot=allow_dot,
            allow_space=allow_space,
            allow_unicode=allow_unicode,
        )

    def coerce_compared_value(self, op, value) -> Unicode:
        return Unicode()

    def process_bind_param(self, value: Any | None, dialect) -> str | None:
        if value is None:
            return value
        try:
            self._tx_slug.check(value)
        except t.DataError as e:
            raise ValueError(e.error, value) from e
        return value


class EndpointIDColumnType(GUID[EndpointId]):
    uuid_subtype_func = lambda v: EndpointId(v)
    cache_ok = True


class SessionIDColumnType(GUID[SessionId]):
    uuid_subtype_func = lambda v: SessionId(v)
    cache_ok = True


class KernelIDColumnType(GUID[KernelId]):
    uuid_subtype_func = lambda v: KernelId(v)
    cache_ok = True


def IDColumn(name="id") -> sa.Column:
    return sa.Column(name, GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()"))


def EndpointIDColumn(name="id") -> sa.Column:
    return sa.Column(
        name, EndpointIDColumnType, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )


def SessionIDColumn(name="id") -> sa.Column:
    return sa.Column(
        name, SessionIDColumnType, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )


def KernelIDColumn(name="id") -> sa.Column:
    return sa.Column(
        name, KernelIDColumnType, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )


def ForeignKeyIDColumn(name, fk_field, nullable=True) -> sa.Column:
    return sa.Column(name, GUID, sa.ForeignKey(fk_field), nullable=nullable)


async def populate_fixture(
    engine: SAEngine,
    fixture_data: Mapping[str, str | Sequence[dict[str, Any]]],
) -> None:
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
            return
        log.debug("Loading the fixture table {0} (mode:{1})", table_name, op_mode.name)
        from .hasher.types import PasswordColumn

        async with engine.begin() as conn:
            # Apply typedecorator manually for required columns
            for col in table.columns:
                if isinstance(col.type, sa.sql.sqltypes.DateTime):
                    for row in rows:
                        if col.name in row:
                            if row[col.name] is not None:
                                row[col.name] = isoparse(row[col.name])
                            else:
                                row[col.name] = None
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

            match op_mode:
                case FixtureOpModes.INSERT:
                    insert_stmt = (
                        sa.dialects.postgresql.insert(table).values(rows).on_conflict_do_nothing()
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
                        datacols: list[sa.Column] = [
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


class DecimalType(TypeDecorator, Decimal):
    """
    Database type adaptor for Decimal
    """

    impl = sa.VARCHAR
    cache_ok = True

    def process_bind_param(
        self,
        value: Optional[Decimal],
        dialect: Dialect,
    ) -> Optional[str]:
        return f"{value:f}" if value is not None else None

    def process_result_value(
        self,
        value: Any | None,
        dialect: Dialect,
    ) -> Optional[Decimal]:
        return Decimal(value) if value is not None else None

    @property
    def python_type(self) -> type[Decimal]:
        return Decimal
