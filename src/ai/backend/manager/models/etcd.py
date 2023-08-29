from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Mapping, Sequence

import graphene

from ai.backend.common.logging import BraceStyleAdapter

from ..config import container_registry_iv
from . import UserRole
from .base import privileged_mutation, set_if_set

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(
    logging.getLogger("ai.backend.manager.models.etcd")
)  # type: ignore[name-defined]

__all__: Sequence[str] = (
    "ContainerRegistry",
    "CreateContainerRegistry",
    "ModifyContainerRegistry",
    "DeleteContainerRegistry",
)


class CreateContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String(required=True)
    registry_type = graphene.String(required=True)
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()


class ModifyContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String(required=True)
    registry_type = graphene.String(required=True)
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()


class ContainerRegistryConfig(graphene.ObjectType):
    url = graphene.String(required=True)
    registry_type = graphene.String(required=True)
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()


class ContainerRegistry(graphene.ObjectType):
    hostname = graphene.String()
    config = graphene.Field(ContainerRegistryConfig)

    @classmethod
    def from_row(cls, hostname: str, config: Mapping[str, str | list | None]) -> ContainerRegistry:
        return cls(
            hostname=hostname,
            config=ContainerRegistryConfig(
                url=config.get(""),
                registry_type=config.get("type"),
                project=config.get("project", None),
                username=config.get("username", None),
                password=config.get("password", None),
            ),
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
    ) -> Sequence[ContainerRegistry]:
        log.info(
            "ETCD.LOAD_ALL_CONTAINER_REGISTRIES (ak:{})",
            ctx.access_key,
        )
        registries = await ctx.shared_config.list_container_registry()
        return [cls.from_row(hostname, config) for hostname, config in registries.items()]

    @classmethod
    async def load_registry(cls, ctx: GraphQueryContext, hostname: str) -> ContainerRegistry:
        log.info(
            "ETCD.LOAD_CONTAINER_REGISTRY (ak:{}, hostname:{})",
            ctx.access_key,
            hostname,
        )
        item = await ctx.shared_config.get_container_registry(hostname)
        return cls.from_row(hostname, item)


class CreateContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    result = graphene.String()

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
        input_config: Dict[str, Any] = {"": props.url, "type": props.registry_type}
        set_if_set(props, input_config, "project")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        registry_config = container_registry_iv.check(input_config)
        log.info(
            "ETCD.CREATE_CONTAINER_REGISTRY (ak:{}, hostname:{}, config:{})",
            ctx.access_key,
            hostname,
            registry_config,
        )
        await ctx.shared_config.add_container_registry(hostname, registry_config)
        return cls(result="ok")


class ModifyContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    result = graphene.String()

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
        input_config: Dict[str, Any] = {"": props.url, "type": props.registry_type}
        set_if_set(props, input_config, "project")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        registry_config = container_registry_iv.check(input_config)
        log.info(
            "ETCD.MODIFY_CONTAINER_REGISTRY (ak:{}, hostname:{}, config:{})",
            ctx.access_key,
            hostname,
            registry_config,
        )
        await ctx.shared_config.modify_container_registry(hostname, registry_config)
        return cls(result="ok")


class DeleteContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    result = graphene.String()

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
        await ctx.shared_config.delete_container_registry(hostname)
        return cls(result="ok")
