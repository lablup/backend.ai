from typing import TYPE_CHECKING, Self

import graphene

from ai.backend.common.utils import deep_merge
from ai.backend.manager.config.local import ManagerLocalConfig
from ai.backend.manager.config.shared import ManagerSharedConfig
from ai.backend.manager.models.user import UserRole

if TYPE_CHECKING:
    from ai.backend.manager.models.gql import GraphQueryContext

_PREFIX = "ai/backend/config"


class Config(graphene.ObjectType):
    """
    Added in 25.8.0.
    """

    service = graphene.String(
        required=True,
        description="Service name. Added in 25.8.0.",
    )
    configuration = graphene.JSONString(
        required=True,
        description="Configuration to mutate. Added in 25.8.0.",
    )
    schema = graphene.JSONString(
        required=False,
        default_value=None,
        description="JSON schema of the configuration. Added in 25.8.0.",
    )

    class Meta:
        description = "Added in 25.8.0."

    @classmethod
    def load(cls, info: graphene.ResolveInfo, service: str) -> Self:
        ctx: GraphQueryContext = info.context
        unified_config_schema = None

        def _fallback(x):
            return str(x)

        merged_raw_unified_config = deep_merge(
            ctx.unified_config.local.model_dump(mode="json", by_alias=True, fallback=_fallback),
            ctx.unified_config.shared.model_dump(mode="json", by_alias=True, fallback=_fallback),
        )

        unified_config_schema = deep_merge(
            ctx.unified_config.local.model_json_schema(mode="serialization"),
            ctx.unified_config.shared.model_json_schema(mode="serialization"),
        )

        return cls(
            service=service,
            configuration=merged_raw_unified_config,
            schema=unified_config_schema,
        )


class AvailableService(graphene.ObjectType):
    """
    Added in 25.8.0.
    """

    service_variants = graphene.List(
        graphene.String,
        required=True,
        description='Possible values of "Config.service". Added in 25.8.0.',
    )

    async def resolve_component_variants(self, info: graphene.ResolveInfo) -> list[str]:
        return ["manager", "common"]


class ModifyEtcdConfigsInput(graphene.InputObjectType):
    """
    Added in 25.8.0.
    """

    service = graphene.String(
        required=True,
        description="Service name. Added in 25.8.0.",
    )
    configuration = graphene.JSONString(
        required=True,
        description="Configuration to mutate. Added in 25.8.0.",
    )


class ModifyEtcdConfigsPayload(graphene.ObjectType):
    """
    Added in 25.8.0.
    """

    service = graphene.String(
        required=True,
        description="Service name. Added in 25.8.0.",
    )
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
    def _get_key(cls, service: str) -> str:
        return f"{_PREFIX}/{service}"

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
            input.configuration,
        )

        ctx.unified_config.local = ManagerLocalConfig.model_validate(merged_raw_unified_config)
        ctx.unified_config.shared = ManagerSharedConfig.model_validate(merged_raw_unified_config)

        await ctx.etcd.put_prefix(cls._get_key(input.service), input.configuration)

        return ModifyEtcdConfigsPayload(
            configuration=input.configuration,
            service=input.service,
        )
