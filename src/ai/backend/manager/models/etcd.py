from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Mapping, Sequence

import graphene

from ai.backend.common.logging import BraceStyleAdapter

from ..api.exceptions import InvalidAPIParameters, ObjectNotFound
from ..config import container_registry_iv
from . import UserRole
from .base import privileged_mutation

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

ETCD_CONTAINER_REGISTRY_KEY = "config/docker/registry"


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
    project = graphene.List(lambda: graphene.String)
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
            "ETCD.LOAD_ALL_CONTAINER_REGISTRIES (ak:{}, key:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
        )
        registries = await ctx.shared_config.get_container_registry()
        return [cls.from_row(hostname, config) for hostname, config in registries.items()]

    @classmethod
    async def load_registry(cls, ctx: GraphQueryContext, hostname: str) -> ContainerRegistry:
        log.info(
            "ETCD.LOAD_CONTAINER_REGISTRY (ak:{}, key:{}, hostname:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
        )
        registries = await ctx.shared_config.get_container_registry()
        try:
            registry = registries[hostname]
        except KeyError:
            raise ObjectNotFound(object_name=f"registry: {hostname}")
        return cls.from_row(hostname, registry)


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
        raw_config = {
            "": props.url,
            "type": props.registry_type,
            "project": props.project,
            "username": props.username,
            "password": props.password,
        }
        container_registry_iv.check(raw_config)
        config = {key: value for key, value in raw_config.items() if value is not None}

        log.info(
            "ETCD.CREATE_CONTAINER_REGISTRY (ak:{}, key: {}, hostname:{}, config:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
            config,
        )
        updates = ctx.shared_config.etcd.flatten(
            f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}", config
        )
        # TODO: chunk support if there are too many keys
        if len(updates) > 16:
            raise InvalidAPIParameters("Too large update! Split into smaller key-value pair sets.")
        await ctx.shared_config.etcd.put_dict(updates)
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
        cls, root, info: graphene.ResolveInfo, hostname: str, props: CreateContainerRegistryInput
    ) -> ModifyContainerRegistry:
        ctx: GraphQueryContext = info.context
        if await ctx.shared_config.etcd.get(f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}") is None:
            raise ObjectNotFound(object_name=f"registry: {hostname}")

        raw_config = {
            "": props.url,
            "type": props.registry_type,
            "project": props.project,
            "username": props.username,
            "password": props.password,
        }
        container_registry_iv.check(raw_config)
        config = {key: value for key, value in raw_config.items() if value is not None}

        log.info(
            "ETCD.MODIFY_CONTAINER_REGISTRY (ak:{}, key: {}, hostname:{}, config:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
            config,
        )
        updates = ctx.shared_config.etcd.flatten(
            f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}", config
        )
        # TODO: chunk support if there are too many keys
        if len(updates) > 16:
            raise InvalidAPIParameters("Too large update! Split into smaller key-value pair sets.")
        await ctx.shared_config.etcd.put_dict(updates)
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
        registries = await ctx.shared_config.get_container_registry()
        try:
            del registries[hostname]
        except KeyError:
            raise ObjectNotFound(object_name=f"registry: {hostname}")
        log.info(
            "ETCD.DELETE_CONTAINER_REGISTRY (ak:{}, key: {}, hostname:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
        )
        await ctx.shared_config.etcd.delete_prefix(f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}")
        await ctx.shared_config.etcd.put_prefix(ETCD_CONTAINER_REGISTRY_KEY, registries)
        return cls(result="ok")
