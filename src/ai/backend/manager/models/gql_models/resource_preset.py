from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import graphene
import sqlalchemy as sa
from graphql import Undefined
from sqlalchemy.engine.row import Row

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.minilang.ordering import ColumnMapType, QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import FieldSpecType, QueryFilterParser
from ai.backend.manager.models.resource_preset import ResourcePresetRow, resource_presets
from ai.backend.manager.services.resource_preset.types import (
    ResourcePresetCreator,
    ResourcePresetModifier,
)
from ai.backend.manager.types import OptionalState, TriState

from ..base import (
    BigInt,
    batch_result,
    batch_result_in_scalar_stream,
)
from .user import UserRole

if TYPE_CHECKING:
    from ..gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models"))

__all__: Sequence[str] = (
    "ResourcePreset",
    "CreateResourcePreset",
    "ModifyResourcePreset",
    "DeleteResourcePreset",
)


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

    def to_creator(self, name: str) -> ResourcePresetCreator:
        return ResourcePresetCreator(
            name=name,
            resource_slots=ResourceSlot.from_user_input(self.resource_slots, None),
            shared_memory=self.shared_memory if self.shared_memory else None,
            scaling_group_name=self.scaling_group_name if self.scaling_group_name else None,
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

    def to_modifier(self) -> ResourcePresetModifier:
        resource_slots = (
            ResourceSlot.from_json(self.resource_slots) if self.resource_slots else Undefined
        )

        return ResourcePresetModifier(
            resource_slots=OptionalState[ResourceSlot].from_graphql(resource_slots),
            name=OptionalState[str].from_graphql(self.name),
            shared_memory=TriState[BinarySize].from_graphql(
                BinarySize.finite_from_str(self.shared_memory)
                if self.shared_memory is not Undefined and self.shared_memory is not None
                else self.shared_memory
            ),
            scaling_group_name=TriState[str].from_graphql(self.scaling_group_name),
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
        from ai.backend.manager.services.resource_preset.actions.create_preset import (
            CreateResourcePresetAction,
        )

        graph_ctx: GraphQueryContext = info.context

        result = await graph_ctx.processors.resource_preset.create_preset.wait_for_complete(
            CreateResourcePresetAction(creator=props.to_creator(name))
        )

        return cls(True, "success", ResourcePreset.from_row(graph_ctx, result.resource_preset))


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
        from ai.backend.manager.services.resource_preset.actions.modify_preset import (
            ModifyResourcePresetAction,
        )

        graph_ctx: GraphQueryContext = info.context

        await graph_ctx.processors.resource_preset.modify_preset.wait_for_complete(
            ModifyResourcePresetAction(id=id, name=name, modifier=props.to_modifier())
        )

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
        from ai.backend.manager.services.resource_preset.actions.delete_preset import (
            DeleteResourcePresetAction,
        )

        graph_ctx: GraphQueryContext = info.context

        await graph_ctx.processors.resource_preset.delete_preset.wait_for_complete(
            DeleteResourcePresetAction(id=id, name=name)
        )

        return cls(True, "success")
