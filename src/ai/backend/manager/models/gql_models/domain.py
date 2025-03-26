from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Self,
    cast,
)

import graphene
import graphql
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.types import ResourceSlot, Sentinel
from ai.backend.manager.services.domain.actions.create_domain_node import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain_node import (
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)
from ai.backend.manager.services.domain.types import DomainData, UserInfo

from ..base import (
    FilterExprArg,
    OrderExprArg,
    PaginatedConnectionField,
    generate_sql_info_for_gql_connection,
)
from ..domain import DomainRow, get_permission_ctx
from ..gql_relay import (
    AsyncNode,
    Connection,
    ConnectionResolverResult,
    GlobalIDField,
    ResolvedGlobalID,
)
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from ..rbac import (
    ClientContext,
    ScopeType,
    SystemScope,
)
from ..rbac.permission_defs import DomainPermission, ScalingGroupPermission
from ..scaling_group import get_scaling_groups
from ..user import UserRole
from .base import Bytes
from .scaling_group import ScalinGroupConnection

if TYPE_CHECKING:
    from ..domain import DomainModel
    from ..gql import GraphQueryContext
    from .scaling_group import ScalingGroupNode


class DomainPermissionValueField(graphene.Scalar):
    class Meta:
        description = f"Added in 24.12.0. One of {[val.value for val in DomainPermission]}."

    @staticmethod
    def serialize(val: DomainPermission) -> str:
        return val.value

    @staticmethod
    def parse_literal(node: Any, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return DomainPermission(node.value)

    @staticmethod
    def parse_value(value: str) -> DomainPermission:
        return DomainPermission(value)


_queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
    "id": ("id", None),
    "row_id": ("id", None),
    "name": ("name", None),
    "is_active": ("is_active", None),
    "created_at": ("created_at", dtparse),
    "modified_at": ("modified_at", dtparse),
}

_queryorder_colmap: Mapping[str, OrderSpecItem] = {
    "id": ("id", None),
    "row_id": ("id", None),
    "name": ("name", None),
    "is_active": ("is_active", None),
    "created_at": ("created_at", None),
    "modified_at": ("modified_at", None),
}


class DomainNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.12.0."

    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    total_resource_slots = graphene.JSONString()
    allowed_vfolder_hosts = graphene.JSONString()
    allowed_docker_registries = graphene.List(lambda: graphene.String)
    dotfiles = Bytes()
    integration_id = graphene.String()

    # Dynamic fields.
    scaling_groups = PaginatedConnectionField(ScalinGroupConnection)

    @classmethod
    def from_rbac_model(
        cls,
        graph_ctx: GraphQueryContext,
        obj: DomainModel,
    ) -> Self:
        return cls(
            id=obj.name,
            name=obj.name,
            description=obj.description,
            is_active=obj.is_active,
            created_at=obj.created_at,
            modified_at=obj.modified_at,
            total_resource_slots=obj.total_resource_slots,
            allowed_vfolder_hosts=obj.allowed_vfolder_hosts.to_json(),
            allowed_docker_registries=obj.allowed_docker_registries,
            dotfiles=obj.dotfiles,
            integration_id=obj.integration_id,
        )

    @classmethod
    def from_orm_model(
        cls,
        graph_ctx: GraphQueryContext,
        obj: DomainRow,
    ) -> Self:
        return cls(
            id=obj.name,
            name=obj.name,
            description=obj.description,
            is_active=obj.is_active,
            created_at=obj.created_at,
            modified_at=obj.modified_at,
            total_resource_slots=obj.total_resource_slots,
            allowed_vfolder_hosts=obj.allowed_vfolder_hosts.to_json(),
            allowed_docker_registries=obj.allowed_docker_registries,
            dotfiles=obj.dotfiles,
            integration_id=obj.integration_id,
        )

    @classmethod
    def from_dto(cls, dto: DomainData) -> Self:
        return cls(
            id=dto.name,
            name=dto.name,
            description=dto.description,
            is_active=dto.is_active,
            created_at=dto.created_at,
            modified_at=dto.modified_at,
            total_resource_slots=dto.total_resource_slots,
            allowed_vfolder_hosts=dto.allowed_vfolder_hosts.to_json(),
            allowed_docker_registries=dto.allowed_docker_registries,
            dotfiles=dto.dotfiles,
            integration_id=dto.integration_id,
        )

    async def resolve_scaling_groups(
        self, info: graphene.ResolveInfo
    ) -> ConnectionResolverResult[ScalingGroupNode]:
        from .scaling_group import ScalingGroupNode

        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader_by_func(
            graph_ctx, ScalingGroupNode.batch_load_by_domain
        )

        sgroups = await loader.load(self.name)
        return ConnectionResolverResult(sgroups, None, None, None, total_count=len(sgroups))

    @classmethod
    async def get_node(
        cls,
        info: graphene.ResolveInfo,
        id: str,
        permission: DomainPermission = DomainPermission.READ_ATTRIBUTE,
    ) -> Optional[Self]:
        from ..domain import DomainModel

        graph_ctx: GraphQueryContext = info.context
        _, domain_name = AsyncNode.resolve_global_id(info, id)
        user = graph_ctx.user
        client_ctx = ClientContext(graph_ctx.db, user["domain_name"], user["uuid"], user["role"])
        async with graph_ctx.db.begin_readonly_session() as db_session:
            permission_ctx = await get_permission_ctx(
                SystemScope(), permission, ctx=client_ctx, db_session=db_session
            )
            cond = permission_ctx.query_condition
            if cond is None:
                return None
            row = await db_session.scalar(sa.select(DomainRow).where(DomainRow.name == domain_name))
            permissions = await permission_ctx.calculate_final_permission(row)

            return cls.from_rbac_model(graph_ctx, DomainModel.from_row(row, permissions))

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        scope: ScopeType,
        permission: DomainPermission,
        filter_expr: Optional[str] = None,
        order_expr: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[Self]:
        from ..domain import DomainModel

        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter_expr, QueryFilterParser(_queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(_queryorder_colmap))
            if order_expr is not None
            else None
        )
        (
            query,
            cnt_query,
            _,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            DomainRow,
            DomainRow.name,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        user = graph_ctx.user
        client_ctx = ClientContext(graph_ctx.db, user["domain_name"], user["uuid"], user["role"])
        result: list[Self] = []
        async with graph_ctx.db.begin_readonly_session() as db_session:
            permission_ctx = await get_permission_ctx(
                scope,
                permission,
                db_session=db_session,
                ctx=client_ctx,
            )
            cond = permission_ctx.query_condition
            if cond is None:
                return ConnectionResolverResult([], cursor, pagination_order, page_size, 0)

            query = query.where(cond)
            cnt_query = cnt_query.where(cond)
            total_cnt = await db_session.scalar(cnt_query)
            async for row in await db_session.stream_scalars(query):
                row = cast(DomainRow, row)
                permissions = await permission_ctx.calculate_final_permission(row)
                result.append(
                    cls.from_rbac_model(graph_ctx, DomainModel.from_row(row, permissions))
                )
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class DomainConnection(Connection):
    class Meta:
        node = DomainNode
        description = "Added in 24.12.0"


async def _ensure_sgroup_permission(
    graph_ctx: GraphQueryContext, sgroup_names: Iterable[str], *, db_session: AsyncSession
) -> None:
    user = graph_ctx.user
    client_ctx = ClientContext(graph_ctx.db, user["domain_name"], user["uuid"], user["role"])
    sgroup_models = await get_scaling_groups(
        SystemScope(),
        ScalingGroupPermission.ASSOCIATE_WITH_SCOPES,
        sgroup_names,
        db_session=db_session,
        ctx=client_ctx,
    )
    not_allowed_sgroups = set(sgroup_names) - set([sg.name for sg in sgroup_models])
    if not_allowed_sgroups:
        raise ValueError(
            f"Not allowed to associate the domain with given scaling groups(s:{not_allowed_sgroups})"
        )


class CreateDomainNodeInput(graphene.InputObjectType):
    class Meta:
        description = "Added in 24.12.0."

    name = graphene.String(required=True)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False, default_value=True)
    total_resource_slots = graphene.JSONString(required=False, default_value={})
    allowed_vfolder_hosts = graphene.JSONString(required=False, default_value={})
    allowed_docker_registries = graphene.List(
        lambda: graphene.String, required=False, default_value=[]
    )
    integration_id = graphene.String(required=False, default_value=None)
    dotfiles = Bytes(required=False, default_value=b"\x90")

    scaling_groups = graphene.List(lambda: graphene.String, required=False)

    def to_action(self, user_info: UserInfo) -> CreateDomainNodeAction:
        return CreateDomainNodeAction(
            name=self.name,
            description=self.description,
            scaling_groups=self.scaling_groups,
            user_info=user_info,
            is_active=self.is_active,
            total_resource_slots=self.total_resource_slots,
            allowed_vfolder_hosts=self.allowed_vfolder_hosts,
            allowed_docker_registries=self.allowed_docker_registries,
            integration_id=self.integration_id,
            dotfiles=self.dotfiles,
        )


class CreateDomainNode(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Meta:
        description = "Added in 24.12.0."

    class Arguments:
        input = CreateDomainNodeInput(required=True)

    # Output fields
    ok = graphene.Boolean()
    msg = graphene.String()
    item = graphene.Field(lambda: DomainNode, required=False)

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        input: CreateDomainNodeInput,
    ) -> CreateDomainNode:
        graph_ctx: GraphQueryContext = info.context

        user_info: UserInfo = UserInfo(
            id=graph_ctx.user["uuid"],
            role=graph_ctx.user["role"],
            domain_name=graph_ctx.user["domain_name"],
        )

        res: CreateDomainNodeActionResult = (
            await graph_ctx.processors.domain.create_domain_node.wait_for_complete(
                input.to_action(user_info)
            )
        )

        domain_data: Optional[DomainData] = res.domain_data

        return CreateDomainNode(
            ok=True, msg="", item=DomainNode.from_dto(domain_data) if domain_data else None
        )


class ModifyDomainNodeInput(graphene.InputObjectType):
    class Meta:
        description = "Added in 24.12.0."

    id = GlobalIDField(required=True)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    allowed_vfolder_hosts = graphene.JSONString(required=False)
    allowed_docker_registries = graphene.List(lambda: graphene.String, required=False)
    integration_id = graphene.String(required=False)
    dotfiles = Bytes(required=False)
    sgroups_to_add = graphene.List(lambda: graphene.String, required=False)
    sgroups_to_remove = graphene.List(lambda: graphene.String, required=False)
    client_mutation_id = graphene.String(required=False)

    def _convert_field(
        self, field_value: Any, converter: Optional[Callable[[Any], Any]] = None
    ) -> Any | Sentinel:
        if field_value is graphql.Undefined:
            return Sentinel.TOKEN
        if converter is not None:
            return converter(field_value)
        return field_value

    def to_action(self, name: str, user_info: UserInfo) -> ModifyDomainNodeAction:
        return ModifyDomainNodeAction(
            name=name,
            user_info=user_info,
            description=self._convert_field(self.description),
            is_active=self._convert_field(self.is_active),
            total_resource_slots=self._convert_field(
                self.total_resource_slots, lambda x: ResourceSlot.from_user_input(x, None)
            ),
            allowed_vfolder_hosts=self._convert_field(self.allowed_vfolder_hosts),
            allowed_docker_registries=self._convert_field(self.allowed_docker_registries),
            integration_id=self._convert_field(self.integration_id),
            dotfiles=self._convert_field(self.dotfiles),
            sgroups_to_add=self._convert_field(self.sgroups_to_add),
            sgroups_to_remove=self._convert_field(self.sgroups_to_remove),
            client_mutation_id=self._convert_field(self.client_mutation_id),
        )


class ModifyDomainNode(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN, UserRole.ADMIN)

    class Meta:
        description = "Added in 24.12.0."

    class Arguments:
        input = ModifyDomainNodeInput(required=True)

    # Output fields
    item = graphene.Field(DomainNode)
    client_mutation_id = graphene.String()  # Relay output

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        input: ModifyDomainNodeInput,
    ) -> ModifyDomainNode:
        _, domain_name = cast(ResolvedGlobalID, input["id"])
        graph_ctx: GraphQueryContext = info.context
        user_info: UserInfo = UserInfo(
            id=graph_ctx.user["uuid"],
            role=graph_ctx.user["role"],
            domain_name=graph_ctx.user["domain_name"],
        )
        res: ModifyDomainNodeActionResult = (
            await graph_ctx.processors.domain.modify_domain_node.wait_for_complete(
                input.to_action(name=domain_name, user_info=user_info)
            )
        )

        domain_data: Optional[DomainData] = res.domain_data

        return ModifyDomainNode(
            item=DomainNode.from_dto(domain_data) if domain_data else None,
            client_mutation_id=input.get("client_mutation_id"),
        )
