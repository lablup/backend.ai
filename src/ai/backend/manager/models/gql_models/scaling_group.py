from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Self,
)

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime

from ai.backend.common.types import AccessKey

from ..base import (
    batch_multiresult_in_scalar_stream,
)
from ..gql_relay import (
    AsyncNode,
    Connection,
)
from ..scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


class ScalingGroupNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.12.0."

    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    is_public = graphene.Boolean()
    created_at = GQLDateTime()
    wsproxy_addr = graphene.String()
    wsproxy_api_token = graphene.String()
    driver = graphene.String()
    driver_opts = graphene.JSONString()
    scheduler = graphene.String()
    scheduler_opts = graphene.JSONString()
    use_host_network = graphene.Boolean()

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: ScalingGroupRow,
    ) -> Self:
        return cls(
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            is_public=row.is_public,
            created_at=row.created_at,
            wsproxy_addr=row.wsproxy_addr,
            wsproxy_api_token=row.wsproxy_api_token,
            driver=row.driver,
            driver_opts=row.driver_opts,
            scheduler=row.scheduler,
            scheduler_opts=row.scheduler_opts,
            use_host_network=row.use_host_network,
        )

    @classmethod
    async def batch_load_by_group(
        cls,
        ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
    ) -> Sequence[Sequence[ScalingGroupNode]]:
        j = sa.join(
            ScalingGroupRow,
            ScalingGroupForProjectRow,
            ScalingGroupRow.name == ScalingGroupForProjectRow.scaling_group,
        )
        _stmt = (
            sa.select(ScalingGroupRow)
            .select_from(j)
            .where(ScalingGroupForProjectRow.group.in_(group_ids))
        )
        async with ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                ctx,
                db_session,
                _stmt,
                cls,
                group_ids,
                lambda row: row.name,
            )

    @classmethod
    async def batch_load_by_domain(
        cls,
        ctx: GraphQueryContext,
        domain_names: Sequence[str],
    ) -> Sequence[Sequence[ScalingGroupNode]]:
        j = sa.join(
            ScalingGroupRow,
            ScalingGroupForDomainRow,
            ScalingGroupRow.name == ScalingGroupForDomainRow.scaling_group,
        )
        _stmt = (
            sa.select(ScalingGroupRow)
            .select_from(j)
            .where(ScalingGroupForDomainRow.domain.in_(domain_names))
        )
        async with ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                ctx,
                db_session,
                _stmt,
                cls,
                domain_names,
                lambda row: row.name,
            )

    @classmethod
    async def batch_load_by_keypair(
        cls,
        ctx: GraphQueryContext,
        access_keys: Sequence[AccessKey],
    ) -> Sequence[Sequence[ScalingGroupNode]]:
        j = sa.join(
            ScalingGroupRow,
            ScalingGroupForKeypairsRow,
            ScalingGroupRow.name == ScalingGroupForKeypairsRow.scaling_group,
        )
        _stmt = (
            sa.select(ScalingGroupRow)
            .select_from(j)
            .where(ScalingGroupForKeypairsRow.access_key.in_(access_keys))
        )
        async with ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                ctx,
                db_session,
                _stmt,
                cls,
                access_keys,
                lambda row: row.name,
            )


class ScalinGroupConnection(Connection):
    class Meta:
        node = ScalingGroupNode
        description = "Added in 24.12.0."
