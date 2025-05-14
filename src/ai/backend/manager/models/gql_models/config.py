import asyncio
import logging
from typing import TYPE_CHECKING, Final, Optional, Self

import graphene

from ai.backend.common.utils import deep_merge
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.local import ManagerLocalConfig
from ai.backend.manager.config.shared import ManagerSharedConfig
from ai.backend.manager.models.gql_relay import AsyncNode
from ai.backend.manager.models.user import UserRole

from ..gql_relay import Connection, ConnectionResolverResult

if TYPE_CHECKING:
    from ..gql import GraphQueryContext

_PREFIX: Final[str] = "ai/backend/config"


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class AvailableServiceNode(graphene.ObjectType):
    """
    Available services for configuration.
    Added in 25.8.0.
    """

    class Meta:
        interfaces = (AsyncNode,)
        description = "Available services for configuration. Added in 25.8.0."

    service_variants = graphene.List(
        graphene.String,
        required=True,
        description='Possible values of "Config.service". Added in 25.8.0.',
    )

    async def resolve_component_variants(self, info: graphene.ResolveInfo) -> list[str]:
        return ["manager", "common"]


class AvailableServiceConnection(Connection):
    """Added in 25.8.0."""

    class Meta:
        node = AvailableServiceNode
        description = "Added in 25.8.0."


class ServiceConfigNode(graphene.ObjectType):
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
        interfaces = (AsyncNode,)
        description = "Configuration data for a specific service. Added in 25.8.0."

    @classmethod
    async def load(cls, info: graphene.ResolveInfo, service: str) -> Self:
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
            id=service,
            service=service,
            configuration=merged_raw_unified_config,
            schema=unified_config_schema,
        )

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        services: list[str],
        filter_expr: Optional[str] = None,
        order_expr: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[Self]:
        tasks = [asyncio.create_task(ServiceConfigNode.load(info, svc)) for svc in services]

        result: list[ServiceConfigNode] = []
        # TODO: Propagate errors
        # errors: list = []

        for task in asyncio.as_completed(tasks):
            try:
                node = await task
                result.append(node)
            except Exception as exc:
                log.error(f"Failed to load service config node: {exc}")

        return ConnectionResolverResult(
            node_list=result,
            cursor=None,
            pagination_order=None,
            requested_page_size=None,
            total_count=len(result),
        )


class ServiceConfigConnection(Connection):
    """Added in 25.8.0."""

    class Meta:
        node = ServiceConfigNode
        description = "Added in 25.8.0."


class ModifyServiceConfigNodeInput(graphene.InputObjectType):
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
        description="Service configuration data to mutate. Added in 25.8.0.",
    )


class ModifyServiceConfigNodePayload(graphene.ObjectType):
    """
    Payload for the ModifyServiceConfigNode mutation.
    Added in 25.8.0.
    """

    service_config = graphene.Field(
        ServiceConfigNode,
        required=True,
        description="ServiceConfiguration Node. Added in 25.8.0.",
    )
    allowed_roles = (UserRole.SUPERADMIN,)


class ModifyServiceConfigNode(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    Output = ModifyServiceConfigNodePayload

    class Meta:
        description = "Updates configuration for a given service. Added in 25.8.0."

    Output = ModifyServiceConfigNodePayload

    class Arguments:
        input = ModifyServiceConfigNodeInput(required=True, description="Added in 25.8.0.")

    @classmethod
    def _get_etcd_prefix_key(cls, service: str) -> str:
        return f"{_PREFIX}/{service}"

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        input: ModifyServiceConfigNodeInput,
    ) -> ModifyServiceConfigNodePayload:
        ctx: GraphQueryContext = info.context

        merged_raw_unified_config = deep_merge(
            ctx.unified_config.local.model_dump(by_alias=True),
            ctx.unified_config.shared.model_dump(by_alias=True),
            input.configuration,
        )

        ctx.unified_config.local = ManagerLocalConfig.model_validate(merged_raw_unified_config)
        ctx.unified_config.shared = ManagerSharedConfig.model_validate(merged_raw_unified_config)

        await ctx.etcd.put_prefix(cls._get_etcd_prefix_key(input.service), input.configuration)

        return ModifyServiceConfigNodePayload(
            service_config=ServiceConfigNode.load(info, input.service),
        )
