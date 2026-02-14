"""Fetcher for RBAC entity search."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.rbac.types import EntityConnection, EntityTypeGQL
from ai.backend.manager.api.gql.rbac.types.entity import EntityEdge
from ai.backend.manager.api.gql.types import StrawberryGQLContext


def _convert(
    edges: list[EntityEdge],
    has_next_page: bool,
    has_previous_page: bool,
    total_count: int,
) -> EntityConnection:
    return EntityConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=total_count,
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
) -> EntityConnection | None:
    match entity_type:
        case EntityTypeGQL.USER:
            from ai.backend.manager.api.gql.user.fetcher.user import fetch_admin_users

            user_conn = await fetch_admin_users(
                info,
                before=before,
                after=after,
                first=first,
                last=last,
                limit=limit,
                offset=offset,
            )
            return _convert(
                [EntityEdge(node=e.node, cursor=e.cursor) for e in user_conn.edges],
                user_conn.page_info.has_next_page,
                user_conn.page_info.has_previous_page,
                user_conn.count,
            )
        case EntityTypeGQL.PROJECT:
            from ai.backend.manager.api.gql.project_v2.fetcher.project import (
                fetch_admin_projects,
            )

            project_conn = await fetch_admin_projects(
                info,
                before=before,
                after=after,
                first=first,
                last=last,
                limit=limit,
                offset=offset,
            )
            return _convert(
                [EntityEdge(node=e.node, cursor=e.cursor) for e in project_conn.edges],
                project_conn.page_info.has_next_page,
                project_conn.page_info.has_previous_page,
                project_conn.count,
            )
        case EntityTypeGQL.DOMAIN:
            from ai.backend.manager.api.gql.domain_v2.fetcher.domain import (
                fetch_admin_domains,
            )

            domain_conn = await fetch_admin_domains(
                info,
                before=before,
                after=after,
                first=first,
                last=last,
                limit=limit,
                offset=offset,
            )
            return _convert(
                [EntityEdge(node=e.node, cursor=e.cursor) for e in domain_conn.edges],
                domain_conn.page_info.has_next_page,
                domain_conn.page_info.has_previous_page,
                domain_conn.count,
            )
        case EntityTypeGQL.ROLE:
            from ai.backend.manager.api.gql.rbac.fetcher.role import fetch_roles

            role_conn = await fetch_roles(
                info,
                before=before,
                after=after,
                first=first,
                last=last,
                limit=limit,
                offset=offset,
            )
            return _convert(
                [EntityEdge(node=e.node, cursor=e.cursor) for e in role_conn.edges],
                role_conn.page_info.has_next_page,
                role_conn.page_info.has_previous_page,
                role_conn.count,
            )
        case EntityTypeGQL.IMAGE:
            from ai.backend.manager.api.gql.image.fetcher import fetch_images

            image_conn = await fetch_images(
                info,
                before=before,
                after=after,
                first=first,
                last=last,
                limit=limit,
                offset=offset,
            )
            return _convert(
                [EntityEdge(node=e.node, cursor=e.cursor) for e in image_conn.edges],
                image_conn.page_info.has_next_page,
                image_conn.page_info.has_previous_page,
                image_conn.count,
            )
        case EntityTypeGQL.SESSION:
            return None
        case EntityTypeGQL.ARTIFACT:
            from ai.backend.manager.api.gql.artifact.fetcher import fetch_artifacts

            artifact_conn = await fetch_artifacts(
                info,
                filter=None,
                order_by=None,
                before=before,
                after=after,
                first=first,
                last=last,
                limit=limit,
                offset=offset,
            )
            return _convert(
                [EntityEdge(node=e.node, cursor=e.cursor) for e in artifact_conn.edges],
                artifact_conn.page_info.has_next_page,
                artifact_conn.page_info.has_previous_page,
                artifact_conn.count,
            )
        case EntityTypeGQL.ARTIFACT_REVISION:
            from ai.backend.manager.api.gql.artifact.fetcher import (
                fetch_artifact_revisions,
            )

            rev_conn = await fetch_artifact_revisions(
                info,
                before=before,
                after=after,
                first=first,
                last=last,
                limit=limit,
                offset=offset,
            )
            return _convert(
                [EntityEdge(node=e.node, cursor=e.cursor) for e in rev_conn.edges],
                rev_conn.page_info.has_next_page,
                rev_conn.page_info.has_previous_page,
                rev_conn.count,
            )
        case EntityTypeGQL.DEPLOYMENT | EntityTypeGQL.MODEL_DEPLOYMENT:
            from ai.backend.manager.api.gql.deployment.fetcher.deployment import (
                fetch_deployments,
            )

            deploy_conn = await fetch_deployments(
                info,
                before=before,
                after=after,
                first=first,
                last=last,
                limit=limit,
                offset=offset,
            )
            return _convert(
                [EntityEdge(node=e.node, cursor=e.cursor) for e in deploy_conn.edges],
                deploy_conn.page_info.has_next_page,
                deploy_conn.page_info.has_previous_page,
                deploy_conn.count,
            )
        case EntityTypeGQL.NOTIFICATION_CHANNEL:
            return None
        case EntityTypeGQL.NOTIFICATION_RULE:
            return None
        case EntityTypeGQL.RESOURCE_GROUP:
            return None
        case EntityTypeGQL.VFOLDER:
            return None
        case EntityTypeGQL.ARTIFACT_REGISTRY:
            return None
        case EntityTypeGQL.APP_CONFIG:
            return None
        case EntityTypeGQL.CONTAINER_REGISTRY:
            return None
        case EntityTypeGQL.STORAGE_HOST:
            return None
