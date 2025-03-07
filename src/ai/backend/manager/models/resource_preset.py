from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Self
from uuid import UUID

import graphene
import sqlalchemy as sa
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.logging import BraceStyleAdapter

from .base import (
    Base,
    BigInt,
    IDColumn,
    ResourceSlotColumn,
    batch_result,
    batch_result_in_scalar_stream,
    cast,
    set_if_set,
)
from .minilang.ordering import ColumnMapType, QueryOrderParser
from .minilang.queryfilter import FieldSpecType, QueryFilterParser
from .user import UserRole
from .utils import execute_with_txn_retry

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models"))

__all__: Sequence[str] = (
    "resource_presets",
    "ResourcePreset",
    "CreateResourcePreset",
    "ModifyResourcePreset",
    "DeleteResourcePreset",
)


type QueryStatement = sa.sql.Select


def filter_by_name(name: str) -> Callable[[QueryStatement], QueryStatement]:
    return lambda query_stmt: query_stmt.where(ResourcePresetRow.name == name)


def filter_by_id(id: UUID) -> Callable[[QueryStatement], QueryStatement]:
    return lambda query_stmt: query_stmt.where(ResourcePresetRow.id == id)


QueryOption = Callable[[Any], Callable[[QueryStatement], QueryStatement]]


class ResourcePresetRow(Base):
    __tablename__ = "resource_presets"
    id = IDColumn()
    name = sa.Column("name", sa.String(length=256), nullable=False)
    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    shared_memory = sa.Column("shared_memory", sa.BigInteger(), nullable=True)

    # If `scaling_group_name` is None, the preset is global
    scaling_group_name = sa.Column(
        "scaling_group_name", sa.String(length=64), nullable=True, server_default=sa.null()
    )
    scaling_group_row = relationship(
        "ScalingGroupRow",
        back_populates="resource_preset_rows",
        primaryjoin="ScalingGroupRow.name == foreign(ResourcePresetRow.scaling_group_name)",
    )

    __table_args__ = (
        sa.Index(
            "ix_resource_presets_name_null_scaling_group_name",
            name,
            postgresql_where=scaling_group_name.is_(None),
            unique=True,
        ),
        sa.Index(
            "ix_resource_presets_name_scaling_group_name",
            name,
            scaling_group_name,
            postgresql_where=scaling_group_name.isnot(None),
            unique=True,
        ),
    )

    @classmethod
    async def create(
        cls,
        name: str,
        resource_slots: ResourceSlot,
        scaling_group_name: Optional[str] = None,
        shared_memory: Optional[int] = None,
        *,
        db_session: AsyncSession,
    ) -> Optional[Self]:
        insert_stmt = (
            sa.insert(ResourcePresetRow)
            .values(
                name=name,
                resource_slots=resource_slots,
                scaling_group_name=scaling_group_name,
                shared_memory=shared_memory,
            )
            .returning(ResourcePresetRow)
        )
        stmt = sa.select(ResourcePresetRow).from_statement(insert_stmt)

        try:
            return await db_session.scalar(stmt)
        except sa.exc.IntegrityError:
            # A resource preset with the given name and scaling group name already exists
            return None

    @classmethod
    async def update(
        cls,
        query_option: QueryOption,
        data: Mapping[str, Any],
        *,
        db_session: AsyncSession,
    ) -> Optional[Self]:
        update_stmt = sa.update(ResourcePresetRow).values(data).returning(ResourcePresetRow)
        update_stmt = query_option(update_stmt)
        stmt = (
            sa.select(ResourcePresetRow)
            .from_statement(update_stmt)
            .execution_options(populate_existing=True)
        )
        try:
            return await db_session.scalar(stmt)
        except sa.exc.IntegrityError:
            return None

    @classmethod
    async def delete(
        cls,
        query_option: QueryOption,
        *,
        db_session: AsyncSession,
    ) -> None:
        delete_stmt = sa.delete(ResourcePresetRow)
        delete_stmt = query_option(delete_stmt)
        return await db_session.execute(delete_stmt)


# For compatibility
resource_presets = ResourcePresetRow.__table__


class ResourcePreset(graphene.ObjectType):
    id = graphene.UUID(description="Added in 25.4.0. ID of the resource preset.")
    name = graphene.String()
    resource_slots = graphene.JSONString()
    shared_memory = BigInt()
    scaling_group_name = graphene.String(
        description=(
            "Added in 25.4.0. A name of scaling group(=resource group) of the resource preset associated with."
        ),
    )

    _queryfilter_fieldspec: FieldSpecType = {
        "id": ("id", None),
        "name": ("name", None),
        "scaling_group_name": ("scaling_group_name", None),
    }

    _queryorder_colmap: ColumnMapType = {
        "id": ("id", None),
        "name": ("name", None),
        "scaling_group_name": ("scaling_group_name", None),
    }

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: ResourcePresetRow | Row | None,
    ) -> ResourcePreset | None:
        match row:
            case ResourcePresetRow():
                shared_memory = str(row.shared_memory) if row.shared_memory is not None else None
                return cls(
                    id=row.id,
                    name=row.name,
                    resource_slots=row.resource_slots.to_json(),
                    shared_memory=shared_memory,
                    scaling_group_name=row.scaling_group_name,
                )
            case Row():
                shared_memory = str(row["shared_memory"]) if row["shared_memory"] else None
                return cls(
                    id=row["id"],
                    name=row["name"],
                    resource_slots=row["resource_slots"].to_json(),
                    shared_memory=shared_memory,
                    scaling_group_name=row["scaling_group_name"],
                )
            case _:
                return None

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[ResourcePreset]:
        query = sa.select(ResourcePresetRow)
        if filter is not None:
            filter_parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = filter_parser.append_filter(query, filter)
        if order is not None:
            order_parser = QueryOrderParser(cls._queryorder_colmap)
            query = order_parser.append_ordering(query, order)
        else:
            query = query.order_by(ResourcePresetRow.name)
        async with ctx.db.begin_readonly_session() as db_session:
            return [
                obj
                async for r in (await db_session.stream_scalars(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]

    @classmethod
    async def batch_load_by_id(
        cls,
        ctx: GraphQueryContext,
        ids: Sequence[UUID],
    ) -> Sequence[ResourcePreset | None]:
        query = (
            sa.select(ResourcePresetRow)
            .where(ResourcePresetRow.id.in_(ids))
            .order_by(ResourcePresetRow.id)
        )
        async with ctx.db.begin_readonly_session() as db_session:
            return await batch_result_in_scalar_stream(
                ctx,
                db_session,
                query,
                cls,
                ids,
                lambda row: row.id,
            )

    @classmethod
    async def batch_load_by_name(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
    ) -> Sequence[ResourcePreset | None]:
        query = (
            sa.select([resource_presets])
            .select_from(resource_presets)
            .where(resource_presets.c.name.in_(names))
            .order_by(resource_presets.c.name)
        )
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                names,
                lambda row: row["name"],
            )


class CreateResourcePresetInput(graphene.InputObjectType):
    resource_slots = graphene.JSONString(required=True)
    shared_memory = graphene.String(required=False)
    scaling_group_name = graphene.String(
        required=False,
        description=(
            "Added in 25.4.0. A name of scaling group(=resource group) of the resource preset associated with."
        ),
    )


class ModifyResourcePresetInput(graphene.InputObjectType):
    name = graphene.String(
        required=False,
        description=("Added in 25.4.0. A name of resource preset."),
    )
    resource_slots = graphene.JSONString(required=False)
    shared_memory = graphene.String(required=False)
    scaling_group_name = graphene.String(
        required=False,
        description=(
            "Added in 25.4.0. A name of scaling group(=resource group) of the resource preset associated with."
        ),
    )


class CreateResourcePreset(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = CreateResourcePresetInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    resource_preset = graphene.Field(lambda: ResourcePreset, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: CreateResourcePresetInput,
    ) -> CreateResourcePreset:
        graph_ctx: GraphQueryContext = info.context
        data: dict[str, Any] = {
            "name": name,
            "resource_slots": ResourceSlot.from_user_input(props.resource_slots, None),
        }
        set_if_set(
            props, data, "shared_memory", clean_func=lambda v: BinarySize.from_str(v) if v else None
        )
        set_if_set(props, data, "scaling_group_name")
        scaling_group_name = cast(Optional[str], data.get("scaling_group_name"))

        async def _create(db_session: AsyncSession) -> Optional[ResourcePresetRow]:
            return await ResourcePresetRow.create(
                name,
                cast(ResourceSlot, data["resource_slots"]),
                scaling_group_name,
                cast(Optional[int], data.get("shared_memory")),
                db_session=db_session,
            )

        async with graph_ctx.db.connect() as db_conn:
            preset_row = await execute_with_txn_retry(_create, graph_ctx.db.begin_session, db_conn)
        if preset_row is None:
            raise ValueError(
                f"Duplicate resource preset name (name:{name}, scaling_group:{scaling_group_name})"
            )
        return cls(True, "success", ResourcePreset.from_row(graph_ctx, preset_row))


class ModifyResourcePreset(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        id = graphene.UUID(
            required=False,
            default_value=None,
            description=("Added in 25.4.0. ID of the resource preset."),
        )
        name = graphene.String(
            required=False, default_value=None, deprecation_reason="Deprecated since 25.4.0."
        )
        props = ModifyResourcePresetInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: Optional[UUID],
        name: Optional[str],
        props: ModifyResourcePresetInput,
    ) -> ModifyResourcePreset:
        graph_ctx: GraphQueryContext = info.context

        data: Dict[str, Any] = {}
        preset_id = id
        if preset_id is None and name is None:
            raise ValueError("One of (`id` or `name`) parameter should be not null")

        set_if_set(
            props,
            data,
            "name",
        )
        set_if_set(
            props,
            data,
            "resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        set_if_set(
            props, data, "shared_memory", clean_func=lambda v: BinarySize.from_str(v) if v else None
        )
        set_if_set(props, data, "scaling_group_name")

        async def _update(db_session: AsyncSession) -> Optional[ResourcePresetRow]:
            if preset_id is not None:
                query_option = filter_by_id(preset_id)
            else:
                if name is None:
                    raise ValueError("One of (`id` or `name`) parameter should be not null")
                query_option = filter_by_name(name)
            return await ResourcePresetRow.update(query_option, data, db_session=db_session)

        async with graph_ctx.db.connect() as db_conn:
            preset_row = await execute_with_txn_retry(_update, graph_ctx.db.begin_session, db_conn)
            if preset_row is None:
                raise ValueError("Duplicate resource preset record")
        return cls(True, "success")


class DeleteResourcePreset(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        id = graphene.UUID(
            required=False,
            default_value=None,
            description=("Added in 25.4.0. ID of the resource preset."),
        )
        name = graphene.String(
            required=False, default_value=None, deprecation_reason="Deprecated since 25.4.0."
        )

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: Optional[UUID],
        name: Optional[str],
    ) -> DeleteResourcePreset:
        graph_ctx: GraphQueryContext = info.context

        preset_id = id
        if preset_id is None and name is None:
            raise ValueError("One of (`id` or `name`) parameter should be not null")

        async def _delete(db_session: AsyncSession) -> None:
            if preset_id is not None:
                query_option = filter_by_id(preset_id)
            else:
                if name is None:
                    raise ValueError("One of (`id` or `name`) parameter should be not null")
                query_option = filter_by_name(name)
            return await ResourcePresetRow.delete(query_option, db_session=db_session)

        async with graph_ctx.db.connect() as db_conn:
            await execute_with_txn_retry(_delete, graph_ctx.db.begin_session, db_conn)
        return cls(True, "success")
