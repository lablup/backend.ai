from __future__ import annotations

import enum
import json
import logging
import uuid
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Optional,
    Type,
    TypeVar,
    cast,
)

import asyncpg.pgproto.pgproto
import sqlalchemy as sa
import yarl
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy.dialects.postgresql import CIDR, ENUM, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import CHAR, SchemaType, TypeDecorator

from ai.backend.appproxy.common.exceptions import InvalidAPIParameters
from ai.backend.appproxy.common.utils import ensure_json_serializable
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.types import ReadableCIDR
from ai.backend.logging import BraceStyleAdapter

SAFE_MIN_INT = -9007199254740991
SAFE_MAX_INT = 9007199254740991

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

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
    def dump_model(self, serializable=True) -> dict[str, Any]:
        o = dict(self.__dict__)
        del o["_sa_instance_state"]
        if serializable:
            return ensure_json_serializable(o)
        else:
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
def zero_if_none(val):
    return 0 if val is None else val


# FIXME: remove type: ignore annotation as soon as possible
class EnumType(TypeDecorator, SchemaType):  # type: ignore
    """
    A stripped-down version of Spoqa's sqlalchemy-enum34.
    It also handles postgres-specific enum type creation.

    The actual postgres enum choices are taken from the Python enum names.
    """

    impl = ENUM
    cache_ok = True

    def __init__(self, enum_cls, **opts):
        assert issubclass(enum_cls, enum.Enum)
        if "name" not in opts:
            opts["name"] = enum_cls.__name__.lower()
        self._opts = opts
        enums = (m.name for m in enum_cls)
        super().__init__(*enums, **opts)
        self._enum_cls = enum_cls

    def process_bind_param(self, value, dialect):
        return value.name if value else None

    def process_result_value(self, value: Any, dialect):
        return self._enum_cls[value] if value else None

    def copy(self):
        return EnumType(self._enum_cls, **self._opts)

    @property
    def python_type(self):
        return self._enum_class


class StrEnumType(TypeDecorator, Generic[T_StrEnum]):
    """
    Maps Postgres VARCHAR(64) column with a Python enum.StrEnum type.
    """

    impl = sa.VARCHAR
    cache_ok = True

    def __init__(self, enum_cls: type[T_StrEnum], use_name: bool = False, **opts) -> None:
        self._opts = opts
        super().__init__(length=64, **opts)
        self._use_name = use_name
        self._enum_cls = enum_cls

    def process_bind_param(
        self,
        value: Optional[T_StrEnum],
        dialect: sa.Dialect,
    ) -> Optional[str]:
        if value is None:
            return None
        if self._use_name:
            return value.name
        else:
            return value.value

    def process_result_value(
        self,
        value: Optional[str],
        dialect: sa.Dialect,
    ) -> Optional[T_StrEnum]:
        if value is None:
            return None
        if self._use_name:
            return self._enum_cls[value]
        else:
            return self._enum_cls(value)

    def copy(self, **kw):
        return StrEnumType(self._enum_cls, self._use_name, **self._opts)

    @property
    def python_type(self) -> type[T_StrEnum]:
        return self._enum_cls


class StructuredJSONColumn(TypeDecorator):
    """
    A column type to convert JSON values back and forth using a Trafaret.
    """

    impl = JSONB
    cache_ok = True
    _schema: type[BaseModel]

    def __init__(self, schema: type[BaseModel]) -> None:
        super().__init__()
        self._schema = schema

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(sa.JSON)
        else:
            return super().load_dialect_impl(dialect)

    def process_bind_param(self, value, dialect):
        if value is None:
            return self._schema()
        try:
            self._schema(**value)
        except ValidationError as e:
            raise ValueError(
                "The given value does not conform with the structured json column format.",
                e.json(),
            )
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return self._schema()
        return self._schema(**value)

    def copy(self):
        return StructuredJSONColumn(self._schema)


class StructuredJSONObjectColumn(TypeDecorator):
    """
    A column type to convert JSON values back and forth using BaseModel.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: Type[BaseModel]) -> None:
        super().__init__()
        self._schema = schema

    def process_bind_param(self, value: BaseModel | None, dialect):
        if value:
            return value.model_dump_json()
        return None

    def process_result_value(self, value: str | None, dialect):
        if value:
            return self._schema(**json.loads(value))
        return None

    def copy(self):
        return StructuredJSONObjectColumn(self._schema)


TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


class StructuredJSONObjectListColumn(TypeDecorator, Generic[TBaseModel]):
    """
    A column type to convert JSON values back and forth using BaseModel,
    but store and load a list of the objects.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: Type[TBaseModel]) -> None:
        super().__init__()
        self._schema = schema

    def process_bind_param(self, value: list[TBaseModel] | None, dialect):
        if value is not None:
            return TypeAdapter(list[TBaseModel]).dump_json(value).decode("utf-8")
        return None

    def process_result_value(self, value: str | None, dialect):
        if value is not None:
            return [self._schema(**i) for i in json.loads(value)]
        return None

    def copy(self):
        return StructuredJSONObjectListColumn(self._schema)


class URLColumn(TypeDecorator):
    """
    A column type for URL strings
    """

    impl = sa.types.UnicodeText
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, yarl.URL):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value is not None:
            return yarl.URL(value)


class IPColumn(TypeDecorator):
    """
    A column type to convert IP string values back and forth to CIDR.
    """

    impl = CIDR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        try:
            cidr = ReadableCIDR(value).address
        except InvalidIpAddressValue:
            raise InvalidAPIParameters(f"{value} is invalid IP address value")
        return cidr

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return ReadableCIDR(value)


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

    def process_bind_param(self, value: Any, dialect):
        # NOTE: EndpointId, SessionId, KernelId are *not* actual types defined as classes,
        #       but a "virtual" type that is an identity function at runtime.
        #       The type checker treats them as distinct derivatives of uuid.UUID.
        #       Therefore, we just do isinstance on uuid.UUID only below.
        if value is None:
            return value
        elif dialect.name == "postgresql":
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value))
        else:
            if isinstance(value, uuid.UUID):
                return value.bytes
            else:
                return uuid.UUID(value).bytes

    def process_result_value(self, value: Any, dialect) -> Optional[UUID_SubType]:
        if value is None:
            return value
        else:
            cls = type(self)
            match value:
                case bytes():
                    return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(bytes=value)))
                case asyncpg.pgproto.pgproto.UUID():
                    return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(str(value))))
                case _:
                    return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(value)))


def IDColumn(name="id"):
    return sa.Column(name, GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()"))


def ForeignKeyIDColumn(name, fk_field, nullable=True):
    return sa.Column(name, GUID, sa.ForeignKey(fk_field), nullable=nullable)
