from typing import TYPE_CHECKING, Final, Self

import graphene

from ai.backend.common.utils import deep_merge
from ai.backend.manager.config.local import ManagerLocalConfig
from ai.backend.manager.config.shared import ManagerSharedConfig
from ai.backend.manager.models.user import UserRole

if TYPE_CHECKING:
    from ai.backend.manager.models.gql import GraphQueryContext

_PREFIX: Final[str] = "ai/backend/config"


class AvailableService(graphene.ObjectType):
    """
    Available services for configuration.
    Added in 25.8.0.
    """

    service_variants = graphene.List(
        graphene.String,
        required=True,
        description='Possible values of "Config.service". Added in 25.8.0.',
    )

    async def resolve_component_variants(self, info: graphene.ResolveInfo) -> list[str]:
        return ["manager", "common"]


class Config(graphene.ObjectType):
    """
    Configuration data for a specific service.
    Added in 25.8.0.
    """

    service = graphene.String(
        required=True,
        description="Service name. See AvailableService.service_variants for possible values. Added in 25.8.0.",
    )
    configuration = graphene.JSONString(
        required=True,
        description="Configuration data. Added in 25.8.0.",
    )
    schema = graphene.JSONString(
        required=True,
        description="JSON schema of the configuration. Added in 25.8.0.",
    )

    class Meta:
        description = "Configuration data for a specific service. Added in 25.8.0."

    @classmethod
    def load(cls, info: graphene.ResolveInfo, service: str) -> Self:
        ctx: GraphQueryContext = info.context

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


class ModifyConfigsInput(graphene.InputObjectType):
    """
    Input data for modifying configuration.
    Added in 25.8.0.
    """

    service = graphene.String(
        required=True,
        description="Service name. See AvailableService.service_variants for possible values. Added in 25.8.0.",
    )
    configuration = graphene.JSONString(
        required=True,
        description="Configuration data to mutate. Added in 25.8.0.",
    )


class ModifyConfigsPayload(graphene.ObjectType):
    """
    Payload for the ModifyConfigs mutation.
    Added in 25.8.0.
    """

    service = graphene.String(
        required=True,
        description="Service name. See AvailableService.service_variants for possible values. Added in 25.8.0.",
    )
    configuration = graphene.JSONString(
        required=True,
        description="Configuration data to mutate. Added in 25.8.0.",
    )
    allowed_roles = (UserRole.SUPERADMIN,)


class ModifyConfigs(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    Output = ModifyConfigsPayload

    class Meta:
        description = "Updates configuration for a given service. Added in 25.8.0."

    Output = ModifyConfigsPayload

    class Arguments:
        input = ModifyConfigsInput(required=True, description="Added in 25.8.0.")

    @classmethod
    def _get_etcd_prefix_key(cls, service: str) -> str:
        return f"{_PREFIX}/{service}"

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        input: ModifyConfigsInput,
    ) -> ModifyConfigsPayload:
        ctx: GraphQueryContext = info.context

        merged_raw_unified_config = deep_merge(
            ctx.unified_config.local.model_dump(by_alias=True),
            ctx.unified_config.shared.model_dump(by_alias=True),
            input.configuration,
        )

        ctx.unified_config.local = ManagerLocalConfig.model_validate(merged_raw_unified_config)
        ctx.unified_config.shared = ManagerSharedConfig.model_validate(merged_raw_unified_config)

        await ctx.etcd.put_prefix(cls._get_etcd_prefix_key(input.service), input.configuration)

        return ModifyConfigsPayload(
            configuration=input.configuration,
            service=input.service,
        )
