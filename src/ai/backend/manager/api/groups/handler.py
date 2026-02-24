"""
REST API handlers for group (project) management.
Provides CRUD endpoints for group operations and member management.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.group import (
    AddGroupMembersRequest,
    AddGroupMembersResponse,
    CreateGroupRequest,
    CreateGroupResponse,
    DeleteGroupResponse,
    GetGroupResponse,
    GroupMemberDTO,
    PaginationInfo,
    RemoveGroupMembersRequest,
    RemoveGroupMembersResponse,
    SearchGroupsRequest,
    SearchGroupsResponse,
    UpdateGroupRequest,
    UpdateGroupResponse,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.group_request import (
    DeleteGroupPathParam,
    GetGroupPathParam,
    GroupMembersPathParam,
    UpdateGroupPathParam,
)
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.group.creators import GroupCreatorSpec
from ai.backend.manager.repositories.group.updaters import GroupUpdaterSpec
from ai.backend.manager.services.group.actions.create_group import CreateGroupAction
from ai.backend.manager.services.group.actions.delete_group import DeleteGroupAction
from ai.backend.manager.services.group.actions.modify_group import ModifyGroupAction
from ai.backend.manager.services.group.actions.search_projects import (
    GetProjectAction,
    SearchProjectsAction,
)
from ai.backend.manager.types import OptionalState

from .adapter import GroupAdapter

__all__ = ("create_app",)


class GroupAPIHandler:
    """REST API handler class for group operations."""

    def __init__(self) -> None:
        self.adapter = GroupAdapter()

    @auth_required_for_method
    @api_handler
    async def create(
        self,
        body: BodyParam[CreateGroupRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new group."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        creator = Creator(
            spec=GroupCreatorSpec(
                name=body.parsed.name,
                domain_name=body.parsed.domain_name,
                description=body.parsed.description,
                total_resource_slots=(
                    ResourceSlot(body.parsed.total_resource_slots)
                    if body.parsed.total_resource_slots is not None
                    else None
                ),
                allowed_vfolder_hosts=body.parsed.allowed_vfolder_hosts,
                integration_id=body.parsed.integration_id,
                resource_policy=body.parsed.resource_policy,
            )
        )

        action_result = await processors.group.create_group.wait_for_complete(
            CreateGroupAction(creator=creator)
        )

        resp = CreateGroupResponse(group=self.adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetGroupPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific group by ID."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        action_result = await processors.group.get_project.wait_for_complete(
            GetProjectAction(project_id=path.parsed.group_id)
        )

        resp = GetGroupResponse(group=self.adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchGroupsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search groups with filters, orders, and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        querier = self.adapter.build_querier(body.parsed)

        action_result = await processors.group.search_projects.wait_for_complete(
            SearchProjectsAction(querier=querier)
        )

        resp = SearchGroupsResponse(
            groups=[self.adapter.convert_to_dto(d) for d in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update(
        self,
        path: PathParam[UpdateGroupPathParam],
        body: BodyParam[UpdateGroupRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing group."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        group_id = path.parsed.group_id
        updater = self.adapter.build_updater(body.parsed, group_id)

        action_result = await processors.group.modify_group.wait_for_complete(
            ModifyGroupAction(updater=updater)
        )

        if action_result.data is not None:
            group_dto = self.adapter.convert_to_dto(action_result.data)
        else:
            # No data changes; re-fetch the group to return current state
            get_result = await processors.group.get_project.wait_for_complete(
                GetProjectAction(project_id=group_id)
            )
            group_dto = self.adapter.convert_to_dto(get_result.data)

        resp = UpdateGroupResponse(group=group_dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete(
        self,
        path: PathParam[DeleteGroupPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete (soft-delete) a group."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        await processors.group.delete_group.wait_for_complete(
            DeleteGroupAction(group_id=path.parsed.group_id)
        )

        resp = DeleteGroupResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def add_members(
        self,
        path: PathParam[GroupMembersPathParam],
        body: BodyParam[AddGroupMembersRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Add members to a group."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        group_id = path.parsed.group_id
        user_uuids_str = [str(uid) for uid in body.parsed.user_ids]

        # Use ModifyGroupAction with user_update_mode="add" and a no-op updater
        updater = Updater(spec=GroupUpdaterSpec(), pk_value=group_id)
        await processors.group.modify_group.wait_for_complete(
            ModifyGroupAction(
                updater=updater,
                user_update_mode=OptionalState.update("add"),
                user_uuids=OptionalState.update(user_uuids_str),
            )
        )

        members = [GroupMemberDTO(user_id=uid, group_id=group_id) for uid in body.parsed.user_ids]
        resp = AddGroupMembersResponse(members=members)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def remove_members(
        self,
        path: PathParam[GroupMembersPathParam],
        body: BodyParam[RemoveGroupMembersRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Remove members from a group."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        group_id = path.parsed.group_id
        user_uuids_str = [str(uid) for uid in body.parsed.user_ids]

        # Use ModifyGroupAction with user_update_mode="remove" and a no-op updater
        updater = Updater(spec=GroupUpdaterSpec(), pk_value=group_id)
        await processors.group.modify_group.wait_for_complete(
            ModifyGroupAction(
                updater=updater,
                user_update_mode=OptionalState.update("remove"),
                user_uuids=OptionalState.update(user_uuids_str),
            )
        )

        resp = RemoveGroupMembersResponse(removed_count=len(body.parsed.user_ids))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for group API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "groups"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    handler = GroupAPIHandler()

    # Group CRUD routes
    cors.add(app.router.add_route("POST", "", handler.create))
    cors.add(app.router.add_route("GET", "/{group_id}", handler.get))
    cors.add(app.router.add_route("POST", "/search", handler.search))
    cors.add(app.router.add_route("PATCH", "/{group_id}", handler.update))
    cors.add(app.router.add_route("DELETE", "/{group_id}", handler.delete))

    # Member management routes
    cors.add(app.router.add_route("POST", "/{group_id}/members", handler.add_members))
    cors.add(app.router.add_route("DELETE", "/{group_id}/members", handler.remove_members))

    return app, []
