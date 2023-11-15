import asyncio
import functools

from graphene.relay.node import Node, NodeField
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
    async def get_node_from_global_id(cls, info, global_id, only_type=None):
        _type, _id = cls.resolve_global_id(info, global_id)

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
            if asyncio.iscoroutinefunction(get_node):
                return await get_node(info, _id)
            else:
                return get_node(info, _id)
