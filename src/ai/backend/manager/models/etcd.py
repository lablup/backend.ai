from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Mapping, Sequence

import graphene

from ai.backend.common.logging import BraceStyleAdapter

from ..api.exceptions import ObjectNotFound
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
            "ETCD.LOAD_ALL_CONTAINER_REGISTRIES (ak:{}, key:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
        )
        registries = await ctx.shared_config.get_container_registry(ETCD_CONTAINER_REGISTRY_KEY)
        return [cls.from_row(hostname, config) for hostname, config in registries.items()]

    @classmethod
    async def load_registry(cls, ctx: GraphQueryContext, hostname: str) -> ContainerRegistry:
        log.info(
            "ETCD.LOAD_CONTAINER_REGISTRY (ak:{}, key:{}, hostname:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
        )
        registries = await ctx.shared_config.get_container_registry(ETCD_CONTAINER_REGISTRY_KEY)
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
        config: Dict[str, Any] = {"": props.url, "type": props.registry_type}
        set_if_set(props, config, "project")
        set_if_set(props, config, "username")
        set_if_set(props, config, "password")
        container_registry_iv.check(config)
        log.info(
            "ETCD.CREATE_CONTAINER_REGISTRY (ak:{}, key: {}, hostname:{}, config:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
            config,
        )
        updates = ctx.shared_config.flatten(ETCD_CONTAINER_REGISTRY_KEY, hostname, config)
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
        cls, root, info: graphene.ResolveInfo, hostname: str, props: ModifyContainerRegistryInput
    ) -> ModifyContainerRegistry:
        ctx: GraphQueryContext = info.context
        raw_registries = await ctx.shared_config.etcd.get_prefix_dict(ETCD_CONTAINER_REGISTRY_KEY)
        registries = dict(raw_registries)
        try:
            del registries[hostname]
        except KeyError:
            raise ObjectNotFound(object_name=f"registry: {hostname}")
        await ctx.shared_config.etcd.delete_prefix(f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}")

        updated_config: Dict[str, Any] = {"": props.url, "type": props.registry_type}
        set_if_set(props, updated_config, "project")
        set_if_set(props, updated_config, "username")
        set_if_set(props, updated_config, "password")
        container_registry_iv.check(updated_config)
        log.info(
            "ETCD.MODIFY_CONTAINER_REGISTRY (ak:{}, key: {}, hostname:{}, config:{})",
            ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
            updated_config,
        )
        updates: Dict[str, Any] = {}
        updates.update(
            ctx.shared_config.flatten(ETCD_CONTAINER_REGISTRY_KEY, hostname, updated_config)
        )
        for hostname, config in registries.items():
            updates.update(ctx.shared_config.flatten(ETCD_CONTAINER_REGISTRY_KEY, hostname, config))
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
        raw_registries = await ctx.shared_config.etcd.get_prefix_dict(ETCD_CONTAINER_REGISTRY_KEY)
        registries = dict(raw_registries)
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
        updates: Dict[str, Any] = {}
        for hostname, config in registries.items():
            updates.update(ctx.shared_config.flatten(ETCD_CONTAINER_REGISTRY_KEY, hostname, config))
        await ctx.shared_config.etcd.put_dict(updates)
        return cls(result="ok")
