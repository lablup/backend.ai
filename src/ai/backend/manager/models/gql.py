# ruff: noqa: E402
from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, cast

import attrs
import graphene
import sqlalchemy as sa
from graphene.types.inputobjecttype import set_input_object_type_default_value
from graphql import GraphQLError, OperationType, Undefined
from graphql.type import GraphQLField
from sqlalchemy.orm import joinedload, selectinload

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    PermissionDeniedError,
)
from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.gql_models.audit_log import (
    AuditLogConnection,
    AuditLogNode,
    AuditLogSchema,
)
from ai.backend.manager.models.gql_models.service_config import (
    AvailableServiceConnection,
    AvailableServiceNode,
    ModifyServiceConfigNode,
    ServiceConfigConnection,
    ServiceConfigNode,
)
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.service.base import ServicesContext
from ai.backend.manager.services.processors import Processors

from .gql_models.container_registry import (
    ContainerRegistryConnection,
    ContainerRegistryNode,
    ContainerRegistryScopeField,
    CreateContainerRegistryNode,
    DeleteContainerRegistryNode,
    ModifyContainerRegistryNode,
)
from .gql_models.container_registry_v2 import (
    CreateContainerRegistryNodeV2,
    DeleteContainerRegistryNodeV2,
    ModifyContainerRegistryNodeV2,
)

set_input_object_type_default_value(Undefined)

from ai.backend.common.types import QuotaScopeID, SessionId
from ai.backend.manager.defs import DEFAULT_IMAGE_ARCH
from ai.backend.manager.models.gql_relay import (
    AsyncListConnectionField,
    AsyncNode,
    ConnectionResolverResult,
    GlobalIDField,
    ResolvedGlobalID,
)
from ai.backend.manager.models.session import SessionRow

from .container_registry import (
    ContainerRegistry,
    CreateContainerRegistry,
    DeleteContainerRegistry,
    ModifyContainerRegistry,
)
from .rbac import ContainerRegistryScope

if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.common.types import (
        AccessKey,
        AgentId,
        SlotName,
        SlotTypes,
    )

    from ..api.manager import ManagerStatus
    from ..idle import IdleCheckerHost
    from ..models.utils import ExtendedAsyncSAEngine
    from ..registry import AgentRegistry
    from ..repositories.agent.repository import AgentRepository
    from ..repositories.scheduler.repository import SchedulerRepository
    from ..repositories.user.repository import UserRepository
    from .storage import StorageSessionManager

from ..data.image.types import ImageStatus
from ..errors.api import InvalidAPIParameters
from ..errors.auth import InsufficientPrivilege
from ..errors.common import ObjectNotFound
from ..errors.image import ImageNotFound
from ..errors.kernel import TooManyKernelsFound
from .acl import PredefinedAtomicPermission
from .base import DataLoaderManager, PaginatedConnectionField, privileged_query, scoped_query
from .gql_models.agent import (
    Agent,
    AgentConnection,
    AgentList,
    AgentNode,
    AgentSummary,
    AgentSummaryList,
    ModifyAgent,
    RescanGPUAllocMaps,
)
from .gql_models.container_registry import (
    CreateContainerRegistryQuota,
    DeleteContainerRegistryQuota,
    UpdateContainerRegistryQuota,
)
from .gql_models.domain import (
    CreateDomain,
    CreateDomainNode,
    DeleteDomain,
    Domain,
    DomainConnection,
    DomainNode,
    DomainPermissionValueField,
    ModifyDomain,
    ModifyDomainNode,
    PurgeDomain,
)
from .gql_models.endpoint import (
    CreateEndpointAutoScalingRuleNode,
    DeleteEndpointAutoScalingRuleNode,
    Endpoint,
    EndpointAutoScalingRuleConnection,
    EndpointAutoScalingRuleNode,
    EndpointList,
    EndpointToken,
    EndpointTokenList,
    ModifyEndpoint,
    ModifyEndpointAutoScalingRuleNode,
)
from .gql_models.fields import AgentPermissionField, ScopeField
from .gql_models.group import (
    CreateGroup,
    DeleteGroup,
    Group,
    GroupConnection,
    GroupNode,
    GroupPermissionField,
    ModifyGroup,
    PurgeGroup,
)
from .gql_models.image import (
    AliasImage,
    ClearImageCustomResourceLimit,
    ClearImages,
    DealiasImage,
    ForgetImage,
    ForgetImageById,
    Image,
    ImageConnection,
    ImageNode,
    ImagePermissionValueField,
    ImageStatusType,
    ModifyImage,
    PreloadImage,
    PurgeImageById,
    PurgeImages,
    RescanImages,
    UnloadImage,
    UntagImageFromRegistry,
)
from .gql_models.kernel import (
    ComputeContainer,
    ComputeContainerList,
    LegacyComputeSession,
    LegacyComputeSessionList,
)
from .gql_models.keypair import CreateKeyPair, DeleteKeyPair, KeyPair, KeyPairList, ModifyKeyPair
from .gql_models.metric.base import ContainerUtilizationMetricMetadata
from .gql_models.metric.user import UserUtilizationMetric, UserUtilizationMetricQueryInput
from .gql_models.pending_queue import SessionPendingQueueConnection
from .gql_models.resource_preset import (
    CreateResourcePreset,
    DeleteResourcePreset,
    ModifyResourcePreset,
    ResourcePreset,
)
from .gql_models.scaling_group import (
    AssociateScalingGroupsWithDomain,
    AssociateScalingGroupsWithKeyPair,
    AssociateScalingGroupsWithUserGroup,
    AssociateScalingGroupWithDomain,
    AssociateScalingGroupWithKeyPair,
    AssociateScalingGroupWithUserGroup,
    CreateScalingGroup,
    DeleteScalingGroup,
    DisassociateAllScalingGroupsWithDomain,
    DisassociateAllScalingGroupsWithGroup,
    DisassociateScalingGroupsWithDomain,
    DisassociateScalingGroupsWithKeyPair,
    DisassociateScalingGroupsWithUserGroup,
    DisassociateScalingGroupWithDomain,
    DisassociateScalingGroupWithKeyPair,
    DisassociateScalingGroupWithUserGroup,
    ModifyScalingGroup,
    ScalingGroup,
)
from .gql_models.session import (
    CheckAndTransitStatus,
    ComputeSession,
    ComputeSessionConnection,
    ComputeSessionList,
    ComputeSessionNode,
    ModifyComputeSession,
    SessionPermissionValueField,
    TotalResourceSlot,
)
from .gql_models.user import (
    CreateUser,
    DeleteUser,
    ModifyUser,
    PurgeUser,
    User,
    UserConnection,
    UserList,
    UserNode,
)
from .gql_models.vfolder import (
    ModelCard,
    ModelCardConnection,
    VFolderPermissionValueField,
    VirtualFolderConnection,
    VirtualFolderNode,
)
from .gql_models.viewer import Viewer
from .group import (
    ProjectType,
)
from .image import (
    ImageLoadFilter,
    PublicImageLoadFilter,
)
from .network import CreateNetwork, DeleteNetwork, ModifyNetwork, NetworkConnection, NetworkNode
from .rbac import ProjectScope, ScopeType, SystemScope
from .rbac.permission_defs import (
    AgentPermission,
    ComputeSessionPermission,
    DomainPermission,
    ImagePermission,
    ProjectPermission,
)
from .rbac.permission_defs import VFolderPermission as VFolderRBACPermission
from .resource_policy import (
    CreateKeyPairResourcePolicy,
    CreateProjectResourcePolicy,
    CreateUserResourcePolicy,
    DeleteKeyPairResourcePolicy,
    DeleteProjectResourcePolicy,
    DeleteUserResourcePolicy,
    KeyPairResourcePolicy,
    ModifyKeyPairResourcePolicy,
    ModifyProjectResourcePolicy,
    ModifyUserResourcePolicy,
    ProjectResourcePolicy,
    UserResourcePolicy,
)
from .routing import Routing, RoutingList
from .scaling_group import (
    ScalingGroupRow,
    and_names,
    query_allowed_sgroups,
)
from .session import (
    SessionStatus,
)
from .storage import StorageVolume, StorageVolumeList
from .user import (
    UserRole,
    UserStatus,
)
from .vfolder import (
    QuotaScope,
    SetQuotaScope,
    UnsetQuotaScope,
    VirtualFolder,
    VirtualFolderList,
    VirtualFolderPermission,
    VirtualFolderPermissionList,
    ensure_quota_scope_accessible_by_user,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _is_legacy_mutation(mutation_cls: Any) -> bool:
    """
    Checks whether the GraphQL mutation is in the legacy format with the fields `ok` and `msg`.
    """
    fields = getattr(mutation_cls, "_meta").fields
    return {"ok", "msg"}.issubset(fields)


@attrs.define(auto_attribs=True, slots=True)
class GraphQueryContext:
    schema: graphene.Schema
    dataloader_manager: DataLoaderManager
    config_provider: ManagerConfigProvider
    etcd: AsyncEtcd
    user: Mapping[str, Any]  # TODO: express using typed dict
    access_key: str
    db: ExtendedAsyncSAEngine
    network_plugin_ctx: NetworkPluginContext
    services_ctx: ServicesContext
    valkey_stat: ValkeyStatClient
    valkey_live: ValkeyLiveClient
    valkey_image: ValkeyImageClient
    valkey_schedule: ValkeyScheduleClient  # TODO: Remove this client from here
    manager_status: ManagerStatus
    known_slot_types: Mapping[SlotName, SlotTypes]
    background_task_manager: BackgroundTaskManager
    storage_manager: StorageSessionManager
    registry: AgentRegistry
    idle_checker_host: IdleCheckerHost
    metric_observer: GraphQLMetricObserver
    processors: Processors
    scheduler_repository: SchedulerRepository
    user_repository: UserRepository
    agent_repository: AgentRepository


class Mutation(graphene.ObjectType):
    """
    All available GraphQL mutations.
    Type name changed from 'Mutations' to 'Mutation' in 25.13.0
    """

    # super-admin only
    modify_agent = ModifyAgent.Field()

    # super-admin only
    create_domain = CreateDomain.Field()
    modify_domain = ModifyDomain.Field()
    delete_domain = DeleteDomain.Field()
    purge_domain = PurgeDomain.Field()

    create_domain_node = CreateDomainNode.Field(description="Added in 24.12.0.")
    modify_domain_node = ModifyDomainNode.Field(description="Added in 24.12.0.")

    # admin only
    create_group = CreateGroup.Field()
    modify_group = ModifyGroup.Field()
    delete_group = DeleteGroup.Field()
    purge_group = PurgeGroup.Field()

    # super-admin only
    create_user = CreateUser.Field()
    modify_user = ModifyUser.Field()
    delete_user = DeleteUser.Field()
    purge_user = PurgeUser.Field()
    rescan_gpu_alloc_maps = RescanGPUAllocMaps.Field(description="Added in 25.4.0.")

    # admin only
    create_keypair = CreateKeyPair.Field()
    modify_keypair = ModifyKeyPair.Field()
    delete_keypair = DeleteKeyPair.Field()

    # admin only
    rescan_images = RescanImages.Field()
    preload_image = PreloadImage.Field()
    unload_image = UnloadImage.Field()
    modify_image = ModifyImage.Field()
    clear_image_custom_resource_limit = ClearImageCustomResourceLimit.Field(
        description="Added in 25.6.0"
    )
    forget_image_by_id = ForgetImageById.Field(description="Added in 24.03.0")
    forget_image = ForgetImage.Field(
        deprecation_reason="Deprecated since 25.4.0. Use `forget_image_by_id` instead."
    )
    purge_image_by_id = PurgeImageById.Field(description="Added in 25.4.0")
    untag_image_from_registry = UntagImageFromRegistry.Field(description="Added in 24.03.1")
    alias_image = AliasImage.Field()
    dealias_image = DealiasImage.Field()
    clear_images = ClearImages.Field()
    purge_images = PurgeImages.Field(description="Added in 25.4.0")

    # super-admin only
    modify_compute_session = ModifyComputeSession.Field()

    # super-admin only
    create_keypair_resource_policy = CreateKeyPairResourcePolicy.Field()
    modify_keypair_resource_policy = ModifyKeyPairResourcePolicy.Field()
    delete_keypair_resource_policy = DeleteKeyPairResourcePolicy.Field()

    # super-admin only
    create_user_resource_policy = CreateUserResourcePolicy.Field()
    modify_user_resource_policy = ModifyUserResourcePolicy.Field()
    delete_user_resource_policy = DeleteUserResourcePolicy.Field()

    # super-admin only
    create_project_resource_policy = CreateProjectResourcePolicy.Field()
    modify_project_resource_policy = ModifyProjectResourcePolicy.Field()
    delete_project_resource_policy = DeleteProjectResourcePolicy.Field()

    # super-admin only
    create_resource_preset = CreateResourcePreset.Field()
    modify_resource_preset = ModifyResourcePreset.Field()
    delete_resource_preset = DeleteResourcePreset.Field()

    # super-admin only
    modify_service_config = ModifyServiceConfigNode.Field()

    # super-admin only
    create_scaling_group = CreateScalingGroup.Field()
    modify_scaling_group = ModifyScalingGroup.Field()
    delete_scaling_group = DeleteScalingGroup.Field()
    associate_scaling_group_with_domain = AssociateScalingGroupWithDomain.Field()
    associate_scaling_groups_with_domain = AssociateScalingGroupsWithDomain.Field(
        description="Added in 24.03.9"
    )
    associate_scaling_group_with_user_group = AssociateScalingGroupWithUserGroup.Field()
    associate_scaling_groups_with_user_group = AssociateScalingGroupsWithUserGroup.Field(
        description="Added in 24.03.9"
    )
    associate_scaling_group_with_keypair = AssociateScalingGroupWithKeyPair.Field()
    associate_scaling_groups_with_keypair = AssociateScalingGroupsWithKeyPair.Field(
        description="Added in 24.03.9"
    )
    disassociate_scaling_group_with_domain = DisassociateScalingGroupWithDomain.Field()
    disassociate_scaling_groups_with_domain = DisassociateScalingGroupsWithDomain.Field(
        description="Added in 24.03.9"
    )
    disassociate_scaling_group_with_user_group = DisassociateScalingGroupWithUserGroup.Field()
    disassociate_scaling_groups_with_user_group = DisassociateScalingGroupsWithUserGroup.Field(
        description="Added in 24.03.9"
    )
    disassociate_scaling_group_with_keypair = DisassociateScalingGroupWithKeyPair.Field()
    disassociate_scaling_groups_with_keypair = DisassociateScalingGroupsWithKeyPair.Field(
        description="Added in 24.03.9"
    )
    disassociate_all_scaling_groups_with_domain = DisassociateAllScalingGroupsWithDomain.Field()
    disassociate_all_scaling_groups_with_group = DisassociateAllScalingGroupsWithGroup.Field()

    set_quota_scope = SetQuotaScope.Field()
    unset_quota_scope = UnsetQuotaScope.Field()

    create_container_registry_node = CreateContainerRegistryNode.Field(
        description="Added in 24.09.0.",
        deprecation_reason="Deprecated since 25.3.0. use `create_container_registry_node_v2` instead.",
    )
    modify_container_registry_node = ModifyContainerRegistryNode.Field(
        description="Added in 24.09.0.",
        deprecation_reason="Deprecated since 25.3.0. use `modify_container_registry_node_v2` instead.",
    )
    delete_container_registry_node = DeleteContainerRegistryNode.Field(
        description="Added in 24.09.0.",
        deprecation_reason="Deprecated since 25.3.0. use `delete_container_registry_node_v2` instead.",
    )

    create_container_registry_node_v2 = CreateContainerRegistryNodeV2.Field(
        description="Added in 25.3.0.",
    )
    modify_container_registry_node_v2 = ModifyContainerRegistryNodeV2.Field(
        description="Added in 25.3.0.",
    )
    delete_container_registry_node_v2 = DeleteContainerRegistryNodeV2.Field(
        description="Added in 25.3.0.",
    )

    create_endpoint_auto_scaling_rule_node = CreateEndpointAutoScalingRuleNode.Field(
        description="Added in 25.1.0."
    )
    modify_endpoint_auto_scaling_rule_node = ModifyEndpointAutoScalingRuleNode.Field(
        description="Added in 25.1.0."
    )
    delete_endpoint_auto_scaling_rule_node = DeleteEndpointAutoScalingRuleNode.Field(
        description="Added in 25.1.0."
    )
    create_container_registry_quota = CreateContainerRegistryQuota.Field(
        description="Added in 25.3.0."
    )
    update_container_registry_quota = UpdateContainerRegistryQuota.Field(
        description="Added in 25.3.0."
    )
    delete_container_registry_quota = DeleteContainerRegistryQuota.Field(
        description="Added in 25.3.0."
    )

    # Legacy mutations
    create_container_registry = CreateContainerRegistry.Field(
        deprecation_reason="Deprecated since 24.09.0. use `create_container_registry_node_v2` instead."
    )
    modify_container_registry = ModifyContainerRegistry.Field(
        deprecation_reason="Deprecated since 24.09.0. use `modify_container_registry_node_v2` instead."
    )
    delete_container_registry = DeleteContainerRegistry.Field(
        deprecation_reason="Deprecated since 24.09.0. use `delete_container_registry_node_v2` instead."
    )

    modify_endpoint = ModifyEndpoint.Field()

    check_and_transit_session_status = CheckAndTransitStatus.Field(description="Added in 24.09.0.")
    create_network = CreateNetwork.Field()
    modify_network = ModifyNetwork.Field()
    delete_network = DeleteNetwork.Field()


class Query(graphene.ObjectType):
    """
    All available GraphQL queries.
    Type name changed from 'Queries' to 'Query' in 25.13.0
    """

    node = AsyncNode.Field()

    # super-admin only
    audit_log_schema = graphene.Field(
        AuditLogSchema,
        description="Added in 25.6.0.",
    )
    audit_log_nodes = PaginatedConnectionField(
        AuditLogConnection,
        description="Added in 25.6.0.",
        filter=graphene.String(
            description="Specifies the criteria used to narrow down the query results based on certain conditions."
        ),
        order=graphene.String(description="Specifies the sorting order of the query result."),
        offset=graphene.Int(
            description="Specifies how many items to skip before beginning to return result."
        ),
        before=graphene.String(
            description="If this value is provided, the query will be limited to that value."
        ),
        after=graphene.String(
            description="Queries the `last` number of results from the query result from last."
        ),
        first=graphene.Int(
            description="Queries the `first` number of results from the query result from first."
        ),
        last=graphene.Int(
            description="If the given value is provided, the query will start from that value."
        ),
    )

    # super-admin only
    agent = graphene.Field(
        Agent,
        agent_id=graphene.String(required=True),
    )

    # super-admin only
    agent_list = graphene.Field(
        AgentList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # filters
        scaling_group=graphene.String(),
        status=graphene.String(),
    )

    # super-admin only
    agents = graphene.List(  # legacy non-paginated list
        Agent,
        scaling_group=graphene.String(),
        status=graphene.String(),
    )

    agent_summary = graphene.Field(
        AgentSummary,
        agent_id=graphene.String(required=True),
    )

    agent_summary_list = graphene.Field(
        AgentSummaryList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # filters
        scaling_group=graphene.String(),
        status=graphene.String(),
    )

    domain_node = graphene.Field(
        DomainNode,
        description="Added in 24.12.0.",
        id=GlobalIDField(required=True),
        permission=DomainPermissionValueField(
            required=False,
            default_value=DomainPermission.READ_ATTRIBUTE,
        ),
    )

    domain_nodes = PaginatedConnectionField(
        DomainConnection,
        description="Added in 24.12.0.",
        filter=graphene.String(),
        order=graphene.String(),
        permission=DomainPermissionValueField(
            required=False,
            default_value=DomainPermission.READ_ATTRIBUTE,
        ),
    )
    agent_nodes = PaginatedConnectionField(
        AgentConnection,
        description="Added in 24.12.0.",
        scope=ScopeField(
            description="Added in 24.12.0. Default is `system`.",
        ),
        permission=AgentPermissionField(
            default_value=AgentPermission.CREATE_COMPUTE_SESSION,
            description=f"Added in 24.12.0. Default is {AgentPermission.CREATE_COMPUTE_SESSION.value}.",
        ),
    )

    domain = graphene.Field(
        Domain,
        name=graphene.String(),
    )

    # super-admin only
    domains = graphene.List(
        Domain,
        is_active=graphene.Boolean(),
    )

    group_node = graphene.Field(
        GroupNode, id=graphene.String(required=True), description="Added in 24.03.0."
    )
    group_nodes = PaginatedConnectionField(
        GroupConnection,
        description="Added in 24.03.0.",
        filter=graphene.String(description="Added in 24.09.0."),
        order=graphene.String(description="Added in 24.09.0."),
        scope=ScopeField(
            description="Added in 25.3.0. Default is `system`.",
        ),
        container_registry_scope=ContainerRegistryScopeField(description="Added in 25.3.0."),
        permission=GroupPermissionField(
            default_value=ProjectPermission.READ_ATTRIBUTE,
            description=f"Added in 25.3.0. Default is {ProjectPermission.READ_ATTRIBUTE.value}.",
        ),
    )

    group = graphene.Field(
        Group,
        id=graphene.UUID(required=True),
        domain_name=graphene.String(),
        type=graphene.List(
            graphene.String,
            default_value=[ProjectType.GENERAL.name],
            description=("Added in 24.03.0."),
        ),
    )

    # Within a single domain, this will always return nothing or a single item,
    # but if queried across all domains by superadmins, it may return multiple results
    # because the group name is unique only inside each domain.
    groups_by_name = graphene.List(
        Group,
        name=graphene.String(required=True),
        domain_name=graphene.String(),
    )

    groups = graphene.List(
        Group,
        domain_name=graphene.String(),
        is_active=graphene.Boolean(),
        type=graphene.List(
            graphene.String,
            default_value=[ProjectType.GENERAL.name],
            description=(
                f"Added in 24.03.0. Available values: {', '.join([p.name for p in ProjectType])}"
            ),
        ),
    )

    image = graphene.Field(
        Image,
        id=graphene.String(description="Added in 24.03.1"),
        reference=graphene.String(),
        architecture=graphene.String(default_value=DEFAULT_IMAGE_ARCH),
    )

    images = graphene.List(
        Image,
        is_installed=graphene.Boolean(
            description="Added in 19.09.0. If it is specified, fetch images installed on at least one agent."
        ),
        is_operation=graphene.Boolean(
            deprecation_reason="Deprecated since 24.03.4. This field is ignored if `load_filters` is specified and is not null."
        ),
        filter_by_statuses=graphene.List(
            ImageStatusType,
            default_value=[ImageStatus.ALIVE],
            description="Added in 25.4.0.",
        ),
        load_filters=graphene.List(
            graphene.String,
            default_value=None,
            description=f"Added in 24.03.8. Allowed values are: [{', '.join([f.value for f in PublicImageLoadFilter])}]. When superuser queries with `customized` option set the resolver will return every customized images (including those not owned by callee). To resolve images owned by user only call `customized_images`.",
        ),
        image_filters=graphene.List(
            graphene.String,
            default_value=None,
            deprecation_reason="Deprecated since 24.03.8. Use `load_filters` instead.",
            description=f"Added in 24.03.4. Allowed values are: [{', '.join([f.value for f in PublicImageLoadFilter])}]. When superuser queries with `customized` option set the resolver will return every customized images (including those not owned by caller). To list the owned images only call `customized_images`.",
        ),
    )

    customized_images = graphene.List(ImageNode, description="Added in 24.03.1")

    image_node = graphene.Field(
        ImageNode,
        description="Added in 25.3.0.",
        id=GlobalIDField(required=True),
        scope_id=ScopeField(),
        permission=ImagePermissionValueField(
            default_value=ImagePermission.READ_ATTRIBUTE,
            description=f"Default is {ImagePermission.READ_ATTRIBUTE.value}.",
        ),
    )
    image_nodes = PaginatedConnectionField(
        ImageConnection,
        description="Added in 25.3.0.",
        scope_id=ScopeField(required=True),
        permission=ImagePermissionValueField(
            default_value=ImagePermission.READ_ATTRIBUTE,
            description=f"Default is {ImagePermission.READ_ATTRIBUTE.value}.",
        ),
        filter_by_statuses=graphene.List(
            ImageStatusType,
            default_value=[ImageStatus.ALIVE],
            description="Added in 25.4.0.",
        ),
    )

    viewer = graphene.Field(
        Viewer, description="Added in 25.14.2. Returns information about the current user."
    )

    user = graphene.Field(
        User,
        domain_name=graphene.String(),
        email=graphene.String(),
    )

    user_from_uuid = graphene.Field(
        User,
        domain_name=graphene.String(),
        user_id=graphene.ID(),
    )

    users = graphene.List(  # legacy non-paginated list
        User,
        domain_name=graphene.String(),
        group_id=graphene.UUID(),
        is_active=graphene.Boolean(),
        status=graphene.String(),
    )

    user_list = graphene.Field(
        UserList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # intrinsic filters
        domain_name=graphene.String(),
        group_id=graphene.UUID(),
        is_active=graphene.Boolean(),
        status=graphene.String(),
    )

    user_node = graphene.Field(
        UserNode, id=graphene.String(required=True), description="Added in 24.03.0."
    )
    user_nodes = PaginatedConnectionField(UserConnection, description="Added in 24.03.0.")

    keypair = graphene.Field(
        KeyPair,
        domain_name=graphene.String(),
        access_key=graphene.String(),
    )

    keypairs = graphene.List(  # legacy non-paginated list
        KeyPair,
        domain_name=graphene.String(),
        email=graphene.String(),
        is_active=graphene.Boolean(),
    )

    keypair_list = graphene.Field(
        KeyPairList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # intrinsic filters
        domain_name=graphene.String(),
        email=graphene.String(),
        is_active=graphene.Boolean(),
    )

    # NOTE: maybe add keypairs_from_user_id?

    keypair_resource_policy = graphene.Field(
        KeyPairResourcePolicy,
        name=graphene.String(),
    )
    user_resource_policy = graphene.Field(
        UserResourcePolicy,
        name=graphene.String(),
    )
    project_resource_policy = graphene.Field(
        ProjectResourcePolicy,
        name=graphene.String(required=True),
    )

    keypair_resource_policies = graphene.List(KeyPairResourcePolicy)
    user_resource_policies = graphene.List(UserResourcePolicy)
    project_resource_policies = graphene.List(ProjectResourcePolicy)

    resource_preset = graphene.Field(
        ResourcePreset,
        name=graphene.String(),
    )
    resource_preset_by_id = graphene.Field(
        ResourcePreset,
        description="Added in 25.4.0.",
        id=graphene.UUID(),
    )

    resource_presets = graphene.List(
        ResourcePreset,
        filter=graphene.String(
            description="Added in 25.4.0.",
        ),
        order=graphene.String(
            description="Added in 25.4.0.",
        ),
    )

    # super-admin only
    scaling_group = graphene.Field(
        ScalingGroup,
        name=graphene.String(),
    )

    # super-admin only
    scaling_groups = graphene.List(
        ScalingGroup,
        name=graphene.String(),
        is_active=graphene.Boolean(),
    )

    accessible_scaling_groups = graphene.List(
        ScalingGroup,
        description=(
            "Added in 25.5.0. This query is available for all users. "
            "It returns the resource groups(=scaling groups) that the user has access to. "
            "Only name, is_active, own_session_occupied_resource_slots and accelerator_quantum_size fields are returned."
        ),
        project_id=graphene.UUID(required=True),
    )

    # super-admin only
    scaling_groups_for_domain = graphene.List(
        ScalingGroup,
        domain=graphene.String(required=True),
        is_active=graphene.Boolean(),
    )

    # super-admin only
    scaling_groups_for_user_group = graphene.List(
        ScalingGroup,
        user_group=graphene.String(required=True),
        is_active=graphene.Boolean(),
    )

    # super-admin only
    scaling_groups_for_keypair = graphene.List(
        ScalingGroup,
        access_key=graphene.String(required=True),
        is_active=graphene.Boolean(),
    )

    # super-admin only
    storage_volume = graphene.Field(
        StorageVolume,
        id=graphene.String(),
    )

    # super-admin only
    storage_volume_list = graphene.Field(
        StorageVolumeList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
    )

    vfolder = graphene.Field(
        VirtualFolder,
        id=graphene.String(),
    )

    vfolder_node = graphene.Field(
        VirtualFolderNode, id=graphene.String(required=True), description="Added in 24.03.4."
    )
    vfolder_nodes = PaginatedConnectionField(
        VirtualFolderConnection,
        description="Added in 24.03.4.",
        scope_id=ScopeField(description="Added in 24.12.0."),
        project_id=graphene.UUID(
            required=False,
            description="Added in 24.09.0.",
            deprecation_reason="Deprecated since 24.12.0. use `scope_id` instead.",
        ),
        permission=VFolderPermissionValueField(description="Added in 24.09.0."),
    )

    vfolder_list = graphene.Field(  # legacy non-paginated list
        VirtualFolderList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # intrinsic filters
        domain_name=graphene.String(),
        group_id=graphene.UUID(),
        access_key=graphene.String(),  # must be empty for user requests
    )

    # super-admin only
    vfolder_permission_list = graphene.Field(
        VirtualFolderPermissionList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
    )

    vfolder_own_list = graphene.Field(
        VirtualFolderList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # intrinsic filters
        domain_name=graphene.String(),
        access_key=graphene.String(),  # must be empty for user requests
    )

    vfolder_invited_list = graphene.Field(
        VirtualFolderList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # intrinsic filters
        domain_name=graphene.String(),
        access_key=graphene.String(),  # must be empty for user requests
    )

    vfolder_project_list = graphene.Field(
        VirtualFolderList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # intrinsic filters
        domain_name=graphene.String(),
        access_key=graphene.String(),  # must be empty for user requests
    )

    vfolders = graphene.List(  # legacy non-paginated list
        VirtualFolder,
        domain_name=graphene.String(),
        group_id=graphene.String(),
        access_key=graphene.String(),  # must be empty for user requests
    )

    compute_session_node = graphene.Field(
        ComputeSessionNode,
        description="Added in 24.09.0.",
        id=GlobalIDField(required=True),
        scope_id=ScopeField(description="Added in 24.12.0."),
        project_id=graphene.UUID(
            required=False,
            description="Added in 24.09.0.",
            deprecation_reason="Deprecated since 24.12.0. use `scope_id` instead.",
        ),
        permission=SessionPermissionValueField(
            default_value=ComputeSessionPermission.READ_ATTRIBUTE,
            description=f"Added in 24.09.0. Default is {ComputeSessionPermission.READ_ATTRIBUTE.value}.",
        ),
    )

    compute_session_nodes = PaginatedConnectionField(
        ComputeSessionConnection,
        description="Added in 24.09.0.",
        scope_id=ScopeField(description="Added in 24.12.0."),
        project_id=graphene.UUID(
            required=False,
            description="Added in 24.09.0.",
            deprecation_reason="Deprecated since 24.12.0. use `scope_id` instead.",
        ),
        permission=SessionPermissionValueField(
            default_value=ComputeSessionPermission.READ_ATTRIBUTE,
            description=f"Added in 24.09.0. Default is {ComputeSessionPermission.READ_ATTRIBUTE.value}.",
        ),
    )

    session_pending_queue = AsyncListConnectionField(
        SessionPendingQueueConnection,
        description="Added in 25.13.0.",
        resource_group_id=graphene.String(required=True),
        offset=graphene.Int(
            description="Specifies how many items to skip before beginning to return result."
        ),
        before=graphene.String(
            description="If this value is provided, the query will be limited to that value."
        ),
        after=graphene.String(
            description="Queries the `last` number of results from the query result from last."
        ),
        first=graphene.Int(
            description="Queries the `first` number of results from the query result from first."
        ),
        last=graphene.Int(
            description="If the given value is provided, the query will start from that value."
        ),
    )

    compute_session = graphene.Field(
        ComputeSession,
        id=graphene.UUID(required=True),
    )

    compute_container = graphene.Field(
        ComputeContainer,
        id=graphene.UUID(required=True),
    )

    compute_session_list = graphene.Field(
        ComputeSessionList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # intrinsic filters
        domain_name=graphene.String(),
        group_id=graphene.String(),
        access_key=graphene.String(),
        status=graphene.String(),
    )

    compute_container_list = graphene.Field(
        ComputeContainerList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # intrinsic filters
        session_id=graphene.ID(required=True),
        role=graphene.String(),
    )

    legacy_compute_session_list = graphene.Field(
        LegacyComputeSessionList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        # legacy ordering
        order_key=graphene.String(),
        order_asc=graphene.Boolean(),
        # intrinsic filters
        domain_name=graphene.String(),
        group_id=graphene.String(),
        access_key=graphene.String(),
        status=graphene.String(),
    )

    legacy_compute_session = graphene.Field(
        LegacyComputeSession,
        sess_id=graphene.String(required=True),
        domain_name=graphene.String(),
        access_key=graphene.String(),
    )

    total_resource_slot = graphene.Field(
        TotalResourceSlot,
        description="Added in 25.5.0.",
        statuses=graphene.List(
            graphene.String,
            default_value=None,
            description=(
                "`statuses` argument is an array of session statuses. "
                "Only sessions with the specified statuses will be queried to calculate the sum of total resource slots. "
                f"The argument should be an array of the following valid status values: {[s.name for s in SessionStatus]}.\n"
                f"Default value is null."
            ),
        ),
        filter=graphene.String(
            description=(
                "`filter` argument is a string that is parsed into query conditions. "
                "It works in the same way as the `filter` argument in the `compute_session` query schema, "
                "meaning the values are parsed into an identical SQL query expression.\n"
                "Default value is `null`."
            ),
        ),
        domain_name=graphene.String(),
        resource_group_name=graphene.String(),
    )

    vfolder_host_permissions = graphene.Field(
        PredefinedAtomicPermission,
    )

    endpoint = graphene.Field(
        Endpoint,
        endpoint_id=graphene.UUID(required=True),
    )

    endpoint_list = graphene.Field(
        EndpointList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # filters
        domain_name=graphene.String(),
        group_id=graphene.String(),
        user_uuid=graphene.String(),
        project=graphene.UUID(),
    )

    routing = graphene.Field(
        Routing,
        routing_id=graphene.UUID(required=True),
    )

    routing_list = graphene.Field(
        RoutingList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # filters
        endpoint_id=graphene.UUID(),
    )

    endpoint_token = graphene.Field(
        EndpointToken,
        token=graphene.String(required=True),
    )

    endpoint_token_list = graphene.Field(
        EndpointTokenList,
        limit=graphene.Int(required=True),
        offset=graphene.Int(required=True),
        filter=graphene.String(),
        order=graphene.String(),
        # filters
        endpoint_id=graphene.UUID(),
    )

    quota_scope = graphene.Field(
        QuotaScope,
        storage_host_name=graphene.String(required=True),
        quota_scope_id=graphene.String(required=True),
    )

    container_registry = graphene.Field(
        ContainerRegistry,
        hostname=graphene.String(required=True),
        deprecation_reason="Deprecated since 24.9.0. use `container_registry_node` instead.",
    )

    container_registries = graphene.List(
        ContainerRegistry,
        deprecation_reason="Deprecated since 24.9.0. use `container_registry_nodes_v2` instead.",
    )

    container_registry_node = graphene.Field(
        ContainerRegistryNode,
        id=graphene.String(required=True),
        description="Added in 24.09.0.",
    )

    container_registry_nodes = PaginatedConnectionField(
        ContainerRegistryConnection,
        description="Added in 24.09.0.",
    )

    model_card = graphene.Field(
        ModelCard, id=graphene.String(required=True), description="Added in 24.03.0."
    )
    model_cards = PaginatedConnectionField(ModelCardConnection, description="Added in 24.03.0.")

    network = graphene.Field(
        NetworkNode, id=graphene.String(required=True), description="Added in 24.12.0."
    )
    networks = PaginatedConnectionField(NetworkConnection, description="Added in 24.12.0.")

    endpoint_auto_scaling_rule_node = graphene.Field(
        EndpointAutoScalingRuleNode,
        id=graphene.String(required=True),
        description="Added in 25.1.0.",
    )

    endpoint_auto_scaling_rule_nodes = PaginatedConnectionField(
        EndpointAutoScalingRuleConnection,
        endpoint=graphene.String(required=True),
        description="Added in 25.1.0.",
    )

    user_utilization_metric = graphene.Field(
        UserUtilizationMetric,
        description="Added in 25.6.0.",
        user_id=graphene.UUID(required=True),
        props=UserUtilizationMetricQueryInput(required=True),
    )
    container_utilization_metric_metadata = graphene.Field(
        ContainerUtilizationMetricMetadata,
        description="Added in 25.6.0.",
    )

    available_service = graphene.Field(
        AvailableServiceNode,
        description="Added in 25.8.0.",
    )
    available_services = PaginatedConnectionField(
        AvailableServiceConnection,
        description="Added in 25.8.0.",
    )
    service_config = graphene.Field(
        ServiceConfigNode,
        service=graphene.String(required=True),
        description="Added in 25.8.0.",
    )
    service_configs = PaginatedConnectionField(
        ServiceConfigConnection,
        services=graphene.List(graphene.String, required=True),
        description="Added in 25.8.0.",
    )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_agent(
        root: Any,
        info: graphene.ResolveInfo,
        agent_id: AgentId,
    ) -> Agent:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader_by_func(
            ctx,
            Agent.batch_load,
            raw_status=None,
        )
        return await loader.load(agent_id)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_agents(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        scaling_group: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Sequence[Agent]:
        return await Agent.load_all(
            info.context,
            scaling_group=scaling_group,
            raw_status=status,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_agent_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        scaling_group: Optional[str] = None,
        status: Optional[str] = None,
    ) -> AgentList:
        total_count = await Agent.load_count(
            info.context,
            scaling_group=scaling_group,
            raw_status=status,
            filter=filter,
        )
        agent_list = await Agent.load_slice(
            info.context,
            limit,
            offset,
            scaling_group=scaling_group,
            raw_status=status,
            filter=filter,
            order=order,
        )
        return AgentList(agent_list, total_count)

    @staticmethod
    @scoped_query(autofill_user=True, user_key="access_key")
    async def resolve_agent_summary(
        root: Any,
        info: graphene.ResolveInfo,
        agent_id: AgentId,
        *,
        access_key: AccessKey,
        domain_name: str | None = None,
        scaling_group: str | None = None,
    ) -> AgentSummary:
        ctx: GraphQueryContext = info.context
        if ctx.config_provider.config.manager.hide_agents:
            raise ObjectNotFound(object_name="agent")

        loader = ctx.dataloader_manager.get_loader_by_func(
            ctx,
            AgentSummary.batch_load,
            raw_status=None,
            scaling_group=scaling_group,
            domain_name=domain_name,
            access_key=access_key,
        )
        return await loader.load(agent_id)

    @staticmethod
    @scoped_query(autofill_user=True, user_key="access_key")
    async def resolve_agent_summary_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        access_key: AccessKey,
        domain_name: str | None = None,
        filter: str | None = None,
        order: str | None = None,
        scaling_group: str | None = None,
        status: str | None = None,
    ) -> AgentSummaryList:
        ctx: GraphQueryContext = info.context
        if ctx.config_provider.config.manager.hide_agents:
            raise ObjectNotFound(object_name="agent")

        total_count = await AgentSummary.load_count(
            ctx,
            access_key=access_key,
            scaling_group=scaling_group,
            domain_name=domain_name,
            raw_status=status,
            filter=filter,
        )
        agent_list = await AgentSummary.load_slice(
            ctx,
            limit,
            offset,
            access_key=access_key,
            scaling_group=scaling_group,
            domain_name=domain_name,
            raw_status=status,
            filter=filter,
            order=order,
        )
        return AgentSummaryList(agent_list, total_count)

    @staticmethod
    async def resolve_domain_node(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        id: str,
        permission: DomainPermission,
    ) -> Optional[DomainNode]:
        return await DomainNode.get_node(info, id, permission)

    @staticmethod
    async def resolve_domain_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        permission: DomainPermission,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[DomainNode]:
        return await DomainNode.get_connection(
            info,
            SystemScope(),
            permission,
            filter_expr=filter,
            order_expr=order,
            after=after,
            first=first,
            before=before,
            last=last,
        )

    async def resolve_agent_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        scope: Optional[ScopeType] = None,
        permission: AgentPermission = AgentPermission.CREATE_COMPUTE_SESSION,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult:
        _scope = scope if scope is not None else SystemScope()
        return await AgentNode.get_connection(
            info,
            _scope,
            permission,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    async def resolve_domain(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        name: Optional[str] = None,
    ) -> Domain:
        ctx: GraphQueryContext = info.context
        name = ctx.user["domain_name"] if name is None else name
        if ctx.user["role"] != UserRole.SUPERADMIN:
            if name != ctx.user["domain_name"]:
                # prevent querying other domains if not superadmin
                raise ObjectNotFound(object_name="domain")
        loader = ctx.dataloader_manager.get_loader(ctx, "Domain.by_name")
        return await loader.load(name)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_domains(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        is_active: Optional[bool] = None,
    ) -> Sequence[Domain]:
        return await Domain.load_all(info.context, is_active=is_active)

    @staticmethod
    async def resolve_group_node(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ):
        return await GroupNode.get_node(info, id)

    @staticmethod
    async def resolve_group_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        scope: Optional[ScopeType] = None,
        container_registry_scope: Optional[ContainerRegistryScope] = None,
        permission: ProjectPermission = ProjectPermission.READ_ATTRIBUTE,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[GroupNode]:
        _scope = scope or SystemScope()
        return await GroupNode.get_connection(
            info,
            _scope,
            container_registry_scope,
            permission,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    async def resolve_vfolder_node(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ):
        return await VirtualFolderNode.get_node(info, id)

    @staticmethod
    async def resolve_vfolder_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        scope_id: Optional[ScopeType] = None,
        project_id: Optional[uuid.UUID] = None,
        permission: VFolderRBACPermission,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[VirtualFolderNode]:
        _scope_id: ScopeType
        if project_id is not None:
            # for backward compatibility.
            # TODO: remove this part after `project_id` argument is fully deprecated
            _scope_id = ProjectScope(project_id)
        else:
            if scope_id is None:
                _scope_id = SystemScope()
            else:
                _scope_id = scope_id
        return await VirtualFolderNode.get_accessible_connection(
            info,
            _scope_id,
            permission,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    async def resolve_group(
        root: Any,
        info: graphene.ResolveInfo,
        id: uuid.UUID,
        *,
        domain_name: str | None = None,
        type: list[str] = [ProjectType.GENERAL.name],
    ) -> Group:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        client_user_id = ctx.user["uuid"]
        if client_role == UserRole.SUPERADMIN:
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_id",
                domain_name=domain_name,
            )
            group = await loader.load(id)
        elif client_role == UserRole.ADMIN:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_id",
                domain_name=client_domain,
            )
            group = await loader.load(id)
        elif client_role == UserRole.USER:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_id",
                domain_name=client_domain,
            )
            group = await loader.load(id)
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_user",
            )
            client_groups = [
                group for group in await loader.load(client_user_id) if group.type in type
            ]
            if group.id not in (g.id for g in client_groups):
                raise InsufficientPrivilege
        else:
            raise InvalidAPIParameters("Unknown client role")
        return group

    @staticmethod
    async def resolve_groups_by_name(
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
        *,
        domain_name: Optional[str] = None,
    ) -> Sequence[Group]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        client_user_id = ctx.user["uuid"]
        if client_role == UserRole.SUPERADMIN:
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_name",
                domain_name=domain_name,
            )
            groups = await loader.load(name)
        elif client_role == UserRole.ADMIN:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_name",
                domain_name=client_domain,
            )
            groups = await loader.load(name)
        elif client_role == UserRole.USER:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_name",
                domain_name=client_domain,
            )
            groups = await loader.load(name)
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_user",
            )
            client_groups = await loader.load(client_user_id)
            client_group_ids = set(g.id for g in client_groups)
            groups = filter(lambda g: g.id in client_group_ids, groups)
        else:
            raise InvalidAPIParameters("Unknown client role")
        return groups

    @staticmethod
    async def resolve_groups(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        type: list[str] = [ProjectType.GENERAL.name],
    ) -> Sequence[Group]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        client_user_id = ctx.user["uuid"]
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role == UserRole.ADMIN:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            domain_name = client_domain
        elif client_role == UserRole.USER:
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "Group.by_user",
                is_active=is_active,
            )
            return await loader.load(client_user_id)
        else:
            raise InvalidAPIParameters("Unknown client role")
        return await Group.load_all(
            info.context,
            domain_name=domain_name,
            is_active=is_active,
            type=[ProjectType(t) for t in type],
        )

    @staticmethod
    async def resolve_image(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        id: str | None = None,
        reference: str | None = None,
        architecture: str | None = None,
    ) -> Image:
        """Loads image information by its ID or reference information. Either ID or reference/architecture pair must be provided."""
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        if id:
            item = await Image.load_item_by_id(info.context, uuid.UUID(id), filter_by_statuses=None)
        else:
            if not (reference and architecture):
                raise InvalidAPIParameters(
                    "reference/architecture and id can't be omitted at the same time!"
                )
            item = await Image.load_item(
                info.context, reference, architecture, filter_by_statuses=None
            )
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role in (UserRole.ADMIN, UserRole.USER):
            items = await Image.filter_allowed(info.context, [item], client_domain)
            if not items:
                raise ImageNotFound
            item = items[0]
        else:
            raise InvalidAPIParameters("Unknown client role")
        return item

    @staticmethod
    async def resolve_customized_images(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> Sequence[ImageNode]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        items = await Image.load_all(
            ctx,
            types=set((ImageLoadFilter.CUSTOMIZED,)),
        )
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role in (UserRole.ADMIN, UserRole.USER):
            items = await Image.filter_allowed(
                info.context,
                items,
                client_domain,
            )
        else:
            raise InvalidAPIParameters("Unknown client role")
        return [
            ImageNode.from_legacy_image(i)
            for i in items
            # access scope to each customized image has already been
            # evaluated at Image.load_all()
            if "ai.backend.customized-image.owner" in i.raw_labels
        ]

    @staticmethod
    async def resolve_images(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        is_installed: bool | None = None,
        is_operation=False,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        load_filters: list[str] | None = None,
        image_filters: list[str] | None = None,
    ) -> Sequence[Image]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        image_load_types: set[ImageLoadFilter] = set()
        _types = load_filters or image_filters
        if _types is not None:
            try:
                _filters: list[PublicImageLoadFilter] = [PublicImageLoadFilter(f) for f in _types]
            except ValueError as e:
                allowed_filter_values = ", ".join([f.value for f in PublicImageLoadFilter])
                raise InvalidAPIParameters(
                    f"{e}. All elements of `load_filters` should be one of ({allowed_filter_values})"
                )
            image_load_types.update([ImageLoadFilter(f) for f in _filters])
            if (
                client_role == UserRole.SUPERADMIN
                and ImageLoadFilter.CUSTOMIZED in image_load_types
            ):
                image_load_types.remove(ImageLoadFilter.CUSTOMIZED)
                image_load_types.add(ImageLoadFilter.CUSTOMIZED_GLOBAL)
        else:
            image_load_types.add(ImageLoadFilter.CUSTOMIZED)
            image_load_types.add(ImageLoadFilter.GENERAL)
            if is_operation is None:
                # I know this logic is quite contradicts to the parameter name,
                # but to conform with previous implementation...
                image_load_types.add(ImageLoadFilter.OPERATIONAL)

        items = await Image.load_all(
            ctx, types=image_load_types, filter_by_statuses=filter_by_statuses
        )
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role in (UserRole.ADMIN, UserRole.USER):
            items = await Image.filter_allowed(
                info.context,
                items,
                client_domain,
            )
        else:
            raise InvalidAPIParameters("Unknown client role")
        if is_installed is not None:
            items = [item for item in items if item.installed == is_installed]
        return items

    @staticmethod
    async def resolve_viewer(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> Optional[Viewer]:
        viewer = await Viewer.get_viewer(info)
        return viewer

    @staticmethod
    @scoped_query(autofill_user=True, user_key="email")
    async def resolve_user(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> User:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            "User.by_email",
            domain_name=domain_name,
        )
        return await loader.load(email)

    @staticmethod
    @scoped_query(autofill_user=True, user_key="user_id")
    async def resolve_user_from_uuid(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: Optional[str] = None,
        user_id: uuid.UUID | str | None = None,
    ) -> User:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            "User.by_uuid",
            domain_name=domain_name,
        )
        # user_id is retrieved as string since it's a GraphQL's generic ID field
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        return await loader.load(user_uuid)

    @staticmethod
    async def resolve_users(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        status: Optional[UserStatus] = None,
    ) -> Sequence[User]:
        from .user import UserRole

        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role == UserRole.ADMIN:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            domain_name = client_domain
        elif client_role == UserRole.USER:
            # Users cannot query other users.
            raise InsufficientPrivilege()
        else:
            raise InvalidAPIParameters("Unknown client role")
        return await User.load_all(
            info.context,
            domain_name=domain_name,
            group_id=group_id,
            is_active=is_active,
            status=status,
            limit=100,
        )

    @staticmethod
    async def resolve_user_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        status: Optional[UserStatus] = None,
    ) -> UserList:
        from .user import UserRole

        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role == UserRole.ADMIN:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            domain_name = client_domain
        elif client_role == UserRole.USER:
            # Users cannot query other users.
            raise InsufficientPrivilege()
        else:
            raise InvalidAPIParameters("Unknown client role")
        total_count = await User.load_count(
            info.context,
            domain_name=domain_name,
            group_id=group_id,
            is_active=is_active,
            status=status,
            filter=filter,
        )
        user_list = await User.load_slice(
            info.context,
            limit,
            offset,
            domain_name=domain_name,
            group_id=group_id,
            is_active=is_active,
            status=status,
            filter=filter,
            order=order,
        )
        return UserList(user_list, total_count)

    @staticmethod
    async def resolve_user_node(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ):
        return await UserNode.get_node(info, id)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_user_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult[UserNode]:
        return await UserNode.get_connection(
            info,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    async def resolve_image_node(
        root: Any,
        info: graphene.ResolveInfo,
        id: ResolvedGlobalID,
        scope_id: Optional[ScopeType] = None,
        permission: ImagePermission = ImagePermission.READ_ATTRIBUTE,
    ) -> Optional[ImageNode]:
        if scope_id is None:
            scope_id = SystemScope()
        return await ImageNode.get_node(info, id, scope_id, permission)

    @staticmethod
    async def resolve_image_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        scope_id: ScopeType,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        permission: ImagePermission = ImagePermission.READ_ATTRIBUTE,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[ImageNode]:
        return await ImageNode.get_connection(
            info,
            scope_id,
            permission,
            filter_by_statuses,
            filter_expr=filter,
            order_expr=order,
            offset=offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )

    @staticmethod
    @scoped_query(autofill_user=True, user_key="access_key")
    async def resolve_keypair(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: Optional[str] = None,
        access_key: Optional[AccessKey] = None,
    ) -> KeyPair:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            "KeyPair.by_ak",
            domain_name=domain_name,
        )
        return await loader.load(access_key)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="email")
    async def resolve_keypairs(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[KeyPair]:
        ctx: GraphQueryContext = info.context
        if email is None:
            return await KeyPair.load_all(
                info.context,
                domain_name=domain_name,
                is_active=is_active,
                limit=100,
            )
        else:
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "KeyPair.by_email",
                domain_name=domain_name,
                is_active=is_active,
            )
            return await loader.load(email)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="email")
    async def resolve_keypair_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        domain_name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> KeyPairList:
        total_count = await KeyPair.load_count(
            info.context,
            domain_name=domain_name,
            email=email,
            is_active=is_active,
            filter=filter,
        )
        keypair_list = await KeyPair.load_slice(
            info.context,
            limit,
            offset,
            domain_name=domain_name,
            email=email,
            is_active=is_active,
            filter=filter,
            order=order,
        )
        return KeyPairList(keypair_list, total_count)

    @staticmethod
    async def resolve_keypair_resource_policy(
        root: Any,
        info: graphene.ResolveInfo,
        name: Optional[str] = None,
    ) -> KeyPairResourcePolicy:
        ctx: GraphQueryContext = info.context
        client_access_key = ctx.access_key
        if name is None:
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "KeyPairResourcePolicy.by_ak",
            )
            return await loader.load(client_access_key)
        else:
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "KeyPairResourcePolicy.by_name",
            )
            return await loader.load(name)

    @staticmethod
    async def resolve_keypair_resource_policies(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> Sequence[KeyPairResourcePolicy]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_access_key = ctx.access_key
        if client_role == UserRole.SUPERADMIN:
            return await KeyPairResourcePolicy.load_all(info.context)
        elif client_role == UserRole.ADMIN:
            # TODO: filter resource policies by domains?
            return await KeyPairResourcePolicy.load_all(info.context)
        elif client_role == UserRole.USER:
            return await KeyPairResourcePolicy.load_all_user(
                info.context,
                client_access_key,
            )
        else:
            raise InvalidAPIParameters("Unknown client role")

    @staticmethod
    async def resolve_user_resource_policy(
        root: Any,
        info: graphene.ResolveInfo,
        name: Optional[str] = None,
    ) -> UserResourcePolicy:
        ctx: GraphQueryContext = info.context
        user_uuid = ctx.user["uuid"]
        if name is None:
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "UserResourcePolicy.by_user",
            )
            return await loader.load(user_uuid)
        else:
            loader = ctx.dataloader_manager.get_loader(
                ctx,
                "UserResourcePolicy.by_name",
            )
            return await loader.load(name)

    @staticmethod
    async def resolve_user_resource_policies(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> Sequence[UserResourcePolicy]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        user_uuid = ctx.user["uuid"]
        if client_role == UserRole.SUPERADMIN:
            return await UserResourcePolicy.load_all(info.context)
        elif client_role == UserRole.ADMIN:
            # TODO: filter resource policies by domains?
            return await UserResourcePolicy.load_all(info.context)
        elif client_role == UserRole.USER:
            return await UserResourcePolicy.batch_load_by_user(
                info.context,
                [user_uuid],
            )
        else:
            raise InvalidAPIParameters("Unknown client role")

    @staticmethod
    async def resolve_project_resource_policy(
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
    ) -> ProjectResourcePolicy:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            "ProjectResourcePolicy.by_name",
        )
        return await loader.load(name)

    @staticmethod
    async def resolve_project_resource_policies(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> Sequence[ProjectResourcePolicy]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        if client_role == UserRole.SUPERADMIN:
            return await ProjectResourcePolicy.load_all(info.context)
        elif client_role == UserRole.ADMIN:
            # TODO: filter resource policies by domains?
            return await ProjectResourcePolicy.load_all(info.context)
        else:
            raise InvalidAPIParameters("Unknown client role")

    @staticmethod
    async def resolve_resource_preset(
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
    ) -> ResourcePreset:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "ResourcePreset.by_name")
        return await loader.load(name)

    @staticmethod
    async def resolve_resource_preset_by_id(
        root: Any,
        info: graphene.ResolveInfo,
        id: uuid.UUID,
    ) -> ResourcePreset:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "ResourcePreset.by_id")
        return await loader.load(id)

    @staticmethod
    async def resolve_resource_presets(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[ResourcePreset]:
        return await ResourcePreset.load_all(info.context, filter=filter, order=order)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_group(
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
    ) -> ScalingGroup:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            "ScalingGroup.by_name",
        )
        return await loader.load(name)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups(
        root: Any,
        info: graphene.ResolveInfo,
        is_active: Optional[bool] = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_all(info.context, is_active=is_active)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_accessible_scaling_groups(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: Optional[str],
        project_id: uuid.UUID,
        group_id: uuid.UUID,  # Not used. `scoped_query()` injects this parameter.
        access_key: AccessKey,
    ) -> Sequence[ScalingGroup]:
        ctx: GraphQueryContext = info.context
        domain_name = domain_name or ctx.user["domain_name"]
        async with ctx.db.begin() as db_conn:
            sgroup_rows = await query_allowed_sgroups(db_conn, domain_name, project_id, access_key)
        conditions = [and_names([sgroup.name for sgroup in sgroup_rows])]
        sgroup_rows = await ScalingGroupRow.list_by_condition(conditions, db=ctx.db)
        return [ScalingGroup.from_orm_row(row).masked for row in sgroup_rows]

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups_for_domain(
        root: Any,
        info: graphene.ResolveInfo,
        domain: str,
        is_active: Optional[bool] = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_by_domain(
            info.context,
            domain,
            is_active=is_active,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups_for_user_group(
        root: Any,
        info: graphene.ResolveInfo,
        user_group,
        is_active: Optional[bool] = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_by_group(
            info.context,
            user_group,
            is_active=is_active,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups_for_keypair(
        root: Any,
        info: graphene.ResolveInfo,
        access_key: AccessKey,
        is_active: Optional[bool] = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_by_keypair(
            info.context,
            access_key,
            is_active=is_active,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_storage_volume(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ) -> StorageVolume:
        return await StorageVolume.load_by_id(info.context, id)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_storage_volume_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> StorageVolumeList:
        total_count = await StorageVolume.load_count(
            info.context,
            filter=filter,
        )
        items = await StorageVolume.load_slice(
            info.context,
            limit,
            offset,
            filter=filter,
            order=order,
        )
        return StorageVolumeList(items, total_count)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_vfolder(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[VirtualFolder]:
        graph_ctx: GraphQueryContext = info.context
        vfolder_id = uuid.UUID(id)
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "VirtualFolder.by_id",
            domain_name=domain_name,
            group_id=group_id,
            user_id=user_id,
            filter=None,
        )
        return await loader.load(vfolder_id)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_id")
    async def resolve_vfolder_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> VirtualFolderList:
        # TODO: adopt the generic queryfilter language
        total_count = await VirtualFolder.load_count(
            info.context,
            domain_name=domain_name,  # scope
            group_id=group_id,  # scope
            user_id=user_id,  # scope
            filter=filter,
        )
        items = await VirtualFolder.load_slice(
            info.context,
            limit,
            offset,
            domain_name=domain_name,  # scope
            group_id=group_id,  # scope
            user_id=user_id,  # scope
            filter=filter,
            order=order,
        )
        return VirtualFolderList(items, total_count)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_vfolder_permission_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> VirtualFolderPermissionList:
        total_count = await VirtualFolderPermission.load_count(
            info.context,
            user_id=user_id,
            filter=filter,
        )
        items = await VirtualFolderPermission.load_slice(
            info.context,
            limit,
            offset,
            user_id=user_id,
            filter=filter,
            order=order,
        )
        return VirtualFolderPermissionList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_id")
    async def resolve_vfolder_own_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> VirtualFolderList:
        total_count = await VirtualFolder.load_count(
            info.context,
            domain_name=domain_name,  # scope
            user_id=info.context.user["uuid"],  # scope
            filter=filter,
        )
        items = await VirtualFolder.load_slice(
            info.context,
            limit,
            offset,
            domain_name=domain_name,  # scopes
            user_id=info.context.user["uuid"],  # scope
            filter=filter,
            order=order,
        )
        return VirtualFolderList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_id")
    async def resolve_vfolder_invited_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,  # not used, fixed
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> VirtualFolderList:
        total_count = await VirtualFolder.load_count_invited(
            info.context,
            domain_name=domain_name,  # scope
            user_id=info.context.user["uuid"],  # scope
            filter=filter,
        )
        items = await VirtualFolder.load_slice_invited(
            info.context,
            limit,
            offset,
            domain_name=domain_name,  # scopes
            user_id=info.context.user["uuid"],  # scope
            filter=filter,
            order=order,
        )
        return VirtualFolderList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_id")
    async def resolve_vfolder_project_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,  # not used, fixed
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> VirtualFolderList:
        total_count = await VirtualFolder.load_count_project(
            info.context,
            domain_name=domain_name,  # scope
            user_id=info.context.user["uuid"],  # scope
            filter=filter,
        )
        items = await VirtualFolder.load_slice_project(
            info.context,
            limit,
            offset,
            domain_name=domain_name,  # scopes
            user_id=info.context.user["uuid"],  # scope
            filter=filter,
            order=order,
        )
        return VirtualFolderList(items, total_count)

    @staticmethod
    async def resolve_compute_session_node(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        id: ResolvedGlobalID,
        scope_id: Optional[ScopeType] = None,
        project_id: Optional[uuid.UUID] = None,
        permission: ComputeSessionPermission = ComputeSessionPermission.READ_ATTRIBUTE,
    ) -> Optional[ComputeSessionNode]:
        if scope_id is None:
            scope_id = SystemScope()
        return await ComputeSessionNode.get_accessible_node(info, id, scope_id, permission)

    @staticmethod
    async def resolve_compute_session_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        scope_id: Optional[ScopeType] = None,
        project_id: Optional[uuid.UUID] = None,
        permission: ComputeSessionPermission = ComputeSessionPermission.READ_ATTRIBUTE,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[ComputeSessionNode]:
        final_scope_id: ScopeType
        if project_id is not None:
            # for backward compatibility.
            # TODO: remove this part after `project_id` argument is fully deprecated
            final_scope_id = ProjectScope(project_id)
        else:
            if scope_id is None:
                final_scope_id = SystemScope()
            else:
                final_scope_id = scope_id
        return await ComputeSessionNode.get_accessible_connection(
            info,
            final_scope_id,
            permission,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    async def resolve_session_pending_queue(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        resource_group_id: str,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[ComputeSessionNode]:
        # TODO: Clean up this function
        graph_ctx: GraphQueryContext = info.context
        pending_sessions = await graph_ctx.valkey_schedule.get_pending_queue(resource_group_id)
        session_order = {sid: idx for idx, sid in enumerate(pending_sessions)}
        result: list[ComputeSessionNode] = []
        async with graph_ctx.db.begin_readonly_session() as db_session:
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.id.in_(pending_sessions))
                .options(selectinload(SessionRow.kernels), joinedload(SessionRow.user))
            )
            query_result = await db_session.scalars(stmt)
            for row in query_result:
                node = ComputeSessionNode.from_row(graph_ctx, row)
                result.append(node)
        result.sort(key=lambda node: session_order[SessionId(node.row_id)])
        total_count = len(result)
        page_size: Optional[int] = None
        cursor: Optional[str] = None
        if offset is not None:
            result = result[offset:]
        if after is not None:
            _, raw_session_id = AsyncNode.resolve_global_id(info, after)
            target_id = uuid.UUID(raw_session_id)
            idx = 0
            for idx, session_node in enumerate(result):
                if session_node.id == target_id:
                    cursor = after
                    break
            result = result[idx + 1 :]
        if first is not None:
            result = result[:first]
            page_size = first
        if before is not None:
            _, raw_session_id = AsyncNode.resolve_global_id(info, before)
            target_id = uuid.UUID(raw_session_id)
            idx = len(result)
            for idx, session_node in enumerate(result):
                if session_node.id == target_id:
                    cursor = before
                    break
            result = result[:idx]
        if last is not None:
            result = result[-last:]
            page_size = last
        return ConnectionResolverResult(
            result,
            cursor,
            None,
            page_size,
            total_count,
        )

    @staticmethod
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_compute_container_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        session_id: SessionId,
        role: Optional[UserRole] = None,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[AccessKey] = None,
    ) -> ComputeContainerList:
        # TODO: adopt the generic queryfilter language
        total_count = await ComputeContainer.load_count(
            info.context,
            session_id,  # filter (mandatory)
            cluster_role=role,  # filter
            domain_name=domain_name,  # scope
            group_id=group_id,  # scope
            access_key=access_key,  # scope
            filter=filter,
        )
        items = await ComputeContainer.load_slice(
            info.context,
            limit,
            offset,  # slice
            session_id,  # filter (mandatory)
            cluster_role=role,  # filter
            domain_name=domain_name,  # scope
            group_id=group_id,  # scope
            access_key=access_key,  # scope
            filter=filter,
            order=order,
        )
        return ComputeContainerList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_compute_container(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
        *,
        domain_name: str | None = None,
        access_key: AccessKey | None = None,
    ) -> ComputeContainer:
        # We need to check the group membership of the designated kernel,
        # but practically a user cannot guess the IDs of kernels launched
        # by other users and in other groups.
        # Let's just protect the domain/user boundary here.
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "ComputeContainer.detail",
            domain_name=domain_name,
            access_key=access_key,
        )
        return await loader.load(id)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_compute_session_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[AccessKey] = None,
        status: Optional[str] = None,
    ) -> ComputeSessionList:
        total_count = await ComputeSession.load_count(
            info.context,
            status=status,  # filter
            domain_name=domain_name,  # scope
            group_id=group_id,  # scope
            access_key=access_key,  # scope
            filter=filter,
        )
        items = await ComputeSession.load_slice(
            info.context,
            limit,
            offset,  # slice
            status=status,  # filter
            domain_name=domain_name,  # scope
            group_id=group_id,  # scope
            access_key=access_key,  # scope
            filter=filter,
            order=order,
        )
        return ComputeSessionList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_compute_session(
        root: Any,
        info: graphene.ResolveInfo,
        id: SessionId,
        *,
        domain_name: Optional[str] = None,
        access_key: Optional[AccessKey] = None,
    ) -> ComputeSession:
        # We need to check the group membership of the designated kernel,
        # but practically a user cannot guess the IDs of kernels launched
        # by other users and in other groups.
        # Let's just protect the domain/user boundary here.
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "ComputeSession.detail",
            domain_name=domain_name,
            access_key=access_key,
        )
        return await loader.load(id)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_legacy_compute_session_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[AccessKey] = None,
        status: Optional[str] = None,
        order_key: Optional[str] = None,
        order_asc: bool = True,
    ) -> LegacyComputeSessionList:
        total_count = await LegacyComputeSession.load_count(
            info.context,
            domain_name=domain_name,
            group_id=group_id,
            access_key=access_key,
            status=status,
        )
        items = await LegacyComputeSession.load_slice(
            info.context,
            limit,
            offset,
            domain_name=domain_name,
            group_id=group_id,
            access_key=access_key,
            status=status,
            order_key=order_key,
            order_asc=order_asc,
        )
        return LegacyComputeSessionList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_legacy_compute_session(
        root: Any,
        info: graphene.ResolveInfo,
        sess_id: str,
        *,
        domain_name: Optional[str] = None,
        access_key: Optional[AccessKey] = None,
        status: Optional[str] = None,
    ) -> Optional[LegacyComputeSession]:
        # We need to check the group membership of the designated kernel,
        # but practically a user cannot guess the IDs of kernels launched
        # by other users and in other groups.
        # Let's just protect the domain/user boundary here.
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "LegacyComputeSession.detail",
            domain_name=domain_name,
            access_key=access_key,
            status=status,
        )

        # Since sess_id is declared as a string type, we have to convert this to UUID type manually.
        matches = await loader.load(SessionId(uuid.UUID(sess_id)))
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            raise TooManyKernelsFound

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_total_resource_slot(
        root: Any,
        info: graphene.ResolveInfo,
        statuses: Optional[list[str]] = None,
        filter: Optional[str] = None,
        domain_name: Optional[str] = None,
        resource_group_name: Optional[str] = None,
    ) -> TotalResourceSlot:
        graph_ctx: GraphQueryContext = info.context

        return await TotalResourceSlot.get_data(
            graph_ctx,
            statuses=statuses,
            domain_name=domain_name,
            resource_group_name=resource_group_name,
            raw_filter=filter,
        )

    @staticmethod
    async def resolve_vfolder_host_permissions(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> PredefinedAtomicPermission:
        graph_ctx: GraphQueryContext = info.context
        return await PredefinedAtomicPermission.load_all(graph_ctx)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_uuid")
    async def resolve_endpoint(
        root: Any,
        info: graphene.ResolveInfo,
        endpoint_id: uuid.UUID,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> Endpoint:
        graph_ctx: GraphQueryContext = info.context
        return await Endpoint.load_item(
            graph_ctx,
            endpoint_id=endpoint_id,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
        )

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_uuid")
    async def resolve_endpoint_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> EndpointList:
        total_count = await Endpoint.load_count(
            info.context,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
            filter=filter,
        )
        endpoint_list = await Endpoint.load_slice(
            info.context,
            limit,
            offset,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
            filter=filter,
            order=order,
        )
        return EndpointList(endpoint_list, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_uuid")
    async def resolve_routing(
        root: Any,
        info: graphene.ResolveInfo,
        routing_id: uuid.UUID,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> Routing:
        graph_ctx: GraphQueryContext = info.context
        return await Routing.load_item(
            graph_ctx,
            routing_id=routing_id,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
        )

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_uuid")
    async def resolve_routing_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        endpoint_id: Optional[uuid.UUID] = None,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> RoutingList:
        total_count = await Routing.load_count(
            info.context,
            endpoint_id=endpoint_id,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
        )
        routing_list = await Routing.load_slice(
            info.context,
            limit,
            offset,
            endpoint_id=endpoint_id,
            filter=filter,
            order=order,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
        )
        return RoutingList(routing_list, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_uuid")
    async def resolve_endpoint_token(
        root: Any,
        info: graphene.ResolveInfo,
        token: str,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> EndpointToken:
        graph_ctx: GraphQueryContext = info.context
        return await EndpointToken.load_item(
            graph_ctx,
            token,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
        )

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_uuid")
    async def resolve_endpoint_token_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        endpoint_id: Optional[uuid.UUID] = None,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> EndpointTokenList:
        total_count = await EndpointToken.load_count(
            info.context,
            endpoint_id=endpoint_id,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
        )
        token_list = await EndpointToken.load_slice(
            info.context,
            limit,
            offset,
            endpoint_id=endpoint_id,
            filter=filter,
            order=order,
            project=project,
            domain_name=domain_name,
            user_uuid=user_uuid,
        )
        return EndpointTokenList(token_list, total_count)

    @staticmethod
    async def resolve_quota_scope(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        quota_scope_id: Optional[str] = None,
        storage_host_name: Optional[str] = None,
    ) -> QuotaScope:
        if not quota_scope_id or not storage_host_name:
            raise ValueError("Either quota_scope_id and storage_host_name has to be defined")
        graph_ctx: GraphQueryContext = info.context
        qsid = QuotaScopeID.parse(quota_scope_id)
        volumes_by_host = await graph_ctx.storage_manager.get_all_volumes()
        for host, volume in volumes_by_host:
            if f"{host}:{volume['name']}" == storage_host_name:
                break
        else:
            raise ValueError(f"storage volume {storage_host_name} does not exist")
        async with graph_ctx.db.begin_readonly_session() as sess:
            await ensure_quota_scope_accessible_by_user(sess, qsid, graph_ctx.user)
            return QuotaScope(
                quota_scope_id=quota_scope_id,
                storage_host_name=storage_host_name,
            )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_container_registry(
        root: Any,
        info: graphene.ResolveInfo,
        hostname: str,
    ) -> ContainerRegistry:
        ctx: GraphQueryContext = info.context
        return await ContainerRegistry.load_by_hostname(ctx, hostname)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_container_registries(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> Sequence[ContainerRegistry]:
        ctx: GraphQueryContext = info.context
        return await ContainerRegistry.load_all(ctx)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_container_registry_node(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ) -> ContainerRegistryNode:
        return await ContainerRegistryNode.get_node(info, id)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_container_registry_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult:
        return await ContainerRegistryNode.get_connection(
            info,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_audit_log_schema(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> AuditLogSchema:
        return AuditLogSchema()

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_audit_log_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult:
        return await AuditLogNode.get_connection(
            info,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_available_service(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> AuditLogSchema:
        return AvailableServiceNode()

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_service_config(
        root: Any,
        info: graphene.ResolveInfo,
        service: str,
    ) -> ServiceConfigNode:
        return await ServiceConfigNode.load(info, service)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_service_configs(
        root: Any,
        info: graphene.ResolveInfo,
        services: list[str],
        *,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult:
        return await ServiceConfigNode.get_connection(
            info,
            services,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    async def resolve_model_card(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ):
        return await ModelCard.get_node(info, id)

    @staticmethod
    async def resolve_model_cards(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult[ModelCard]:
        return await ModelCard.get_connection(
            info,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    async def resolve_network(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ):
        return await NetworkNode.get_node(info, id)

    @staticmethod
    async def resolve_networks(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult:
        return await NetworkNode.get_connection(
            info,
            filter,
            order,
            offset,
            after,
            first,
            before,
            last,
        )

    @staticmethod
    async def resolve_endpoint_auto_scaling_rule_node(
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ) -> EndpointAutoScalingRuleNode:
        return await EndpointAutoScalingRuleNode.get_node(info, id)

    @staticmethod
    async def resolve_endpoint_auto_scaling_rule_nodes(
        root: Any,
        info: graphene.ResolveInfo,
        endpoint: str,
        *,
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult:
        return await EndpointAutoScalingRuleNode.get_connection(
            info,
            endpoint,
            filter_expr=filter,
            order_expr=order,
            offset=offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )

    @staticmethod
    async def resolve_user_utilization_metric(
        root: Any,
        info: graphene.ResolveInfo,
        user_id: uuid.UUID,
        *,
        props: UserUtilizationMetricQueryInput,
    ) -> UserUtilizationMetric:
        graph_ctx = cast(GraphQueryContext, info.context)
        user = graph_ctx.user
        if user["role"] not in (UserRole.SUPERADMIN, UserRole.MONITOR):
            if user["uuid"] != user_id:
                raise RuntimeError("Permission denied.")
        return await UserUtilizationMetric.get_object(
            info,
            user_id,
            props.metric_query_param(),
        )

    @staticmethod
    async def resolve_container_utilization_metric_metadata(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> ContainerUtilizationMetricMetadata:
        return await ContainerUtilizationMetricMetadata.get_object(info)


class GQLMutationPrivilegeCheckMiddleware:
    def resolve(self, next, root, info: graphene.ResolveInfo, **args) -> Any:
        graph_ctx: GraphQueryContext = info.context
        if info.operation.operation == OperationType.MUTATION:
            mutation_field: GraphQLField | None = getattr(Mutation, info.field_name, None)  # noqa
            if mutation_field is None:
                return next(root, info, **args)
            mutation_cls = mutation_field.type
            # default is allow nobody.
            allowed_roles = getattr(mutation_cls, "allowed_roles", [])
            if graph_ctx.user["role"] not in allowed_roles:
                if _is_legacy_mutation(mutation_cls):
                    return mutation_cls(False, f"no permission to execute {info.path.key}")  # type: ignore
                raise PermissionDeniedError()
        return next(root, info, **args)


class GQLExceptionMiddleware:
    def resolve(self, next, root, info: graphene.ResolveInfo, **args) -> Any:
        try:
            res = next(root, info, **args)
        except BackendAIError as e:
            if e.status_code // 100 == 4:
                log.debug("GraphQL client error: {}", e)
            elif e.status_code // 100 == 5:
                log.exception("GraphQL Server error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={
                    "code": str(e.error_code()),
                },
            )
        except Exception as e:
            log.exception("GraphQL unexpected error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={
                    "code": str(ErrorCode.default()),
                },
            )
        return res


class GQLMetricMiddleware:
    def resolve(self, next, root, info: graphene.ResolveInfo, **args) -> Any:
        graph_ctx: GraphQueryContext = info.context
        operation_type = info.operation.operation
        field_name = info.field_name
        parent_type = info.parent_type.name
        operation_name = (
            info.operation.name.value if info.operation.name is not None else "anonymous"
        )
        start = time.perf_counter()
        try:
            info.field_name
            res = next(root, info, **args)
            graph_ctx.metric_observer.observe_request(
                operation_type=operation_type,
                field_name=field_name,
                parent_type=parent_type,
                operation_name=operation_name,
                error_code=None,
                success=True,
                duration=time.perf_counter() - start,
            )
        except BackendAIError as e:
            graph_ctx.metric_observer.observe_request(
                operation_type=operation_type,
                field_name=field_name,
                parent_type=parent_type,
                operation_name=operation_name,
                error_code=e.error_code(),
                success=False,
                duration=time.perf_counter() - start,
            )
            raise e
        except BaseException as e:
            graph_ctx.metric_observer.observe_request(
                operation_type=operation_type,
                field_name=field_name,
                parent_type=parent_type,
                operation_name=operation_name,
                error_code=ErrorCode.default(),
                success=False,
                duration=time.perf_counter() - start,
            )
            raise e
        return res
