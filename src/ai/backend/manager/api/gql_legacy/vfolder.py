from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Self,
    cast,
)

import graphene
import graphene_federation
import graphql
import sqlalchemy as sa
import trafaret as t
from dateutil.parser import ParserError
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import joinedload, selectinload

from ai.backend.common.config import model_definition_iv
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import VFolderNotFound
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderID,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.resource import DataTransformationFailed
from ai.backend.manager.errors.storage import (
    ModelCardParseError,
    QuotaScopeNotFoundError,
    VFolderBadRequest,
    VFolderOperationFailed,
)
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.minilang import FieldSpecItem, OrderSpecItem
from ai.backend.manager.models.minilang.ordering import QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser
from ai.backend.manager.models.rbac import (
    ScopeType,
    SystemScope,
)
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.rbac.permission_defs import (
    VFolderPermission as VFolderRBACPermission,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.vfolder import (
    DEAD_VFOLDER_STATUSES,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderRow,
    ensure_quota_scope_accessible_by_user,
    get_permission_ctx,
    is_unmanaged,
    vfolder_permissions,
    vfolders,
)

# Re-export for backward compatibility
__all__ = (
    "ModelCard",
    "ModelCardConnection",
    "QuotaDetails",
    "QuotaScope",
    "QuotaScopeInput",
    "SetQuotaScope",
    "UnsetQuotaScope",
    "VFolderPermissionValueField",
    "VirtualFolder",
    "VirtualFolderConnection",
    "VirtualFolderList",
    "VirtualFolderNode",
    "VirtualFolderPermission",
    "VirtualFolderPermissionList",
)
from .base import (
    BigInt,
    FilterExprArg,
    Item,
    OrderExprArg,
    PaginatedList,
    batch_multiresult,
    batch_multiresult_in_scalar_stream,
    batch_result_in_scalar_stream,
    generate_sql_info_for_gql_connection,
)
from .gql_relay import AsyncNode, Connection, ConnectionResolverResult

if TYPE_CHECKING:
    from .schema import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFolderPermissionValueField(graphene.Scalar):
    class Meta:
        description = f"Added in 24.09.0. One of {[val.value for val in VFolderRBACPermission]}."

    @staticmethod
    def serialize(val: VFolderRBACPermission) -> str:
        return val.value

    @staticmethod
    def parse_literal(node: Any, _variables: dict | None = None) -> VFolderRBACPermission | None:
        if isinstance(node, graphql.language.ast.StringValueNode):
            return VFolderRBACPermission(node.value)
        return None

    @staticmethod
    def parse_value(value: str) -> VFolderRBACPermission:
        return VFolderRBACPermission(value)


@graphene_federation.key("id")
class VirtualFolderNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.03.4"

    row_id = graphene.UUID(description="Added in 24.03.4. ID of VFolder.")
    host = graphene.String()
    quota_scope_id = graphene.String()
    name = graphene.String()
    user = graphene.UUID()  # User.id (current owner, null in project vfolders)
    user_email = graphene.String()  # User.email (current owner, null in project vfolders)
    group = graphene.UUID()  # Group.id (current owner, null in user vfolders)
    group_name = graphene.String()  # Group.name (current owenr, null in user vfolders)
    creator = graphene.String()  # User.email (always set)
    unmanaged_path = graphene.String()
    usage_mode = graphene.String()
    permission = graphene.String()
    ownership_type = graphene.String()
    max_files = graphene.Int()
    max_size = BigInt()  # in MiB
    created_at = GQLDateTime()
    last_used = GQLDateTime()

    num_files = graphene.Int()
    cur_size = BigInt()
    # num_attached = graphene.Int()
    cloneable = graphene.Boolean()
    status = graphene.String()

    permissions = graphene.List(
        VFolderPermissionValueField,
        description=f"Added in 24.09.0. One of {[val.value for val in VFolderRBACPermission]}.",
    )

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("id", uuid.UUID),
        "host": ("host", None),
        "quota_scope_id": ("quota_scope_id", None),
        "name": ("name", None),
        "group": ("group", uuid.UUID),
        "user": ("user", uuid.UUID),
        "creator": ("creator", None),
        "unmanaged_path": ("unmanaged_path", None),
        "usage_mode": (
            "usage_mode",
            VFolderUsageMode,
        ),
        "permission": (
            "permission",
            VFolderPermission,
        ),
        "ownership_type": (
            "ownership_type",
            VFolderOwnershipType,
        ),
        "max_files": ("max_files", None),
        "max_size": ("max_size", None),
        "created_at": ("created_at", dtparse),
        "last_used": ("last_used", dtparse),
        "cloneable": ("cloneable", None),
        "status": (
            "status",
            VFolderOperationStatus,
        ),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("id", None),
        "host": ("host", None),
        "quota_scope_id": ("quota_scope_id", None),
        "name": ("name", None),
        "group": ("group", None),
        "user": ("user", None),
        "creator": ("creator", None),
        "usage_mode": ("usage_mode", None),
        "permission": ("permission", None),
        "ownership_type": ("ownership_type", None),
        "max_files": ("max_files", None),
        "max_size": ("max_size", None),
        "created_at": ("created_at", None),
        "last_used": ("last_used", None),
        "cloneable": ("cloneable", None),
        "status": ("status", None),
        "cur_size": ("cur_size", None),
    }

    def resolve_created_at(
        self,
        info: graphene.ResolveInfo,
    ) -> datetime:
        if isinstance(self.created_at, datetime):
            return self.created_at

        try:
            return dtparse(self.created_at)
        except ParserError:
            return self.created_at

    @classmethod
    def from_row(
        cls,
        graph_ctx: GraphQueryContext,
        row: VFolderRow,
        *,
        permissions: Optional[Iterable[VFolderRBACPermission]] = None,
    ) -> Self:
        result = cls(
            id=row.id,
            row_id=row.id,
            host=row.host,
            quota_scope_id=row.quota_scope_id,
            name=row.name,
            user=row.user,
            user_email=row.user_row.email if row.user_row else None,
            group=row.group_row.id if row.group_row else None,
            group_name=row.group_row.name if row.group_row else None,
            creator=row.creator,
            unmanaged_path=row.unmanaged_path or None,
            usage_mode=row.usage_mode,
            permission=row.permission,
            ownership_type=row.ownership_type,
            max_files=row.max_files,
            max_size=row.max_size,  # in B
            created_at=row.created_at,
            last_used=row.last_used,
            cloneable=row.cloneable,
            status=row.status,
            cur_size=row.cur_size,
        )
        result.permissions = [] if permissions is None else permissions
        return result

    @classmethod
    async def batch_load_by_id(
        cls,
        graph_ctx: GraphQueryContext,
        folder_ids: Sequence[uuid.UUID],
    ) -> Sequence[Sequence[Self]]:
        query = (
            sa.select(VFolderRow)
            .where(VFolderRow.id.in_(folder_ids))
            .options(
                joinedload(VFolderRow.user_row),
                joinedload(VFolderRow.group_row),
            )
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                graph_ctx, db_session, query, cls, folder_ids, lambda row: row.id
            )

    @classmethod
    async def get_node(
        cls,
        info: graphene.ResolveInfo,
        id: str,
        scope_id: Optional[ScopeType] = None,
        permission: VFolderRBACPermission = VFolderRBACPermission.READ_ATTRIBUTE,
    ) -> Optional[Self]:
        graph_ctx: GraphQueryContext = info.context
        _, vfolder_row_id = AsyncNode.resolve_global_id(info, id)
        query = sa.select(VFolderRow).options(
            joinedload(VFolderRow.user_row),
            joinedload(VFolderRow.group_row),
        )
        if scope_id is None:
            scope_id = SystemScope()
        async with graph_ctx.db.connect() as db_conn:
            user = graph_ctx.user
            client_ctx = ClientContext(
                graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
            )
            permission_ctx = await get_permission_ctx(db_conn, client_ctx, scope_id, permission)
            cond = permission_ctx.query_condition
            if cond is None:
                return None
            query = query.where(sa.and_(cond, VFolderRow.id == uuid.UUID(vfolder_row_id)))
            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                vfolder_row = await db_session.scalar(query)
                vfolder_row = cast(Optional[VFolderRow], vfolder_row)
        if vfolder_row is None:
            return None
        return cls.from_row(
            graph_ctx,
            vfolder_row,
            permissions=await permission_ctx.calculate_final_permission(vfolder_row),
        )

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        filter_expr: str | None = None,
        order_expr: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult[Self]:
        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter_expr, QueryFilterParser(cls._queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(cls._queryorder_colmap))
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
            VFolderRow,
            VFolderRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )

        query = query.options(
            joinedload(VFolderRow.user_row),
            joinedload(VFolderRow.group_row),
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            vfolder_rows = (await db_session.scalars(query)).all()
            total_cnt = await db_session.scalar(cnt_query)
        result: list[Self] = [cls.from_row(graph_ctx, vf) for vf in vfolder_rows]
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    @classmethod
    async def get_accessible_connection(
        cls,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
        permission: VFolderRBACPermission,
        filter_expr: str | None = None,
        order_expr: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult[Self]:
        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter_expr, QueryFilterParser(cls._queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(cls._queryorder_colmap))
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
            VFolderRow,
            VFolderRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )

        query = query.options(
            joinedload(VFolderRow.user_row),
            joinedload(VFolderRow.group_row),
        )
        async with graph_ctx.db.connect() as db_conn:
            user = graph_ctx.user
            client_ctx = ClientContext(
                graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
            )
            permission_ctx = await get_permission_ctx(db_conn, client_ctx, scope_id, permission)
            cond = permission_ctx.query_condition
            if cond is None:
                return ConnectionResolverResult([], cursor, pagination_order, page_size, 0)
            query = query.where(cond)
            cnt_query = cnt_query.where(cond)
            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                vfolder_rows = (await db_session.scalars(query)).all()
                total_cnt = await db_session.scalar(cnt_query)
        result: list[Self] = [
            cls.from_row(
                graph_ctx,
                vf,
                permissions=await permission_ctx.calculate_final_permission(vf),
            )
            for vf in vfolder_rows
        ]
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    async def __resolve_reference(
        self, info: graphene.ResolveInfo, **kwargs: Any
    ) -> VirtualFolderNode:
        vfolder_node = await VirtualFolderNode.get_node(info, self.id)
        if vfolder_node is None:
            raise VFolderNotFound(f"Virtual folder not found: {self.id}")
        return vfolder_node


class VirtualFolderConnection(Connection):
    class Meta:
        node = VirtualFolderNode
        description = "Added in 24.03.4"


class ModelCard(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    name = graphene.String()
    row_id = graphene.UUID(description="Added in 24.03.8. ID of VFolder.")
    vfolder = graphene.Field("ai.backend.manager.api.gql_legacy.vfolder.VirtualFolder")
    vfolder_node = graphene.Field(VirtualFolderNode, description="Added in 24.09.0.")
    author = graphene.String()
    title = graphene.String(description="Human readable name of the model.")
    version = graphene.String()
    created_at = GQLDateTime(description="The time the model was created.")
    modified_at = GQLDateTime(description="The last time the model was modified.")
    description = graphene.String()
    task = graphene.String()
    category = graphene.String()
    architecture = graphene.String()
    framework = graphene.List(lambda: graphene.String)
    label = graphene.List(lambda: graphene.String)
    license = graphene.String()
    min_resource = graphene.JSONString()
    readme = graphene.String()
    readme_filetype = graphene.String(
        description=(
            "Type (mostly extension of the filename) of the README file. e.g. md, rst, txt, ..."
        )
    )
    error_msg = graphene.String(description="Added in 24.03.8.")

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("vfolders_id", uuid.UUID),
        "host": ("vfolders_host", None),
        "quota_scope_id": ("vfolders_quota_scope_id", None),
        "name": ("vfolders_name", None),
        "group": ("vfolders_group", uuid.UUID),
        "group_name": ("groups_name", None),
        "user": ("vfolders_user", uuid.UUID),
        "user_email": ("users_email", None),
        "creator": ("vfolders_creator", None),
        "unmanaged_path": ("vfolders_unmanaged_path", None),
        "usage_mode": (
            "vfolders_usage_mode",
            VFolderUsageMode,
        ),
        "permission": (
            "vfolders_permission",
            VFolderPermission,
        ),
        "ownership_type": (
            "vfolders_ownership_type",
            VFolderOwnershipType,
        ),
        "max_files": ("vfolders_max_files", None),
        "max_size": ("vfolders_max_size", None),
        "created_at": ("vfolders_created_at", dtparse),
        "last_used": ("vfolders_last_used", dtparse),
        "cloneable": ("vfolders_cloneable", None),
        "status": (
            "vfolders_status",
            VFolderOperationStatus,
        ),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("vfolders_id", None),
        "host": ("vfolders_host", None),
        "quota_scope_id": ("vfolders_quota_scope_id", None),
        "name": ("vfolders_name", None),
        "group": ("vfolders_group", None),
        "group_name": ("groups_name", None),
        "user": ("vfolders_user", None),
        "user_email": ("users_email", None),
        "creator": ("vfolders_creator", None),
        "usage_mode": ("vfolders_usage_mode", None),
        "permission": ("vfolders_permission", None),
        "ownership_type": ("vfolders_ownership_type", None),
        "max_files": ("vfolders_max_files", None),
        "max_size": ("vfolders_max_size", None),
        "created_at": ("vfolders_created_at", None),
        "last_used": ("vfolders_last_used", None),
        "cloneable": ("vfolders_cloneable", None),
        "status": ("vfolders_status", None),
        "cur_size": ("vfolders_cur_size", None),
    }

    def resolve_created_at(
        self,
        info: graphene.ResolveInfo,
    ) -> datetime:
        try:
            return dtparse(self.created_at)
        except (TypeError, ParserError):
            return self.created_at

    def resolve_modified_at(
        self,
        info: graphene.ResolveInfo,
    ) -> datetime:
        try:
            return dtparse(self.modified_at)
        except (TypeError, ParserError):
            return self.modified_at

    @classmethod
    def parse_model(
        cls,
        graph_ctx: GraphQueryContext,
        vfolder_row: VFolderRow,
        *,
        model_def: dict[str, Any] | None = None,
        readme: str | None = None,
        readme_filetype: str | None = None,
    ) -> Self:
        if model_def is not None:
            models = model_def["models"]
        else:
            models = []
        try:
            metadata = models[0]["metadata"] or {}
            name = models[0]["name"]
        except (IndexError, KeyError):
            metadata = {}
            name = vfolder_row.name
        return cls(
            id=vfolder_row.id,
            row_id=vfolder_row.id,
            vfolder=VirtualFolder.from_orm_row(vfolder_row),
            vfolder_node=VirtualFolderNode.from_row(graph_ctx, vfolder_row),
            name=name,
            author=metadata.get("author") or vfolder_row.creator or "",
            title=metadata.get("title") or vfolder_row.name,
            version=metadata.get("version") or "",
            created_at=metadata.get("created") or vfolder_row.created_at,
            modified_at=metadata.get("last_modified") or vfolder_row.created_at,
            description=metadata.get("description") or "",
            task=metadata.get("task") or "",
            architecture=metadata.get("architecture") or "",
            framework=metadata.get("framework") or [],
            label=metadata.get("label") or [],
            category=metadata.get("category") or "",
            license=metadata.get("license") or "",
            min_resource=metadata.get("min_resource") or {},
            readme=readme,
            readme_filetype=readme_filetype,
        )

    @classmethod
    async def from_row(
        cls, graph_ctx: GraphQueryContext, vfolder_row: VFolderRow
    ) -> Optional[Self]:
        try:
            return await cls.parse_row(graph_ctx, vfolder_row)
        except Exception as e:
            log.exception(
                "Failed to parse model card from vfolder (id: {}, error: {})",
                vfolder_row.id,
                repr(e),
            )
            if (
                graph_ctx.user["role"] in (UserRole.SUPERADMIN, UserRole.ADMIN)
                or vfolder_row.creator == graph_ctx.user["email"]
            ):
                return cls(
                    id=vfolder_row.id,
                    row_id=vfolder_row.id,
                    name=vfolder_row.name,
                    author=vfolder_row.creator or "",
                    error_msg=str(e),
                )
            return None

    @classmethod
    async def parse_row(cls, graph_ctx: GraphQueryContext, vfolder_row: VFolderRow) -> Self:
        vfolder_row_id = vfolder_row.id
        quota_scope_id = vfolder_row.quota_scope_id
        host = vfolder_row.host
        vfolder_id = VFolderID(quota_scope_id, vfolder_row_id)
        proxy_name, volume_name = graph_ctx.storage_manager.get_proxy_and_volume(
            host, is_unmanaged(vfolder_row.unmanaged_path)
        )
        manager_facing_client = graph_ctx.storage_manager.get_manager_facing_client(proxy_name)
        result = await manager_facing_client.list_files(
            volume_name,
            str(vfolder_id),
            ".",
        )
        vfolder_files = result["items"]

        model_definition_filename: str | None = None
        readme_idx: int | None = None

        for idx, item in enumerate(vfolder_files):
            if (item["name"] in ("model-definition.yml", "model-definition.yaml")) and (
                not model_definition_filename
            ):
                model_definition_filename = item["name"]
            if item["name"].lower().startswith("readme."):
                readme_idx = idx

        if model_definition_filename:
            chunks = await manager_facing_client.fetch_file_content(
                volume_name,
                str(vfolder_id),
                f"./{model_definition_filename}",
            )
            model_definition_yaml = chunks.decode("utf-8")
            try:
                yaml = YAML()
                model_definition_dict = yaml.load(model_definition_yaml)
            except YAMLError as e:
                raise ModelCardParseError(
                    extra_msg=f"Invalid YAML syntax (filename:{model_definition_filename}, detail:{e!s})"
                ) from e
            try:
                model_definition = model_definition_iv.check(model_definition_dict)
            except t.DataError as e:
                raise ModelCardParseError(
                    extra_msg=f"Failed to validate model definition file (data:{model_definition_dict}, detail:{e!s})"
                ) from e
            if model_definition is None:
                raise DataTransformationFailed(
                    "Model definition validation returned None unexpectedly"
                )
            model_definition["id"] = vfolder_row_id
        else:
            model_definition = None

        if readme_idx is not None:
            readme_filename: str = vfolder_files[readme_idx]["name"]
            try:
                chunks = await manager_facing_client.fetch_file_content(
                    volume_name,
                    str(vfolder_id),
                    f"./{readme_filename}",
                )
            except (VFolderOperationFailed, VFolderBadRequest):
                readme = "Failed to fetch README file."
                readme_filetype = None
            else:
                readme = chunks.decode("utf-8")
                readme_filetype = readme_filename.split(".")[-1]
        else:
            readme = None
            readme_filetype = None

        return cls.parse_model(
            graph_ctx,
            vfolder_row,
            model_def=model_definition,
            readme=readme,
            readme_filetype=readme_filetype,
        )

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id: str) -> Self | None:
        graph_ctx: GraphQueryContext = info.context

        _, vfolder_row_id = AsyncNode.resolve_global_id(info, id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            vfolder_row = await VFolderRow.get(
                db_session, uuid.UUID(vfolder_row_id), load_user=True, load_group=True
            )
            if vfolder_row.usage_mode != VFolderUsageMode.MODEL:
                raise ValueError(
                    f"The vfolder is not model. expect: {VFolderUsageMode.MODEL.value}, got:"
                    f" {vfolder_row.usage_mode.value}. (id: {vfolder_row_id})"
                )
            if vfolder_row.status in DEAD_VFOLDER_STATUSES:
                raise ValueError(
                    f"The vfolder is deleted. (id: {vfolder_row_id}, status: {vfolder_row.status})"
                )
        return await cls.from_row(graph_ctx, vfolder_row)

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        filter_expr: str | None = None,
        order_expr: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult[Self]:
        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter_expr, QueryFilterParser(cls._queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(cls._queryorder_colmap))
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
            VFolderRow,
            VFolderRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            model_store_project_gids = (
                (
                    await db_session.execute(
                        sa.select(GroupRow.id).where(
                            (GroupRow.type == ProjectType.MODEL_STORE)
                            & (GroupRow.domain_name == graph_ctx.user["domain_name"])
                        )
                    )
                )
                .scalars()
                .all()
            )
            additional_cond = (VFolderRow.status.not_in(DEAD_VFOLDER_STATUSES)) & (
                VFolderRow.group.in_(model_store_project_gids)
            )
            query = query.where(additional_cond)
            cnt_query = cnt_query.where(additional_cond)
            query = query.options(
                joinedload(VFolderRow.user_row),
                joinedload(VFolderRow.group_row),
            )
            vfolder_rows = (await db_session.scalars(query)).all()
            total_cnt = await db_session.scalar(cnt_query)
        result = []
        for vf in vfolder_rows:
            if (_node := await cls.from_row(graph_ctx, vf)) is not None:
                result.append(_node)
            else:
                total_cnt -= 1
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class ModelCardConnection(Connection):
    class Meta:
        node = ModelCard
        description = "Added in 24.03.4"


# Legacy GraphQL classes (moved from models.vfolder.row)


class VirtualFolder(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    host = graphene.String()
    quota_scope_id = graphene.String()
    name = graphene.String()
    user = graphene.UUID()  # User.id (current owner, null in project vfolders)
    user_email = graphene.String()  # User.email (current owner, null in project vfolders)
    group = graphene.UUID()  # Group.id (current owner, null in user vfolders)
    group_name = graphene.String()  # Group.name (current owenr, null in user vfolders)
    creator = graphene.String()  # User.email (always set)
    domain_name = graphene.String(description="Added in 24.09.0.")
    unmanaged_path = graphene.String()
    usage_mode = graphene.String()
    permission = graphene.String()
    ownership_type = graphene.String()
    max_files = graphene.Int()
    max_size = BigInt()  # in MiB
    created_at = GQLDateTime()
    last_used = GQLDateTime()

    num_files = graphene.Int()
    cur_size = BigInt()
    # num_attached = graphene.Int()
    cloneable = graphene.Boolean()
    status = graphene.String()

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row | VFolderRow | None) -> Optional[Self]:
        match row:
            case None:
                return None
            case VFolderRow():
                return cls(
                    id=row.id,
                    host=row.host,
                    quota_scope_id=row.quota_scope_id,
                    name=row.name,
                    user=row.user,
                    user_email=row.user_row.email if row.user_row is not None else None,
                    group=row.group,
                    group_name=row.group_row.name if row.group_row is not None else None,
                    creator=row.creator,
                    domain_name=row.domain_name,
                    unmanaged_path=row.unmanaged_path or None,
                    usage_mode=row.usage_mode,
                    permission=row.permission,
                    ownership_type=row.ownership_type,
                    max_files=row.max_files,
                    max_size=row.max_size,  # in MiB
                    created_at=row.created_at,
                    last_used=row.last_used,
                    cloneable=row.cloneable,
                    status=row.status,
                    cur_size=row.cur_size,
                )
            case Row():
                return cls(
                    id=row.id,
                    host=row.host,
                    quota_scope_id=row.quota_scope_id,
                    name=row.name,
                    user=row.user,
                    user_email=row._mapping.get("users_email"),
                    group=row.group,
                    group_name=row._mapping.get("groups_name"),
                    creator=row.creator,
                    domain_name=row.domain_name,
                    unmanaged_path=row.unmanaged_path or None,
                    usage_mode=row.usage_mode,
                    permission=row.permission,
                    ownership_type=row.ownership_type,
                    max_files=row.max_files,
                    max_size=row.max_size,  # in MiB
                    created_at=row.created_at,
                    last_used=row.last_used,
                    # num_attached=row['num_attached'],
                    cloneable=row.cloneable,
                    status=row.status,
                    cur_size=row.cur_size,
                )
        raise ValueError(f"Type not allowed to parse (t:{type(row)})")

    @classmethod
    def from_orm_row(cls, row: VFolderRow) -> VirtualFolder:
        return cls(
            id=row.id,
            host=row.host,
            quota_scope_id=row.quota_scope_id,
            name=row.name,
            user=row.user,
            user_email=row.user_row.email if row.user_row is not None else None,
            group=row.group,
            group_name=row.group_row.name if row.group_row is not None else None,
            creator=row.creator,
            unmanaged_path=row.unmanaged_path or None,
            usage_mode=row.usage_mode,
            permission=row.permission,
            ownership_type=row.ownership_type,
            max_files=row.max_files,
            max_size=row.max_size,
            created_at=row.created_at,
            last_used=row.last_used,
            cloneable=row.cloneable,
            status=row.status,
            cur_size=row.cur_size,
        )

    async def resolve_num_files(self, info: graphene.ResolveInfo) -> int:
        # TODO: measure on-the-fly
        return 0

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("vfolders_id", uuid.UUID),
        "host": ("vfolders_host", None),
        "quota_scope_id": ("vfolders_quota_scope_id", None),
        "name": ("vfolders_name", None),
        "group": ("vfolders_group", uuid.UUID),
        "group_name": ("groups_name", None),
        "user": ("vfolders_user", uuid.UUID),
        "user_email": ("users_email", None),
        "creator": ("vfolders_creator", None),
        "domain_name": ("vfolders_domain_name", None),
        "unmanaged_path": ("vfolders_unmanaged_path", None),
        "usage_mode": (
            "vfolders_usage_mode",
            lambda s: VFolderUsageMode(s),
        ),
        "permission": (
            "vfolders_permission",
            lambda s: VFolderPermission(s),
        ),
        "ownership_type": (
            "vfolders_ownership_type",
            lambda s: VFolderOwnershipType(s),
        ),
        "max_files": ("vfolders_max_files", None),
        "max_size": ("vfolders_max_size", None),
        "created_at": ("vfolders_created_at", dtparse),
        "last_used": ("vfolders_last_used", dtparse),
        "cloneable": ("vfolders_cloneable", None),
        "status": (
            "vfolders_status",
            lambda s: VFolderOperationStatus(s),
        ),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("vfolders_id", None),
        "host": ("vfolders_host", None),
        "quota_scope_id": ("vfolders_quota_scope_id", None),
        "name": ("vfolders_name", None),
        "group": ("vfolders_group", None),
        "group_name": ("groups_name", None),
        "domain_name": ("domain_name", None),
        "user": ("vfolders_user", None),
        "user_email": ("users_email", None),
        "creator": ("vfolders_creator", None),
        "usage_mode": ("vfolders_usage_mode", None),
        "permission": ("vfolders_permission", None),
        "ownership_type": ("vfolders_ownership_type", None),
        "max_files": ("vfolders_max_files", None),
        "max_size": ("vfolders_max_size", None),
        "created_at": ("vfolders_created_at", None),
        "last_used": ("vfolders_last_used", None),
        "cloneable": ("vfolders_cloneable", None),
        "status": ("vfolders_status", None),
        "cur_size": ("vfolders_cur_size", None),
    }

    @classmethod
    async def load_count(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
    ) -> int:
        from ai.backend.manager.models.group import groups
        from ai.backend.manager.models.user import users

        j = vfolders.join(users, vfolders.c.user == users.c.uuid, isouter=True).join(
            groups, vfolders.c.group == groups.c.id, isouter=True
        )
        query = sa.select(sa.func.count()).select_from(j)
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(vfolders.c.group == group_id)
        if user_id is not None:
            query = query.where(vfolders.c.user == user_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar() or 0

    @classmethod
    async def load_slice(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[VirtualFolder]:
        from ai.backend.manager.models.group import groups
        from ai.backend.manager.models.user import users

        j = vfolders.join(users, vfolders.c.user == users.c.uuid, isouter=True).join(
            groups, vfolders.c.group == groups.c.id, isouter=True
        )
        query = (
            sa.select(vfolders, users.c.email, groups.c.name.label("groups_name"))
            .select_from(j)
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(vfolders.c.group == group_id)
        if user_id is not None:
            query = query.where(vfolders.c.user == user_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(vfolders.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, r)) is not None
            ]

    @classmethod
    async def batch_load_by_id(
        cls,
        graph_ctx: GraphQueryContext,
        ids: list[uuid.UUID],
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
    ) -> Sequence[Optional[VirtualFolder]]:
        query = (
            sa.select(VFolderRow)
            .where(VFolderRow.id.in_(ids))
            .options(joinedload(VFolderRow.user_row), joinedload(VFolderRow.group_row))
            .order_by(sa.desc(VFolderRow.created_at))
        )
        if user_id is not None:
            query = query.where(VFolderRow.user == user_id)
            if domain_name is not None:
                query = query.where(UserRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(VFolderRow.group == group_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly_session() as db_sess:
            return await batch_result_in_scalar_stream(
                graph_ctx,
                db_sess,
                query,
                cls,
                ids,
                lambda row: row.id,
            )

    @classmethod
    async def batch_load_by_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_uuids: Sequence[uuid.UUID],
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
    ) -> Sequence[Sequence[VirtualFolder]]:
        from ai.backend.manager.models.user import users

        # TODO: num_attached count group-by
        j = sa.join(vfolders, users, vfolders.c.user == users.c.uuid)
        query = (
            sa.select(vfolders)
            .select_from(j)
            .where(vfolders.c.user.in_(user_uuids))
            .order_by(sa.desc(vfolders.c.created_at))
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(vfolders.c.group == group_id)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx,
                conn,
                query,
                cls,
                user_uuids,
                lambda row: row.user,
            )

    @classmethod
    async def load_count_invited(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
    ) -> int:
        from ai.backend.manager.models.user import users

        j = vfolders.join(
            vfolder_permissions,
            vfolders.c.id == vfolder_permissions.c.vfolder,
        ).join(
            users,
            vfolder_permissions.c.user == users.c.uuid,
        )
        query = (
            sa.select(sa.func.count())
            .select_from(j)
            .where(
                (vfolder_permissions.c.user == user_id)
                & (vfolders.c.ownership_type == VFolderOwnershipType.USER),
            )
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar() or 0

    @classmethod
    async def load_slice_invited(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> list[VirtualFolder]:
        from ai.backend.manager.models.user import users

        j = vfolders.join(
            vfolder_permissions,
            vfolders.c.id == vfolder_permissions.c.vfolder,
        ).join(
            users,
            vfolder_permissions.c.user == users.c.uuid,
        )
        query = (
            sa.select(vfolders, users.c.email)
            .select_from(j)
            .where(
                (vfolder_permissions.c.user == user_id)
                & (vfolders.c.ownership_type == VFolderOwnershipType.USER),
            )
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(vfolders.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, r)) is not None
            ]

    @classmethod
    async def load_count_project(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
    ) -> int:
        from ai.backend.manager.models.group import association_groups_users as agus
        from ai.backend.manager.models.group import groups

        query = sa.select(agus.c.group_id).select_from(agus).where(agus.c.user_id == user_id)

        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)

        grps = result.fetchall()
        group_ids = [g.group_id for g in grps]
        j = sa.join(vfolders, groups, vfolders.c.group == groups.c.id)
        query = sa.select(sa.func.count()).select_from(j).where(vfolders.c.group.in_(group_ids))

        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar() or 0

    @classmethod
    async def load_slice_project(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> list[VirtualFolder]:
        from ai.backend.manager.models.group import association_groups_users as agus
        from ai.backend.manager.models.group import groups

        query = sa.select(agus.c.group_id).select_from(agus).where(agus.c.user_id == user_id)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
        grps = result.fetchall()
        group_ids = [g.group_id for g in grps]
        j = vfolders.join(groups, vfolders.c.group == groups.c.id)
        query = (
            sa.select(
                vfolders,
                groups.c.name.label("groups_name"),
            )
            .select_from(j)
            .where(vfolders.c.group.in_(group_ids))
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(vfolders.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, r)) is not None
            ]


class VirtualFolderList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(VirtualFolder, required=True)


class VirtualFolderPermissionGQL(graphene.ObjectType):
    """Legacy VirtualFolderPermission GraphQL type (renamed to avoid conflict with VFolderPermission enum)."""

    class Meta:
        interfaces = (Item,)
        name = "VirtualFolderPermission"  # Preserve GraphQL type name for backward compatibility

    permission = graphene.String()
    vfolder = graphene.UUID()
    vfolder_name = graphene.String()
    user = graphene.UUID()
    user_email = graphene.String()

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[VirtualFolderPermissionGQL]:
        if row is None:
            return None
        return cls(
            permission=row.permission,
            vfolder=row.vfolder,
            vfolder_name=row.name,
            user=row.user,
            user_email=row.email,
        )

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "permission": ("vfolder_permissions_permission", VFolderPermission),
        "vfolder": ("vfolder_permissions_vfolder", None),
        "vfolder_name": ("vfolders_name", None),
        "user": ("vfolder_permissions_user", None),
        "user_email": ("users_email", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "permission": ("vfolder_permissions_permission", None),
        "vfolder": ("vfolder_permissions_vfolder", None),
        "vfolder_name": ("vfolders_name", None),
        "user": ("vfolder_permissions_user", None),
        "user_email": ("users_email", None),
    }

    @classmethod
    async def load_count(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
    ) -> int:
        from ai.backend.manager.models.user import users

        j = vfolder_permissions.join(vfolders, vfolders.c.id == vfolder_permissions.c.vfolder).join(
            users, users.c.uuid == vfolder_permissions.c.user
        )
        query = sa.select(sa.func.count()).select_from(j)
        if user_id is not None:
            query = query.where(vfolders.c.user == user_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar() or 0

    @classmethod
    async def load_slice(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> list[VirtualFolderPermissionGQL]:
        from ai.backend.manager.models.user import users

        j = vfolder_permissions.join(vfolders, vfolders.c.id == vfolder_permissions.c.vfolder).join(
            users, users.c.uuid == vfolder_permissions.c.user
        )
        query = (
            sa.select(vfolder_permissions, vfolders.c.name, users.c.email)
            .select_from(j)
            .limit(limit)
            .offset(offset)
        )
        if user_id is not None:
            query = query.where(vfolders.c.user == user_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(vfolders.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, r)) is not None
            ]


# Alias for backward compatibility
VirtualFolderPermission = VirtualFolderPermissionGQL


class VirtualFolderPermissionList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(VirtualFolderPermissionGQL, required=True)


class QuotaDetails(graphene.ObjectType):
    usage_bytes = BigInt(required=False)
    usage_count = BigInt(required=False)
    hard_limit_bytes = BigInt(required=False)


class QuotaScope(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    id = graphene.ID(required=True)
    quota_scope_id = graphene.String(required=True)
    storage_host_name = graphene.String(required=True)
    details = graphene.NonNull(QuotaDetails)

    @classmethod
    def from_vfolder_row(cls, ctx: GraphQueryContext, row: VFolderRow) -> QuotaScope:
        return QuotaScope(
            quota_scope_id=str(row.quota_scope_id),
            storage_host_name=row.host,
        )

    def resolve_id(self, info: graphene.ResolveInfo) -> str:
        return f"QuotaScope:{self.storage_host_name}/{self.quota_scope_id}"

    async def resolve_details(self, info: graphene.ResolveInfo) -> Optional[int]:
        graph_ctx: GraphQueryContext = info.context
        proxy_name, volume_name = graph_ctx.storage_manager.get_proxy_and_volume(
            self.storage_host_name
        )
        try:
            manager_client = graph_ctx.storage_manager.get_manager_facing_client(proxy_name)
            quota_config = await manager_client.get_quota_scope(volume_name, self.quota_scope_id)
            usage_bytes = quota_config["used_bytes"]
            if usage_bytes is not None and usage_bytes < 0:
                usage_bytes = None
            return QuotaDetails(
                # FIXME: limit scaning this only for fast scan capable volumes
                usage_bytes=usage_bytes,
                hard_limit_bytes=quota_config["limit_bytes"] or None,
                usage_count=None,  # TODO: Implement
            )
        except QuotaScopeNotFoundError as e:
            qsid = QuotaScopeID.parse(self.quota_scope_id)
            async with graph_ctx.db.begin_readonly_session() as sess:
                await ensure_quota_scope_accessible_by_user(sess, qsid, graph_ctx.user)
                if qsid.scope_type == QuotaScopeType.USER:
                    query = (
                        sa.select(UserRow)
                        .where(UserRow.uuid == qsid.scope_id)
                        .options(selectinload(UserRow.resource_policy_row))
                    )
                    result = await sess.scalar(query)
                    if result is None:
                        raise QuotaScopeNotFoundError(
                            f"User not found for quota scope id: {self.quota_scope_id}"
                        ) from e
                    resource_policy_constraint: int | None = (
                        result.resource_policy_row.max_quota_scope_size
                    )
                else:
                    query = (
                        sa.select(GroupRow)
                        .where(GroupRow.id == qsid.scope_id)
                        .options(selectinload(GroupRow.resource_policy_row))
                    )
                    result = await sess.scalar(query)
                    if result is None:
                        raise QuotaScopeNotFoundError(
                            f"Group not found for quota scope id: {self.quota_scope_id}"
                        ) from e
                    resource_policy_constraint = result.resource_policy_row.max_quota_scope_size
                if resource_policy_constraint is not None and resource_policy_constraint < 0:
                    resource_policy_constraint = None

            return QuotaDetails(
                usage_bytes=None,
                hard_limit_bytes=resource_policy_constraint,
                usage_count=None,  # TODO: Implement
            )


class QuotaScopeInput(graphene.InputObjectType):
    hard_limit_bytes = BigInt(required=False)


class SetQuotaScope(graphene.Mutation):
    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        quota_scope_id = graphene.String(required=True)
        storage_host_name = graphene.String(required=True)
        props = QuotaScopeInput(required=True)

    quota_scope = graphene.Field(lambda: QuotaScope)

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        quota_scope_id: str,
        storage_host_name: str,
        props: QuotaScopeInput,
    ) -> SetQuotaScope:
        qsid = QuotaScopeID.parse(quota_scope_id)
        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_readonly_session() as sess:
            await ensure_quota_scope_accessible_by_user(sess, qsid, graph_ctx.user)
        if props.hard_limit_bytes is Undefined:
            # Do nothing but just return the quota scope object.
            return cls(
                QuotaScope(
                    quota_scope_id=quota_scope_id,
                    storage_host_name=storage_host_name,
                )
            )
        max_vfolder_size = props.hard_limit_bytes
        proxy_name, volume_name = graph_ctx.storage_manager.get_proxy_and_volume(storage_host_name)
        manager_client = graph_ctx.storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.update_quota_scope(
            volume_name,
            str(qsid),
            max_vfolder_size,
        )
        return cls(
            QuotaScope(
                quota_scope_id=quota_scope_id,
                storage_host_name=storage_host_name,
            )
        )


class UnsetQuotaScope(graphene.Mutation):
    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        quota_scope_id = graphene.String(required=True)
        storage_host_name = graphene.String(required=True)

    quota_scope = graphene.Field(lambda: QuotaScope)

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        quota_scope_id: str,
        storage_host_name: str,
    ) -> SetQuotaScope:
        qsid = QuotaScopeID.parse(quota_scope_id)
        graph_ctx: GraphQueryContext = info.context
        proxy_name, volume_name = graph_ctx.storage_manager.get_proxy_and_volume(storage_host_name)
        async with graph_ctx.db.begin_readonly_session() as sess:
            await ensure_quota_scope_accessible_by_user(sess, qsid, graph_ctx.user)
        manager_client = graph_ctx.storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.delete_quota_scope_quota(volume_name, str(qsid))

        return cls(
            QuotaScope(
                quota_scope_id=quota_scope_id,
                storage_host_name=storage_host_name,
            )
        )
