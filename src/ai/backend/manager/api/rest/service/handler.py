"""Service (model serving) handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``PathParam``, ``UserContext``, ``RequestCtx``)
are automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import logging
import uuid
from http import HTTPStatus
from typing import Any, Final

import yarl
from aiohttp import web
from pydantic import HttpUrl

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    QueryParam,
)
from ai.backend.common.dto.manager.model_serving.request import (
    ListServeRequestModel,
    NewServiceRequestModel,
    ScaleRequestModel,
    SearchServicesRequestModel,
    ServiceIdPathParam,
    ServiceRouteIdPathParam,
    TokenRequestModel,
    UpdateRouteRequestModel,
)
from ai.backend.common.dto.manager.model_serving.response import (
    CompactServeInfoModel,
    ErrorInfoModel,
    ErrorListResponseModel,
    PaginationInfoModel,
    RouteInfoModel,
    RuntimeInfo,
    RuntimeInfoModel,
    ScaleResponseModel,
    SearchServicesResponseModel,
    ServeInfoModel,
    ServiceSearchItemModel,
    SuccessResponseModel,
    TokenResponseModel,
    TryStartResponseModel,
)
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AccessKey,
    ClusterMode,
    MountPermission,
    MountTypes,
    RuntimeVariant,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.utils import get_access_key_scopes
from ai.backend.manager.data.deployment.creator import DeploymentCreationDraft
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ExecutionSpec,
    ImageIdentifierDraft,
    ModelRevisionSpecDraft,
    MountMetadata,
    ReplicaSpec,
    ResourceSpecDraft,
)
from ai.backend.manager.data.model_serving.types import (
    ModelServicePrepareCtx,
    MountOption,
    ServiceConfig,
    ServiceInfo,
)
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.services.deployment.actions.create_legacy_deployment import (
    CreateLegacyDeploymentAction,
    CreateLegacyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.model_serving.actions.clear_error import ClearErrorAction
from ai.backend.manager.services.model_serving.actions.delete_route import DeleteRouteAction
from ai.backend.manager.services.model_serving.actions.dry_run_model_service import (
    DryRunModelServiceAction,
)
from ai.backend.manager.services.model_serving.actions.force_sync import ForceSyncAction
from ai.backend.manager.services.model_serving.actions.generate_token import GenerateTokenAction
from ai.backend.manager.services.model_serving.actions.get_model_service_info import (
    GetModelServiceInfoAction,
    GetModelServiceInfoActionResult,
)
from ai.backend.manager.services.model_serving.actions.list_errors import ListErrorsAction
from ai.backend.manager.services.model_serving.actions.list_model_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.scale_service_replicas import (
    ScaleServiceReplicasAction,
)
from ai.backend.manager.services.model_serving.actions.search_services import (
    SearchServicesAction,
    SearchServicesActionResult,
)
from ai.backend.manager.services.model_serving.actions.update_route import UpdateRouteAction
from ai.backend.manager.services.model_serving.actions.validate_model_service import (
    ValidateModelServiceAction,
    ValidateModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.adapter import ServiceSearchAdapter
from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _serve_info_from_dto(dto: ServiceInfo) -> ServeInfoModel:
    return ServeInfoModel(
        endpoint_id=dto.endpoint_id,
        model_id=dto.model_id,
        extra_mounts=dto.extra_mounts,
        name=dto.name,
        model_definition_path=dto.model_definition_path,
        replicas=dto.replicas,
        desired_session_count=dto.replicas,
        active_routes=[
            RouteInfoModel(
                route_id=route.route_id,
                session_id=route.session_id,
                traffic_ratio=route.traffic_ratio,
            )
            for route in dto.active_routes
        ],
        service_endpoint=dto.service_endpoint,
        is_public=dto.is_public,
        runtime_variant=dto.runtime_variant,
    )


def _serve_info_from_deployment_info(deployment_info: DeploymentInfo) -> ServeInfoModel:
    """Convert DeploymentInfo to ServeInfoModel."""
    model_revision = deployment_info.model_revisions[0] if deployment_info.model_revisions else None

    return ServeInfoModel(
        endpoint_id=deployment_info.id,
        model_id=model_revision.mounts.model_vfolder_id if model_revision else uuid.UUID(int=0),
        extra_mounts=[m.vfid.folder_id for m in model_revision.mounts.extra_mounts]
        if model_revision
        else [],
        name=deployment_info.metadata.name,
        model_definition_path=model_revision.mounts.model_definition_path
        if model_revision
        else None,
        replicas=deployment_info.replica_spec.replica_count,
        desired_session_count=deployment_info.replica_spec.replica_count,
        active_routes=[],
        service_endpoint=HttpUrl(deployment_info.network.url)
        if deployment_info.network.url
        else None,
        is_public=deployment_info.network.open_to_public,
        runtime_variant=model_revision.execution.runtime_variant
        if model_revision
        else RuntimeVariant.CUSTOM,
    )


class ServiceHandler:
    """Service (model serving) API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        processors: Processors,
    ) -> None:
        self._processors = processors

    # ------------------------------------------------------------------
    # list_serve (GET /services)
    # ------------------------------------------------------------------

    async def list_serve(
        self, query: QueryParam[ListServeRequestModel], ctx: UserContext
    ) -> APIResponse | web.StreamResponse:
        params = query.parsed
        log.info("SERVE.LIST (email:{}, ak:{})", ctx.user_email, ctx.access_key)

        action = ListModelServiceAction(session_owener_id=ctx.user_uuid, name=params.name)
        result: ListModelServiceActionResult = (
            await self._processors.model_serving.list_model_service.wait_for_complete(action)
        )

        items = [
            CompactServeInfoModel(
                id=info.id,
                name=info.name,
                replicas=info.replicas,
                desired_session_count=info.replicas,
                active_route_count=info.active_route_count,
                service_endpoint=info.service_endpoint,
                is_public=info.is_public,
            )
            for info in result.data
        ]
        return web.json_response(
            [item.model_dump(mode="json") for item in items],
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # search_services (POST /services/_/search)
    # ------------------------------------------------------------------

    async def search_services(
        self, body: BodyParam[SearchServicesRequestModel], ctx: UserContext
    ) -> APIResponse:
        params = body.parsed
        log.info("SERVE.SEARCH (email:{}, ak:{})", ctx.user_email, ctx.access_key)

        adapter = ServiceSearchAdapter()
        conditions = adapter.convert_filter(params.filter) if params.filter else []

        action = SearchServicesAction(
            session_owner_id=ctx.user_uuid,
            conditions=conditions,
            offset=params.offset,
            limit=params.limit,
        )
        result: SearchServicesActionResult = (
            await self._processors.model_serving.search_services.wait_for_complete(action)
        )

        resp = SearchServicesResponseModel(
            items=[
                ServiceSearchItemModel(
                    id=item.id,
                    name=item.name,
                    desired_session_count=item.replicas,
                    replicas=item.replicas,
                    active_route_count=item.active_route_count,
                    service_endpoint=item.service_endpoint,
                    resource_slots=dict(item.resource_slots),
                    resource_group=item.resource_group,
                    open_to_public=item.open_to_public,
                )
                for item in result.items
            ],
            pagination=PaginationInfoModel(
                total=result.total_count,
                offset=result.offset,
                limit=result.limit,
            ),
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # get_info (GET /services/{service_id})
    # ------------------------------------------------------------------

    async def get_info(self, path: PathParam[ServiceIdPathParam], ctx: UserContext) -> APIResponse:
        params = path.parsed
        log.info(
            "SERVE.GET_INFO (email:{}, ak:{}, s:{})",
            ctx.user_email,
            ctx.access_key,
            params.service_id,
        )

        action = GetModelServiceInfoAction(service_id=params.service_id)
        result: GetModelServiceInfoActionResult = (
            await self._processors.model_serving.get_model_service_info.wait_for_complete(action)
        )

        resp = _serve_info_from_dto(result.data)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # create (POST /services)
    # ------------------------------------------------------------------

    async def create(self, body: BodyParam[NewServiceRequestModel], req: RequestCtx) -> APIResponse:
        params = body.parsed
        request = req.request
        validation_result = await self._run_validation(request, params)

        deployment_action = CreateLegacyDeploymentAction(
            draft=DeploymentCreationDraft(
                metadata=DeploymentMetadata(
                    name=params.service_name,
                    domain=params.domain_name,
                    project=validation_result.group_id,
                    resource_group=validation_result.scaling_group,
                    created_user=request["user"]["uuid"],
                    session_owner=validation_result.owner_uuid,
                    created_at=None,
                    revision_history_limit=10,
                    tag=params.tag,
                ),
                replica_spec=ReplicaSpec(
                    replica_count=params.replicas,
                ),
                draft_model_revision=self._to_model_revision(params, validation_result),
                network=DeploymentNetworkSpec(
                    open_to_public=params.open_to_public,
                ),
            )
        )
        deployment_result: CreateLegacyDeploymentActionResult = (
            await self._processors.deployment.create_legacy_deployment.wait_for_complete(
                deployment_action
            )
        )
        resp = _serve_info_from_deployment_info(deployment_result.data)
        return APIResponse.build(HTTPStatus.CREATED, resp)

    # ------------------------------------------------------------------
    # try_start (POST /services/_/try)
    # ------------------------------------------------------------------

    async def try_start(
        self, body: BodyParam[NewServiceRequestModel], req: RequestCtx
    ) -> APIResponse:
        params = body.parsed
        request = req.request
        validation_result = await self._run_validation(request, params)

        action = self._to_start_action(params, validation_result, request)
        result = await self._processors.model_serving.dry_run_model_service.wait_for_complete(
            action
        )

        resp = TryStartResponseModel(task_id=str(result.task_id))
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # list_supported_runtimes (GET /services/_/runtimes)
    # ------------------------------------------------------------------

    async def list_supported_runtimes(self, ctx: UserContext) -> APIResponse:
        resp = RuntimeInfoModel(
            runtimes=[
                RuntimeInfo(
                    name=v.value,
                    human_readable_name=MODEL_SERVICE_RUNTIME_PROFILES[v].name,
                )
                for v in RuntimeVariant
            ]
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # delete (DELETE /services/{service_id})
    # ------------------------------------------------------------------

    async def delete(self, path: PathParam[ServiceIdPathParam], ctx: UserContext) -> APIResponse:
        params = path.parsed
        log.info(
            "SERVE.DELETE (email:{}, ak:{}, s:{})",
            ctx.user_email,
            ctx.access_key,
            params.service_id,
        )

        deployment_action = DestroyDeploymentAction(endpoint_id=params.service_id)
        deployment_result: DestroyDeploymentActionResult = (
            await self._processors.deployment.destroy_deployment.wait_for_complete(
                deployment_action
            )
        )
        resp = SuccessResponseModel(success=deployment_result.success)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # sync (POST /services/{service_id}/sync)
    # ------------------------------------------------------------------

    async def sync(self, path: PathParam[ServiceIdPathParam], ctx: UserContext) -> APIResponse:
        params = path.parsed
        log.info(
            "SERVE.SYNC (email:{}, ak:{}, s:{})",
            ctx.user_email,
            ctx.access_key,
            params.service_id,
        )

        action = ForceSyncAction(service_id=params.service_id)
        result = await self._processors.model_serving.force_sync.wait_for_complete(action)

        resp = SuccessResponseModel(success=result.success)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # scale (POST /services/{service_id}/scale)
    # ------------------------------------------------------------------

    async def scale(
        self,
        path: PathParam[ServiceIdPathParam],
        body: BodyParam[ScaleRequestModel],
        req: RequestCtx,
    ) -> APIResponse:
        path_params = path.parsed
        params = body.parsed
        request = req.request
        log.info(
            "SERVE.SCALE (email:{}, ak:{}, s:{})",
            request["user"]["email"],
            request["keypair"]["access_key"],
            path_params.service_id,
        )

        action = ScaleServiceReplicasAction(
            max_session_count_per_model_session=request["user"]["resource_policy"][
                "max_session_count_per_model_session"
            ],
            service_id=path_params.service_id,
            to=params.to,
        )

        result = await self._processors.model_serving_auto_scaling.scale_service_replicas.wait_for_complete(
            action
        )

        resp = ScaleResponseModel(
            current_route_count=result.current_route_count,
            target_count=result.target_count,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # update_route (PUT /services/{service_id}/routings/{route_id})
    # ------------------------------------------------------------------

    async def update_route(
        self,
        path: PathParam[ServiceRouteIdPathParam],
        body: BodyParam[UpdateRouteRequestModel],
        ctx: UserContext,
    ) -> APIResponse:
        path_params = path.parsed
        params = body.parsed
        log.info(
            "SERVE.UPDATE_ROUTE (email:{}, ak:{}, s:{}, r:{})",
            ctx.user_email,
            ctx.access_key,
            path_params.service_id,
            path_params.route_id,
        )

        action = UpdateRouteAction(
            service_id=path_params.service_id,
            route_id=path_params.route_id,
            traffic_ratio=params.traffic_ratio,
        )

        result = await self._processors.model_serving.update_route.wait_for_complete(action)

        resp = SuccessResponseModel(success=result.success)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # delete_route (DELETE /services/{service_id}/routings/{route_id})
    # ------------------------------------------------------------------

    async def delete_route(
        self, path: PathParam[ServiceRouteIdPathParam], ctx: UserContext
    ) -> APIResponse:
        path_params = path.parsed
        log.info(
            "SERVE.DELETE_ROUTE (email:{}, ak:{}, s:{})",
            ctx.user_email,
            ctx.access_key,
            path_params.service_id,
        )

        action = DeleteRouteAction(
            service_id=path_params.service_id,
            route_id=path_params.route_id,
        )

        result = await self._processors.model_serving.delete_route.wait_for_complete(action)

        resp = SuccessResponseModel(success=result.success)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # generate_token (POST /services/{service_id}/token)
    # ------------------------------------------------------------------

    async def generate_token(
        self,
        path: PathParam[ServiceIdPathParam],
        body: BodyParam[TokenRequestModel],
        ctx: UserContext,
    ) -> APIResponse:
        path_params = path.parsed
        params = body.parsed
        log.info(
            "SERVE.GENERATE_TOKEN (email:{}, ak:{}, s:{})",
            ctx.user_email,
            ctx.access_key,
            path_params.service_id,
        )

        action = GenerateTokenAction(
            service_id=path_params.service_id,
            duration=params.duration,
            valid_until=params.valid_until,
            expires_at=params.expires_at,
        )

        result = await self._processors.model_serving.generate_token.wait_for_complete(action)

        resp = TokenResponseModel(token=result.data.token)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # list_errors (GET /services/{service_id}/errors)
    # ------------------------------------------------------------------

    async def list_errors(
        self, path: PathParam[ServiceIdPathParam], ctx: UserContext
    ) -> APIResponse:
        path_params = path.parsed
        log.info(
            "SERVE.LIST_ERRORS (email:{}, ak:{}, s:{})",
            ctx.user_email,
            ctx.access_key,
            path_params.service_id,
        )

        action = ListErrorsAction(service_id=path_params.service_id)
        result = await self._processors.model_serving.list_errors.wait_for_complete(action)

        resp = ErrorListResponseModel(
            errors=[
                ErrorInfoModel(session_id=info.session_id, error=info.error)
                for info in result.error_info
            ],
            retries=result.retries,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # clear_error (POST /services/{service_id}/errors/clear)
    # ------------------------------------------------------------------

    async def clear_error(
        self, path: PathParam[ServiceIdPathParam], ctx: UserContext
    ) -> APIResponse:
        path_params = path.parsed
        log.info(
            "SERVE.CLEAR_ERROR (email:{}, ak:{}, s:{})",
            ctx.user_email,
            ctx.access_key,
            path_params.service_id,
        )

        action = ClearErrorAction(service_id=path_params.service_id)
        await self._processors.model_serving.clear_error.wait_for_complete(action)

        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _run_validation(
        self,
        request: Any,
        params: NewServiceRequestModel,
    ) -> ValidateModelServiceActionResult:
        requester_access_key, owner_access_key = await get_access_key_scopes(
            request, {"owner_access_key": params.owner_access_key}
        )
        action = ValidateModelServiceAction(
            requester_access_key=requester_access_key,
            owner_access_key=owner_access_key,
            requester_uuid=request["user"]["uuid"],
            requester_role=request["user"]["role"],
            requester_domain=request["user"]["domain_name"],
            keypair_resource_policy=request["user"]["resource_policy"],
            domain_name=params.domain_name,
            group_name=params.group_name,
            config=ServiceConfig(
                model=params.config.model,
                model_definition_path=params.config.model_definition_path,
                model_version=params.config.model_version,
                model_mount_destination=params.config.model_mount_destination,
                extra_mounts={
                    k: MountOption(
                        mount_destination=v.get("mount_destination"),
                        type=MountTypes(v["type"]) if v.get("type") else MountTypes.BIND,
                        permission=MountPermission(v["permission"])
                        if v.get("permission")
                        else None,
                    )
                    for k, v in params.config.extra_mounts.items()
                },
                environ=params.config.environ,
                scaling_group=params.config.scaling_group,
                resources=params.config.resources,
                resource_opts=params.config.resource_opts,
            ),
            replicas=params.replicas,
            runtime_variant=params.runtime_variant,
            max_session_count_per_model_session=request["user"]["resource_policy"][
                "max_session_count_per_model_session"
            ],
            owner_access_key_override=AccessKey(params.owner_access_key)
            if params.owner_access_key
            else None,
        )
        return await self._processors.model_serving.validate_model_service.wait_for_complete(action)

    @staticmethod
    def _to_model_revision(
        params: NewServiceRequestModel,
        validation_result: ValidateModelServiceActionResult,
    ) -> ModelRevisionSpecDraft:
        return ModelRevisionSpecDraft(
            image_identifier=ImageIdentifierDraft(
                canonical=params.image,
                architecture=params.architecture,
            ),
            resource_spec=ResourceSpecDraft(
                cluster_mode=ClusterMode(params.cluster_mode),
                cluster_size=params.cluster_size,
                resource_slots=params.config.resources,
                resource_opts=params.config.resource_opts,
            ),
            mounts=MountMetadata(
                model_vfolder_id=validation_result.model_id,
                model_definition_path=validation_result.model_definition_path,
                model_mount_destination=params.config.model_mount_destination,
                extra_mounts=list(validation_result.extra_mounts),
            ),
            execution=ExecutionSpec(
                startup_command=params.startup_command,
                bootstrap_script=params.bootstrap_script,
                environ=params.config.environ,
                runtime_variant=params.runtime_variant,
                callback_url=yarl.URL(str(params.callback_url)) if params.callback_url else None,
            ),
        )

    @staticmethod
    def _to_start_action(
        params: NewServiceRequestModel,
        validation_result: ValidateModelServiceActionResult,
        request: Any,
    ) -> DryRunModelServiceAction:
        return DryRunModelServiceAction(
            service_name=params.service_name,
            replicas=params.replicas,
            image=params.image,
            runtime_variant=params.runtime_variant,
            architecture=params.architecture,
            group_name=params.group_name,
            domain_name=params.domain_name,
            cluster_size=params.cluster_size,
            cluster_mode=ClusterMode(params.cluster_mode),
            tag=params.tag,
            startup_command=params.startup_command,
            bootstrap_script=params.bootstrap_script,
            callback_url=params.callback_url,
            owner_access_key=params.owner_access_key,
            open_to_public=params.open_to_public,
            config=ServiceConfig(
                model=params.config.model,
                model_definition_path=params.config.model_definition_path,
                model_version=params.config.model_version,
                model_mount_destination=params.config.model_mount_destination,
                extra_mounts={
                    k: MountOption(
                        mount_destination=v.get("mount_destination"),
                        type=MountTypes(v["type"]) if v.get("type") else MountTypes.BIND,
                        permission=MountPermission(v["permission"])
                        if v.get("permission")
                        else None,
                    )
                    for k, v in params.config.extra_mounts.items()
                },
                environ=params.config.environ,
                scaling_group=params.config.scaling_group,
                resources=params.config.resources,
                resource_opts=params.config.resource_opts,
            ),
            request_user_id=request["user"]["uuid"],
            sudo_session_enabled=request["user"]["sudo_session_enabled"],
            model_service_prepare_ctx=ModelServicePrepareCtx(
                model_id=validation_result.model_id,
                model_definition_path=validation_result.model_definition_path,
                requester_access_key=validation_result.requester_access_key,
                owner_access_key=validation_result.owner_access_key,
                owner_uuid=validation_result.owner_uuid,
                owner_role=validation_result.owner_role,
                group_id=validation_result.group_id,
                resource_policy=validation_result.resource_policy,
                scaling_group=validation_result.scaling_group,
                extra_mounts=validation_result.extra_mounts,
            ),
        )
