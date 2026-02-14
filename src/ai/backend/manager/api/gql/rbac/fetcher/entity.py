"""Fetcher for RBAC entity search."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import Info

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import EntityConnection, EntityTypeGQL
from ai.backend.manager.api.gql.rbac.types.entity import EntityEdge, EntityNode
from ai.backend.manager.api.gql.rbac.types.role import RoleGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.options import (
    EntityScopeConditions,
)
from ai.backend.manager.services.permission_contoller.actions.search_entities import (
    SearchEntitiesAction,
)


async def fetch_entities(
    info: Info[StrawberryGQLContext],
    entity_type: EntityTypeGQL,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityConnection:
    internal_entity_type = entity_type.to_internal()

    pagination = OffsetPagination(
        limit=limit if limit is not None else (first if first is not None else 20),
        offset=offset if offset is not None else 0,
    )

    conditions = [
        EntityScopeConditions.by_entity_type(internal_entity_type),
    ]

    querier = BatchQuerier(
        conditions=conditions,
        orders=[],
        pagination=pagination,
    )

    action_result = (
        await info.context.processors.permission_controller.search_entities.wait_for_complete(
            SearchEntitiesAction(querier=querier)
        )
    )

    data_loaders = info.context.data_loaders
    edges: list[EntityEdge] = []
    for entity_data in action_result.result.items:
        node = await _load_entity_node(data_loaders, entity_data.entity_type, entity_data.entity_id)
        if node is None:
            continue
        edges.append(EntityEdge(node=node, cursor=encode_cursor(entity_data.entity_id)))

    return EntityConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.result.has_next_page,
            has_previous_page=action_result.result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.result.total_count,
    )


async def _load_entity_node(
    data_loaders: object,
    entity_type: EntityType,
    entity_id: str,
) -> EntityNode | None:
    """Load a full entity object via the appropriate data loader.

    Returns None for entity types without a supported data loader.
    """
    from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL

    if not isinstance(data_loaders, DataLoaders):
        return None

    match entity_type:
        case EntityType.USER:
            user_data = await data_loaders.user_loader.load(uuid.UUID(entity_id))
            if user_data is None:
                return None
            return UserV2GQL.from_data(user_data)
        case EntityType.PROJECT:
            project_data = await data_loaders.project_loader.load(uuid.UUID(entity_id))
            if project_data is None:
                return None
            return ProjectV2GQL.from_data(project_data)
        case EntityType.DOMAIN:
            domain_data = await data_loaders.domain_loader.load(entity_id)
            if domain_data is None:
                return None
            return DomainV2GQL.from_data(domain_data)
        case EntityType.ROLE:
            role_data = await data_loaders.role_loader.load(uuid.UUID(entity_id))
            if role_data is None:
                return None
            return RoleGQL.from_dataclass(role_data)
        case _:
            return None
