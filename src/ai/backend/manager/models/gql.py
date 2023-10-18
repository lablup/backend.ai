from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

import attrs
import graphene

from ai.backend.common.types import QuotaScopeID
from ai.backend.manager.defs import DEFAULT_IMAGE_ARCH

from .etcd import (
    ContainerRegistry,
    CreateContainerRegistry,
    DeleteContainerRegistry,
    ModifyContainerRegistry,
)

if TYPE_CHECKING:
    from ai.backend.common.bgtask import BackgroundTaskManager
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.common.types import (
        AccessKey,
        AgentId,
        RedisConnectionInfo,
        SessionId,
        SlotName,
        SlotTypes,
    )

    from ..api.manager import ManagerStatus
    from ..config import LocalConfig, SharedConfig
    from ..idle import IdleCheckerHost
    from ..models.utils import ExtendedAsyncSAEngine
    from ..registry import AgentRegistry
    from .storage import StorageSessionManager

from ..api.exceptions import (
    ImageNotFound,
    InsufficientPrivilege,
    InvalidAPIParameters,
    ObjectNotFound,
    TooManyKernelsFound,
)
from .acl import PredefinedAtomicPermission
from .agent import Agent, AgentList, AgentSummary, AgentSummaryList, ModifyAgent
from .base import DataLoaderManager, privileged_query, scoped_query
from .domain import CreateDomain, DeleteDomain, Domain, ModifyDomain, PurgeDomain
from .endpoint import Endpoint, EndpointList, EndpointToken, EndpointTokenList
from .group import CreateGroup, DeleteGroup, Group, ModifyGroup, PurgeGroup
from .image import (
    AliasImage,
    ClearImages,
    DealiasImage,
    ForgetImage,
    Image,
    ModifyImage,
    PreloadImage,
    RescanImages,
    UnloadImage,
)
from .kernel import (
    ComputeContainer,
    ComputeContainerList,
    LegacyComputeSession,
    LegacyComputeSessionList,
)
from .keypair import CreateKeyPair, DeleteKeyPair, KeyPair, KeyPairList, ModifyKeyPair
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
from .resource_preset import (
    CreateResourcePreset,
    DeleteResourcePreset,
    ModifyResourcePreset,
    ResourcePreset,
)
from .routing import Routing, RoutingList
from .scaling_group import (
    AssociateScalingGroupWithDomain,
    AssociateScalingGroupWithKeyPair,
    AssociateScalingGroupWithUserGroup,
    CreateScalingGroup,
    DeleteScalingGroup,
    DisassociateAllScalingGroupsWithDomain,
    DisassociateAllScalingGroupsWithGroup,
    DisassociateScalingGroupWithDomain,
    DisassociateScalingGroupWithKeyPair,
    DisassociateScalingGroupWithUserGroup,
    ModifyScalingGroup,
    ScalingGroup,
)
from .session import ComputeSession, ComputeSessionList
from .storage import StorageVolume, StorageVolumeList
from .user import (
    CreateUser,
    DeleteUser,
    ModifyUser,
    PurgeUser,
    User,
    UserList,
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


@attrs.define(auto_attribs=True, slots=True)
class GraphQueryContext:
    schema: graphene.Schema
    dataloader_manager: DataLoaderManager
    local_config: LocalConfig
    shared_config: SharedConfig
    etcd: AsyncEtcd
    user: Mapping[str, Any]  # TODO: express using typed dict
    access_key: str
    db: ExtendedAsyncSAEngine
    redis_stat: RedisConnectionInfo
    redis_live: RedisConnectionInfo
    redis_image: RedisConnectionInfo
    manager_status: ManagerStatus
    known_slot_types: Mapping[SlotName, SlotTypes]
    background_task_manager: BackgroundTaskManager
    storage_manager: StorageSessionManager
    registry: AgentRegistry
    idle_checker_host: IdleCheckerHost


class Mutations(graphene.ObjectType):
    """
    All available GraphQL mutations.
    """

    # super-admin only
    modify_agent = ModifyAgent.Field()

    # super-admin only
    create_domain = CreateDomain.Field()
    modify_domain = ModifyDomain.Field()
    delete_domain = DeleteDomain.Field()
    purge_domain = PurgeDomain.Field()

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

    # admin only
    create_keypair = CreateKeyPair.Field()
    modify_keypair = ModifyKeyPair.Field()
    delete_keypair = DeleteKeyPair.Field()

    # admin only
    rescan_images = RescanImages.Field()
    preload_image = PreloadImage.Field()
    unload_image = UnloadImage.Field()
    modify_image = ModifyImage.Field()
    forget_image = ForgetImage.Field()
    alias_image = AliasImage.Field()
    dealias_image = DealiasImage.Field()
    clear_images = ClearImages.Field()

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
    create_scaling_group = CreateScalingGroup.Field()
    modify_scaling_group = ModifyScalingGroup.Field()
    delete_scaling_group = DeleteScalingGroup.Field()
    associate_scaling_group_with_domain = AssociateScalingGroupWithDomain.Field()
    associate_scaling_group_with_user_group = AssociateScalingGroupWithUserGroup.Field()
    associate_scaling_group_with_keypair = AssociateScalingGroupWithKeyPair.Field()
    disassociate_scaling_group_with_domain = DisassociateScalingGroupWithDomain.Field()
    disassociate_scaling_group_with_user_group = DisassociateScalingGroupWithUserGroup.Field()
    disassociate_scaling_group_with_keypair = DisassociateScalingGroupWithKeyPair.Field()
    disassociate_all_scaling_groups_with_domain = DisassociateAllScalingGroupsWithDomain.Field()
    disassociate_all_scaling_groups_with_group = DisassociateAllScalingGroupsWithGroup.Field()

    set_quota_scope = SetQuotaScope.Field()
    unset_quota_scope = UnsetQuotaScope.Field()

    create_container_registry = CreateContainerRegistry.Field()
    modify_container_registry = ModifyContainerRegistry.Field()
    delete_container_registry = DeleteContainerRegistry.Field()


class Queries(graphene.ObjectType):
    """
    All available GraphQL queries.
    """

    node = graphene.relay.Node.Field()

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

    domain = graphene.Field(
        Domain,
        name=graphene.String(),
    )

    # super-admin only
    domains = graphene.List(
        Domain,
        is_active=graphene.Boolean(),
    )

    group = graphene.Field(
        Group,
        id=graphene.UUID(required=True),
        domain_name=graphene.String(),
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
    )

    image = graphene.Field(
        Image,
        reference=graphene.String(required=True),
        architecture=graphene.String(default_value=DEFAULT_IMAGE_ARCH),
    )

    images = graphene.List(
        Image,
        is_installed=graphene.Boolean(),
        is_operation=graphene.Boolean(),
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

    resource_presets = graphene.List(
        ResourcePreset,
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
        access_key=graphene.String(),
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

    container_registry = graphene.Field(ContainerRegistry, hostname=graphene.String(required=True))

    container_registries = graphene.List(ContainerRegistry)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_agent(
        root: Any,
        info: graphene.ResolveInfo,
        agent_id: AgentId,
    ) -> Agent:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            "Agent",
            raw_status=None,
        )
        return await loader.load(agent_id)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_agents(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        scaling_group: str = None,
        status: str = None,
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
        filter: str = None,
        order: str = None,
        scaling_group: str = None,
        status: str = None,
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
        if ctx.local_config["manager"]["hide-agents"]:
            raise ObjectNotFound(object_name="agent")

        loader = ctx.dataloader_manager.get_loader(
            ctx,
            "Agent",
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
        if ctx.local_config["manager"]["hide-agents"]:
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
    async def resolve_domain(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        name: str = None,
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
        is_active: bool = None,
    ) -> Sequence[Domain]:
        return await Domain.load_all(info.context, is_active=is_active)

    @staticmethod
    async def resolve_group(
        root: Any,
        info: graphene.ResolveInfo,
        id: uuid.UUID,
        *,
        domain_name: str = None,
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
            client_groups = await loader.load(client_user_id)
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
        domain_name: str = None,
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
        domain_name: str = None,
        is_active: bool = None,
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
            )
            client_groups = await loader.load(client_user_id)
            return client_groups
        else:
            raise InvalidAPIParameters("Unknown client role")
        return await Group.load_all(info.context, domain_name=domain_name, is_active=is_active)

    @staticmethod
    async def resolve_image(
        root: Any,
        info: graphene.ResolveInfo,
        reference: str,
        architecture: str,
    ) -> Image:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        item = await Image.load_item(info.context, reference, architecture)
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
    async def resolve_images(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        is_installed=None,
        is_operation=False,
    ) -> Sequence[Image]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]
        client_domain = ctx.user["domain_name"]
        items = await Image.load_all(ctx, is_installed=is_installed, is_operation=is_operation)
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role in (UserRole.ADMIN, UserRole.USER):
            items = await Image.filter_allowed(
                info.context,
                items,
                client_domain,
                is_installed=is_installed,
                is_operation=is_operation,
            )
        else:
            raise InvalidAPIParameters("Unknown client role")
        return items

    @staticmethod
    @scoped_query(autofill_user=True, user_key="email")
    async def resolve_user(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: str = None,
        email: str = None,
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
        domain_name: str = None,
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
        domain_name: str = None,
        group_id: uuid.UUID = None,
        is_active: bool = None,
        status: UserStatus = None,
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
        filter: str = None,
        order: str = None,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        is_active: bool = None,
        status: UserStatus = None,
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
    @scoped_query(autofill_user=True, user_key="access_key")
    async def resolve_keypair(
        root: Any,
        info: graphene.ResolveInfo,
        *,
        domain_name: str = None,
        access_key: AccessKey = None,
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
        domain_name: str = None,
        email: str = None,
        is_active: bool = None,
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
        filter: str = None,
        order: str = None,
        domain_name: str = None,
        email: str = None,
        is_active: bool = None,
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
        name: str = None,
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
        name: str = None,
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
    async def resolve_resource_presets(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> Sequence[ResourcePreset]:
        return await ResourcePreset.load_all(info.context)

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
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_all(info.context, is_active=is_active)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups_for_domain(
        root: Any,
        info: graphene.ResolveInfo,
        domain: str,
        is_active: bool = None,
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
        is_active: bool = None,
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
        is_active: bool = None,
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
        filter: str = None,
        order: str = None,
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
        domain_name: str = None,
        group_id: uuid.UUID = None,
        user_id: uuid.UUID = None,
    ) -> Optional[VirtualFolder]:
        graph_ctx: GraphQueryContext = info.context
        user_role = graph_ctx.user["role"]
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "VirtualFolder.by_id",
            user_uuid=user_id,
            user_role=user_role,
            domain_name=domain_name,
            group_id=group_id,
        )
        return await loader.load(id)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="user_id")
    async def resolve_vfolder_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        user_id: uuid.UUID = None,
        filter: str = None,
        order: str = None,
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
        user_id: uuid.UUID = None,
        filter: str = None,
        order: str = None,
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
        domain_name: str = None,
        user_id: uuid.UUID = None,
        filter: str = None,
        order: str = None,
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
        domain_name: str = None,
        user_id: uuid.UUID = None,  # not used, fixed
        filter: str = None,
        order: str = None,
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
        domain_name: str = None,
        user_id: uuid.UUID = None,  # not used, fixed
        filter: str = None,
        order: str = None,
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
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_compute_container_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: str = None,
        order: str = None,
        session_id: SessionId,
        role: UserRole = None,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        access_key: AccessKey = None,
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
        container_id: str,
    ) -> ComputeContainer:
        # We need to check the group membership of the designated kernel,
        # but practically a user cannot guess the IDs of kernels launched
        # by other users and in other groups.
        # Let's just protect the domain/user boundary here.
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "ComputeContainer.detail")
        return await loader.load(container_id)

    @staticmethod
    @scoped_query(autofill_user=False, user_key="access_key")
    async def resolve_compute_session_list(
        root: Any,
        info: graphene.ResolveInfo,
        limit: int,
        offset: int,
        *,
        filter: str = None,
        order: str = None,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        access_key: AccessKey = None,
        status: str = None,
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
        domain_name: str = None,
        access_key: AccessKey = None,
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
        domain_name: str = None,
        group_id: uuid.UUID = None,
        access_key: AccessKey = None,
        status: str = None,
        order_key: str = None,
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
        domain_name: str = None,
        access_key: AccessKey = None,
        status: str = None,
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
        matches = await loader.load(sess_id)
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            raise TooManyKernelsFound

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
        return await ContainerRegistry.load_registry(ctx, hostname)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_container_registries(
        root: Any,
        info: graphene.ResolveInfo,
    ) -> Sequence[ContainerRegistry]:
        ctx: GraphQueryContext = info.context
        return await ContainerRegistry.load_all(ctx)


class GQLMutationPrivilegeCheckMiddleware:
    def resolve(self, next, root, info: graphene.ResolveInfo, **args) -> Any:
        graph_ctx: GraphQueryContext = info.context
        if info.operation.operation == "mutation" and len(info.path) == 1:
            mutation_cls = getattr(Mutations, info.field_name).type
            # default is allow nobody.
            allowed_roles = getattr(mutation_cls, "allowed_roles", [])
            if graph_ctx.user["role"] not in allowed_roles:
                return mutation_cls(False, f"no permission to execute {info.path[0]}")
        return next(root, info, **args)
