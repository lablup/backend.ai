from typing import TYPE_CHECKING

import graphene

from ai.backend.common.utils import deep_merge
from ai.backend.manager.config.local import ManagerLocalConfig
from ai.backend.manager.config.shared import ManagerSharedConfig
from ai.backend.manager.models.user import UserRole

if TYPE_CHECKING:
    from ai.backend.manager.models.gql import GraphQueryContext

_PREFIX = "ai/backend/config"


class ModifyEtcdConfigsInput(graphene.InputObjectType):
    """
    Added in 25.8.0.
    """

    component = graphene.String(
        required=True,
        description="Component name. Added in 25.8.0.",
    )
    configs = graphene.JSONString(
        required=True,
        description="Configuration to mutate. Added in 25.8.0.",
    )


class ModifyEtcdConfigsPayload(graphene.ObjectType):
    """
    Added in 25.8.0.
    """

    configs = graphene.JSONString(
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
            input.configs,
        )

        ctx.unified_config.local = ManagerLocalConfig.model_validate(merged_raw_unified_config)
        ctx.unified_config.shared = ManagerSharedConfig.model_validate(merged_raw_unified_config)

        await ctx.etcd.put_prefix(f"{_PREFIX}/{input.component}", input.configs)

        return ModifyEtcdConfigsPayload(
            configs=input.configs,
        )
