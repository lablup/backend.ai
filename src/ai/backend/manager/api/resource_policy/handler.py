"""
REST API handlers for Resource Policy management.
Provides CRUD endpoints for keypair, user, and project resource policies.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import Field

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseRequestModel,
    BodyParam,
    PathParam,
    Sentinel,
    api_handler,
)
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.resource_policy.request import (
    CreateKeypairResourcePolicyRequest,
    CreateProjectResourcePolicyRequest,
    CreateUserResourcePolicyRequest,
    DeleteKeypairResourcePolicyRequest,
    DeleteProjectResourcePolicyRequest,
    DeleteUserResourcePolicyRequest,
    SearchKeypairResourcePoliciesRequest,
    SearchProjectResourcePoliciesRequest,
    SearchUserResourcePoliciesRequest,
    UpdateKeypairResourcePolicyRequest,
    UpdateProjectResourcePolicyRequest,
    UpdateUserResourcePolicyRequest,
)
from ai.backend.common.dto.manager.resource_policy.response import (
    CreateKeypairResourcePolicyResponse,
    CreateProjectResourcePolicyResponse,
    CreateUserResourcePolicyResponse,
    DeleteKeypairResourcePolicyResponse,
    DeleteProjectResourcePolicyResponse,
    DeleteUserResourcePolicyResponse,
    GetKeypairResourcePolicyResponse,
    GetProjectResourcePolicyResponse,
    GetUserResourcePolicyResponse,
    KeypairResourcePolicyDTO,
    PaginationInfo,
    ProjectResourcePolicyDTO,
    SearchKeypairResourcePoliciesResponse,
    SearchProjectResourcePoliciesResponse,
    SearchUserResourcePoliciesResponse,
    UpdateKeypairResourcePolicyResponse,
    UpdateProjectResourcePolicyResponse,
    UpdateUserResourcePolicyResponse,
    UserResourcePolicyDTO,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx, RequestCtx
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.keypair_resource_policy.creators import (
    KeyPairResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.keypair_resource_policy.updaters import (
    KeyPairResourcePolicyUpdaterSpec,
)
from ai.backend.manager.repositories.project_resource_policy.creators import (
    ProjectResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.project_resource_policy.updaters import (
    ProjectResourcePolicyUpdaterSpec,
)
from ai.backend.manager.repositories.user_resource_policy.creators import (
    UserResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.user_resource_policy.updaters import (
    UserResourcePolicyUpdaterSpec,
)
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
)
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("create_app",)


class PolicyNamePathParam(BaseRequestModel):
    """Path parameter for resource policy operations identified by name."""

    policy_name: str = Field(description="The resource policy name")


def _check_superadmin() -> None:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can manage resource policies.")


class ResourcePolicyAPIHandler:
    """REST API handler class for resource policy operations."""

    # ---- Keypair Resource Policy ----

    @auth_required_for_method
    @api_handler
    async def create_keypair_policy(
        self,
        body: BodyParam[CreateKeypairResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new keypair resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        creator = Creator(
            spec=KeyPairResourcePolicyCreatorSpec(
                name=body.parsed.name,
                default_for_unspecified=body.parsed.default_for_unspecified,
                total_resource_slots=ResourceSlot(body.parsed.total_resource_slots),
                max_session_lifetime=body.parsed.max_session_lifetime,
                max_concurrent_sessions=body.parsed.max_concurrent_sessions,
                max_pending_session_count=body.parsed.max_pending_session_count,
                max_pending_session_resource_slots=(
                    ResourceSlot(body.parsed.max_pending_session_resource_slots)
                    if body.parsed.max_pending_session_resource_slots is not None
                    else None
                ),
                max_concurrent_sftp_sessions=body.parsed.max_concurrent_sftp_sessions,
                max_containers_per_session=body.parsed.max_containers_per_session,
                idle_timeout=body.parsed.idle_timeout,
                allowed_vfolder_hosts=body.parsed.allowed_vfolder_hosts,
                max_quota_scope_size=None,
                max_vfolder_count=None,
                max_vfolder_size=None,
            )
        )

        action_result = await processors.keypair_resource_policy.create_keypair_resource_policy.wait_for_complete(
            CreateKeyPairResourcePolicyAction(creator=creator)
        )

        data = action_result.keypair_resource_policy
        resp = CreateKeypairResourcePolicyResponse(
            item=KeypairResourcePolicyDTO(
                name=data.name,
                created_at=data.created_at,
                default_for_unspecified=data.default_for_unspecified,
                total_resource_slots=dict(data.total_resource_slots),
                max_session_lifetime=data.max_session_lifetime,
                max_concurrent_sessions=data.max_concurrent_sessions,
                max_pending_session_count=data.max_pending_session_count,
                max_pending_session_resource_slots=(
                    dict(data.max_pending_session_resource_slots)
                    if data.max_pending_session_resource_slots is not None
                    else None
                ),
                max_concurrent_sftp_sessions=data.max_concurrent_sftp_sessions,
                max_containers_per_session=data.max_containers_per_session,
                idle_timeout=data.idle_timeout,
                allowed_vfolder_hosts=dict(data.allowed_vfolder_hosts),
            )
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_keypair_policy(
        self,
        path: PathParam[PolicyNamePathParam],
        request_ctx: RequestCtx,
    ) -> APIResponse:
        """Get a specific keypair resource policy by name."""

        _check_superadmin()

        root_ctx: RootContext = request_ctx.request.app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as db_sess:
            stmt = sa.select(KeyPairResourcePolicyRow).where(
                KeyPairResourcePolicyRow.name == path.parsed.policy_name
            )
            row: KeyPairResourcePolicyRow | None = await db_sess.scalar(stmt)
            if row is None:
                raise web.HTTPNotFound(
                    reason=f"Keypair resource policy '{path.parsed.policy_name}' not found."
                )
            data = row.to_dataclass()

        resp = GetKeypairResourcePolicyResponse(
            item=KeypairResourcePolicyDTO(
                name=data.name,
                created_at=data.created_at,
                default_for_unspecified=data.default_for_unspecified,
                total_resource_slots=dict(data.total_resource_slots),
                max_session_lifetime=data.max_session_lifetime,
                max_concurrent_sessions=data.max_concurrent_sessions,
                max_pending_session_count=data.max_pending_session_count,
                max_pending_session_resource_slots=(
                    dict(data.max_pending_session_resource_slots)
                    if data.max_pending_session_resource_slots is not None
                    else None
                ),
                max_concurrent_sftp_sessions=data.max_concurrent_sftp_sessions,
                max_containers_per_session=data.max_containers_per_session,
                idle_timeout=data.idle_timeout,
                allowed_vfolder_hosts=dict(data.allowed_vfolder_hosts),
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_keypair_policies(
        self,
        body: BodyParam[SearchKeypairResourcePoliciesRequest],
        request_ctx: RequestCtx,
    ) -> APIResponse:
        """Search keypair resource policies."""

        _check_superadmin()

        root_ctx: RootContext = request_ctx.request.app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as db_sess:
            stmt = sa.select(KeyPairResourcePolicyRow)
            count_stmt = sa.select(sa.func.count()).select_from(KeyPairResourcePolicyRow)

            total: int = await db_sess.scalar(count_stmt) or 0
            stmt = stmt.offset(body.parsed.offset).limit(body.parsed.limit)
            result = await db_sess.scalars(stmt)
            rows = result.all()

        items = []
        for row in rows:
            data = row.to_dataclass()
            items.append(
                KeypairResourcePolicyDTO(
                    name=data.name,
                    created_at=data.created_at,
                    default_for_unspecified=data.default_for_unspecified,
                    total_resource_slots=dict(data.total_resource_slots),
                    max_session_lifetime=data.max_session_lifetime,
                    max_concurrent_sessions=data.max_concurrent_sessions,
                    max_pending_session_count=data.max_pending_session_count,
                    max_pending_session_resource_slots=(
                        dict(data.max_pending_session_resource_slots)
                        if data.max_pending_session_resource_slots is not None
                        else None
                    ),
                    max_concurrent_sftp_sessions=data.max_concurrent_sftp_sessions,
                    max_containers_per_session=data.max_containers_per_session,
                    idle_timeout=data.idle_timeout,
                    allowed_vfolder_hosts=dict(data.allowed_vfolder_hosts),
                )
            )

        resp = SearchKeypairResourcePoliciesResponse(
            items=items,
            pagination=PaginationInfo(
                total=total, offset=body.parsed.offset, limit=body.parsed.limit
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_keypair_policy(
        self,
        path: PathParam[PolicyNamePathParam],
        body: BodyParam[UpdateKeypairResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update a keypair resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        spec = KeyPairResourcePolicyUpdaterSpec()
        if not isinstance(body.parsed.default_for_unspecified, Sentinel):
            spec.default_for_unspecified = OptionalState.update(body.parsed.default_for_unspecified)
        if not isinstance(body.parsed.total_resource_slots, Sentinel):
            spec.total_resource_slots = OptionalState.update(
                ResourceSlot(body.parsed.total_resource_slots)
            )
        if not isinstance(body.parsed.max_session_lifetime, Sentinel):
            spec.max_session_lifetime = OptionalState.update(body.parsed.max_session_lifetime)
        if not isinstance(body.parsed.max_concurrent_sessions, Sentinel):
            spec.max_concurrent_sessions = OptionalState.update(body.parsed.max_concurrent_sessions)
        if not isinstance(body.parsed.max_pending_session_count, Sentinel):
            if body.parsed.max_pending_session_count is None:
                spec.max_pending_session_count = TriState.nullify()
            else:
                spec.max_pending_session_count = TriState.update(
                    body.parsed.max_pending_session_count
                )
        if not isinstance(body.parsed.max_pending_session_resource_slots, Sentinel):
            if body.parsed.max_pending_session_resource_slots is None:
                spec.max_pending_session_resource_slots = TriState.nullify()
            else:
                spec.max_pending_session_resource_slots = TriState.update(
                    body.parsed.max_pending_session_resource_slots
                )
        if not isinstance(body.parsed.max_concurrent_sftp_sessions, Sentinel):
            spec.max_concurrent_sftp_sessions = OptionalState.update(
                body.parsed.max_concurrent_sftp_sessions
            )
        if not isinstance(body.parsed.max_containers_per_session, Sentinel):
            spec.max_containers_per_session = OptionalState.update(
                body.parsed.max_containers_per_session
            )
        if not isinstance(body.parsed.idle_timeout, Sentinel):
            spec.idle_timeout = OptionalState.update(body.parsed.idle_timeout)
        if not isinstance(body.parsed.allowed_vfolder_hosts, Sentinel):
            spec.allowed_vfolder_hosts = OptionalState.update(body.parsed.allowed_vfolder_hosts)

        updater: Updater[KeyPairResourcePolicyRow] = Updater(
            pk_value=path.parsed.policy_name,
            spec=spec,
        )

        action_result = await processors.keypair_resource_policy.modify_keypair_resource_policy.wait_for_complete(
            ModifyKeyPairResourcePolicyAction(name=path.parsed.policy_name, updater=updater)
        )

        data = action_result.keypair_resource_policy
        resp = UpdateKeypairResourcePolicyResponse(
            item=KeypairResourcePolicyDTO(
                name=data.name,
                created_at=data.created_at,
                default_for_unspecified=data.default_for_unspecified,
                total_resource_slots=dict(data.total_resource_slots),
                max_session_lifetime=data.max_session_lifetime,
                max_concurrent_sessions=data.max_concurrent_sessions,
                max_pending_session_count=data.max_pending_session_count,
                max_pending_session_resource_slots=(
                    dict(data.max_pending_session_resource_slots)
                    if data.max_pending_session_resource_slots is not None
                    else None
                ),
                max_concurrent_sftp_sessions=data.max_concurrent_sftp_sessions,
                max_containers_per_session=data.max_containers_per_session,
                idle_timeout=data.idle_timeout,
                allowed_vfolder_hosts=dict(data.allowed_vfolder_hosts),
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete_keypair_policy(
        self,
        body: BodyParam[DeleteKeypairResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a keypair resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        await processors.keypair_resource_policy.delete_keypair_resource_policy.wait_for_complete(
            DeleteKeyPairResourcePolicyAction(name=body.parsed.name)
        )

        resp = DeleteKeypairResourcePolicyResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ---- User Resource Policy ----

    @auth_required_for_method
    @api_handler
    async def create_user_policy(
        self,
        body: BodyParam[CreateUserResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new user resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        creator = Creator(
            spec=UserResourcePolicyCreatorSpec(
                name=body.parsed.name,
                max_vfolder_count=body.parsed.max_vfolder_count,
                max_quota_scope_size=body.parsed.max_quota_scope_size,
                max_session_count_per_model_session=body.parsed.max_session_count_per_model_session,
                max_customized_image_count=body.parsed.max_customized_image_count,
            )
        )

        action_result = (
            await processors.user_resource_policy.create_user_resource_policy.wait_for_complete(
                CreateUserResourcePolicyAction(creator=creator)
            )
        )

        data = action_result.user_resource_policy
        resp = CreateUserResourcePolicyResponse(
            item=UserResourcePolicyDTO(
                name=data.name,
                max_vfolder_count=data.max_vfolder_count,
                max_quota_scope_size=data.max_quota_scope_size,
                max_session_count_per_model_session=data.max_session_count_per_model_session,
                max_customized_image_count=data.max_customized_image_count,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_user_policy(
        self,
        path: PathParam[PolicyNamePathParam],
        request_ctx: RequestCtx,
    ) -> APIResponse:
        """Get a specific user resource policy by name."""

        _check_superadmin()

        root_ctx: RootContext = request_ctx.request.app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as db_sess:
            stmt = sa.select(UserResourcePolicyRow).where(
                UserResourcePolicyRow.name == path.parsed.policy_name
            )
            row: UserResourcePolicyRow | None = await db_sess.scalar(stmt)
            if row is None:
                raise web.HTTPNotFound(
                    reason=f"User resource policy '{path.parsed.policy_name}' not found."
                )
            data = row.to_dataclass()

        resp = GetUserResourcePolicyResponse(
            item=UserResourcePolicyDTO(
                name=data.name,
                max_vfolder_count=data.max_vfolder_count,
                max_quota_scope_size=data.max_quota_scope_size,
                max_session_count_per_model_session=data.max_session_count_per_model_session,
                max_customized_image_count=data.max_customized_image_count,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_user_policies(
        self,
        body: BodyParam[SearchUserResourcePoliciesRequest],
        request_ctx: RequestCtx,
    ) -> APIResponse:
        """Search user resource policies."""

        _check_superadmin()

        root_ctx: RootContext = request_ctx.request.app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as db_sess:
            stmt = sa.select(UserResourcePolicyRow)
            count_stmt = sa.select(sa.func.count()).select_from(UserResourcePolicyRow)

            total: int = await db_sess.scalar(count_stmt) or 0
            stmt = stmt.offset(body.parsed.offset).limit(body.parsed.limit)
            result = await db_sess.scalars(stmt)
            rows = result.all()

        items = []
        for row in rows:
            data = row.to_dataclass()
            items.append(
                UserResourcePolicyDTO(
                    name=data.name,
                    max_vfolder_count=data.max_vfolder_count,
                    max_quota_scope_size=data.max_quota_scope_size,
                    max_session_count_per_model_session=data.max_session_count_per_model_session,
                    max_customized_image_count=data.max_customized_image_count,
                )
            )

        resp = SearchUserResourcePoliciesResponse(
            items=items,
            pagination=PaginationInfo(
                total=total, offset=body.parsed.offset, limit=body.parsed.limit
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_user_policy(
        self,
        path: PathParam[PolicyNamePathParam],
        body: BodyParam[UpdateUserResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update a user resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        spec = UserResourcePolicyUpdaterSpec()
        if not isinstance(body.parsed.max_vfolder_count, Sentinel):
            spec.max_vfolder_count = OptionalState.update(body.parsed.max_vfolder_count)
        if not isinstance(body.parsed.max_quota_scope_size, Sentinel):
            spec.max_quota_scope_size = OptionalState.update(body.parsed.max_quota_scope_size)
        if not isinstance(body.parsed.max_session_count_per_model_session, Sentinel):
            spec.max_session_count_per_model_session = OptionalState.update(
                body.parsed.max_session_count_per_model_session
            )
        if not isinstance(body.parsed.max_customized_image_count, Sentinel):
            spec.max_customized_image_count = OptionalState.update(
                body.parsed.max_customized_image_count
            )

        updater: Updater[UserResourcePolicyRow] = Updater(
            pk_value=path.parsed.policy_name,
            spec=spec,
        )

        action_result = (
            await processors.user_resource_policy.modify_user_resource_policy.wait_for_complete(
                ModifyUserResourcePolicyAction(name=path.parsed.policy_name, updater=updater)
            )
        )

        data = action_result.user_resource_policy
        resp = UpdateUserResourcePolicyResponse(
            item=UserResourcePolicyDTO(
                name=data.name,
                max_vfolder_count=data.max_vfolder_count,
                max_quota_scope_size=data.max_quota_scope_size,
                max_session_count_per_model_session=data.max_session_count_per_model_session,
                max_customized_image_count=data.max_customized_image_count,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete_user_policy(
        self,
        body: BodyParam[DeleteUserResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a user resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        await processors.user_resource_policy.delete_user_resource_policy.wait_for_complete(
            DeleteUserResourcePolicyAction(name=body.parsed.name)
        )

        resp = DeleteUserResourcePolicyResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ---- Project Resource Policy ----

    @auth_required_for_method
    @api_handler
    async def create_project_policy(
        self,
        body: BodyParam[CreateProjectResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new project resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        creator = Creator(
            spec=ProjectResourcePolicyCreatorSpec(
                name=body.parsed.name,
                max_vfolder_count=body.parsed.max_vfolder_count,
                max_quota_scope_size=body.parsed.max_quota_scope_size,
                max_network_count=body.parsed.max_network_count,
            )
        )

        action_result = await processors.project_resource_policy.create_project_resource_policy.wait_for_complete(
            CreateProjectResourcePolicyAction(creator=creator)
        )

        data = action_result.project_resource_policy
        resp = CreateProjectResourcePolicyResponse(
            item=ProjectResourcePolicyDTO(
                name=data.name,
                max_vfolder_count=data.max_vfolder_count,
                max_quota_scope_size=data.max_quota_scope_size,
                max_network_count=data.max_network_count,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_project_policy(
        self,
        path: PathParam[PolicyNamePathParam],
        request_ctx: RequestCtx,
    ) -> APIResponse:
        """Get a specific project resource policy by name."""

        _check_superadmin()

        root_ctx: RootContext = request_ctx.request.app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as db_sess:
            stmt = sa.select(ProjectResourcePolicyRow).where(
                ProjectResourcePolicyRow.name == path.parsed.policy_name
            )
            row: ProjectResourcePolicyRow | None = await db_sess.scalar(stmt)
            if row is None:
                raise web.HTTPNotFound(
                    reason=f"Project resource policy '{path.parsed.policy_name}' not found."
                )
            data = row.to_dataclass()

        resp = GetProjectResourcePolicyResponse(
            item=ProjectResourcePolicyDTO(
                name=data.name,
                max_vfolder_count=data.max_vfolder_count,
                max_quota_scope_size=data.max_quota_scope_size,
                max_network_count=data.max_network_count,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_project_policies(
        self,
        body: BodyParam[SearchProjectResourcePoliciesRequest],
        request_ctx: RequestCtx,
    ) -> APIResponse:
        """Search project resource policies."""

        _check_superadmin()

        root_ctx: RootContext = request_ctx.request.app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as db_sess:
            stmt = sa.select(ProjectResourcePolicyRow)
            count_stmt = sa.select(sa.func.count()).select_from(ProjectResourcePolicyRow)

            total: int = await db_sess.scalar(count_stmt) or 0
            stmt = stmt.offset(body.parsed.offset).limit(body.parsed.limit)
            result = await db_sess.scalars(stmt)
            rows = result.all()

        items = []
        for row in rows:
            data = row.to_dataclass()
            items.append(
                ProjectResourcePolicyDTO(
                    name=data.name,
                    max_vfolder_count=data.max_vfolder_count,
                    max_quota_scope_size=data.max_quota_scope_size,
                    max_network_count=data.max_network_count,
                )
            )

        resp = SearchProjectResourcePoliciesResponse(
            items=items,
            pagination=PaginationInfo(
                total=total, offset=body.parsed.offset, limit=body.parsed.limit
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_project_policy(
        self,
        path: PathParam[PolicyNamePathParam],
        body: BodyParam[UpdateProjectResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update a project resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        spec = ProjectResourcePolicyUpdaterSpec()
        if not isinstance(body.parsed.max_vfolder_count, Sentinel):
            spec.max_vfolder_count = OptionalState.update(body.parsed.max_vfolder_count)
        if not isinstance(body.parsed.max_quota_scope_size, Sentinel):
            spec.max_quota_scope_size = OptionalState.update(body.parsed.max_quota_scope_size)
        if not isinstance(body.parsed.max_network_count, Sentinel):
            spec.max_network_count = OptionalState.update(body.parsed.max_network_count)

        updater: Updater[ProjectResourcePolicyRow] = Updater(
            pk_value=path.parsed.policy_name,
            spec=spec,
        )

        action_result = await processors.project_resource_policy.modify_project_resource_policy.wait_for_complete(
            ModifyProjectResourcePolicyAction(name=path.parsed.policy_name, updater=updater)
        )

        data = action_result.project_resource_policy
        resp = UpdateProjectResourcePolicyResponse(
            item=ProjectResourcePolicyDTO(
                name=data.name,
                max_vfolder_count=data.max_vfolder_count,
                max_quota_scope_size=data.max_quota_scope_size,
                max_network_count=data.max_network_count,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete_project_policy(
        self,
        body: BodyParam[DeleteProjectResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a project resource policy."""
        _check_superadmin()
        processors = processors_ctx.processors

        await processors.project_resource_policy.delete_project_resource_policy.wait_for_complete(
            DeleteProjectResourcePolicyAction(name=body.parsed.name)
        )

        resp = DeleteProjectResourcePolicyResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for Resource Policy API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "v2.0"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = ResourcePolicyAPIHandler()

    # Keypair resource policy routes
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/keypair",
            api_handler.create_keypair_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/keypair/search",
            api_handler.search_keypair_policies,
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/admin/resource-policies/keypair/{policy_name}",
            api_handler.get_keypair_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "PATCH",
            "/admin/resource-policies/keypair/{policy_name}",
            api_handler.update_keypair_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/keypair/delete",
            api_handler.delete_keypair_policy,
        )
    )

    # User resource policy routes
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/user",
            api_handler.create_user_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/user/search",
            api_handler.search_user_policies,
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/admin/resource-policies/user/{policy_name}",
            api_handler.get_user_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "PATCH",
            "/admin/resource-policies/user/{policy_name}",
            api_handler.update_user_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/user/delete",
            api_handler.delete_user_policy,
        )
    )

    # Project resource policy routes
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/project",
            api_handler.create_project_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/project/search",
            api_handler.search_project_policies,
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/admin/resource-policies/project/{policy_name}",
            api_handler.get_project_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "PATCH",
            "/admin/resource-policies/project/{policy_name}",
            api_handler.update_project_policy,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/resource-policies/project/delete",
            api_handler.delete_project_policy,
        )
    )

    return app, []
