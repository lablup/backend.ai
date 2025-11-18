import logging
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Optional, Self

import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
import yarl
from aiohttp import web
from pydantic import (
    AliasChoices,
    AnyUrl,
    ConfigDict,
    Field,
    HttpUrl,
    NonNegativeFloat,
    NonNegativeInt,
    model_validator,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common import typed_validators as tv
from ai.backend.common.api_handlers import BaseFieldModel
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AccessKey,
    ClusterMode,
    RuntimeVariant,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ExecutionSpec,
    ModelRevisionSpec,
    MountMetadata,
    ReplicaSpec,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.model_serving.creator import ModelServiceCreator
from ai.backend.manager.data.model_serving.types import (
    ModelServicePrepareCtx,
    MountOption,
    RequesterCtx,
    ServiceConfig,
    ServiceInfo,
)
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.model_serving.actions.clear_error import ClearErrorAction
from ai.backend.manager.services.model_serving.actions.create_model_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.delete_model_service import (
    DeleteModelServiceAction,
)
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
from ai.backend.manager.services.model_serving.actions.update_route import UpdateRouteAction

from ..defs import DEFAULT_IMAGE_ARCH
from ..errors.api import InvalidAPIParameters
from ..errors.storage import VFolderNotFound
from ..models import (
    ModelServiceHelper,
    UserRole,
    UserRow,
    query_accessible_vfolders,
    vfolders,
)
from ..types import MountOptionModel, UserScope
from .auth import auth_required
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .session import query_userinfo
from .types import CORSOptions, WebMiddleware
from .utils import (
    LegacyBaseRequestModel,
    LegacyBaseResponseModel,
    get_access_key_scopes,
    pydantic_params_api_handler,
    pydantic_response_api_handler,
    undefined,
)

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))


async def is_user_allowed_to_access_resource(
    db_sess: AsyncSession,
    request: web.Request,
    resource_owner: uuid.UUID,
) -> bool:
    if request["user"]["is_superadmin"]:
        return True
    elif request["user"]["is_admin"]:
        query = sa.select(UserRow).filter(UserRow.uuid == resource_owner)
        result = await db_sess.execute(query)
        user = result.scalar()
        return user.domain_name == request["user"]["domain_name"]
    else:
        return request["user"]["uyud"] == resource_owner


class ListServeRequestModel(LegacyBaseRequestModel):
    name: str | None = Field(default=None)


class SuccessResponseModel(LegacyBaseResponseModel):
    success: bool = Field(default=True)


class CompactServeInfoModel(LegacyBaseResponseModel):
    id: uuid.UUID = Field(description="Unique ID referencing the model service.")
    name: str = Field(description="Name of the model service.")
    replicas: NonNegativeInt = Field(description="Number of identical inference sessions.")
    desired_session_count: NonNegativeInt = Field(description="Deprecated; use `replicas` instead.")
    active_route_count: NonNegativeInt = Field(
        description=(
            "Information of routes which are actually spawned and ready to accept the traffic."
        )
    )
    service_endpoint: HttpUrl | None = Field(
        default=None,
        description=(
            "HTTP(S) endpoint to the API service. This field will be filed after the attempt to"
            " create a first inference session succeeds. Endpoint created is fixed and immutable"
            " for the bound endpoint until the endpoint is destroyed."
        ),
    )
    is_public: bool = Field(
        description=(
            'Indicates if the API endpoint is open to public. In this context "public" means there'
            " will be no authentication required to communicate with this API service."
        )
    )


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_params_api_handler(ListServeRequestModel)
async def list_serve(
    request: web.Request, params: ListServeRequestModel
) -> list[CompactServeInfoModel]:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]

    log.info("SERVE.LIST (email:{}, ak:{})", request["user"]["email"], access_key)

    action = ListModelServiceAction(session_owener_id=request["user"]["uuid"], name=params.name)
    result: ListModelServiceActionResult = (
        await root_ctx.processors.model_serving.list_model_service.wait_for_complete(action)
    )

    return [
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


class RouteInfoModel(BaseFieldModel):
    route_id: uuid.UUID = Field(
        description=(
            "Unique ID referencing endpoint route. Each endpoint route has a one-to-one"
            " relationship with the inference session."
        )
    )
    session_id: Optional[uuid.UUID] = Field(
        description="Unique ID referencing the inference session."
    )
    traffic_ratio: NonNegativeFloat


class ServeInfoModel(LegacyBaseResponseModel):
    model_config = ConfigDict(protected_namespaces=())

    endpoint_id: uuid.UUID = Field(description="Unique ID referencing the model service.")
    model_id: uuid.UUID = Field(description="ID of model VFolder.")
    extra_mounts: Sequence[uuid.UUID] = Field(
        description="List of extra VFolders which will be mounted to model service session."
    )
    name: str = Field(description="Name of the model service.")
    replicas: NonNegativeInt = Field(description="Number of identical inference sessions.")
    desired_session_count: NonNegativeInt = Field(description="Deprecated; use `replicas` instead.")
    model_definition_path: str | None = Field(
        description="Path to the the model definition file. If not set, Backend.AI will look for model-definition.yml or model-definition.yaml by default."
    )
    active_routes: list[RouteInfoModel] = Field(
        description="Information of routes which are bound with healthy sessions."
    )
    service_endpoint: HttpUrl | None = Field(
        default=None,
        description=(
            "HTTP(S) endpoint to the API service. This field will be filed after the attempt to"
            " create a first inference session succeeds. Endpoint created is fixed and immutable"
            " for the bound endpoint until the endpoint is destroyed."
        ),
    )
    is_public: bool = Field(
        description=(
            'Indicates if the API endpoint is open to public. In this context "public" means there'
            " will be no authentication required to communicate with this API service."
        )
    )
    runtime_variant: RuntimeVariant = Field(
        description="Type of the inference runtime the image will try to load."
    )

    @classmethod
    def from_dto(cls, dto: ServiceInfo) -> Self:
        return cls(
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

    @classmethod
    def from_deployment_info(cls, deployment_info: DeploymentInfo) -> Self:
        """Convert DeploymentInfo to ServeInfoModel."""
        # Get the first model revision (should only have one for now)
        model_revision = (
            deployment_info.model_revisions[0] if deployment_info.model_revisions else None
        )

        return cls(
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
            active_routes=[],  # Will be populated once sessions are created
            service_endpoint=HttpUrl(deployment_info.network.url)
            if deployment_info.network.url
            else None,
            is_public=deployment_info.network.open_to_public,
            runtime_variant=model_revision.execution.runtime_variant
            if model_revision
            else RuntimeVariant.CUSTOM,
        )


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def get_info(request: web.Request) -> ServeInfoModel:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.GET_INFO (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    action = GetModelServiceInfoAction(
        requester_ctx=RequesterCtx(
            is_authorized=request["is_authorized"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        ),
        service_id=service_id,
    )
    result: GetModelServiceInfoActionResult = (
        await root_ctx.processors.model_serving.get_model_service_info.wait_for_complete(action)
    )

    return ServeInfoModel.from_dto(result.data)


class ServiceConfigModel(LegacyBaseRequestModel):
    model_config = ConfigDict(protected_namespaces=())

    model: str = Field(description="Name or ID of the model VFolder", examples=["ResNet50"])
    model_definition_path: str | None = Field(
        description="Path to the model definition file. If not set, Backend.AI will look for model-definition.yml or model-definition.yaml by default.",
        default=None,
    )
    model_version: int = Field(
        description="Unused; Reserved for future works",
        default=1,
        alias="modelVersion",
    )
    model_mount_destination: str = Field(
        default="/models",
        description=(
            "Mount destination for the model VFolder will be mounted inside the inference session. Must be set to `/models` when choosing `runtime_variant` other than `CUSTOM` or `CMD`."
        ),
        alias="modelMountDestination",
    )

    extra_mounts: dict[uuid.UUID, MountOptionModel] = Field(
        description=(
            "Specifications about extra VFolders mounted to model service session. "
            "MODEL type VFolders are not allowed to be attached to model service session with this option."
        ),
        default_factory=dict,
    )

    environ: Optional[dict[str, str]] = Field(
        description="Environment variables to be set inside the inference session",
        default=None,
    )
    scaling_group: str = Field(
        description="Name of the resource group to spawn inference sessions",
        examples=["nvidia-H100"],
        alias="scalingGroup",
    )
    resources: dict[str, str | int] = Field(examples=[{"cpu": 4, "mem": "32g", "cuda.shares": 2.5}])
    resource_opts: dict[str, str | int | bool] = Field(examples=[{"shmem": "2g"}], default={})

    def to_dataclass(self) -> ServiceConfig:
        extra_mounts_converted = {}
        for key, mount_option in self.extra_mounts.items():
            extra_mounts_converted[key] = MountOption(
                mount_destination=mount_option.mount_destination,
                type=mount_option.type,
                permission=mount_option.permission,
            )

        return ServiceConfig(
            model=self.model,
            model_definition_path=self.model_definition_path,
            model_version=self.model_version,
            model_mount_destination=self.model_mount_destination,
            extra_mounts=extra_mounts_converted,
            environ=self.environ,
            scaling_group=self.scaling_group,
            resources=self.resources,
            resource_opts=self.resource_opts,
        )


@dataclass
class ValidationResult:
    model_id: uuid.UUID
    model_definition_path: Optional[str]
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    owner_uuid: uuid.UUID
    owner_role: UserRole
    group_id: uuid.UUID
    resource_policy: dict
    scaling_group: str
    extra_mounts: Sequence[VFolderMount]


class NewServiceRequestModel(LegacyBaseRequestModel):
    service_name: str = Field(
        description="Name of the service",
        validation_alias=AliasChoices("name", "clientSessionToken"),
        pattern=r"^\w[\w-]*\w$",
        min_length=4,
        max_length=tv.SESSION_NAME_MAX_LENGTH,
    )
    replicas: int = Field(
        description="Number of sessions to serve traffic. Replacement of `desired_session_count` (or `desiredSessionCount`).",
        validation_alias=AliasChoices("desired_session_count", "desiredSessionCount"),
    )
    image: str = Field(
        description="String reference of the image which will be used to create session",
        examples=["cr.backend.ai/stable/python-tensorflow:2.7-py38-cuda11.3"],
        alias="lang",
    )
    runtime_variant: RuntimeVariant = Field(
        description="Type of the inference runtime the image will try to load.",
        default=RuntimeVariant.CUSTOM,
    )
    architecture: str = Field(
        description="Image architecture",
        default=DEFAULT_IMAGE_ARCH,
        alias="arch",
    )
    group_name: str = Field(
        description="Name of project to spawn session",
        default="default",
        validation_alias=AliasChoices("group", "groupName"),
        serialization_alias="group",
    )
    domain_name: str = Field(
        description="Name of domain to spawn session",
        default="default",
        validation_alias=AliasChoices("domain", "domainName"),
        serialization_alias="domain",
    )
    cluster_size: int = Field(
        default=1,
        alias="clusterSize",
    )
    cluster_mode: str = Field(
        default="SINGLE_NODE",
        alias="clusterMode",
    )
    tag: str | None = Field(default=None)
    startup_command: str | None = Field(
        default=None,
        alias="startupCommand",
    )
    bootstrap_script: str | None = Field(
        default=None,
        alias="bootstrapScript",
    )
    callback_url: AnyUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("callbackUrl", "CallbackURL"),
    )
    owner_access_key: str | None = Field(
        description=(
            "(for privileged users only) when specified, transfer ownership of the inference"
            " session to specified user"
        ),
        default=None,
    )
    open_to_public: bool = Field(
        description="If set to true, do not require an API key to access the model service",
        default=False,
    )
    config: ServiceConfigModel

    def to_create_action(
        self,
        validation_result: ValidationResult,
        request_user_id: uuid.UUID,
        sudo_session_enabled: bool,
    ) -> CreateModelServiceAction:
        return CreateModelServiceAction(
            request_user_id=request_user_id,
            creator=ModelServiceCreator(
                service_name=self.service_name,
                replicas=self.replicas,
                image=self.image,
                runtime_variant=self.runtime_variant,
                architecture=self.architecture,
                group_name=self.group_name,
                domain_name=self.domain_name,
                cluster_size=self.cluster_size,
                cluster_mode=ClusterMode(self.cluster_mode),
                tag=self.tag,
                startup_command=self.startup_command,
                bootstrap_script=self.bootstrap_script,
                callback_url=self.callback_url,
                open_to_public=self.open_to_public,
                config=self.config.to_dataclass(),
                sudo_session_enabled=sudo_session_enabled,
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
            ),
        )

    def to_start_action(
        self,
        validation_result: ValidationResult,
        request_user_id: uuid.UUID,
        sudo_session_enabled: bool,
    ) -> DryRunModelServiceAction:
        return DryRunModelServiceAction(
            service_name=self.service_name,
            replicas=self.replicas,
            image=self.image,
            runtime_variant=self.runtime_variant,
            architecture=self.architecture,
            group_name=self.group_name,
            domain_name=self.domain_name,
            cluster_size=self.cluster_size,
            cluster_mode=ClusterMode(self.cluster_mode),
            tag=self.tag,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            callback_url=self.callback_url,
            owner_access_key=self.owner_access_key,
            open_to_public=self.open_to_public,
            config=self.config.to_dataclass(),
            request_user_id=request_user_id,
            sudo_session_enabled=sudo_session_enabled,
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

    def to_image_identifier(self) -> ImageIdentifier:
        """Convert to ImageIdentifier for deployment."""
        return ImageIdentifier(
            canonical=self.image,
            architecture=self.architecture,
        )

    def to_model_revision(self, validation_result: ValidationResult) -> ModelRevisionSpec:
        """Convert to ModelRevisionSpec for deployment."""
        return ModelRevisionSpec(
            image_identifier=self.to_image_identifier(),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode(self.cluster_mode),
                cluster_size=self.cluster_size,
                resource_slots=self.config.resources,
                resource_opts=self.config.resource_opts,
            ),
            mounts=MountMetadata(
                model_vfolder_id=validation_result.model_id,
                model_definition_path=validation_result.model_definition_path,
                model_mount_destination=self.config.model_mount_destination,
                extra_mounts=list(validation_result.extra_mounts),
            ),
            execution=ExecutionSpec(
                startup_command=self.startup_command,
                bootstrap_script=self.bootstrap_script,
                environ=self.config.environ,
                runtime_variant=self.runtime_variant,
                callback_url=yarl.URL(str(self.callback_url)) if self.callback_url else None,
            ),
        )


async def _validate(request: web.Request, params: NewServiceRequestModel) -> ValidationResult:
    root_ctx: RootContext = request.app["_root.context"]
    scopes_param = {
        "owner_access_key": (
            None if params.owner_access_key is undefined else params.owner_access_key
        ),
    }

    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)
    if params.replicas > (
        _m := request["user"]["resource_policy"]["max_session_count_per_model_session"]
    ):
        raise InvalidAPIParameters(f"Cannot spawn more than {_m} sessions for a single service")

    async with root_ctx.db.begin_readonly() as conn:
        checked_scaling_group = await ModelServiceHelper.check_scaling_group(
            conn,
            params.config.scaling_group,
            owner_access_key,
            params.domain_name,
            params.group_name,
        )

        params.config.scaling_group = checked_scaling_group

        owner_uuid, group_id, resource_policy = await query_userinfo(
            request, params.model_dump(by_alias=True), conn
        )
        query = sa.select([UserRow.role]).where(UserRow.uuid == owner_uuid)
        owner_role = (await conn.execute(query)).scalar()
        assert owner_role

        allowed_vfolder_types = (
            await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        try:
            extra_vf_conds = vfolders.c.id == uuid.UUID(params.config.model)
            matched_vfolders = await query_accessible_vfolders(
                conn,
                owner_uuid,
                user_role=owner_role,
                domain_name=params.domain_name,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=extra_vf_conds,
            )
        except Exception as e:
            # just catching ValueError | VFolderNotFound will raise
            # TypeError: catching classes that do not inherit from BaseException is not allowed
            if isinstance(e, ValueError) or isinstance(e, VFolderNotFound):
                try:
                    extra_vf_conds = (vfolders.c.name == params.config.model) & (
                        vfolders.c.usage_mode == VFolderUsageMode.MODEL
                    )
                    matched_vfolders = await query_accessible_vfolders(
                        conn,
                        owner_uuid,
                        user_role=owner_role,
                        domain_name=params.domain_name,
                        allowed_vfolder_types=allowed_vfolder_types,
                        extra_vf_conds=extra_vf_conds,
                    )
                except VFolderNotFound as e:
                    raise VFolderNotFound("Cannot find model folder") from e
            else:
                raise
        if len(matched_vfolders) == 0:
            raise VFolderNotFound
        folder_row = matched_vfolders[0]
        if folder_row["usage_mode"] != VFolderUsageMode.MODEL:
            raise InvalidAPIParameters("Selected VFolder is not a model folder")

        model_id = folder_row["id"]

        vfolder_mounts = await ModelServiceHelper.check_extra_mounts(
            conn,
            root_ctx.config_provider.legacy_etcd_config_loader,
            root_ctx.storage_manager,
            model_id,
            params.config.model_mount_destination,
            params.config.extra_mounts,
            UserScope(
                domain_name=params.domain_name,
                group_id=group_id,
                user_uuid=owner_uuid,
                user_role=owner_role,
            ),
            resource_policy,
        )

    if params.runtime_variant == RuntimeVariant.CUSTOM:
        vfid = VFolderID(folder_row["quota_scope_id"], folder_row["id"])
        yaml_path = await ModelServiceHelper.validate_model_definition_file_exists(
            root_ctx.storage_manager,
            folder_row["host"],
            vfid,
            params.config.model_definition_path,
        )
        await ModelServiceHelper.validate_model_definition(
            root_ctx.storage_manager,
            folder_row["host"],
            vfid,
            yaml_path,
        )
    else:
        if (
            params.runtime_variant != RuntimeVariant.CMD
            and params.config.model_mount_destination != "/models"
        ):
            raise InvalidAPIParameters(
                "Model mount destination must be /models for non-custom runtimes"
            )
        # this path won't be used on actual session but just to keep the convention
        yaml_path = "model-definition.yaml"

    return ValidationResult(
        model_id,
        yaml_path,
        requester_access_key,
        owner_access_key,
        owner_uuid,
        owner_role,
        group_id,
        resource_policy,
        checked_scaling_group,
        vfolder_mounts,
    )


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(NewServiceRequestModel)
async def create(request: web.Request, params: NewServiceRequestModel) -> ServeInfoModel:
    """
    Creates a new model service. If `replicas` is greater than zero,
    then inference sessions will be automatically scheduled upon successful creation of model service.
    """
    root_ctx: RootContext = request.app["_root.context"]

    validation_result = await _validate(request, params)
    # Use deployment service if sokovan is enabled, otherwise fall back to model_serving
    if (
        root_ctx.config_provider.config.manager.use_sokovan
        and root_ctx.processors.deployment is not None
    ):
        # Create deployment using the new deployment controller
        deployment_action = CreateDeploymentAction(
            creator=DeploymentCreator(
                metadata=DeploymentMetadata(
                    name=params.service_name,
                    domain=params.domain_name,
                    project=validation_result.group_id,
                    resource_group=validation_result.scaling_group,
                    created_user=request["user"]["uuid"],
                    session_owner=validation_result.owner_uuid,
                    created_at=None,  # Will be set by controller
                    tag=params.tag,
                ),
                replica_spec=ReplicaSpec(
                    replica_count=params.replicas,
                ),
                model_revision=params.to_model_revision(validation_result),
                network=DeploymentNetworkSpec(
                    open_to_public=params.open_to_public,
                ),
            )
        )
        deployment_result: CreateDeploymentActionResult = (
            await root_ctx.processors.deployment.create_deployment.wait_for_complete(
                deployment_action
            )
        )
        return ServeInfoModel.from_deployment_info(deployment_result.data)
    else:
        # Fall back to model_serving
        action = params.to_create_action(
            validation_result=validation_result,
            request_user_id=request["user"]["uuid"],
            sudo_session_enabled=request["user"]["sudo_session_enabled"],
        )
        result: CreateModelServiceActionResult = (
            await root_ctx.processors.model_serving.create_model_service.wait_for_complete(action)
        )
        return ServeInfoModel.from_dto(result.data)


class TryStartResponseModel(LegacyBaseResponseModel):
    task_id: str


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(NewServiceRequestModel)
async def try_start(request: web.Request, params: NewServiceRequestModel) -> TryStartResponseModel:
    root_ctx: RootContext = request.app["_root.context"]

    validation_result = await _validate(request, params)

    action = params.to_start_action(
        validation_result=validation_result,
        request_user_id=request["user"]["uuid"],
        sudo_session_enabled=request["user"]["sudo_session_enabled"],
    )

    result = await root_ctx.processors.model_serving.dry_run_model_service.wait_for_complete(action)

    return TryStartResponseModel(task_id=str(result.task_id))


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def delete(request: web.Request) -> SuccessResponseModel:
    """
    Removes model service (and inference sessions for the service also).
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.DELETE (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    # Use deployment service if sokovan is enabled, otherwise fall back to model_serving
    if (
        root_ctx.config_provider.config.manager.use_sokovan
        and root_ctx.processors.deployment is not None
    ):
        # Use deployment destroy action
        deployment_action = DestroyDeploymentAction(
            endpoint_id=service_id,
        )
        deployment_result: DestroyDeploymentActionResult = (
            await root_ctx.processors.deployment.destroy_deployment.wait_for_complete(
                deployment_action
            )
        )
        return SuccessResponseModel(success=deployment_result.success)
    else:
        # Fall back to model_serving
        action = DeleteModelServiceAction(
            service_id=service_id,
            requester_ctx=RequesterCtx(
                is_authorized=request["is_authorized"],
                user_id=request["user"]["uuid"],
                user_role=request["user"]["role"],
                domain_name=request["user"]["domain_name"],
            ),
        )
        result = await root_ctx.processors.model_serving.delete_model_service.wait_for_complete(
            action
        )
        return SuccessResponseModel(success=result.success)


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def sync(request: web.Request) -> SuccessResponseModel:
    """
    Force syncs up-to-date model service information with AppProxy.
    In normal situations this will be automatically handled by Backend.AI schedulers,
    but this API is left open in case of unexpected restart of AppProxy process.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info("SERVE.SYNC (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id)

    action = ForceSyncAction(
        service_id=service_id,
        requester_ctx=RequesterCtx(
            is_authorized=request["is_authorized"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        ),
    )
    result = await root_ctx.processors.model_serving.force_sync.wait_for_complete(action)

    return SuccessResponseModel(success=result.success)


class ScaleRequestModel(LegacyBaseRequestModel):
    to: int = Field(description="Ideal number of inference sessions")


class ScaleResponseModel(LegacyBaseResponseModel):
    current_route_count: int
    target_count: int


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_params_api_handler(ScaleRequestModel)
async def scale(request: web.Request, params: ScaleRequestModel) -> ScaleResponseModel:
    """
    Updates ideal inference session count manually. Based on the difference of this number,
    inference sessions will be created or removed automatically.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.SCALE (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    action = ScaleServiceReplicasAction(
        requester_ctx=RequesterCtx(
            is_authorized=request["is_authorized"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        ),
        max_session_count_per_model_session=request["user"]["resource_policy"][
            "max_session_count_per_model_session"
        ],
        service_id=service_id,
        to=params.to,
    )

    result = await root_ctx.processors.model_serving_auto_scaling.scale_service_replicas.wait_for_complete(
        action
    )

    return ScaleResponseModel(
        current_route_count=result.current_route_count, target_count=result.target_count
    )


class UpdateRouteRequestModel(LegacyBaseRequestModel):
    traffic_ratio: NonNegativeFloat


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_params_api_handler(UpdateRouteRequestModel)
async def update_route(
    request: web.Request, params: UpdateRouteRequestModel
) -> SuccessResponseModel:
    """
    Updates traffic bias of specific route.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])
    route_id = uuid.UUID(request.match_info["route_id"])

    log.info(
        "SERVE.UPDATE_ROUTE (email:{}, ak:{}, s:{}, r:{})",
        request["user"]["email"],
        access_key,
        service_id,
        route_id,
    )

    action = UpdateRouteAction(
        requester_ctx=RequesterCtx(
            is_authorized=request["is_authorized"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        ),
        service_id=service_id,
        route_id=route_id,
        traffic_ratio=params.traffic_ratio,
    )

    result = await root_ctx.processors.model_serving.update_route.wait_for_complete(action)

    return SuccessResponseModel(success=result.success)


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def delete_route(request: web.Request) -> SuccessResponseModel:
    """
    Scales down the service by removing specific inference session.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])
    route_id = uuid.UUID(request.match_info["route_id"])

    log.info(
        "SERVE.DELETE_ROUTE (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )

    action = DeleteRouteAction(
        requester_ctx=RequesterCtx(
            is_authorized=request["is_authorized"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        ),
        service_id=service_id,
        route_id=route_id,
    )

    result = await root_ctx.processors.model_serving.delete_route.wait_for_complete(action)

    return SuccessResponseModel(success=result.success)


class TokenRequestModel(LegacyBaseRequestModel):
    duration: tv.TimeDuration | None = Field(
        default=None, description="The lifetime duration of the token."
    )
    valid_until: int | None = Field(
        default=None,
        description="The absolute token expiry date expressed in the Unix epoch format.",
    )
    expires_at: int = Field(
        default=-1,
        description="The expiration timestamp computed from duration or valid_until.",
    )

    @model_validator(mode="after")
    def check_lifetime(self) -> Self:
        now = datetime.now()
        if self.valid_until is not None:
            self.expires_at = self.valid_until
        elif self.duration is not None:
            self.expires_at = int((now + self.duration).timestamp())
        else:
            raise ValueError("Either valid_until or duration must be specified.")
        if now.timestamp() > self.expires_at:
            raise ValueError("The expiration time cannot be in the past.")
        return self


class TokenResponseModel(LegacyBaseResponseModel):
    token: str


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_params_api_handler(TokenRequestModel)
async def generate_token(request: web.Request, params: TokenRequestModel) -> TokenResponseModel:
    """
    Generates a token which acts as an API key to authenticate when calling model service endpoint.
    If both duration and valid_until is not set then the AppProxy will determine appropriate lifetime of the token.
    duration and valid_until can't be both specified.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.GENERATE_TOKEN (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )

    action = GenerateTokenAction(
        requester_ctx=RequesterCtx(
            is_authorized=request["is_authorized"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        ),
        service_id=service_id,
        duration=params.duration,
        valid_until=params.valid_until,
        expires_at=params.expires_at,
    )

    result = await root_ctx.processors.model_serving.generate_token.wait_for_complete(action)

    return TokenResponseModel(token=result.data.token)


class ErrorInfoModel(BaseFieldModel):
    session_id: uuid.UUID | None
    error: dict[str, Any]


class ErrorListResponseModel(LegacyBaseResponseModel):
    errors: list[ErrorInfoModel]
    retries: int


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def list_errors(request: web.Request) -> ErrorListResponseModel:
    """
    List errors raised while trying to create the inference sessions. Backend.AI will
    stop trying to create an inference session for the model service if six (6) error stacks
    up. The only way to clear the error and retry spawning session is to call
    `clear_error` (POST /services/{service_id}/errors/clear) API.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.LIST_ERRORS (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )

    action = ListErrorsAction(
        requester_ctx=RequesterCtx(
            is_authorized=request["is_authorized"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        ),
        service_id=service_id,
    )

    result = await root_ctx.processors.model_serving.list_errors.wait_for_complete(action)

    return ErrorListResponseModel(
        errors=[
            ErrorInfoModel(session_id=info.session_id, error=info.error)
            for info in result.error_info
        ],
        retries=result.retries,
    )


@auth_required
@server_status_required(READ_ALLOWED)
async def clear_error(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.CLEAR_ERROR (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )

    action = ClearErrorAction(
        requester_ctx=RequesterCtx(
            is_authorized=request["is_authorized"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        ),
        service_id=service_id,
    )

    await root_ctx.processors.model_serving.clear_error.wait_for_complete(action)

    return web.Response(status=HTTPStatus.NO_CONTENT)


class RuntimeInfo(BaseFieldModel):
    name: str = Field(description="Identifier to be passed later inside request body")
    human_readable_name: str = Field(description="Use this value as displayed label to user")


class RuntimeInfoModel(LegacyBaseResponseModel):
    runtimes: list[RuntimeInfo]


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def list_supported_runtimes(request: web.Request) -> RuntimeInfoModel:
    return RuntimeInfoModel(
        runtimes=[
            RuntimeInfo(name=v.value, human_readable_name=MODEL_SERVICE_RUNTIME_PROFILES[v].name)
            for v in RuntimeVariant
        ]
    )


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    await app_ctx.database_ptask_group.shutdown()


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "services"
    app["api_versions"] = (4, 5)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["services.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_serve))
    cors.add(root_resource.add_route("POST", create))
    cors.add(add_route("POST", "/_/try", try_start))
    cors.add(add_route("GET", "/_/runtimes", list_supported_runtimes))
    cors.add(add_route("GET", "/{service_id}", get_info))
    cors.add(add_route("DELETE", "/{service_id}", delete))
    cors.add(add_route("GET", "/{service_id}/errors", list_errors))
    cors.add(add_route("POST", "/{service_id}/errors/clear", clear_error))
    cors.add(add_route("POST", "/{service_id}/scale", scale))
    cors.add(add_route("POST", "/{service_id}/sync", sync))
    cors.add(add_route("PUT", "/{service_id}/routings/{route_id}", update_route))
    cors.add(add_route("DELETE", "/{service_id}/routings/{route_id}", delete_route))
    cors.add(add_route("POST", "/{service_id}/token", generate_token))
    return app, []
