from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Self,
    Sequence,
)

import graphene
import graphql
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.engine.row import Row

from ai.backend.common.exception import (
    InvalidAPIParameters,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.group.types import GroupCreator, GroupData, GroupModifier
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.group.actions.create_group import CreateGroupAction
from ai.backend.manager.services.group.actions.delete_group import (
    DeleteGroupAction,
)
from ai.backend.manager.services.group.actions.modify_group import ModifyGroupAction
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
)
from ai.backend.manager.types import OptionalState, TriState

from ..base import (
    BigInt,
    FilterExprArg,
    OrderExprArg,
    PaginatedConnectionField,
    batch_multiresult,
    batch_result,
    generate_sql_info_for_gql_connection,
    privileged_mutation,
)
from ..gql_relay import (
    AsyncNode,
    Connection,
    ConnectionResolverResult,
)
from ..group import (
    AssocGroupUserRow,
    GroupRow,
    ProjectType,
    association_groups_users,
    get_permission_ctx,
    groups,
)
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from ..rbac.context import ClientContext
from ..rbac.permission_defs import ProjectPermission
from .user import UserConnection, UserNode

if TYPE_CHECKING:
    from ..gql import GraphQueryContext
    from ..rbac import ContainerRegistryScope, ScopeType
    from .scaling_group import ScalingGroup


__all__ = (
    "GroupNode",
    "GroupConnection",
    "Group",
    "GroupInput",
    "ModifyGroupInput",
    "CreateGroup",
    "ModifyGroup",
    "DeleteGroup",
    "PurgeGroup",
    "GroupPermissionField",
)


class GroupNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    row_id = graphene.UUID(description="Added in 24.03.7. The undecoded id value stored in DB.")
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    domain_name = graphene.String()
    total_resource_slots = graphene.JSONString()
    allowed_vfolder_hosts = graphene.JSONString()
    integration_id = graphene.String()
    resource_policy = graphene.String()
    type = graphene.String(description=f"Added in 24.03.7. One of {[t.name for t in ProjectType]}.")
    container_registry = graphene.JSONString(description="Added in 24.03.7.")
    scaling_groups = graphene.List(
        lambda: graphene.String,
    )

    registry_quota = BigInt(description="Added in 25.3.0.")

    user_nodes = PaginatedConnectionField(
        UserConnection,
    )

    queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("id", None),
        "name": ("name", None),
        "is_active": ("is_active", None),
        "created_at": ("created_at", dtparse),
        "modified_at": ("modified_at", dtparse),
        "domain_name": ("domain_name", None),
        "resource_policy": ("resource_policy", None),
    }

    queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("id", None),
        "name": ("name", None),
        "is_active": ("is_active", None),
        "created_at": ("created_at", None),
        "modified_at": ("modified_at", None),
        "domain_name": ("domain_name", None),
        "resource_policy": ("resource_policy", None),
    }

    @classmethod
    def from_row(
        cls,
        graph_ctx: GraphQueryContext,
        row: GroupRow,
    ) -> Self:
        return cls(
            id=row.id,
            row_id=row.id,
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            modified_at=row.modified_at,
            domain_name=row.domain_name,
            total_resource_slots=row.total_resource_slots.to_json() or {},
            allowed_vfolder_hosts=row.allowed_vfolder_hosts.to_json() or {},
            integration_id=row.integration_id,
            resource_policy=row.resource_policy,
            type=row.type.name,
            container_registry=row.container_registry,
        )

    async def resolve_scaling_groups(self, info: graphene.ResolveInfo) -> Sequence[ScalingGroup]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "ScalingGroup.by_group",
        )
        sgroups = await loader.load(self.id)
        return [sg.name for sg in sgroups]

    async def resolve_user_nodes(
        self,
        info: graphene.ResolveInfo,
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult[Self]:
        from ..user import UserRow

        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter, QueryFilterParser(UserNode._queryfilter_fieldspec))
            if filter is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order, QueryOrderParser(UserNode._queryorder_colmap))
            if order is not None
            else None
        )
        (
            query,
            _,
            conditions,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            UserRow,
            UserRow.uuid,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        j = sa.join(UserRow, AssocGroupUserRow)
        user_query = query.select_from(j).where(AssocGroupUserRow.group_id == self.id)
        cnt_query = (
            sa.select(sa.func.count()).select_from(j).where(AssocGroupUserRow.group_id == self.id)
        )
        for cond in conditions:
            cnt_query = cnt_query.where(cond)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            user_rows = (await db_session.scalars(user_query)).all()
            result = [type(self).from_row(graph_ctx, row) for row in user_rows]
            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    async def resolve_registry_quota(self, info: graphene.ResolveInfo) -> int:
        graph_ctx: GraphQueryContext = info.context
        scope_id = ProjectScope(project_id=self.id, domain_name=None)

        return await graph_ctx.services_ctx.per_project_container_registries_quota.read_quota(
            scope_id,
        )

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id) -> Self:
        graph_ctx: GraphQueryContext = info.context
        _, group_id = AsyncNode.resolve_global_id(info, id)
        query = sa.select(GroupRow).where(GroupRow.id == group_id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            group_row = (await db_session.scalars(query)).first()
            return cls.from_row(graph_ctx, group_row)

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        scope: ScopeType,
        container_registry_scope: Optional[ContainerRegistryScope] = None,
        permission: ProjectPermission = ProjectPermission.READ_ATTRIBUTE,
        filter_expr: Optional[str] = None,
        order_expr: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[Self]:
        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter_expr, QueryFilterParser(cls.queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(cls.queryorder_colmap))
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
            GroupRow,
            GroupRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.connect() as db_conn:
            user = graph_ctx.user
            client_ctx = ClientContext(
                graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
            )
            permission_ctx = await get_permission_ctx(
                db_conn, client_ctx, permission, scope, container_registry_scope
            )
            cond = permission_ctx.query_condition
            if cond is None:
                return ConnectionResolverResult([], cursor, pagination_order, page_size, 0)
            query = query.where(cond)
            cnt_query = cnt_query.where(cond)

            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                group_rows = (await db_session.scalars(query)).all()
                total_cnt = await db_session.scalar(cnt_query)
                result = [cls.from_row(graph_ctx, row) for row in group_rows]

        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class GroupConnection(Connection):
    class Meta:
        node = GroupNode
        description = "Added in 24.03.0"


class GroupPermissionField(graphene.Scalar):
    class Meta:
        description = f"Added in 25.3.0. One of {[val.value for val in ProjectPermission]}."

    @staticmethod
    def serialize(val: ProjectPermission) -> str:
        return val.value

    @staticmethod
    def parse_literal(node: Any, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return ProjectPermission(node.value)

    @staticmethod
    def parse_value(value: str) -> ProjectPermission:
        return ProjectPermission(value)


class Group(graphene.ObjectType):
    id = graphene.UUID()
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    domain_name = graphene.String()
    total_resource_slots = graphene.JSONString()
    allowed_vfolder_hosts = graphene.JSONString()
    integration_id = graphene.String()
    resource_policy = graphene.String()
    type = graphene.String(description="Added in 24.03.0.")
    container_registry = graphene.JSONString(description="Added in 24.03.0.")

    scaling_groups = graphene.List(lambda: graphene.String)

    @classmethod
    def from_row(cls, graph_ctx: GraphQueryContext, row: Row) -> Optional[Group]:
        if row is None:
            return None
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            domain_name=row["domain_name"],
            total_resource_slots=(
                row["total_resource_slots"].to_json()
                if row["total_resource_slots"] is not None
                else {}
            ),
            allowed_vfolder_hosts=row["allowed_vfolder_hosts"].to_json(),
            integration_id=row["integration_id"],
            resource_policy=row["resource_policy"],
            type=row["type"].name,
            container_registry=row["container_registry"],
        )

    @classmethod
    def from_dto(cls, dto: Optional[GroupData]) -> Optional[Self]:
        if dto is None:
            return None
        return cls(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            is_active=dto.is_active,
            created_at=dto.created_at,
            modified_at=dto.modified_at,
            domain_name=dto.domain_name,
            total_resource_slots=dto.total_resource_slots.to_json()
            if dto.total_resource_slots
            else {},
            allowed_vfolder_hosts=dto.allowed_vfolder_hosts.to_json(),
            integration_id=dto.integration_id,
            resource_policy=dto.resource_policy,
            type=dto.type.name,
            container_registry=dto.container_registry,
        )

    async def resolve_scaling_groups(self, info: graphene.ResolveInfo) -> Sequence[ScalingGroup]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "ScalingGroup.by_group",
        )
        sgroups = await loader.load(self.id)
        return [sg.name for sg in sgroups]

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        type: list[ProjectType] = [ProjectType.GENERAL],
    ) -> Sequence[Group]:
        query = sa.select([groups]).select_from(groups).where(groups.c.type.in_(type))
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if is_active is not None:
            query = query.where(groups.c.is_active == is_active)
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_id(
        cls,
        graph_ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[Group | None]:
        query = sa.select([groups]).select_from(groups).where(groups.c.id.in_(group_ids))
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if is_active is not None:
            query = query.where(groups.c.is_active == is_active)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_result(
                graph_ctx,
                conn,
                query,
                cls,
                group_ids,
                lambda row: row["id"],
            )

    @classmethod
    async def batch_load_by_name(
        cls,
        graph_ctx: GraphQueryContext,
        group_names: Sequence[str],
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[Sequence[Group | None]]:
        query = sa.select([groups]).select_from(groups).where(groups.c.name.in_(group_names))
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if is_active is not None:
            query = query.where(groups.c.is_active == is_active)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx,
                conn,
                query,
                cls,
                group_names,
                lambda row: row["name"],
            )

    @classmethod
    async def batch_load_by_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_ids: Sequence[uuid.UUID],
        *,
        type: list[ProjectType] | None = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[Sequence[Group | None]]:
        if type is None:
            _type = [ProjectType.GENERAL]
        else:
            _type = type
        j = sa.join(
            groups,
            association_groups_users,
            groups.c.id == association_groups_users.c.group_id,
        )
        query = (
            sa.select([groups, association_groups_users.c.user_id])
            .select_from(j)
            .where(association_groups_users.c.user_id.in_(user_ids) & (groups.c.type.in_(_type)))
        )
        if is_active is not None:
            query = query.where(groups.c.is_active == is_active)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx,
                conn,
                query,
                cls,
                user_ids,
                lambda row: row["user_id"],
            )

    @classmethod
    async def get_groups_for_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_id: uuid.UUID,
    ) -> Sequence[Group]:
        j = sa.join(
            groups,
            association_groups_users,
            groups.c.id == association_groups_users.c.group_id,
        )
        query = (
            sa.select([groups]).select_from(j).where(association_groups_users.c.user_id == user_id)
        )
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]


class GroupInput(graphene.InputObjectType):
    type = graphene.String(
        required=False,
        default_value="GENERAL",
        description=(
            f"Added in 24.03.0. Available values: {', '.join([p.name for p in ProjectType])}"
        ),
    )
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    domain_name = graphene.String(required=True)
    total_resource_slots = graphene.JSONString(required=False, default_value={})
    allowed_vfolder_hosts = graphene.JSONString(required=False, default_value={})
    integration_id = graphene.String(required=False, default_value="")
    resource_policy = graphene.String(required=False, default_value="default")
    container_registry = graphene.JSONString(
        required=False, default_value={}, description="Added in 24.03.0"
    )

    def to_action(self, name: str) -> CreateGroupAction:
        def value_or_none(value):
            return value if value is not Undefined else None

        type_val = None if self.type is Undefined else ProjectType[self.type]
        description_val = value_or_none(self.description)
        is_active_val = value_or_none(self.is_active)
        total_resource_slots_val = (
            None
            if self.total_resource_slots is Undefined
            else ResourceSlot.from_user_input(self.total_resource_slots, None)
        )
        allowed_vfolder_hosts_val = value_or_none(self.allowed_vfolder_hosts)
        integration_id_val = value_or_none(self.integration_id)
        resource_policy_val = value_or_none(self.resource_policy)
        container_registry_val = value_or_none(self.container_registry)

        return CreateGroupAction(
            input=GroupCreator(
                name=name,
                domain_name=self.domain_name,
                type=type_val,
                description=description_val,
                is_active=is_active_val,
                total_resource_slots=total_resource_slots_val,
                allowed_vfolder_hosts=allowed_vfolder_hosts_val,
                integration_id=integration_id_val,
                resource_policy=resource_policy_val,
                container_registry=container_registry_val,
            ),
        )


class ModifyGroupInput(graphene.InputObjectType):
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    domain_name = graphene.String(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    user_update_mode = graphene.String(required=False)
    user_uuids = graphene.List(lambda: graphene.String, required=False)
    allowed_vfolder_hosts = graphene.JSONString(required=False)
    integration_id = graphene.String(required=False)
    resource_policy = graphene.String(required=False)
    container_registry = graphene.JSONString(
        required=False, default_value={}, description="Added in 24.03.0"
    )

    def to_action(self, group_id: uuid.UUID) -> ModifyGroupAction:
        return ModifyGroupAction(
            group_id=group_id,
            modifier=GroupModifier(
                name=OptionalState[str].from_graphql(
                    self.name,
                ),
                domain_name=OptionalState[str].from_graphql(
                    self.domain_name,
                ),
                description=TriState[str].from_graphql(
                    self.description,
                ),
                is_active=OptionalState[bool].from_graphql(
                    self.is_active,
                ),
                total_resource_slots=OptionalState[ResourceSlot].from_graphql(
                    self.total_resource_slots
                    if (self.total_resource_slots is Undefined or self.total_resource_slots is None)
                    else ResourceSlot.from_user_input(self.total_resource_slots, None),
                ),
                allowed_vfolder_hosts=OptionalState[dict[str, str]].from_graphql(
                    self.allowed_vfolder_hosts,
                ),
                integration_id=OptionalState[str].from_graphql(
                    self.integration_id,
                ),
                resource_policy=OptionalState[str].from_graphql(
                    self.resource_policy,
                ),
                container_registry=TriState[dict[str, str]].from_graphql(
                    self.container_registry,
                ),
            ),
            user_update_mode=OptionalState[str].from_graphql(
                self.user_update_mode,
            ),
            user_uuids=OptionalState[list[str]].from_graphql(
                self.user_uuids,
            ),
        )


class CreateGroup(graphene.Mutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        name = graphene.String(required=True)
        props = GroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    group = graphene.Field(lambda: Group, required=False)

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda name, props, **kwargs: (props.domain_name, None),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: GroupInput,
    ) -> CreateGroup:
        graph_ctx: GraphQueryContext = info.context
        if name.strip() == "" or len(name) > 64:
            raise InvalidAPIParameters(
                "Group name cannot be empty or whitespace and must not exceed 64 characters."
            )

        action = props.to_action(name)
        res = await graph_ctx.processors.group.create_group.wait_for_complete(action)
        return cls(
            ok=True,
            msg="success",
            group=Group.from_dto(res.data),
        )


class ModifyGroup(graphene.Mutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)
        props = ModifyGroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    group = graphene.Field(lambda: Group, required=False)

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        gid: uuid.UUID,
        props: ModifyGroupInput,
    ) -> ModifyGroup:
        graph_ctx: GraphQueryContext = info.context

        action = props.to_action(gid)
        res = await graph_ctx.processors.group.modify_group.wait_for_complete(action)
        return cls(
            ok=True,
            msg="success",
            group=Group.from_dto(res.data) if res.data else None,
        )


class DeleteGroup(graphene.Mutation):
    """
    Instead of deleting the group, just mark it as inactive.
    """

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(cls, root, info: graphene.ResolveInfo, gid: uuid.UUID) -> DeleteGroup:
        ctx: GraphQueryContext = info.context
        await ctx.processors.group.delete_group.wait_for_complete(DeleteGroupAction(gid))
        return cls(ok=True, msg="success")


class PurgeGroup(graphene.Mutation):
    """
    Completely deletes a group from DB.

    Group's vfolders and their data will also be lost
    as well as the kernels run from the group.
    There is no migration of the ownership for group folders.
    """

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(cls, root, info: graphene.ResolveInfo, gid: uuid.UUID) -> PurgeGroup:
        graph_ctx: GraphQueryContext = info.context

        await graph_ctx.processors.group.purge_group.wait_for_complete(PurgeGroupAction(gid))
        return cls(ok=True, msg="success")
