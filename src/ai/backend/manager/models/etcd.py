from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Mapping, Sequence

import graphene

from ai.backend.common.logging import BraceStyleAdapter

from ..defs import PASSWORD_PLACEHOLDER
from . import UserRole
from .base import privileged_mutation, set_if_set
from .gql_relay import AsyncNode

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models.etcd"))  # type: ignore[name-defined]

__all__: Sequence[str] = (
    "ContainerRegistry",
    "CreateContainerRegistry",
    "ModifyContainerRegistry",
    "DeleteContainerRegistry",
)


class CreateContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String(required=True)
    type = graphene.String(required=True)
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ModifyContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String()
    type = graphene.String()
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ContainerRegistryConfig(graphene.ObjectType):
    url = graphene.String(required=True)
    type = graphene.String(required=True)
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ContainerRegistry(graphene.ObjectType):
    hostname = graphene.String()
    config = graphene.Field(ContainerRegistryConfig)

    class Meta:
        interfaces = (AsyncNode,)

    # TODO: `get_node()` should be implemented to query a scalar object directly by ID
    #       (https://docs.graphene-python.org/en/latest/relay/nodes/#nodes)
    # @classmethod
    # def get_node(cls, info: graphene.ResolveInfo, id):
    #     raise NotImplementedError

    @classmethod
    def from_row(cls, hostname: str, config: Mapping[str, str | list | None]) -> ContainerRegistry:
        password = config.get("password", None)
        return cls(
            id=hostname,
            hostname=hostname,
            config=ContainerRegistryConfig(
                url=config.get(""),
                type=config.get("type"),
                project=config.get("project", None),
                username=config.get("username", None),
                password=PASSWORD_PLACEHOLDER if password is not None else None,
                ssl_verify=config.get("ssl_verify", None),
            ),
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
    ) -> Sequence[ContainerRegistry]:
        log.info(
            "ETCD.LIST_CONTAINER_REGISTRY (ak:{})",
            ctx.access_key,
        )
        registries = await ctx.shared_config.list_container_registry()
        return [cls.from_row(hostname, config) for hostname, config in registries.items()]

    @classmethod
    async def load_registry(cls, ctx: GraphQueryContext, hostname: str) -> ContainerRegistry:
        log.info(
            "ETCD.GET_CONTAINER_REGISTRY (ak:{}, hostname:{})",
            ctx.access_key,
            hostname,
        )
        item = await ctx.shared_config.get_container_registry(hostname)
        return cls.from_row(hostname, item)


class CreateContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)
        props = CreateContainerRegistryInput(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls, root, info: graphene.ResolveInfo, hostname: str, props: CreateContainerRegistryInput
    ) -> CreateContainerRegistry:
        ctx: GraphQueryContext = info.context
        input_config: Dict[str, Any] = {"": props.url, "type": props.type}
        set_if_set(props, input_config, "project")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "ssl_verify")
        log.info(
            "ETCD.CREATE_CONTAINER_REGISTRY (ak:{}, hostname:{}, config:{})",
            ctx.access_key,
            hostname,
            input_config,
        )
        await ctx.shared_config.add_container_registry(hostname, input_config)
        container_registry = await ContainerRegistry.load_registry(ctx, hostname)
        return cls(container_registry=container_registry)


class ModifyContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)
        props = ModifyContainerRegistryInput(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        hostname: str,
        props: ModifyContainerRegistryInput,
    ) -> ModifyContainerRegistry:
        ctx: GraphQueryContext = info.context
        input_config: Dict[str, Any] = {}
        set_if_set(props, input_config, "url")
        set_if_set(props, input_config, "type")
        set_if_set(props, input_config, "project")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "ssl_verify")
        if "url" in input_config:
            input_config[""] = input_config.pop("url")
        log.info(
            "ETCD.MODIFY_CONTAINER_REGISTRY (ak:{}, hostname:{}, config:{})",
            ctx.access_key,
            hostname,
            input_config,
        )
        await ctx.shared_config.modify_container_registry(hostname, input_config)
        container_registry = await ContainerRegistry.load_registry(ctx, hostname)
        return cls(container_registry=container_registry)


class DeleteContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        hostname: str,
    ) -> DeleteContainerRegistry:
        ctx: GraphQueryContext = info.context
        log.info(
            "ETCD.DELETE_CONTAINER_REGISTRY (ak:{}, hostname:{})",
            ctx.access_key,
            hostname,
        )
        container_registry = await ContainerRegistry.load_registry(ctx, hostname)
        await ctx.shared_config.delete_container_registry(hostname)
        return cls(container_registry=container_registry)
