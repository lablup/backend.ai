from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Mapping, Sequence

import graphene
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.logging import BraceStyleAdapter

from ..api.exceptions import InvalidAPIParameters, ObjectNotFound
from . import UserRole
from .base import privileged_mutation

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models.kernel"))  # type: ignore[name-defined]

__all__: Sequence[str] = (
    "ContainerRegistry",
    "ContainerRegistries",
    "CreateContainerRegistry",
    "ModifyContainerRegistry",
    "DeleteContainerRegistry",
)

ETCD_CONTAINER_REGISTRY_KEY = "config/docker/registry"
ETCD_CONTAINER_REGISTRY_CONFIG = {"username", "password", "project", "type", "ssl-verify"}

container_registry_iv = t.Dict(
    {
        t.Key(""): tx.URL,
        t.Key("type", default="docker"): t.String,
        t.Key("username", default=None): t.Null | t.String,
        t.Key("password", default=None): t.Null | t.String,
        t.Key("project", default=None): t.Null | tx.StringList(empty_str_as_empty_list=True),
        t.Key("ssl-verify", default=True): t.ToBool,
    }
).allow_extra("*")


class CreateContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String(required=True)
    container_type = graphene.String(required=True)
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()


class ModifyContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String(required=True)
    container_type = graphene.String(required=True)
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()


class ContainerRegistryConfig(graphene.ObjectType):
    url = graphene.String(required=True)
    container_type = graphene.String(required=True)
    project = graphene.List(lambda: graphene.String)
    username = graphene.String()
    password = graphene.String()


class ContainerRegistry(graphene.ObjectType):
    hostname = graphene.String()
    config = graphene.Field(ContainerRegistryConfig)

    @classmethod
    def from_row(cls, hostname: str, config: Mapping[str, str | None | Any]) -> ContainerRegistry:
        return cls(
            hostname=hostname,
            config=ContainerRegistryConfig(
                url=config.get(""),
                container_type=config.get("type"),
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
        raw_registries = await ctx.shared_config.etcd.get_prefix_dict(ETCD_CONTAINER_REGISTRY_KEY)
        registries = t.Mapping(t.String, container_registry_iv).check(raw_registries)

        for _, value in registries.items():
            if value["project"][0] == "[]":
                value["project"].pop()
        return [cls.from_row(hostname, config) for hostname, config in registries.items()]

    @classmethod
    async def load_registry(
        cls, graph_ctx: GraphQueryContext, hostname: str
    ) -> ContainerRegistry | None:
        log.info(
            "ETCD.LOAD_CONTAINER_REGISTRY (ak:{}, key:{}, hostname:{})",
            graph_ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
        )

        raw_registry = {
            "": await graph_ctx.shared_config.etcd.get(f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}")
        }
        if raw_registry[""] is None:
            raise ObjectNotFound(object_name=f"registry: {hostname}")
        for value in ETCD_CONTAINER_REGISTRY_CONFIG:
            raw_registry[value] = await graph_ctx.shared_config.etcd.get(
                f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}/{value}"
            )
        registry = container_registry_iv.check(raw_registry)

        if registry["project"][0] == "[]":
            registry["project"].pop()
        return cls.from_row(hostname, registry)


class ContainerRegistries(graphene.ObjectType):
    items = graphene.List(ContainerRegistry, required=True)


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
        graph_ctx: GraphQueryContext = info.context
        raw_config = {
            "": props.url,
            "type": props.container_type,
            "project": props.project,
            "username": props.username,
            "password": props.password,
        }
        valid_config = container_registry_iv.check(raw_config)
        config = {key: value for key, value in valid_config.items() if value is not None}

        log.info(
            "ETCD.CREATE_CONTAINER_REGISTRY (ak:{}, key: {}, hostname:{}, config:{})",
            graph_ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
            config,
        )
        updates = {}

        def flatten(o):
            for k, v in o.items():
                if k == "":
                    inner_prefix = f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}"
                else:
                    inner_prefix = f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}/{k}"
                if isinstance(v, Mapping):
                    flatten(v)
                else:
                    updates[inner_prefix] = v

        flatten(config)
        # TODO: chunk support if there are too many keys
        if len(updates) > 16:
            raise InvalidAPIParameters("Too large update! Split into smaller key-value pair sets.")
        await graph_ctx.shared_config.etcd.put_dict(updates)
        return cls(result="ok")


class ModifyContainerRegistry(graphene.Mutation):
    """
    CreateContainerRegistry class and ModifyContainerRegistry class share the same logic.
    """

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
        graph_ctx: GraphQueryContext = info.context
        raw_config = {
            "": props.url,
            "type": props.container_type,
            "project": props.project,
            "username": props.username,
            "password": props.password,
        }
        valid_config = container_registry_iv.check(raw_config)
        config = {key: value for key, value in valid_config.items() if value is not None}

        log.info(
            "ETCD.MODIFY_CONTAINER_REGISTRY (ak:{}, key: {}, hostname:{}, config:{})",
            graph_ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
            config,
        )
        updates = {}

        def flatten(o):
            for k, v in o.items():
                if k == "":
                    inner_prefix = f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}"
                else:
                    inner_prefix = f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}/{k}"
                if isinstance(v, Mapping):
                    flatten(v)
                else:
                    updates[inner_prefix] = v

        flatten(config)
        # TODO: chunk support if there are too many keys
        if len(updates) > 16:
            raise InvalidAPIParameters("Too large update! Split into smaller key-value pair sets.")
        await graph_ctx.shared_config.etcd.put_dict(updates)
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
        graph_ctx: GraphQueryContext = info.context
        log.info(
            "ETCD.DELETE_CONTAINER_REGISTRY (ak:{}, key: {}, hostname:{})",
            graph_ctx.access_key,
            ETCD_CONTAINER_REGISTRY_KEY,
            hostname,
        )

        for value in ETCD_CONTAINER_REGISTRY_CONFIG:
            await graph_ctx.shared_config.etcd.delete(
                f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}/{value}"
            )
        await graph_ctx.shared_config.etcd.delete(f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}")
        return cls(result="ok")
