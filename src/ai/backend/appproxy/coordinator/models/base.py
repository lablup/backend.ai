from __future__ import annotations

import enum
import ipaddress
import json
import logging
import uuid
from collections.abc import Callable
from typing import (
    Any,
    ClassVar,
    TypeVar,
    cast,
)

import asyncpg.pgproto.pgproto
import sqlalchemy as sa
import yarl
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy.dialects.postgresql import CIDR, ENUM, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import CHAR, SchemaType, TypeDecorator, TypeEngine

from ai.backend.appproxy.common.errors import InvalidAPIParameters
from ai.backend.appproxy.common.utils import ensure_json_serializable
from ai.backend.appproxy.coordinator.errors import InvalidEnumTypeError
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.types import ReadableCIDR
from ai.backend.logging import BraceStyleAdapter

SAFE_MIN_INT = -9007199254740991
SAFE_MAX_INT = 9007199254740991

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# The common shared metadata instance
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata_obj = sa.MetaData(naming_convention=convention)
T_StrEnum = TypeVar("T_StrEnum", bound=enum.Enum, covariant=True)


Base = declarative_base(metadata=metadata_obj)


class BaseMixin:
    def dump_model(self, serializable: bool = True) -> dict[str, Any]:
        o = dict(self.__dict__)
        del o["_sa_instance_state"]
        if serializable:
            return ensure_json_serializable(o)
        return o


pgsql_connect_opts = {
    "server_settings": {
        "jit": "off",
        # 'deadlock_timeout': '10000',  # FIXME: AWS RDS forbids settings this via connection arguments
        "lock_timeout": "60000",  # 60 secs
        "idle_in_transaction_session_timeout": "60000",  # 60 secs
    },
}


# helper functions
def zero_if_none(val: int | None) -> int:
    return 0 if val is None else val


class EnumType(TypeDecorator[enum.Enum], SchemaType):
    """
    A stripped-down version of Spoqa's sqlalchemy-enum34.
    It also handles postgres-specific enum type creation.

    The actual postgres enum choices are taken from the Python enum names.
    """

    impl = ENUM
    cache_ok = True

    def __init__(self, enum_cls: type[enum.Enum], **opts: Any) -> None:
        if not issubclass(enum_cls, enum.Enum):
            raise InvalidEnumTypeError(f"Expected an Enum subclass, got {enum_cls}")
        if "name" not in opts:
            opts["name"] = enum_cls.__name__.lower()
        self._opts = opts
        enums = (m.name for m in enum_cls)
        super().__init__(*enums, **opts)
        self._enum_cls = enum_cls

    def process_bind_param(self, value: enum.Enum | None, dialect: sa.Dialect) -> str | None:
        return value.name if value else None

    def process_result_value(self, value: Any, dialect: sa.Dialect) -> enum.Enum | None:
        return self._enum_cls[value] if value else None

    def copy(self, **kw: Any) -> EnumType:
        return EnumType(self._enum_cls, **self._opts)

    @property
    def python_type(self) -> type[enum.Enum]:
        return self._enum_class


class StrEnumType[T_StrEnum: enum.Enum](TypeDecorator[T_StrEnum]):
    """
    Maps Postgres VARCHAR(64) column with a Python enum.StrEnum type.
    """

    impl = sa.VARCHAR
    cache_ok = True

    def __init__(self, enum_cls: type[T_StrEnum], use_name: bool = False, **opts: Any) -> None:
        self._opts = opts
        super().__init__(length=64, **opts)
        self._use_name = use_name
        self._enum_cls = enum_cls

    def process_bind_param(
        self,
        value: T_StrEnum | None,
        dialect: sa.Dialect,
    ) -> str | None:
        if value is None:
            return None
        if self._use_name:
            return value.name
        return value.value

    def process_result_value(
        self,
        value: str | None,
        dialect: sa.Dialect,
    ) -> T_StrEnum | None:
        if value is None:
            return None
        if self._use_name:
            return self._enum_cls[value]
        return self._enum_cls(value)

    def copy(self, **kw: Any) -> StrEnumType[T_StrEnum]:
        return StrEnumType(self._enum_cls, self._use_name, **self._opts)

    @property
    def python_type(self) -> type[T_StrEnum]:
        return self._enum_cls


class StructuredJSONColumn(TypeDecorator[BaseModel]):
    """
    A column type to convert JSON values back and forth using a Trafaret.
    """

    impl = JSONB
    cache_ok = True
    _schema: type[BaseModel]

    def __init__(self, schema: type[BaseModel]) -> None:
        super().__init__()
        self._schema = schema

    def load_dialect_impl(self, dialect: sa.Dialect) -> TypeEngine[Any]:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(sa.JSON())
        return super().load_dialect_impl(dialect)

    def process_bind_param(self, value: Any, dialect: sa.Dialect) -> BaseModel:
        if value is None:
            return self._schema()
        try:
            self._schema(**value)
        except ValidationError as e:
            raise ValueError(
                "The given value does not conform with the structured json column format.",
                e.json(),
            ) from e
        return value

    def process_result_value(self, value: Any, dialect: sa.Dialect) -> BaseModel:
        if value is None:
            return self._schema()
        return self._schema(**value)

    def copy(self, **kw: Any) -> StructuredJSONColumn:
        return StructuredJSONColumn(self._schema)


class StructuredJSONObjectColumn(TypeDecorator[BaseModel]):
    """
    A column type to convert JSON values back and forth using BaseModel.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: type[BaseModel]) -> None:
        super().__init__()
        self._schema = schema

    def process_bind_param(self, value: BaseModel | None, dialect: sa.Dialect) -> str | None:
        if value:
            return value.model_dump_json()
        return None

    def process_result_value(self, value: str | None, dialect: sa.Dialect) -> BaseModel | None:
        if value:
            return self._schema(**json.loads(value))
        return None

    def copy(self, **kw: Any) -> StructuredJSONObjectColumn:
        return StructuredJSONObjectColumn(self._schema)


TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


class StructuredJSONObjectListColumn[TBaseModel: BaseModel](TypeDecorator[list[TBaseModel]]):
    """
    A column type to convert JSON values back and forth using BaseModel,
    but store and load a list of the objects.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: type[TBaseModel]) -> None:
        super().__init__()
        self._schema = schema

    def process_bind_param(self, value: list[TBaseModel] | None, dialect: sa.Dialect) -> str | None:
        if value is not None:
            return TypeAdapter(list[TBaseModel]).dump_json(value).decode("utf-8")
        return None

    def process_result_value(
        self, value: str | None, dialect: sa.Dialect
    ) -> list[TBaseModel] | None:
        if value is not None:
            return [self._schema(**i) for i in json.loads(value)]
        return None

    def copy(self, **kw: Any) -> StructuredJSONObjectListColumn[TBaseModel]:
        return StructuredJSONObjectListColumn(self._schema)


class URLColumn(TypeDecorator[yarl.URL]):
    """
    A column type for URL strings
    """

    impl = sa.types.UnicodeText
    cache_ok = True

    def process_bind_param(self, value: yarl.URL | str | None, dialect: sa.Dialect) -> str | None:
        if isinstance(value, yarl.URL):
            return str(value)
        return value

    def process_result_value(self, value: str | None, dialect: sa.Dialect) -> yarl.URL | None:
        if value is None:
            return None
        if value is not None:
            return yarl.URL(value)
        return None


class IPColumn(
    TypeDecorator[ReadableCIDR[ipaddress.IPv4Network | ipaddress.IPv6Network]]
):
    """
    A column type to convert IP string values back and forth to CIDR.
    """

    impl = CIDR
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: sa.Dialect) -> str | None:
        if value is None:
            return value
        try:
            cidr = ReadableCIDR(value).address
        except InvalidIpAddressValue as e:
            raise InvalidAPIParameters(f"{value} is invalid IP address value") from e
        return cidr

    def process_result_value(
        self, value: str | None, dialect: sa.Dialect
    ) -> ReadableCIDR[ipaddress.IPv4Network | ipaddress.IPv6Network] | None:
        if value is None:
            return None
        return ReadableCIDR(value)


UUID_SubType = TypeVar("UUID_SubType", bound=uuid.UUID)


class GUID[UUID_SubType: uuid.UUID](TypeDecorator[UUID_SubType]):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(16) storing as raw bytes.
    """

    impl = CHAR
    uuid_subtype_func: ClassVar[Callable[[Any], Any]] = lambda v: v
    cache_ok = True

    def load_dialect_impl(self, dialect: sa.Dialect) -> TypeEngine[Any]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        return dialect.type_descriptor(CHAR(16))

    def process_bind_param(self, value: Any, dialect: sa.Dialect) -> str | bytes | None:
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

    def process_result_value(self, value: Any, dialect: sa.Dialect) -> UUID_SubType | None:
        if value is None:
            return value
        cls = type(self)
        match value:
            case bytes():
                return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(bytes=value)))
            case asyncpg.pgproto.pgproto.UUID():
                return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(str(value))))
            case _:
                return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(value)))


def IDColumn(name: str = "id") -> sa.Column[Any]:
    return sa.Column(name, GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()"))


def ForeignKeyIDColumn(name: str, fk_field: str, nullable: bool = True) -> sa.Column[Any]:
    return sa.Column(name, GUID, sa.ForeignKey(fk_field), nullable=nullable)
