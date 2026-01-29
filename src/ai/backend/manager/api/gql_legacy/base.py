from __future__ import annotations

import asyncio
import functools
import logging
import uuid
from collections.abc import (
    Awaitable,
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Final,
    NamedTuple,
    Protocol,
    TypeVar,
    cast,
)
from uuid import UUID

import graphene
import graphql
import sqlalchemy as sa
from aiodataloader import DataLoader
from aiotools import apartial
from graphene.types import Scalar
from graphene.types.scalars import MAX_INT, MIN_INT
from graphene_federation import shareable
from graphql import GraphQLError, Undefined
from graphql.language.ast import FloatValueNode, IntValueNode, ObjectValueNode, ValueNode
from graphql.language.printer import print_ast
from sqlalchemy.engine.result import Result
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.orm.attributes import InstrumentedAttribute

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericForbidden, ObjectNotFound
from ai.backend.manager.models.minilang.ordering import (
    OrderDirection,
    OrderingItem,
    QueryOrderParser,
)
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser, WhereClauseType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import execute_with_retry

from .gql_relay import (
    AsyncListConnectionField,
    AsyncNode,
    ConnectionPaginationOrder,
)

if TYPE_CHECKING:
    from sqlalchemy.orm.attributes import InstrumentedAttribute
    from sqlalchemy.sql.selectable import ScalarSelect

    from .schema import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

SAFE_MIN_INT = -9007199254740991
SAFE_MAX_INT = 9007199254740991

DEFAULT_PAGE_SIZE: Final[int] = 10


@shareable
class ResourceLimit(graphene.ObjectType):
    key = graphene.String()
    min = graphene.String()
    max = graphene.String(
        deprecation_reason="Deprecated since 25.14.0. The max slot limit validation has been removed as it was deemed obsolete."
    )


@shareable
class KVPair(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class ResourceLimitInput(graphene.InputObjectType):
    key = graphene.String()
    min = graphene.String()
    max = graphene.String(
        deprecation_reason="Deprecated since 25.14.0. The max slot limit validation has been removed as it was deemed obsolete."
    )


class KVPairInput(graphene.InputObjectType):
    key = graphene.String()
    value = graphene.String()


class BigInt(Scalar):
    """
    BigInt is an extension of the regular graphene.Int scalar type
    to support integers outside the range of a signed 32-bit integer.
    """

    @staticmethod
    def coerce_bigint(value: int | str) -> int | float:
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
    def parse_literal(node: graphql.language.ast.IntValueNode) -> int | float | None:
        if isinstance(node, graphql.language.ast.IntValueNode):
            num = int(node.value)
            if not (SAFE_MIN_INT <= num <= SAFE_MAX_INT):
                raise ValueError("Cannot parse integer out of the safe range.")
            if not (MIN_INT <= num <= MAX_INT):
                # treat as float
                return float(int(num))
            return num
        return None


class Bytes(Scalar):
    class Meta:
        description = "Added in 24.09.1."

    @staticmethod
    def serialize(val: bytes) -> str:
        return val.hex()

    @staticmethod
    def parse_literal(node: Any, _variables: dict[str, Any] | None = None) -> bytes | None:
        if isinstance(node, graphql.language.ast.StringValueNode):
            return bytes.fromhex(node.value)
        return None

    @staticmethod
    def parse_value(value: str) -> bytes:
        return bytes.fromhex(value)


class ImageRefType(graphene.InputObjectType):
    name = graphene.String(required=True)
    registry = graphene.String()
    architecture = graphene.String()


class UUIDFloatMap(Scalar):
    """
    Added in 25.4.0.
    Verifies that the key is a UUID (represented as a string) and the value is a float.
    """

    @staticmethod
    def serialize(value: Any) -> dict[str, float]:
        if not isinstance(value, dict):
            raise GraphQLError(f"UUIDFloatMap cannot represent non-dict value: {value!r}")

        validated: dict[str, float] = {}
        for k, v in value.items():
            try:
                key_str = str(uuid.UUID(k))
            except ValueError as e:
                raise GraphQLError(f"UUIDFloatMap cannot represent key {k} as a valid UUID") from e

            if not isinstance(v, float):
                raise GraphQLError(f"UUIDFloatMap cannot represent value {v} as a float")
            validated[key_str] = v
        return validated

    @classmethod
    def parse_literal(
        cls, node: ValueNode, _variables: dict[str, Any] | None = None
    ) -> dict[str, float]:
        if not isinstance(node, ObjectValueNode):
            raise GraphQLError(f"UUIDFloatMap cannot represent non-object value: {print_ast(node)}")
        validated: dict[str, Any] = {}
        for field in node.fields:
            key = field.name.value
            if isinstance(field.value, (FloatValueNode, IntValueNode)):
                try:
                    validated[key] = float(field.value.value)
                except Exception as e:
                    raise GraphQLError(
                        f"UUIDFloatMap cannot represent value for key {key} as a float"
                    ) from e
            else:
                raise GraphQLError(
                    f"UUIDFloatMap cannot represent non-numeric value for key {key}: {print_ast(field.value)}"
                )
        return validated

    @staticmethod
    def parse_value(value: Any) -> dict[str, float]:
        if not isinstance(value, dict):
            raise GraphQLError(f"UUIDFloatMap cannot represent non-dict value: {value!r}")
        validated: dict[str, float] = {}
        for k, v in value.items():
            try:
                key_str = str(uuid.UUID(k))
            except ValueError as e:
                raise GraphQLError(f"UUIDFloatMap cannot represent key {k} as a valid UUID") from e
            if not isinstance(v, float):
                raise GraphQLError(f"UUIDFloatMap cannot represent value {v} as a float")
            validated[key_str] = v
        return validated


def extract_object_uuid(info: graphene.ResolveInfo, global_id: str, object_name: str) -> UUID:
    """
    Converts a GraphQL global ID to its corresponding UUID.
    If the global ID is not valid, raises an error using the provided object name.
    """

    _, raw_id = AsyncNode.resolve_global_id(info, global_id)
    if not raw_id:
        raw_id = global_id

    try:
        return UUID(raw_id)
    except ValueError as e:
        raise ObjectNotFound(object_name) from e


# DataLoader-related types and classes
TContext = TypeVar("TContext")
TLoaderKey = TypeVar("TLoaderKey")
TLoaderResult = TypeVar("TLoaderResult")


def _build_gql_type_cache() -> dict[str, Any]:
    """Build a cache mapping type names to their classes from gql_legacy submodules."""
    import importlib
    from pathlib import Path

    cache: dict[str, Any] = {}
    gql_legacy_path = Path(__file__).parent

    for py_file in gql_legacy_path.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        module_name = py_file.stem
        try:
            submod = importlib.import_module(f".{module_name}", "ai.backend.manager.api.gql_legacy")
            for attr_name in getattr(submod, "__all__", dir(submod)):
                if not attr_name.startswith("_"):
                    attr = getattr(submod, attr_name, None)
                    if isinstance(attr, type):
                        cache[attr_name] = attr
        except ImportError:
            continue
    return cache


class DataLoaderManager[TContext, TLoaderKey, TLoaderResult]:
    """
    For every different combination of filtering conditions, we need to make a
    new DataLoader instance because it "batches" the database queries.
    This manager get-or-creates dataloaders with fixed conditions (represetned
    as arguments) like a cache.

    NOTE: Just like DataLoaders, it is recommended to instantiate this manager
    for every incoming API request.
    """

    cache: dict[int, DataLoader[TLoaderKey, TLoaderResult]]
    _type_cache: dict[str, Any] | None = None

    def __init__(self) -> None:
        self.cache = {}

    @classmethod
    def _get_type_cache(cls) -> dict[str, Any]:
        if cls._type_cache is None:
            cls._type_cache = _build_gql_type_cache()
        return cls._type_cache

    @staticmethod
    def _get_key(otname: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> int:
        """
        Calculate the hash of the all arguments and keyword arguments.
        """
        key = (otname,) + args
        for item in kwargs.items():
            key += item
        return hash(key)

    def load_attr(self, objtype_name: str) -> Any:
        """Load a GraphQL type class by name from gql_legacy submodules."""
        type_cache = self._get_type_cache()
        if objtype_name not in type_cache:
            raise AttributeError(f"Type '{objtype_name}' not found in gql_legacy submodules")
        return type_cache[objtype_name]

    def get_loader(
        self, context: GraphQueryContext, objtype_name: str, *args, **kwargs
    ) -> DataLoader:
        k = self._get_key(objtype_name, args, kwargs)
        loader = self.cache.get(k)
        if loader is None:
            objtype_name, has_variant, variant_name = objtype_name.partition(".")
            objtype = self.load_attr(objtype_name)
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

    @staticmethod
    def _get_func_key(
        func: Callable[
            Concatenate[TContext, Sequence[TLoaderKey], ...],
            Awaitable[Sequence[TLoaderResult]],
        ],
        **kwargs,
    ) -> int:
        func_and_kwargs = (func, *[(k, kwargs[k]) for k in sorted(kwargs.keys())])
        return hash(func_and_kwargs)

    def get_loader_by_func(
        self,
        context: TContext,
        batch_load_func: Callable[
            Concatenate[TContext, Sequence[TLoaderKey], ...],
            Awaitable[Sequence[TLoaderResult]],
        ],
        # Using kwargs-only to prevent argument position confusion
        # when DataLoader calls `batch_load_func(keys)` which is `partial(batch_load_func, **kwargs)(keys)`.
        **kwargs,
    ) -> DataLoader[TLoaderKey, TLoaderResult]:
        async def batch_load_wrapper(keys: Sequence[TLoaderKey]) -> list[TLoaderResult]:
            # aiodataloader always converts the result via list(),
            # so we can enforce type-casting here.
            return cast(list[TLoaderResult], await batch_load_func(context, keys, **kwargs))

        key = self._get_func_key(batch_load_func, **kwargs)
        loader = self.cache.get(key)
        if loader is None:
            loader = DataLoader(
                batch_load_wrapper,
                max_batch_size=128,
            )
            self.cache[key] = loader
        return loader


class Item(graphene.Interface):
    id = graphene.ID()


class PaginatedList(graphene.Interface):
    items = graphene.List(Item, required=True)
    total_count = graphene.Int(required=True)


# ref: https://github.com/python/mypy/issues/1212
T_SQLBasedGQLObject = TypeVar("T_SQLBasedGQLObject", bound="_SQLBasedGQLObject")
T_Key = TypeVar("T_Key")


class _SQLBasedGQLObject(Protocol):
    @classmethod
    def from_row(
        cls: type[T_SQLBasedGQLObject],
        ctx: GraphQueryContext,
        row: Row | DeclarativeMeta,
    ) -> T_SQLBasedGQLObject: ...


async def batch_result(
    graph_ctx: GraphQueryContext,
    db_conn: SAConnection | SASession,
    query: sa.sql.Select,
    obj_type: type[T_SQLBasedGQLObject],
    key_list: Iterable[T_Key],
    key_getter: Callable[[Row], T_Key],
) -> Sequence[T_SQLBasedGQLObject | None]:
    """
    A batched query adaptor for (key -> item) resolving patterns.
    """
    objs_per_key: dict[T_Key, T_SQLBasedGQLObject | None]
    objs_per_key = dict()
    for key in key_list:
        objs_per_key[key] = None
    if isinstance(db_conn, SASession):
        async for row in await db_conn.stream_scalars(query):
            objs_per_key[key_getter(row)] = obj_type.from_row(graph_ctx, row)
    else:
        async for row in await db_conn.stream(query):
            objs_per_key[key_getter(row)] = obj_type.from_row(graph_ctx, row)
    return [*objs_per_key.values()]


async def batch_multiresult(
    graph_ctx: GraphQueryContext,
    db_conn: SAConnection | SASession,
    query: sa.sql.Select,
    obj_type: type[T_SQLBasedGQLObject],
    key_list: Iterable[T_Key],
    key_getter: Callable[[Row], T_Key],
) -> Sequence[Sequence[T_SQLBasedGQLObject]]:
    """
    A batched query adaptor for (key -> [item]) resolving patterns.
    """
    objs_per_key: dict[T_Key, list[T_SQLBasedGQLObject]]
    objs_per_key = dict()
    for key in key_list:
        objs_per_key[key] = list()
    if isinstance(db_conn, SASession):
        async for row in await db_conn.stream_scalars(query):
            objs_per_key[key_getter(row)].append(obj_type.from_row(graph_ctx, row))
    else:
        async for row in await db_conn.stream(query):
            objs_per_key[key_getter(row)].append(obj_type.from_row(graph_ctx, row))
    return [*objs_per_key.values()]


async def batch_result_in_session(
    graph_ctx: GraphQueryContext,
    db_sess: SASession,
    query: sa.sql.Select,
    obj_type: type[T_SQLBasedGQLObject],
    key_list: Iterable[T_Key],
    key_getter: Callable[[Row], T_Key],
) -> Sequence[T_SQLBasedGQLObject | None]:
    """
    A batched query adaptor for (key -> item) resolving patterns.
    stream the result in async session.
    """
    objs_per_key: dict[T_Key, T_SQLBasedGQLObject | None]
    objs_per_key = dict()
    for key in key_list:
        objs_per_key[key] = None
    async for row in await db_sess.stream(query):
        objs_per_key[key_getter(row)] = obj_type.from_row(graph_ctx, row)
    return [*objs_per_key.values()]


async def batch_result_in_scalar_stream(
    graph_ctx: GraphQueryContext,
    db_sess: SASession,
    query: sa.sql.Select,
    obj_type: type[T_SQLBasedGQLObject],
    key_list: Iterable[T_Key],
    key_getter: Callable[[Row], T_Key],
) -> Sequence[T_SQLBasedGQLObject | None]:
    """
    A batched query adaptor for (key -> item) resolving patterns.
    stream the result scalar in async session.
    """
    objs_per_key: dict[T_Key, T_SQLBasedGQLObject | None]
    objs_per_key = {}
    for key in key_list:
        objs_per_key[key] = None
    async for row in await db_sess.stream_scalars(query):
        objs_per_key[key_getter(row)] = obj_type.from_row(graph_ctx, row)
    return [*objs_per_key.values()]


async def batch_multiresult_in_session(
    graph_ctx: GraphQueryContext,
    db_sess: SASession,
    query: sa.sql.Select,
    obj_type: type[T_SQLBasedGQLObject],
    key_list: Iterable[T_Key],
    key_getter: Callable[[Row], T_Key],
) -> Sequence[Sequence[T_SQLBasedGQLObject]]:
    """
    A batched query adaptor for (key -> [item]) resolving patterns.
    stream the result in async session.
    """
    objs_per_key: dict[T_Key, list[T_SQLBasedGQLObject]]
    objs_per_key = dict()
    for key in key_list:
        objs_per_key[key] = list()
    async for row in await db_sess.stream(query):
        objs_per_key[key_getter(row)].append(
            obj_type.from_row(graph_ctx, row),
        )
    return [*objs_per_key.values()]


async def batch_multiresult_in_scalar_stream(
    graph_ctx: GraphQueryContext,
    db_sess: SASession,
    query: sa.sql.Select,
    obj_type: type[T_SQLBasedGQLObject],
    key_list: Iterable[T_Key],
    key_getter: Callable[[Row], T_Key],
) -> Sequence[Sequence[T_SQLBasedGQLObject]]:
    """
    A batched query adaptor for (key -> [item]) resolving patterns.
    stream the result in async session.
    """
    objs_per_key: dict[T_Key, list[T_SQLBasedGQLObject]]
    objs_per_key = dict()
    for key in key_list:
        objs_per_key[key] = list()
    async for row in await db_sess.stream_scalars(query):
        objs_per_key[key_getter(row)].append(
            obj_type.from_row(graph_ctx, row),
        )
    return [*objs_per_key.values()]


def privileged_query(required_role: UserRole) -> Callable:
    def wrap(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(
            root: Any,
            info: graphene.ResolveInfo,
            *args,
            **kwargs,
        ) -> Any:
            from ai.backend.manager.models.user import UserRole

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
) -> Callable:
    """
    Prepends checks for domain/group/user access rights depending
    on the client's user and keypair information.

    :param autofill_user: When the *user_key* is not specified,
        automatically fills out the user data with the current
        user who is makeing the API request.
    :param user_key: The key used for storing user identification value
        in the keyword arguments.
    """

    def wrap(resolve_func: Callable) -> Callable:
        @functools.wraps(resolve_func)
        async def wrapped(
            root: Any,
            info: graphene.ResolveInfo,
            *args,
            **kwargs,
        ) -> Any:
            from ai.backend.manager.models.user import UserRole

            ctx: GraphQueryContext = info.context
            client_role = ctx.user["role"]
            if user_key == "access_key":
                client_user_id = ctx.access_key
            elif user_key == "email":
                client_user_id = ctx.user["email"]
            else:
                client_user_id = ctx.user["uuid"]
            client_domain = ctx.user["domain_name"]
            domain_name = kwargs.get("domain_name")
            group_id = kwargs.get("group_id") or kwargs.get("project_id")
            user_id = kwargs.get(user_key)
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
            if kwargs.get("project") is not None:
                kwargs["project"] = group_id
            kwargs[user_key] = user_id
            return await resolve_func(root, info, *args, **kwargs)

        return wrapped

    return wrap


def privileged_mutation(required_role: UserRole, target_func: Callable | None = None) -> Callable:
    def wrap(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(cls: type, root: Any, info: graphene.ResolveInfo, *args, **kwargs) -> Any:
            from ai.backend.manager.models.group import groups  # , association_groups_users
            from ai.backend.manager.models.user import UserRole

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
    result_cls: type[ResultType], _do_mutate: Callable[[], Awaitable[ResultType]]
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
    except (TimeoutError, asyncio.CancelledError):
        raise
    except Exception as e:
        log.exception("gql_mutation_wrapper(): other error")
        return result_cls(False, f"unexpected error: {e}")


async def simple_db_mutate[ResultType: graphene.ObjectType](
    result_cls: type[ResultType],
    graph_ctx: GraphQueryContext,
    mutation_query: sa.sql.Update
    | sa.sql.Insert
    | sa.sql.Delete
    | Callable[[], sa.sql.Update | sa.sql.Insert | sa.sql.Delete],
    *,
    pre_func: Callable[[SAConnection], Awaitable[None]] | None = None,
    post_func: Callable[[SAConnection, Result], Awaitable[None]] | None = None,
) -> ResultType:
    """
    Performs a database mutation based on the given
    :class:`sqlalchemy.sql.Update`, :class:`sqlalchemy.sql.Insert`, or
    :class:`sqlalchemy.sql.Delete` query, and return the wrapped result as the
    GraphQL object type given as **result_cls**.
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
        return result_cls(False, f"no matching {result_cls.__name__.lower()}")

    return await gql_mutation_wrapper(result_cls, _do_mutate)


async def simple_db_mutate_returning_item[
    ResultType: graphene.ObjectType,
    ItemType: graphene.ObjectType,
](
    result_cls: type[ResultType],
    graph_ctx: GraphQueryContext,
    mutation_query: sa.sql.Update | sa.sql.Insert | Callable[[], sa.sql.Update | sa.sql.Insert],
    *,
    item_cls: type[ItemType],
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
            row: Row[Any] | None
            if post_func:
                row = await post_func(conn, result)
            else:
                row = result.first()
            if result.rowcount > 0 and row is not None:
                return result_cls(True, "success", item_cls.from_row(graph_ctx, row))
            return result_cls(False, f"no matching {result_cls.__name__.lower()}", None)

    return await gql_mutation_wrapper(result_cls, _do_mutate)


def set_if_set(
    src: Any,
    target: MutableMapping[str, Any],
    name: str,
    *,
    clean_func: Callable[[Any], Any] | None = None,
    target_key: str | None = None,
) -> None:
    """
    Set the target dict with only non-undefined keys and their values
    from a Graphene's input object.
    (server-side function)
    """
    match src:
        case Mapping():
            v = src.get(name, Undefined)
        case _:
            v = getattr(src, name)
    # NOTE: unset optional fields are passed as graphql.Undefined.
    if v is not Undefined:
        if callable(clean_func):
            target[target_key or name] = clean_func(v)
        else:
            target[target_key or name] = v


def orm_set_if_set(
    src: object,
    target: MutableMapping[str, Any],
    name: str,
    *,
    clean_func: Callable[[Any], Any] | None = None,
    target_key: str | None = None,
) -> None:
    """
    Set the target ORM row object with only non-undefined keys and their values
    from a Graphene's input object.
    (server-side function)
    """
    v = getattr(src, name)
    # NOTE: unset optional fields are passed as graphql.Undefined.
    if v is not Undefined:
        if callable(clean_func):
            setattr(target, target_key or name, clean_func(v))
        else:
            setattr(target, target_key or name, v)


def filter_gql_undefined[T](val: T, *, default_value: T | None = None) -> T | None:
    if val is Undefined:
        return default_value
    return val


class InferenceSessionError(graphene.ObjectType):
    class InferenceSessionErrorInfo(graphene.ObjectType):
        src = graphene.String(required=True)
        name = graphene.String(required=True)
        repr = graphene.String(required=True)

    session_id = graphene.UUID()

    errors = graphene.List(graphene.NonNull(InferenceSessionErrorInfo), required=True)


class AsyncPaginatedConnectionField(AsyncListConnectionField):
    def __init__(self, type: type | str, *args, **kwargs) -> None:
        kwargs.setdefault("filter", graphene.String())
        kwargs.setdefault("order", graphene.String())
        kwargs.setdefault("offset", graphene.Int())
        super().__init__(type, *args, **kwargs)  # type: ignore[arg-type]


PaginatedConnectionField = AsyncPaginatedConnectionField


class ConnectionArgs(NamedTuple):
    cursor: str | None
    pagination_order: ConnectionPaginationOrder | None
    requested_page_size: int


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
                " one of (after, first) or (before, last)."
            )
        order = ConnectionPaginationOrder.BACKWARD
        cursor = before
    if last is not None:
        if last < 0:
            raise ValueError("Argument 'last' must be a non-negative integer.")
        if order is ConnectionPaginationOrder.FORWARD:
            raise ValueError(
                "Can only paginate with single direction, forwards or backwards. Please set only"
                " one of (after, first) or (before, last)."
            )
        order = ConnectionPaginationOrder.BACKWARD
        requested_page_size = last

    if requested_page_size is None:
        requested_page_size = DEFAULT_PAGE_SIZE

    return ConnectionArgs(cursor, order, requested_page_size)


@dataclass
class _StmtWithConditions:
    stmt: sa.sql.Select
    conditions: list[WhereClauseType]


def _apply_ordering(
    stmt: sa.sql.Select,
    id_column: sa.Column[Any] | InstrumentedAttribute[Any],
    ordering_item_list: list[OrderingItem],
    pagination_order: ConnectionPaginationOrder | None,
) -> sa.sql.Select:
    """
    Apply ORDER BY clauses for cursor-based pagination with deterministic ordering.
    This function applies the user-specified ordering columns first, then adds the id column
    as the last tiebreaker to ensure deterministic ordering (required for stable cursor pagination).
    """
    match pagination_order:
        case ConnectionPaginationOrder.FORWARD | None:
            # Default ordering by id column (ascending for forward pagination)
            id_ordering_item = OrderingItem(id_column, OrderDirection.ASC)

            def set_ordering(
                col: sa.Column[Any]
                | InstrumentedAttribute[Any]
                | sa.sql.elements.KeyedColumnElement[Any],
                direction: OrderDirection,
            ) -> Any:
                return col.asc() if direction == OrderDirection.ASC else col.desc()

        case ConnectionPaginationOrder.BACKWARD:
            # Default ordering by id column (descending for backward pagination)
            id_ordering_item = OrderingItem(id_column, OrderDirection.DESC)

            # Reverse ordering direction for backward pagination
            def set_ordering(
                col: sa.Column[Any]
                | InstrumentedAttribute[Any]
                | sa.sql.elements.KeyedColumnElement[Any],
                direction: OrderDirection,
            ) -> Any:
                return col.desc() if direction == OrderDirection.ASC else col.asc()

    # Apply ordering to stmt (id column should be applied last for deterministic ordering)
    for col, direction in [*ordering_item_list, id_ordering_item]:
        stmt = stmt.order_by(set_ordering(col, direction))

    return stmt


def _apply_filter_conditions(
    stmt: sa.sql.Select,
    orm_class: type[Any],
    filter_expr: FilterExprArg,
) -> _StmtWithConditions:
    """
    Filter conditions should be applied to both the main query statement and the count statement,
    as they define which items are included in the result set regardless of pagination.
    """
    filter_conditions: list[WhereClauseType] = []
    condition_parser = filter_expr.parser
    filter_cond = condition_parser.parse_filter(orm_class, filter_expr.expr)
    filter_conditions.append(filter_cond)
    stmt = stmt.where(filter_cond)

    return _StmtWithConditions(stmt, filter_conditions)


def _apply_cursor_pagination(
    info: graphene.ResolveInfo,
    stmt: sa.sql.Select,
    id_column: sa.Column[Any] | InstrumentedAttribute[Any],
    ordering_item_list: list[OrderingItem],
    cursor_id: str,
    pagination_order: ConnectionPaginationOrder | None,
) -> _StmtWithConditions:
    """
    Apply cursor-based pagination WHERE conditions to the statement.
    """
    cursor_conditions: list[WhereClauseType] = []
    _, cursor_row_id_str = AsyncNode.resolve_global_id(info, cursor_id)

    cursor_row_id: UUID | str
    try:
        cursor_row_id = uuid.UUID(cursor_row_id_str)
    except (ValueError, AttributeError):
        # Fall back to string if not a valid UUID (for other ID types)
        cursor_row_id = cursor_row_id_str

    def subq_to_condition(
        column_to_be_compared: sa.Column[Any]
        | InstrumentedAttribute[Any]
        | sa.sql.elements.KeyedColumnElement[Any],
        subquery: ScalarSelect[Any],
        direction: OrderDirection,
    ) -> WhereClauseType:
        """Generate cursor condition for a specific ordering column.

        This handles cursor conditions when explicit order_expr is provided.
        For example, if ordering by "created_at DESC", this ensures we only get items
        where created_at < cursor_created_at, or where created_at = cursor_created_at but id < cursor_id.
        """
        match pagination_order:
            case ConnectionPaginationOrder.FORWARD | None:
                if direction == OrderDirection.ASC:
                    cond = column_to_be_compared > subquery
                else:
                    cond = column_to_be_compared < subquery

                # Comparing ID field - The direction of inequality sign is not affected by `direction` argument here
                # because the ordering direction of ID field is always determined by `pagination_order` only.
                condition_when_same_with_subq = (column_to_be_compared == subquery) & (
                    id_column > cursor_row_id
                )
            case ConnectionPaginationOrder.BACKWARD:
                if direction == OrderDirection.ASC:
                    cond = column_to_be_compared < subquery
                else:
                    cond = column_to_be_compared > subquery
                condition_when_same_with_subq = (column_to_be_compared == subquery) & (
                    id_column < cursor_row_id
                )

        return cond | condition_when_same_with_subq

    # Add cursor conditions for explicit ordering columns (if any)
    for col, direction in ordering_item_list:
        subq = sa.select(col).where(id_column == cursor_row_id).scalar_subquery()
        cursor_conditions.append(subq_to_condition(col, subq, direction))

    # Add id-based cursor WHERE condition ONLY when no explicit ordering is provided.
    # This is CRITICAL for pagination to work when no explicit order_expr is provided.
    # When ordering_item_list is not empty, the id condition is already embedded
    # in the ordering cursor conditions above (via condition_when_same_with_subq).
    if not ordering_item_list:
        match pagination_order:
            case ConnectionPaginationOrder.FORWARD | None:
                cursor_conditions.append(id_column > cursor_row_id)
            case ConnectionPaginationOrder.BACKWARD:
                cursor_conditions.append(id_column < cursor_row_id)

    for cond in cursor_conditions:
        stmt = stmt.where(cond)

    return _StmtWithConditions(stmt, cursor_conditions)


def _build_sql_stmt_from_connection_args(
    info: graphene.ResolveInfo,
    orm_class: type[Any],
    id_column: sa.Column[Any] | InstrumentedAttribute[Any],
    filter_expr: FilterExprArg | None = None,
    order_expr: OrderExprArg | None = None,
    *,
    connection_args: ConnectionArgs,
) -> tuple[sa.sql.Select, sa.sql.Select, list[WhereClauseType]]:
    stmt = sa.select(orm_class)
    count_stmt = sa.select(sa.func.count()).select_from(orm_class)

    cursor_id, pagination_order, requested_page_size = connection_args

    # Parse explicit ordering from order_expr parameter (if provided)
    ordering_item_list: list[OrderingItem] = []
    if order_expr is not None:
        ordering_item_list = order_expr.parser.parse_order(orm_class, order_expr.expr)

    # Apply ORDER BY for cursor-based pagination
    stmt = _apply_ordering(stmt, id_column, ordering_item_list, pagination_order)

    # Apply filter conditions
    filter_conditions = []
    if filter_expr is not None:
        filter_result = _apply_filter_conditions(stmt, orm_class, filter_expr)
        stmt = filter_result.stmt
        for cond in filter_result.conditions:
            count_stmt = count_stmt.where(cond)
        filter_conditions = filter_result.conditions

    # Apply cursor pagination WHERE conditions (to stmt only)
    cursor_conditions = []
    if cursor_id is not None:
        cursor_result = _apply_cursor_pagination(
            info, stmt, id_column, ordering_item_list, cursor_id, pagination_order
        )
        stmt = cursor_result.stmt
        cursor_conditions = cursor_result.conditions

    # Apply LIMIT (to stmt only)
    if requested_page_size is not None:
        stmt = stmt.limit(requested_page_size + 1)

    return stmt, count_stmt, [*filter_conditions, *cursor_conditions]


def _build_sql_stmt_from_sql_arg(
    info: graphene.ResolveInfo,
    orm_class: type[Any],
    id_column: sa.Column[Any] | InstrumentedAttribute[Any],
    filter_expr: FilterExprArg | None = None,
    order_expr: OrderExprArg | None = None,
    *,
    limit: int,
    offset: int | None = None,
) -> tuple[sa.sql.Select, sa.sql.Select, list[WhereClauseType]]:
    stmt = sa.select(orm_class)
    count_stmt = sa.select(sa.func.count()).select_from(orm_class)
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
        count_stmt = count_stmt.where(cond)
    return stmt, count_stmt, conditions


class GraphQLConnectionSQLInfo(NamedTuple):
    sql_stmt: sa.sql.Select
    sql_count_stmt: sa.sql.Select
    sql_conditions: list[WhereClauseType]
    cursor: str | None
    pagination_order: ConnectionPaginationOrder | None
    requested_page_size: int


class FilterExprArg(NamedTuple):
    expr: str
    parser: QueryFilterParser


class OrderExprArg(NamedTuple):
    expr: str
    parser: QueryOrderParser


def generate_sql_info_for_gql_connection(
    info: graphene.ResolveInfo,
    orm_class: type[Any],
    id_column: sa.Column[Any] | InstrumentedAttribute[Any],
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
        stmt, count_stmt, conditions = _build_sql_stmt_from_connection_args(
            info,
            orm_class,
            id_column,
            filter_expr,
            order_expr,
            connection_args=connection_args,
        )
        ret = GraphQLConnectionSQLInfo(
            stmt,
            count_stmt,
            conditions,
            connection_args.cursor,
            connection_args.pagination_order,
            connection_args.requested_page_size,
        )
    else:
        page_size = first if first is not None else DEFAULT_PAGE_SIZE
        stmt, count_stmt, conditions = _build_sql_stmt_from_sql_arg(
            info,
            orm_class,
            id_column,
            filter_expr,
            order_expr,
            limit=page_size,
            offset=offset,
        )
        ret = GraphQLConnectionSQLInfo(stmt, count_stmt, conditions, None, None, page_size)

    ctx: GraphQueryContext = info.context
    max_page_size = cast(int | None, ctx.config_provider.config.api.max_gql_connection_page_size)
    if max_page_size is not None and ret.requested_page_size > max_page_size:
        raise ValueError(
            f"Cannot fetch a page larger than {max_page_size}. "
            "Set 'first' or 'last' to a smaller integer."
        )
    return ret
