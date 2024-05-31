from __future__ import annotations

import asyncio
import collections
import enum
import functools
import logging
import sys
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    ClassVar,
    Coroutine,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    NamedTuple,
    Optional,
    Protocol,
    Self,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

import graphene
import sqlalchemy as sa
import trafaret as t
import yarl
from aiodataloader import DataLoader
from aiotools import apartial
from graphene.types import Scalar
from graphene.types.scalars import MAX_INT, MIN_INT
from graphql import Undefined
from graphql.language.ast import IntValueNode
from sqlalchemy.dialects.postgresql import ARRAY, CIDR, ENUM, JSONB, UUID
from sqlalchemy.engine.result import Result
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import registry
from sqlalchemy.types import CHAR, SchemaType, TypeDecorator

from ai.backend.common.auth import PublicKey
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.logging import BraceStyleAdapter
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
from ai.backend.manager.models.utils import execute_with_retry

from .. import models
from ..api.exceptions import GenericForbidden, InvalidAPIParameters
from .gql_relay import (
    AsyncListConnectionField,
    AsyncNode,
    ConnectionPaginationOrder,
)
from .minilang.ordering import OrderDirection, OrderingItem, QueryOrderParser
from .minilang.queryfilter import QueryFilterParser, WhereClauseType

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect

    from .gql import GraphQueryContext
    from .user import UserRole

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
metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()  # TODO: remove Any after #422 is merged

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


class FixtureOpModes(enum.StrEnum):
    INSERT = "insert"
    UPDATE = "update"


T_Enum = TypeVar("T_Enum", bound=enum.Enum, covariant=True)
T_StrEnum = TypeVar("T_StrEnum", bound=enum.Enum, covariant=True)


class EnumType(TypeDecorator, SchemaType, Generic[T_Enum]):
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
        value: str,
        dialect: Dialect,
    ) -> Optional[T_Enum]:
        return self._enum_cls[value] if value else None

    def copy(self, **kw) -> type[Self]:
        return EnumType(self._enum_cls, **self._opts)

    @property
    def python_type(self):
        return self._enum_class


class EnumValueType(TypeDecorator, SchemaType, Generic[T_Enum]):
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
        value: str,
        dialect: Dialect,
    ) -> Optional[T_Enum]:
        return self._enum_cls(value) if value else None

    def copy(self, **kw) -> type[Self]:
        return EnumValueType(self._enum_cls, **self._opts)

    @property
    def python_type(self) -> T_Enum:
        return self._enum_class


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
        value: Optional[T_StrEnum],
        dialect: Dialect,
    ) -> Optional[str]:
        return value.value if value is not None else None

    def process_result_value(
        self,
        value: str,
        dialect: Dialect,
    ) -> Optional[T_StrEnum]:
        return self._enum_cls(value) if value is not None else None

    def copy(self, **kw) -> type[Self]:
        return StrEnumType(self._enum_cls, **self._opts)

    @property
    def python_type(self) -> T_StrEnum:
        return self._enum_class


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

    def load_dialect_impl(self, dialect):
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

    def load_dialect_impl(self, dialect):
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

    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(sa.JSON)
        else:
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
            )
        return value

    def process_result_value(
        self,
        value: Optional[Any],
        dialect: Dialect,
    ) -> Optional[Any]:
        if value is None:
            return self._schema.check({})
        return self._schema.check(value)

    def copy(self, **kw) -> type[Self]:
        return StructuredJSONColumn(self._schema)


class StructuredJSONObjectColumn(TypeDecorator):
    """
    A column type to convert JSON values back and forth using JSONSerializableMixin.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: Type[JSONSerializableMixin]) -> None:
        super().__init__()
        self._schema = schema

    def process_bind_param(self, value, dialect):
        return self._schema.to_json(value)

    def process_result_value(self, value, dialect):
        return self._schema.from_json(value)

    def copy(self, **kw) -> type[Self]:
        return StructuredJSONObjectColumn(self._schema)


class StructuredJSONObjectListColumn(TypeDecorator):
    """
    A column type to convert JSON values back and forth using JSONSerializableMixin,
    but store and load a list of the objects.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: Type[JSONSerializableMixin]) -> None:
        super().__init__()
        self._schema = schema

    def process_bind_param(self, value, dialect):
        return [self._schema.to_json(item) for item in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return [self._schema.from_json(item) for item in value]

    def copy(self, **kw) -> type[Self]:
        return StructuredJSONObjectListColumn(self._schema)


class URLColumn(TypeDecorator):
    """
    A column type for URL strings
    """

    impl = sa.types.UnicodeText
    cache_ok = True

    def process_bind_param(self, value: Optional[yarl.URL], dialect: Dialect) -> Optional[str]:
        return str(value)

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[yarl.URL]:
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


class PermissionListColumn(TypeDecorator):
    """
    A column type to convert Permission values back and forth.
    """

    impl = ARRAY
    cache_ok = True

    def __init__(self, perm_type: Type[AbstractPermission]) -> None:
        super().__init__(sa.String)
        self._perm_type = perm_type

    @overload
    def process_bind_param(
        self, value: Sequence[AbstractPermission], dialect: Dialect
    ) -> List[str]: ...

    @overload
    def process_bind_param(self, value: Sequence[str], dialect: Dialect) -> List[str]: ...

    @overload
    def process_bind_param(self, value: None, dialect: Dialect) -> List[str]: ...

    def process_bind_param(
        self,
        value: Sequence[AbstractPermission] | Sequence[str] | None,
        dialect: Dialect,
    ) -> List[str]:
        if value is None:
            return []
        try:
            return [self._perm_type(perm).value for perm in value]
        except ValueError:
            raise InvalidAPIParameters(f"Invalid value for binding to {self._perm_type}")

    def process_result_value(
        self,
        value: Sequence[str] | None,
        dialect: Dialect,
    ) -> set[AbstractPermission]:
        if value is None:
            return set()
        return set(self._perm_type(perm) for perm in value)


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
            host: self.perm_col.process_bind_param(perms, None) for host, perms in value.items()
        }

    def process_result_value(
        self,
        value: Mapping[str, Any] | None,
        dialect: Dialect,
    ) -> VFolderHostPermissionMap:
        if value is None:
            return VFolderHostPermissionMap()
        return VFolderHostPermissionMap({
            host: self.perm_col.process_result_value(perms, None) for host, perms in value.items()
        })


class CurrencyTypes(enum.Enum):
    KRW = "KRW"
    USD = "USD"


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

    def process_bind_param(self, value: Union[UUID_SubType, uuid.UUID], dialect):
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
            if isinstance(value, bytes):
                return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(bytes=value)))
            else:
                return cast(UUID_SubType, cls.uuid_subtype_func(uuid.UUID(value)))


class EndpointIDColumnType(GUID[EndpointId]):
    uuid_subtype_func = EndpointId
    cache_ok = True


class SessionIDColumnType(GUID[SessionId]):
    uuid_subtype_func = SessionId
    cache_ok = True


class KernelIDColumnType(GUID[KernelId]):
    uuid_subtype_func = KernelId
    cache_ok = True


def IDColumn(name="id"):
    return sa.Column(name, GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()"))


def EndpointIDColumn(name="id"):
    return sa.Column(
        name, EndpointIDColumnType, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )


def SessionIDColumn(name="id"):
    return sa.Column(
        name, SessionIDColumnType, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )


def KernelIDColumn(name="id"):
    return sa.Column(
        name, KernelIDColumnType, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )


def ForeignKeyIDColumn(name, fk_field, nullable=True):
    return sa.Column(name, GUID, sa.ForeignKey(fk_field), nullable=nullable)


class DataLoaderManager:
    """
    For every different combination of filtering conditions, we need to make a
    new DataLoader instance because it "batches" the database queries.
    This manager get-or-creates dataloaders with fixed conditions (represetned
    as arguments) like a cache.

    NOTE: Just like DataLoaders, it is recommended to instantiate this manager
    for every incoming API request.
    """

    cache: Dict[int, DataLoader]

    def __init__(self) -> None:
        self.cache = {}
        self.mod = sys.modules["ai.backend.manager.models"]

    @staticmethod
    def _get_key(otname: str, args, kwargs) -> int:
        """
        Calculate the hash of the all arguments and keyword arguments.
        """
        key = (otname,) + args
        for item in kwargs.items():
            key += item
        return hash(key)

    def get_loader(
        self, context: GraphQueryContext, objtype_name: str, *args, **kwargs
    ) -> DataLoader:
        k = self._get_key(objtype_name, args, kwargs)
        loader = self.cache.get(k)
        if loader is None:
            objtype_name, has_variant, variant_name = objtype_name.partition(".")
            objtype = getattr(self.mod, objtype_name)
            if has_variant:
                batch_load_fn = getattr(objtype, "batch_load_" + variant_name)
            else:
                batch_load_fn = objtype.batch_load
            loader = DataLoader(
                apartial(batch_load_fn, context, *args, **kwargs),
                max_batch_size=128,
            )
            self.cache[k] = loader
        return loader


class ResourceLimit(graphene.ObjectType):
    key = graphene.String()
    min = graphene.String()
    max = graphene.String()


class KVPair(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class ResourceLimitInput(graphene.InputObjectType):
    key = graphene.String()
    min = graphene.String()
    max = graphene.String()


class KVPairInput(graphene.InputObjectType):
    key = graphene.String()
    value = graphene.String()


class BigInt(Scalar):
    """
    BigInt is an extension of the regular graphene.Int scalar type
    to support integers outside the range of a signed 32-bit integer.
    """

    @staticmethod
    def coerce_bigint(value):
        num = int(value)
        if not (SAFE_MIN_INT <= num <= SAFE_MAX_INT):
            raise ValueError("Cannot serialize integer out of the safe range.")
        if not (MIN_INT <= num <= MAX_INT):
            # treat as float
            return float(int(num))
        return num

    serialize = coerce_bigint
    parse_value = coerce_bigint

    @staticmethod
    def parse_literal(node):
        if isinstance(node, IntValueNode):
            num = int(node.value)
            if not (SAFE_MIN_INT <= num <= SAFE_MAX_INT):
                raise ValueError("Cannot parse integer out of the safe range.")
            if not (MIN_INT <= num <= MAX_INT):
                # treat as float
                return float(int(num))
            return num


class Item(graphene.Interface):
    id = graphene.ID()


class PaginatedList(graphene.Interface):
    items = graphene.List(Item, required=True)
    total_count = graphene.Int(required=True)


# ref: https://github.com/python/mypy/issues/1212
_GenericSQLBasedGQLObject = TypeVar("_GenericSQLBasedGQLObject", bound="_SQLBasedGQLObject")
_Key = TypeVar("_Key")


class _SQLBasedGQLObject(Protocol):
    @classmethod
    def from_row(
        cls: Type[_GenericSQLBasedGQLObject],
        ctx: GraphQueryContext,
        row: Row,
    ) -> _GenericSQLBasedGQLObject: ...


async def batch_result(
    graph_ctx: GraphQueryContext,
    db_conn: SAConnection | SASession,
    query: sa.sql.Select,
    obj_type: Type[_GenericSQLBasedGQLObject],
    key_list: Iterable[_Key],
    key_getter: Callable[[Row], _Key],
) -> Sequence[Optional[_GenericSQLBasedGQLObject]]:
    """
    A batched query adaptor for (key -> item) resolving patterns.
    """
    objs_per_key: Dict[_Key, Optional[_GenericSQLBasedGQLObject]]
    objs_per_key = collections.OrderedDict()
    for key in key_list:
        objs_per_key[key] = None
    if isinstance(db_conn, SASession):
        stream_func = db_conn.stream_scalars
    else:
        stream_func = db_conn.stream
    async for row in await stream_func(query):
        objs_per_key[key_getter(row)] = obj_type.from_row(graph_ctx, row)
    return [*objs_per_key.values()]


async def batch_multiresult(
    graph_ctx: GraphQueryContext,
    db_conn: SAConnection | SASession,
    query: sa.sql.Select,
    obj_type: Type[_GenericSQLBasedGQLObject],
    key_list: Iterable[_Key],
    key_getter: Callable[[Row], _Key],
) -> Sequence[Sequence[_GenericSQLBasedGQLObject]]:
    """
    A batched query adaptor for (key -> [item]) resolving patterns.
    """
    objs_per_key: Dict[_Key, List[_GenericSQLBasedGQLObject]]
    objs_per_key = collections.OrderedDict()
    for key in key_list:
        objs_per_key[key] = list()
    if isinstance(db_conn, SASession):
        stream_func = db_conn.stream_scalars
    else:
        stream_func = db_conn.stream
    async for row in await stream_func(query):
        objs_per_key[key_getter(row)].append(
            obj_type.from_row(graph_ctx, row),
        )
    return [*objs_per_key.values()]


async def batch_result_in_session(
    graph_ctx: GraphQueryContext,
    db_sess: SASession,
    query: sa.sql.Select,
    obj_type: Type[_GenericSQLBasedGQLObject],
    key_list: Iterable[_Key],
    key_getter: Callable[[Row], _Key],
) -> Sequence[Optional[_GenericSQLBasedGQLObject]]:
    """
    A batched query adaptor for (key -> item) resolving patterns.
    stream the result in async session.
    """
    objs_per_key: Dict[_Key, Optional[_GenericSQLBasedGQLObject]]
    objs_per_key = collections.OrderedDict()
    for key in key_list:
        objs_per_key[key] = None
    async for row in await db_sess.stream(query):
        objs_per_key[key_getter(row)] = obj_type.from_row(graph_ctx, row)
    return [*objs_per_key.values()]


async def batch_multiresult_in_session(
    graph_ctx: GraphQueryContext,
    db_sess: SASession,
    query: sa.sql.Select,
    obj_type: Type[_GenericSQLBasedGQLObject],
    key_list: Iterable[_Key],
    key_getter: Callable[[Row], _Key],
) -> Sequence[Sequence[_GenericSQLBasedGQLObject]]:
    """
    A batched query adaptor for (key -> [item]) resolving patterns.
    stream the result in async session.
    """
    objs_per_key: Dict[_Key, List[_GenericSQLBasedGQLObject]]
    objs_per_key = collections.OrderedDict()
    for key in key_list:
        objs_per_key[key] = list()
    async for row in await db_sess.stream(query):
        objs_per_key[key_getter(row)].append(
            obj_type.from_row(graph_ctx, row),
        )
    return [*objs_per_key.values()]


def privileged_query(required_role: UserRole):
    def wrap(func):
        @functools.wraps(func)
        async def wrapped(
            root: Any,
            info: graphene.ResolveInfo,
            *args,
            **kwargs,
        ) -> Any:
            from .user import UserRole

            ctx: GraphQueryContext = info.context
            if ctx.user["role"] != UserRole.SUPERADMIN:
                raise GenericForbidden("superadmin privilege required")
            return await func(root, info, *args, **kwargs)

        return wrapped

    return wrap


def scoped_query(
    *,
    autofill_user: bool = False,
    user_key: str = "access_key",
):
    """
    Prepends checks for domain/group/user access rights depending
    on the client's user and keypair information.

    :param autofill_user: When the *user_key* is not specified,
        automatically fills out the user data with the current
        user who is makeing the API request.
    :param user_key: The key used for storing user identification value
        in the keyword arguments.
    """

    def wrap(resolve_func):
        @functools.wraps(resolve_func)
        async def wrapped(
            root: Any,
            info: graphene.ResolveInfo,
            *args,
            **kwargs,
        ) -> Any:
            from .user import UserRole

            ctx: GraphQueryContext = info.context
            client_role = ctx.user["role"]
            if user_key == "access_key":
                client_user_id = ctx.access_key
            elif user_key == "email":
                client_user_id = ctx.user["email"]
            else:
                client_user_id = ctx.user["uuid"]
            client_domain = ctx.user["domain_name"]
            domain_name = kwargs.get("domain_name", None)
            group_id = kwargs.get("group_id", None)
            user_id = kwargs.get(user_key, None)
            if client_role == UserRole.SUPERADMIN:
                if autofill_user:
                    if user_id is None:
                        user_id = client_user_id
            elif client_role == UserRole.ADMIN:
                if domain_name is not None and domain_name != client_domain:
                    raise GenericForbidden
                domain_name = client_domain
                if group_id is not None:
                    # TODO: check if the group is a member of the domain
                    pass
                if autofill_user:
                    if user_id is None:
                        user_id = client_user_id
            elif client_role == UserRole.USER:
                if domain_name is not None and domain_name != client_domain:
                    raise GenericForbidden
                domain_name = client_domain
                if group_id is not None:
                    # TODO: check if the group is a member of the domain
                    # TODO: check if the client is a member of the group
                    pass
                if user_id is not None and user_id != client_user_id:
                    raise GenericForbidden
                user_id = client_user_id
            else:
                raise InvalidAPIParameters("Unknown client role")
            kwargs["domain_name"] = domain_name
            if group_id is not None:
                kwargs["group_id"] = group_id
            if kwargs.get("project", None) is not None:
                kwargs["project"] = group_id
            kwargs[user_key] = user_id
            return await resolve_func(root, info, *args, **kwargs)

        return wrapped

    return wrap


def privileged_mutation(required_role, target_func=None):
    def wrap(func):
        @functools.wraps(func)
        async def wrapped(cls, root, info: graphene.ResolveInfo, *args, **kwargs) -> Any:
            from .group import groups  # , association_groups_users
            from .user import UserRole

            ctx: GraphQueryContext = info.context
            permitted = False
            if required_role == UserRole.SUPERADMIN:
                if ctx.user["role"] == required_role:
                    permitted = True
            elif required_role == UserRole.ADMIN:
                if ctx.user["role"] == UserRole.SUPERADMIN:
                    permitted = True
                elif ctx.user["role"] == UserRole.USER:
                    permitted = False
                else:
                    if target_func is None:
                        return cls(False, "misconfigured privileged mutation: no target_func", None)
                    target_domain, target_group = target_func(*args, **kwargs)
                    if target_domain is None and target_group is None:
                        return cls(
                            False,
                            "misconfigured privileged mutation: "
                            "both target_domain and target_group missing",
                            None,
                        )
                    permit_chains = []
                    if target_domain is not None:
                        if ctx.user["domain_name"] == target_domain:
                            permit_chains.append(True)
                    if target_group is not None:
                        async with ctx.db.begin() as conn:
                            # check if the group is part of the requester's domain.
                            query = groups.select().where(
                                (groups.c.id == target_group)
                                & (groups.c.domain_name == ctx.user["domain_name"]),
                            )
                            result = await conn.execute(query)
                            if result.rowcount > 0:
                                permit_chains.append(True)
                            # TODO: check the group permission if implemented
                            # query = (
                            #     association_groups_users.select()
                            #     .where(association_groups_users.c.group_id == target_group)
                            # )
                            # result = await conn.execute(query)
                            # if result.rowcount > 0:
                            #     permit_chains.append(True)
                    permitted = all(permit_chains) if permit_chains else False
            elif required_role == UserRole.USER:
                permitted = True
            # assuming that mutation result objects has 2 or 3 fields:
            # success(bool), message(str) - usually for delete mutations
            # success(bool), message(str), item(object)
            if permitted:
                return await func(cls, root, info, *args, **kwargs)
            return cls(False, f"no permission to execute {info.path[0]}")

        return wrapped

    return wrap


ResultType = TypeVar("ResultType", bound=graphene.ObjectType)
ItemType = TypeVar("ItemType", bound=graphene.ObjectType)


async def gql_mutation_wrapper(
    result_cls: Type[ResultType], _do_mutate: Callable[[], Coroutine[Any, Any, ResultType]]
) -> ResultType:
    try:
        return await execute_with_retry(_do_mutate)
    except sa.exc.IntegrityError as e:
        log.warning("gql_mutation_wrapper(): integrity error ({})", repr(e))
        return result_cls(False, f"integrity error: {e}")
    except sa.exc.StatementError as e:
        log.warning(
            "gql_mutation_wrapper(): statement error ({})\n{}", repr(e), e.statement or "(unknown)"
        )
        orig_exc = e.orig
        return result_cls(False, str(orig_exc), None)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        raise
    except Exception as e:
        log.exception("gql_mutation_wrapper(): other error")
        return result_cls(False, f"unexpected error: {e}")


async def simple_db_mutate(
    result_cls: Type[ResultType],
    graph_ctx: GraphQueryContext,
    mutation_query: sa.sql.Update | sa.sql.Insert | Callable[[], sa.sql.Update | sa.sql.Insert],
    *,
    pre_func: Callable[[SAConnection], Awaitable[None]] | None = None,
    post_func: Callable[[SAConnection, Result], Awaitable[None]] | None = None,
) -> ResultType:
    """
    Performs a database mutation based on the given
    :class:`sqlalchemy.sql.Update` or :class:`sqlalchemy.sql.Insert` query,
    and return the wrapped result as the GraphQL object type given as **result_cls**.
    **result_cls** should have two initialization arguments: success (bool)
    and message (str).

    See details about the arguments in :func:`simple_db_mutate_returning_item`.
    """

    async def _do_mutate() -> ResultType:
        async with graph_ctx.db.begin() as conn:
            if pre_func:
                await pre_func(conn)
            _query = mutation_query() if callable(mutation_query) else mutation_query
            result = await conn.execute(_query)
            if post_func:
                await post_func(conn, result)
        if result.rowcount > 0:
            return result_cls(True, "success")
        else:
            return result_cls(False, f"no matching {result_cls.__name__.lower()}")

    return await gql_mutation_wrapper(result_cls, _do_mutate)


async def simple_db_mutate_returning_item(
    result_cls: Type[ResultType],
    graph_ctx: GraphQueryContext,
    mutation_query: sa.sql.Update | sa.sql.Insert | Callable[[], sa.sql.Update | sa.sql.Insert],
    *,
    item_cls: Type[ItemType],
    pre_func: Callable[[SAConnection], Awaitable[None]] | None = None,
    post_func: Callable[[SAConnection, Result], Awaitable[Row]] | None = None,
) -> ResultType:
    """
    Performs a database mutation based on the given
    :class:`sqlalchemy.sql.Update` or :class:`sqlalchemy.sql.Insert` query,
    and return the wrapped result as the GraphQL object type given as **result_cls**
    and the inserted/updated row wrapped as its 3rd argument in **item_cls**.

    If mutation_query uses external variable updated by pre_func, you should wrap the query
    with lambda so that its parameters are re-evaluated when the transaction is retried.

    :param result_cls: The GraphQL Object Type used to wrap the result.
        It should have two initialization arguments: success (bool),
        message (str), and the item (ItemType).
    :param graph_ctx: The common context that provides the reference to the database engine
        and other stuffs required to resolve the GraphQL query.
    :param mutation_query: A SQLAlchemy query object.
    :param item_cls: The GraphQL Object Type used to wrap the returned row from the mutation query.
    :param pre_func: An extra function that is executed before the mutation query, where the caller
        may perform additional database queries.
    :param post_func: An extra function that is executed after the mutation query, where the caller
        may perform additional database queries.  Note that it **MUST return the returned row
        from the given mutation result**, because the result object could be fetched only one
        time due to its cursor-like nature.
    """

    async def _do_mutate() -> ResultType:
        async with graph_ctx.db.begin() as conn:
            if pre_func:
                await pre_func(conn)
            _query = mutation_query() if callable(mutation_query) else mutation_query
            _query = _query.returning(_query.table)
            result = await conn.execute(_query)
            if post_func:
                row = await post_func(conn, result)
            else:
                row = result.first()
            if result.rowcount > 0:
                return result_cls(True, "success", item_cls.from_row(graph_ctx, row))
            else:
                return result_cls(False, f"no matching {result_cls.__name__.lower()}", None)

    return await gql_mutation_wrapper(result_cls, _do_mutate)


def set_if_set(
    src: object,
    target: MutableMapping[str, Any],
    name: str,
    *,
    clean_func=None,
    target_key: Optional[str] = None,
) -> None:
    """
    Set the target dict with only non-undefined keys and their values
    from a Graphene's input object.
    (server-side function)
    """
    v = getattr(src, name)
    # NOTE: unset optional fields are passed as graphql.Undefined.
    if v is not Undefined:
        if callable(clean_func):
            target[target_key or name] = clean_func(v)
        else:
            target[target_key or name] = v


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
        table: sa.Table = getattr(models, table_name)
        assert isinstance(table, sa.Table)
        if not rows:
            return
        log.debug("Loading the fixture taable {0} (mode:{1})", table_name, op_mode.name)
        async with engine.begin() as conn:
            # Apply typedecorator manually for required columns
            for col in table.columns:
                if isinstance(col.type, EnumType):
                    for row in rows:
                        if col.name in row:
                            row[col.name] = col.type._enum_cls[row[col.name]]
                elif isinstance(col.type, EnumValueType):
                    for row in rows:
                        if col.name in row:
                            row[col.name] = col.type._enum_cls(row[col.name])
                elif isinstance(
                    col.type, (StructuredJSONObjectColumn, StructuredJSONObjectListColumn)
                ):
                    for row in rows:
                        if col.name in row:
                            row[col.name] = col.type._schema.from_json(row[col.name])

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


class InferenceSessionError(graphene.ObjectType):
    class InferenceSessionErrorInfo(graphene.ObjectType):
        src = graphene.String(required=True)
        name = graphene.String(required=True)
        repr = graphene.String(required=True)

    session_id = graphene.UUID()

    errors = graphene.List(graphene.NonNull(InferenceSessionErrorInfo), required=True)


class AsyncPaginatedConnectionField(AsyncListConnectionField):
    def __init__(self, type, *args, **kwargs):
        kwargs.setdefault("filter", graphene.String())
        kwargs.setdefault("order", graphene.String())
        kwargs.setdefault("offset", graphene.Int())
        super().__init__(type, *args, **kwargs)


PaginatedConnectionField = AsyncPaginatedConnectionField


class ConnectionArgs(NamedTuple):
    cursor: str | None
    pagination_order: ConnectionPaginationOrder | None
    requested_page_size: int | None


def validate_connection_args(
    *,
    after: str | None = None,
    first: int | None = None,
    before: str | None = None,
    last: int | None = None,
) -> ConnectionArgs:
    """
    Validate arguments used for GraphQL relay connection, and determine pagination ordering, cursor and page size.
    It is not allowed to use arguments for forward pagination and arguments for backward pagination at the same time.
    """
    order: ConnectionPaginationOrder | None = None
    cursor: str | None = None
    requested_page_size: int | None = None

    if after is not None:
        order = ConnectionPaginationOrder.FORWARD
        cursor = after
    if first is not None:
        if first < 0:
            raise ValueError("Argument 'first' must be a non-negative integer.")
        order = ConnectionPaginationOrder.FORWARD
        requested_page_size = first

    if before is not None:
        if order is ConnectionPaginationOrder.FORWARD:
            raise ValueError(
                "Can only paginate with single direction, forwards or backwards. Please set only"
                " one of (after, first) and (before, last)."
            )
        order = ConnectionPaginationOrder.BACKWARD
        cursor = before
    if last is not None:
        if last < 0:
            raise ValueError("Argument 'last' must be a non-negative integer.")
        if order is ConnectionPaginationOrder.FORWARD:
            raise ValueError(
                "Can only paginate with single direction, forwards or backwards. Please set only"
                " one of (after, first) and (before, last)."
            )
        order = ConnectionPaginationOrder.BACKWARD
        requested_page_size = last

    return ConnectionArgs(cursor, order, requested_page_size)


def _build_sql_stmt_from_connection_args(
    info: graphene.ResolveInfo,
    orm_class,
    id_column: sa.Column,
    filter_expr: FilterExprArg | None = None,
    order_expr: OrderExprArg | None = None,
    *,
    connection_args: ConnectionArgs,
) -> tuple[sa.sql.Select, list[WhereClauseType]]:
    stmt = sa.select(orm_class)
    conditions: list[WhereClauseType] = []

    cursor_id, pagination_order, requested_page_size = connection_args

    # Default ordering by id column
    id_ordering_item: OrderingItem = OrderingItem(id_column, OrderDirection.ASC)
    ordering_item_list: list[OrderingItem] = []
    if order_expr is not None:
        parser = order_expr.parser
        ordering_item_list = parser.parse_order(orm_class, order_expr.expr)

    # Apply SQL order_by
    match pagination_order:
        case ConnectionPaginationOrder.FORWARD | None:
            set_ordering = lambda col, direction: (
                col.asc() if direction == OrderDirection.ASC else col.desc()
            )
        case ConnectionPaginationOrder.BACKWARD:
            set_ordering = lambda col, direction: (
                col.desc() if direction == OrderDirection.ASC else col.asc()
            )
    # id column should be applied last
    for col, direction in [*ordering_item_list, id_ordering_item]:
        stmt = stmt.order_by(set_ordering(col, direction))

    # Set cursor by comparing scalar values of subquery that queried by cursor id
    if cursor_id is not None:
        _, _id = AsyncNode.resolve_global_id(info, cursor_id)
        match pagination_order:
            case ConnectionPaginationOrder.FORWARD | None:
                conditions.append(id_column > _id)
                set_subquery = lambda col, subquery, direction: (
                    col >= subquery if direction == OrderDirection.ASC else col <= subquery
                )
            case ConnectionPaginationOrder.BACKWARD:
                conditions.append(id_column < _id)
                set_subquery = lambda col, subquery, direction: (
                    col <= subquery if direction == OrderDirection.ASC else col >= subquery
                )
        for col, direction in ordering_item_list:
            subq = sa.select(col).where(id_column == _id).scalar_subquery()
            stmt = stmt.where(set_subquery(col, subq, direction))

    if requested_page_size is not None:
        # Add 1 to determine has_next_page or has_previous_page
        stmt = stmt.limit(requested_page_size + 1)

    if filter_expr is not None:
        condition_parser = filter_expr.parser
        conditions.append(condition_parser.parse_filter(orm_class, filter_expr.expr))

    for cond in conditions:
        stmt = stmt.where(cond)
    return stmt, conditions


def _build_sql_stmt_from_sql_arg(
    info: graphene.ResolveInfo,
    orm_class,
    id_column: sa.Column,
    filter_expr: FilterExprArg | None = None,
    order_expr: OrderExprArg | None = None,
    *,
    limit: int | None = None,
    offset: int | None = None,
) -> tuple[sa.sql.Select, list[WhereClauseType]]:
    stmt = sa.select(orm_class)
    conditions: list[WhereClauseType] = []

    if order_expr is not None:
        parser = order_expr.parser
        stmt = parser.append_ordering(stmt, order_expr.expr)

    # default order_by id column
    stmt = stmt.order_by(id_column.asc())

    if filter_expr is not None:
        condition_parser = filter_expr.parser
        conditions.append(condition_parser.parse_filter(orm_class, filter_expr.expr))

    if limit is not None:
        stmt = stmt.limit(limit)

    if offset is not None:
        stmt = stmt.offset(offset)
    for cond in conditions:
        stmt = stmt.where(cond)
    return stmt, conditions


class GraphQLConnectionSQLInfo(NamedTuple):
    sql_stmt: sa.sql.Select
    sql_conditions: list[WhereClauseType]
    cursor: str | None
    pagination_order: ConnectionPaginationOrder | None
    requested_page_size: int | None


class FilterExprArg(NamedTuple):
    expr: str
    parser: QueryFilterParser


class OrderExprArg(NamedTuple):
    expr: str
    parser: QueryOrderParser


def generate_sql_info_for_gql_connection(
    info: graphene.ResolveInfo,
    orm_class,
    id_column: sa.Column,
    filter_expr: FilterExprArg | None = None,
    order_expr: OrderExprArg | None = None,
    offset: int | None = None,
    after: str | None = None,
    first: int | None = None,
    before: str | None = None,
    last: int | None = None,
) -> GraphQLConnectionSQLInfo:
    """
    Get GraphQL arguments and generate SQL query statement, cursor that points an id of a node, pagination order, and page size.
    If `offset` is None, return SQL query parsed from GraphQL Connection spec arguments.
    Else, return normally paginated SQL query and `first` is used as SQL limit.
    """

    if offset is None:
        connection_args = validate_connection_args(
            after=after, first=first, before=before, last=last
        )
        stmt, conditions = _build_sql_stmt_from_connection_args(
            info,
            orm_class,
            id_column,
            filter_expr,
            order_expr,
            connection_args=connection_args,
        )
        return GraphQLConnectionSQLInfo(
            stmt,
            conditions,
            connection_args.cursor,
            connection_args.pagination_order,
            connection_args.requested_page_size,
        )
    else:
        page_size = first
        stmt, conditions = _build_sql_stmt_from_sql_arg(
            info,
            orm_class,
            id_column,
            filter_expr,
            order_expr,
            limit=page_size,
            offset=offset,
        )
        return GraphQLConnectionSQLInfo(stmt, conditions, None, None, page_size)
