import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, Sequence

import graphene
from pydantic import BaseModel

from ai.backend.common.utils import deep_merge
from ai.backend.manager.config.local import ManagerLocalConfig
from ai.backend.manager.config.shared import ManagerSharedConfig
from ai.backend.manager.models.user import UserRole

if TYPE_CHECKING:
    from ai.backend.manager.models.gql import GraphQueryContext

_PREFIX = "ai/backend/config"


def _get_target_attr(cfg: Any, path: Sequence[str]) -> Any:
    *keys, last_key = path
    target = cfg

    try:
        # find the target object
        for key in keys:
            target = target[key] if isinstance(target, Mapping) else getattr(target, key)

        if isinstance(target, Mapping):
            return target[last_key]
        else:
            return getattr(target, last_key)
    except (KeyError, AttributeError):
        return None


def _dump_json_str(cfg: Any) -> Any:
    if isinstance(cfg, BaseModel):
        return cfg.model_dump_json()
    return json.dumps(cfg)


class Config(graphene.ObjectType):
    """
    Added in 25.8.0.
    """

    component = graphene.String(
        required=True,
        description="Component name. Added in 25.8.0.",
    )
    server_id = graphene.String(
        required=True,
        description="Server ID. Added in 25.8.0.",
    )
    configuration = graphene.JSONString(
        required=True,
        description="Configuration to mutate. Added in 25.8.0.",
    )

    class Meta:
        description = "Added in 25.8.0."

    @classmethod
    def load(
        cls, info: graphene.ResolveInfo, component: str, server_id: str, paths: list[str]
    ) -> Self:
        ctx: GraphQueryContext = info.context
        result = _get_target_attr(ctx.unified_config.local, paths) or _get_target_attr(
            ctx.unified_config.shared, paths
        )

        return cls(
            component=component,
            server_id=server_id,
            configuration=_dump_json_str(result),
        )


class EtcdConfigSchema(graphene.ObjectType):
    """
    Added in 25.8.0.
    """

    component_variants = graphene.List(
        graphene.String,
        required=True,
        description='Possible values of "Config.component". Added in 25.8.0.',
    )

    async def resolve_component_variants(self, info: graphene.ResolveInfo) -> list[str]:
        return ["manager", "common"]


class ModifyEtcdConfigsInput(graphene.InputObjectType):
    """
    Added in 25.8.0.
    """

    component = graphene.String(
        required=True,
        description="Component name. Added in 25.8.0.",
    )
    configuration = graphene.JSONString(
        required=True,
        description="Configuration to mutate. Added in 25.8.0.",
    )


class ModifyEtcdConfigsPayload(graphene.ObjectType):
    """
    Added in 25.8.0.
    """

    configuration = graphene.JSONString(
        required=True,
        description="Configuration to mutate. Added in 25.8.0.",
    )
    allowed_roles = (UserRole.SUPERADMIN,)


class ModifyEtcdConfigs(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    Output = ModifyEtcdConfigsPayload

    class Meta:
        description = "Added in 25.8.0."

    Output = ModifyEtcdConfigsPayload

    class Arguments:
        input = ModifyEtcdConfigsInput(required=True, description="Added in 25.8.0.")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        input: ModifyEtcdConfigsInput,
    ) -> ModifyEtcdConfigsPayload:
        ctx: GraphQueryContext = info.context

        merged_raw_unified_config = deep_merge(
            ctx.unified_config.local.model_dump(by_alias=True),
            ctx.unified_config.shared.model_dump(by_alias=True),
        )
        merged_raw_unified_config = deep_merge(
            merged_raw_unified_config,
            input.configuration,
        )

        ctx.unified_config.local = ManagerLocalConfig.model_validate(merged_raw_unified_config)
        ctx.unified_config.shared = ManagerSharedConfig.model_validate(merged_raw_unified_config)

        await ctx.etcd.put_prefix(f"{_PREFIX}/{input.component}", input.configuration)

        return ModifyEtcdConfigsPayload(
            configuration=input.configuration,
        )
