from __future__ import annotations

import asyncio
import collections
import enum
import functools
import logging
import trafaret as t
from typing import (
    Any,
    Awaitable,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Protocol,
    Sequence,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
    cast,
)
import sys
import uuid

from aiodataloader import DataLoader
from aiotools import apartial
import graphene
from graphene.types import Scalar
from graphql.language import ast
from graphene.types.scalars import MIN_INT, MAX_INT
import sqlalchemy as sa
from sqlalchemy.engine.result import Result
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import (
    AsyncConnection as SAConnection,
    AsyncEngine as SAEngine,
)
from sqlalchemy.orm import (
    registry,
)
from sqlalchemy.types import (
    SchemaType,
    TypeDecorator,
    CHAR,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
import yarl

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    BinarySize,
    KernelId,
    ResourceSlot,
    SessionId,
    JSONSerializableMixin,
)

from ai.backend.manager.models.utils import execute_with_retry

from .. import models
from ..api.exceptions import (
    GenericForbidden, InvalidAPIParameters,
)
if TYPE_CHECKING:
    from graphql.execution.executors.asyncio import AsyncioExecutor

    from .gql import GraphQueryContext
    from .user import UserRole

SAFE_MIN_INT = -9007199254740991
SAFE_MAX_INT = 9007199254740991

log = BraceStyleAdapter(logging.getLogger(__name__))

# The common shared metadata instance
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()  # TODO: remove Any after #422 is merged

pgsql_connect_opts = {
    'server_settings': {
        'jit': 'off',
        # 'deadlock_timeout': '10000',  # FIXME: AWS RDS forbids settings this via connection arguments
        'lock_timeout': '60000',  # 60 secs
        'idle_in_transaction_session_timeout': '60000',  # 60 secs
    },
}


# helper functions
def zero_if_none(val):
    return 0 if val is None else val


class EnumType(TypeDecorator, SchemaType):
    """
    A stripped-down version of Spoqa's sqlalchemy-enum34.
    It also handles postgres-specific enum type creation.

    The actual postgres enum choices are taken from the Python enum names.
    """

    impl = ENUM
    cache_ok = True

    def __init__(self, enum_cls, **opts):
        assert issubclass(enum_cls, enum.Enum)
        if 'name' not in opts:
            opts['name'] = enum_cls.__name__.lower()
        self._opts = opts
        enums = (m.name for m in enum_cls)
        super().__init__(*enums, **opts)
        self._enum_cls = enum_cls

    def process_bind_param(self, value, dialect):
        return value.name if value else None

    def process_result_value(self, value: str, dialect):
        return self._enum_cls[value] if value else None

    def copy(self):
        return EnumType(self._enum_cls, **self._opts)

    @property
    def python_type(self):
        return self._enum_class


class EnumValueType(TypeDecorator, SchemaType):
    """
    A stripped-down version of Spoqa's sqlalchemy-enum34.
    It also handles postgres-specific enum type creation.

    The actual postgres enum choices are taken from the Python enum values.
    """

    impl = ENUM
    cache_ok = True

    def __init__(self, enum_cls, **opts):
        assert issubclass(enum_cls, enum.Enum)
        if 'name' not in opts:
            opts['name'] = enum_cls.__name__.lower()
        self._opts = opts
        enums = (m.value for m in enum_cls)
        super().__init__(*enums, **opts)
        self._enum_cls = enum_cls

    def process_bind_param(self, value, dialect):
        return value.value if value else None

    def process_result_value(self, value: str, dialect):
        return self._enum_cls(value) if value else None

    def copy(self):
        return EnumValueType(self._enum_cls, **self._opts)

    @property
    def python_type(self):
        return self._enum_class


class ResourceSlotColumn(TypeDecorator):
    """
    A column type wrapper for ResourceSlot from JSONB.
    """

    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: Union[Mapping, ResourceSlot], dialect):
        if isinstance(value, Mapping) and not isinstance(value, ResourceSlot):
            return value
        return value.to_json() if value is not None else None

    def process_result_value(self, raw_value: Dict[str, str], dialect):
        # legacy handling
        interim_value: Dict[str, Any] = raw_value
        mem = raw_value.get('mem')
        if isinstance(mem, str) and not mem.isdigit():
            interim_value['mem'] = BinarySize.from_str(mem)
        return ResourceSlot.from_json(interim_value) if raw_value is not None else None

    def copy(self):
        return ResourceSlotColumn()


class StructuredJSONColumn(TypeDecorator):
    """
    A column type to convert JSON values back and forth using a Trafaret.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, schema: t.Trafaret) -> None:
        super().__init__()
        self._schema = schema

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(sa.JSON)
        else:
            return super().load_dialect_impl(dialect)

    def process_bind_param(self, value, dialect):
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

    def process_result_value(self, raw_value, dialect):
        if raw_value is None:
            return self._schema.check({})
        return self._schema.check(raw_value)

    def copy(self):
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

    def process_result_value(self, raw_value, dialect):
        return self._schema.from_json(raw_value)

    def copy(self):
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

    def process_result_value(self, raw_value, dialect):
        if raw_value is None:
            return []
        return [self._schema.from_json(item) for item in raw_value]

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


class CurrencyTypes(enum.Enum):
    KRW = 'KRW'
    USD = 'USD'


UUID_SubType = TypeVar('UUID_SubType', bound=uuid.UUID)


class GUID(TypeDecorator, Generic[UUID_SubType]):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(16) storing as raw bytes.
    """
    impl = CHAR
    uuid_subtype_func: ClassVar[Callable[[Any], Any]] = lambda v: v
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(16))

    def process_bind_param(self, value: Union[UUID_SubType, uuid.UUID], dialect):
        # NOTE: SessionId, KernelId are *not* actual types defined as classes,
        #       but a "virtual" type that is an identity function at runtime.
        #       The type checker treats them as distinct derivatives of uuid.UUID.
        #       Therefore, we just do isinstance on uuid.UUID only below.
        if value is None:
            return value
        elif dialect.name == 'postgresql':
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


class SessionIDColumnType(GUID[SessionId]):
    uuid_subtype_func = SessionId
    cache_ok = True


class KernelIDColumnType(GUID[KernelId]):
    uuid_subtype_func = KernelId
    cache_ok = True


def IDColumn(name='id'):
    return sa.Column(name, GUID, primary_key=True,
                     server_default=sa.text("uuid_generate_v4()"))


def SessionIDColumn(name='id'):
    return sa.Column(name, SessionIDColumnType, primary_key=True,
                     server_default=sa.text("uuid_generate_v4()"))


def KernelIDColumn(name='id'):
    return sa.Column(name, KernelIDColumnType, primary_key=True,
                     server_default=sa.text("uuid_generate_v4()"))


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
        self.mod = sys.modules['ai.backend.manager.models']

    @staticmethod
    def _get_key(otname: str, args, kwargs) -> int:
        """
        Calculate the hash of the all arguments and keyword arguments.
        """
        key = (otname, ) + args
        for item in kwargs.items():
            key += item
        return hash(key)

    def get_loader(self, context: GraphQueryContext, objtype_name: str, *args, **kwargs) -> DataLoader:
        k = self._get_key(objtype_name, args, kwargs)
        loader = self.cache.get(k)
        if loader is None:
            objtype_name, has_variant, variant_name = objtype_name.partition('.')
            objtype = getattr(self.mod, objtype_name)
            if has_variant:
                batch_load_fn = getattr(objtype, 'batch_load_' + variant_name)
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
            raise ValueError(
                'Cannot serialize integer out of the safe range.')
        if not (MIN_INT <= num <= MAX_INT):
            # treat as float
            return float(int(num))
        return num

    serialize = coerce_bigint
    parse_value = coerce_bigint

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.IntValue):
            num = int(node.value)
            if not (SAFE_MIN_INT <= num <= SAFE_MAX_INT):
                raise ValueError(
                    'Cannot parse integer out of the safe range.')
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
_GenericSQLBasedGQLObject = TypeVar('_GenericSQLBasedGQLObject', bound='_SQLBasedGQLObject')
_Key = TypeVar('_Key')


class _SQLBasedGQLObject(Protocol):
    @classmethod
    def from_row(
        cls: Type[_GenericSQLBasedGQLObject],
        ctx: GraphQueryContext,
        row: Row,
    ) -> _GenericSQLBasedGQLObject:
        ...


async def batch_result(
    graph_ctx: GraphQueryContext,
    db_conn: SAConnection,
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
    async for row in (await db_conn.stream(query)):
        objs_per_key[key_getter(row)] = obj_type.from_row(graph_ctx, row)
    return [*objs_per_key.values()]


async def batch_multiresult(
    graph_ctx: GraphQueryContext,
    db_conn: SAConnection,
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
    async for row in (await db_conn.stream(query)):
        objs_per_key[key_getter(row)].append(
            obj_type.from_row(graph_ctx, row),
        )
    return [*objs_per_key.values()]


def privileged_query(required_role: UserRole):

    def wrap(func):

        @functools.wraps(func)
        async def wrapped(executor: AsyncioExecutor, info: graphene.ResolveInfo, *args, **kwargs) -> Any:
            from .user import UserRole
            ctx: GraphQueryContext = info.context
            if ctx.user['role'] != UserRole.SUPERADMIN:
                raise GenericForbidden('superadmin privilege required')
            return await func(executor, info, *args, **kwargs)

        return wrapped

    return wrap


def scoped_query(
    *,
    autofill_user: bool = False,
    user_key: str = 'access_key',
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
        async def wrapped(executor: AsyncioExecutor, info: graphene.ResolveInfo, *args, **kwargs) -> Any:
            from .user import UserRole
            ctx: GraphQueryContext = info.context
            client_role = ctx.user['role']
            if user_key == 'access_key':
                client_user_id = ctx.access_key
            elif user_key == 'email':
                client_user_id = ctx.user['email']
            else:
                client_user_id = ctx.user['uuid']
            client_domain = ctx.user['domain_name']
            domain_name = kwargs.get('domain_name', None)
            group_id = kwargs.get('group_id', None)
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
                raise InvalidAPIParameters('Unknown client role')
            kwargs['domain_name'] = domain_name
            if group_id is not None:
                kwargs['group_id'] = group_id
            kwargs[user_key] = user_id
            return await resolve_func(executor, info, *args, **kwargs)

        return wrapped

    return wrap


def privileged_mutation(required_role, target_func=None):

    def wrap(func):

        @functools.wraps(func)
        async def wrapped(cls, root, info: graphene.ResolveInfo, *args, **kwargs) -> Any:
            from .user import UserRole
            from .group import groups  # , association_groups_users
            ctx: GraphQueryContext = info.context
            permitted = False
            if required_role == UserRole.SUPERADMIN:
                if ctx.user['role'] == required_role:
                    permitted = True
            elif required_role == UserRole.ADMIN:
                if ctx.user['role'] == UserRole.SUPERADMIN:
                    permitted = True
                elif ctx.user['role'] == UserRole.USER:
                    permitted = False
                else:
                    if target_func is None:
                        return cls(False, 'misconfigured privileged mutation: no target_func', None)
                    target_domain, target_group = target_func(*args, **kwargs)
                    if target_domain is None and target_group is None:
                        return cls(False, 'misconfigured privileged mutation: '
                                          'both target_domain and target_group missing', None)
                    permit_chains = []
                    if target_domain is not None:
                        if ctx.user['domain_name'] == target_domain:
                            permit_chains.append(True)
                    if target_group is not None:
                        async with ctx.db.begin() as conn:
                            # check if the group is part of the requester's domain.
                            query = (
                                groups.select()
                                .where(
                                    (groups.c.id == target_group) &
                                    (groups.c.domain_name == ctx.user['domain_name']),
                                )
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


ResultType = TypeVar('ResultType', bound=graphene.ObjectType)
ItemType = TypeVar('ItemType', bound=graphene.ObjectType)


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

    try:
        return await execute_with_retry(_do_mutate)
    except sa.exc.IntegrityError as e:
        return result_cls(False, f"integrity error: {e}")
    except (asyncio.CancelledError, asyncio.TimeoutError):
        raise
    except Exception as e:
        return result_cls(False, f"unexpected error: {e}")


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

    try:
        return await execute_with_retry(_do_mutate)
    except sa.exc.IntegrityError as e:
        return result_cls(False, f"integrity error: {e}", None)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        raise
    except Exception as e:
        return result_cls(False, f"unexpected error: {e}", None)


def set_if_set(
    src: object, target: MutableMapping[str, Any], name: str, *,
    clean_func=None, target_key: Optional[str] = None,
) -> None:
    v = getattr(src, name)
    # NOTE: unset optional fields are passed as null.
    if v is not None:
        if callable(clean_func):
            target[target_key or name] = clean_func(v)
        else:
            target[target_key or name] = v


async def populate_fixture(
    engine: SAEngine,
    fixture_data: Mapping[str, Sequence[Dict[str, Any]]],
    *,
    ignore_unique_violation: bool = False,
) -> None:
    for table_name, rows in fixture_data.items():
        table: sa.Table = getattr(models, table_name)
        assert isinstance(table, sa.Table)
        async with engine.begin() as conn:
            for col in table.columns:
                if isinstance(col.type, EnumType):
                    for row in rows:
                        row[col.name] = col.type._enum_cls[row[col.name]]
                elif isinstance(col.type, EnumValueType):
                    for row in rows:
                        row[col.name] = col.type._enum_cls(row[col.name])
                elif isinstance(col.type, (StructuredJSONObjectColumn, StructuredJSONObjectListColumn)):
                    for row in rows:
                        row[col.name] = col.type._schema.from_json(row[col.name])
            await conn.execute(sa.dialects.postgresql.insert(table, rows).on_conflict_do_nothing())
