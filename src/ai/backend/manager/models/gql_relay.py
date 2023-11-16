import functools
import re
from typing import Any, Callable

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
    async def get_node_from_global_id(cls, info, global_id, only_type=None) -> Any:
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


class AsyncIterableConnectionField(IterableConnectionField):
    def __init__(self, type, *args, **kwargs):
        kwargs.setdefault("filter", graphene.String())
        kwargs.setdefault("order", graphene.String())
        super().__init__(type, *args, **kwargs)

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
    async def connection_resolver(
        cls,
        resolver: Callable,
        connection_type: Connection,
        root,
        info,
        **args,
    ) -> tuple[list[graphene.ObjectType], int]:
        resolved = await resolver(root, info, **args)

        if isinstance(connection_type, graphene.NonNull):
            connection_type = connection_type.of_type

        connection = cls.resolve_connection(connection_type, args, resolved)
        connection.count = len(resolved)
        return connection


ConnectionField = AsyncIterableConnectionField
