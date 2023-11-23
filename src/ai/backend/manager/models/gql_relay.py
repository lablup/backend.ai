from __future__ import annotations

import enum
import functools
import re
from typing import Any, Awaitable, Callable, NamedTuple, Protocol

import graphene
from graphene.relay.connection import (
    ConnectionOptions,
    IterableConnectionField,
    PageInfo,
    get_edge_class,
)
from graphene.relay.node import Node, NodeField, is_node
from graphene.types.utils import get_type
from graphql_relay.utils import base64, unbase64


class PageInfoType(Protocol):
    @property
    def start_cursor(self) -> str | None: ...

    @property
    def end_cursor(self) -> str | None: ...

    @property
    def has_previous_page(self) -> bool: ...

    @property
    def has_next_page(self) -> bool: ...


class EdgeType(Protocol):
    @property
    def node(self) -> Any: ...

    @property
    def cursor(self) -> str: ...


class ConnectionType(Protocol):
    @property
    def edges(self) -> list[EdgeType]: ...

    @property
    def page_info(self) -> PageInfoType: ...


class EdgeConstructor(Protocol):
    def __call__(
        self,
        *,
        node: Any,
        cursor: str,
    ) -> EdgeType: ...


class ConnectionConstructor(Protocol):
    @property
    def Edge(self) -> EdgeConstructor: ...

    def __call__(
        self,
        *,
        edges: list[EdgeType],
        page_info: PageInfoType,
        count: int,
    ) -> Connection: ...


class AsyncNodeField(NodeField):
    def wrap_resolve(self, parent_resolver):
        return functools.partial(self.node_type.node_resolver, get_type(self.field_type))


class AsyncNode(Node):
    class Meta:
        name = "AsyncNode"

    @classmethod
    def Field(cls, *args, **kwargs):
        return AsyncNodeField(cls, *args, **kwargs)

    @classmethod
    async def node_resolver(cls, only_type, root, info, id):
        return await cls.get_node_from_global_id(info, id, only_type=only_type)

    @staticmethod
    def to_global_id(type_, id) -> str:
        return base64(f"{type_}:{id}")

    @classmethod
    def resolve_global_id(cls, info, global_id: str) -> tuple[str, str]:
        unbased_global_id = unbase64(global_id)
        type_, _, id_ = unbased_global_id.partition(":")
        return type_, id_

    @classmethod
    async def get_node_from_global_id(cls, info, global_id: str, only_type=None) -> Any:
        _type, _ = cls.resolve_global_id(info, global_id)

        graphene_type = info.schema.get_type(_type)
        if graphene_type is None:
            raise Exception(f'Relay Node "{_type}" not found in schema')

        graphene_type = graphene_type.graphene_type

        if only_type:
            assert graphene_type == only_type, f"Must receive a {only_type._meta.name} id."

        if cls not in graphene_type._meta.interfaces:
            raise Exception(f'ObjectType "{_type}" does not implement the "{cls}" interface.')

        get_node = getattr(graphene_type, "get_node", None)
        if get_node:
            return await get_node(info, global_id)
        raise Exception(f'ObjectType "{_type}" does not implement `get_node` method.')


class Connection(graphene.ObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls, node=None, name=None, strict_types=False, _meta=None, **options
    ):
        if not _meta:
            _meta = ConnectionOptions(cls)
        assert node, f"You have to provide a node in {cls.__name__}.Meta"
        assert isinstance(node, graphene.NonNull) or issubclass(
            node,
            (
                graphene.Scalar,
                graphene.Enum,
                graphene.ObjectType,
                graphene.Interface,
                graphene.Union,
                graphene.NonNull,
            ),
        ), f'Received incompatible node "{node}" for Connection {cls.__name__}.'

        base_name = re.sub("Connection$", "", name or cls.__name__) or node._meta.name
        if not name:
            name = f"{base_name}Connection"

        options["name"] = name

        _meta.node = node

        if not _meta.fields:
            _meta.fields = {}

        if "page_info" not in _meta.fields:
            _meta.fields["page_info"] = graphene.Field(
                PageInfo,
                name="pageInfo",
                required=True,
                description="Pagination data for this connection.",
            )

        if "edges" not in _meta.fields:
            edge_class = get_edge_class(cls, node, base_name, strict_types)  # type: ignore
            cls.Edge = edge_class
            _meta.fields["edges"] = graphene.Field(
                graphene.NonNull(
                    graphene.List(graphene.NonNull(edge_class) if strict_types else edge_class)
                ),
                description="Contains the nodes in this connection.",
            )

        if "count" not in _meta.fields:
            _meta.fields["count"] = graphene.Field(
                graphene.Int(),
                name="count",
                description="Total count of the GQL nodes of the query.",
            )

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class PaginationOrder(enum.Enum):
    FORWARD = "forward"
    BACKWARD = "backward"


class ConnectionArgs(NamedTuple):
    cursor: str | None
    pagination_order: PaginationOrder
    page_size: int | None


class ConnectionResolverResult(NamedTuple):
    node_list: list[Any]
    cursor: str | None
    pagination_order: PaginationOrder
    page_size: int | None
    total_count: int


class AsyncListConnectionField(IterableConnectionField):
    @property
    def type(self):
        type_ = super(IterableConnectionField, self).type
        connection_type = type_
        if isinstance(type_, graphene.NonNull):
            connection_type = type_.of_type

        if is_node(connection_type):
            raise Exception("ConnectionFields now need a explicit ConnectionType for Nodes.")

        assert issubclass(connection_type, Connection), (
            f"{self.__class__.__name__} type has to be a subclass of"
            f' ai.backend.manager.models.gql_relay.Connection. Received "{connection_type}".'
        )
        return type_

    @classmethod
    def resolve_connection(
        cls,
        connection_type: ConnectionConstructor,
        args: dict[str, Any] | None,
        resolved: list[Any] | Connection,
        *,
        cursor: str | None = None,
        page_size: int | None = None,
        pagination_order: PaginationOrder = PaginationOrder.FORWARD,
        count: int = -1,
    ) -> Connection:
        if not isinstance(resolved, list):
            return resolved

        assert isinstance(resolved, list), (
            "Resolved value from the connection field has to be a list or instance of"
            f' {connection_type}. Received "{resolved}"'
        )

        orig_resolved_len = len(resolved)
        if page_size is not None:
            resolved = resolved[:page_size]
        if pagination_order == PaginationOrder.BACKWARD:
            resolved = resolved[::-1]
        edge_type = connection_type.Edge
        edges = [
            edge_type(
                node=value,
                cursor=AsyncNode.to_global_id(str(connection_type._meta.node), value.id),  # type: ignore[attr-defined]
            )
            for value in resolved
        ]
        return connection_type(
            edges=edges,
            page_info=PageInfo(
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                has_previous_page=(
                    pagination_order == PaginationOrder.BACKWARD
                    and page_size is not None
                    and page_size < orig_resolved_len
                ),
                has_next_page=(
                    pagination_order == PaginationOrder.FORWARD
                    and page_size is not None
                    and page_size < orig_resolved_len
                ),
            ),
            count=count,
        )

    @classmethod
    async def connection_resolver(
        cls,
        resolver: Callable[..., Awaitable[ConnectionResolverResult]],
        connection_type: ConnectionConstructor,
        root,
        info,
        **args,
    ) -> Connection:
        resolved, cursor, pagination_order, page_size, total_count = await resolver(
            root, info, **args
        )

        if isinstance(connection_type, graphene.NonNull):
            connection_type = connection_type.of_type

        return cls.resolve_connection(
            connection_type,
            args,
            resolved,
            cursor=cursor,
            page_size=page_size,
            pagination_order=pagination_order,
            count=total_count,
        )


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

    Default pagination direction is Forward.
    """
    order: PaginationOrder | None = None
    cursor: str | None = None
    page_size: int | None = None

    if after is not None:
        order = PaginationOrder.FORWARD
        cursor = after
    if first is not None:
        if first < 0:
            raise ValueError("Argument 'first' must be a non-negative integer.")
        order = PaginationOrder.FORWARD
        page_size = first

    if before is not None:
        if order is PaginationOrder.FORWARD:
            raise ValueError(
                "Can only paginate with single direction, forwards or backwards. Please set only"
                " one of (after, first) and (before, last)."
            )
        order = PaginationOrder.BACKWARD
        cursor = before
    if last is not None:
        if last < 0:
            raise ValueError("Argument 'last' must be a non-negative integer.")
        if order is PaginationOrder.FORWARD:
            raise ValueError(
                "Can only paginate with single direction, forwards or backwards. Please set only"
                " one of (after, first) and (before, last)."
            )
        order = PaginationOrder.BACKWARD
        page_size = last

    return ConnectionArgs(cursor, order or PaginationOrder.FORWARD, page_size)


ConnectionField = AsyncListConnectionField
