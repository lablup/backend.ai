from __future__ import annotations

from typing import Any, Optional, Mapping, Sequence, TYPE_CHECKING
import uuid

import attr
import graphene

from ai.backend.manager.defs import DEFAULT_IMAGE_ARCH

if TYPE_CHECKING:
    from graphql.execution.executors.asyncio import AsyncioExecutor

    from ai.backend.common.bgtask import BackgroundTaskManager
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.common.types import (
        AccessKey,
        AgentId,
        RedisConnectionInfo,
        SlotName,
        SlotTypes,
        SessionId,
    )

    from ..api.manager import ManagerStatus
    from ..config import LocalConfig, SharedConfig
    from ..registry import AgentRegistry
    from ..models.utils import ExtendedAsyncSAEngine
    from .storage import StorageSessionManager

from .base import DataLoaderManager, privileged_query, scoped_query
from .agent import (
    Agent,
    AgentList,
    ModifyAgent,
)
from .domain import (
    Domain,
    CreateDomain,
    ModifyDomain,
    DeleteDomain,
    PurgeDomain,
)
from .group import (
    Group,
    CreateGroup,
    ModifyGroup,
    DeleteGroup,
    PurgeGroup,
)
from .image import (
    ClearImages,
    Image,
    ModifyImage,
    RescanImages,
    PreloadImage,
    UnloadImage,
    ForgetImage,
    AliasImage,
    DealiasImage,
)
from .kernel import (
    ComputeSession,
    ComputeSessionList,
    ComputeContainer,
    ComputeContainerList,
    LegacyComputeSession,
    LegacyComputeSessionList,
)
from .keypair import (
    KeyPair,
    KeyPairList,
    CreateKeyPair,
    ModifyKeyPair,
    DeleteKeyPair,
)
from .resource_policy import (
    KeyPairResourcePolicy,
    CreateKeyPairResourcePolicy,
    ModifyKeyPairResourcePolicy,
    DeleteKeyPairResourcePolicy,
)
from .resource_preset import (
    ResourcePreset,
    CreateResourcePreset,
    ModifyResourcePreset,
    DeleteResourcePreset,
)
from .scaling_group import (
    ScalingGroup,
    CreateScalingGroup,
    ModifyScalingGroup,
    DeleteScalingGroup,
    AssociateScalingGroupWithDomain,
    DisassociateScalingGroupWithDomain,
    DisassociateAllScalingGroupsWithDomain,
    AssociateScalingGroupWithUserGroup,
    DisassociateScalingGroupWithUserGroup,
    DisassociateAllScalingGroupsWithGroup,
    AssociateScalingGroupWithKeyPair,
    DisassociateScalingGroupWithKeyPair,
)
from .storage import (
    StorageVolume,
    StorageVolumeList,
)
from .user import (
    User,
    UserList,
    CreateUser,
    ModifyUser,
    DeleteUser,
    PurgeUser,
    UserRole,
    UserStatus,
)
from .vfolder import (
    VirtualFolder,
    VirtualFolderList,
)
from ..api.exceptions import (
    ObjectNotFound,
    ImageNotFound,
    InsufficientPrivilege,
    InvalidAPIParameters,
    TooManyKernelsFound,
)


@attr.s(auto_attribs=True, slots=True)
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
    redis_image: RedisConnectionInfo
    manager_status: ManagerStatus
    known_slot_types: Mapping[SlotName, SlotTypes]
    background_task_manager: BackgroundTaskManager
    storage_manager: StorageSessionManager
    registry: AgentRegistry


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


class Queries(graphene.ObjectType):
    """
    All available GraphQL queries.
    """

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

    keypair_resource_policies = graphene.List(
        KeyPairResourcePolicy)

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

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_agent(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        agent_id: AgentId,
    ) -> Agent:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            'Agent',
            raw_status=None,
        )
        return await loader.load(agent_id)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_agents(
        executor: AsyncioExecutor,
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
        executor: AsyncioExecutor,
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
            info.context, limit, offset,
            scaling_group=scaling_group,
            raw_status=status,
            filter=filter,
            order=order,
        )
        return AgentList(agent_list, total_count)

    @staticmethod
    async def resolve_domain(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo, *,
        name: str = None,
    ) -> Domain:
        ctx: GraphQueryContext = info.context
        name = ctx.user['domain_name'] if name is None else name
        if ctx.user['role'] != UserRole.SUPERADMIN:
            if name != ctx.user['domain_name']:
                # prevent querying other domains if not superadmin
                raise ObjectNotFound(object_name='domain')
        loader = ctx.dataloader_manager.get_loader(ctx, 'Domain.by_name')
        return await loader.load(name)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_domains(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        *,
        is_active: bool = None,
    ) -> Sequence[Domain]:
        return await Domain.load_all(info.context, is_active=is_active)

    @staticmethod
    async def resolve_group(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        id: uuid.UUID,
        *,
        domain_name: str = None,
    ) -> Group:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user['role']
        client_domain = ctx.user['domain_name']
        client_user_id = ctx.user['uuid']
        if client_role == UserRole.SUPERADMIN:
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_id', domain_name=domain_name,
            )
            group = await loader.load(id)
        elif client_role == UserRole.ADMIN:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_id', domain_name=client_domain,
            )
            group = await loader.load(id)
        elif client_role == UserRole.USER:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_id', domain_name=client_domain,
            )
            group = await loader.load(id)
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_user',
            )
            client_groups = await loader.load(client_user_id)
            if group.id not in (g.id for g in client_groups):
                raise InsufficientPrivilege
        else:
            raise InvalidAPIParameters('Unknown client role')
        return group

    @staticmethod
    async def resolve_groups_by_name(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        name: str,
        *,
        domain_name: str = None,
    ) -> Sequence[Group]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user['role']
        client_domain = ctx.user['domain_name']
        client_user_id = ctx.user['uuid']
        if client_role == UserRole.SUPERADMIN:
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_name', domain_name=domain_name,
            )
            groups = await loader.load(name)
        elif client_role == UserRole.ADMIN:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_name', domain_name=client_domain,
            )
            groups = await loader.load(name)
        elif client_role == UserRole.USER:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_name', domain_name=client_domain,
            )
            groups = await loader.load(name)
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_user',
            )
            client_groups = await loader.load(client_user_id)
            client_group_ids = set(g.id for g in client_groups)
            groups = filter(lambda g: g.id in client_group_ids, groups)
        else:
            raise InvalidAPIParameters('Unknown client role')
        return groups

    @staticmethod
    async def resolve_groups(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        *,
        domain_name: str = None,
        is_active: bool = None,
    ) -> Sequence[Group]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user['role']
        client_domain = ctx.user['domain_name']
        client_user_id = ctx.user['uuid']
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role == UserRole.ADMIN:
            if domain_name is not None and domain_name != client_domain:
                raise InsufficientPrivilege
            domain_name = client_domain
        elif client_role == UserRole.USER:
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'Group.by_user',
            )
            client_groups = await loader.load(client_user_id)
            return client_groups
        else:
            raise InvalidAPIParameters('Unknown client role')
        return await Group.load_all(
            info.context,
            domain_name=domain_name,
            is_active=is_active)

    @staticmethod
    async def resolve_image(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        reference: str,
        architecture: str,
    ) -> Image:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user['role']
        client_domain = ctx.user['domain_name']
        item = await Image.load_item(info.context, reference, architecture)
        if client_role == UserRole.SUPERADMIN:
            pass
        elif client_role in (UserRole.ADMIN, UserRole.USER):
            items = await Image.filter_allowed(info.context, [item], client_domain)
            if not items:
                raise ImageNotFound
            item = items[0]
        else:
            raise InvalidAPIParameters('Unknown client role')
        return item

    @staticmethod
    async def resolve_images(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        *,
        is_installed=None,
        is_operation=False,
    ) -> Sequence[Image]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user['role']
        client_domain = ctx.user['domain_name']
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
            raise InvalidAPIParameters('Unknown client role')
        return items

    @staticmethod
    @scoped_query(autofill_user=True, user_key='email')
    async def resolve_user(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        *,
        domain_name: str = None,
        email: str = None,
    ) -> User:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx, 'User.by_email', domain_name=domain_name,
        )
        return await loader.load(email)

    @staticmethod
    @scoped_query(autofill_user=True, user_key='user_id')
    async def resolve_user_from_uuid(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        *,
        domain_name: str = None,
        user_id: uuid.UUID | str | None = None,
    ) -> User:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx, 'User.by_uuid', domain_name=domain_name,
        )
        # user_id is retrieved as string since it's a GraphQL's generic ID field
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        return await loader.load(user_uuid)

    @staticmethod
    async def resolve_users(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        is_active: bool = None,
        status: UserStatus = None,
    ) -> Sequence[User]:
        from .user import UserRole
        ctx: GraphQueryContext = info.context
        client_role = ctx.user['role']
        client_domain = ctx.user['domain_name']
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
            raise InvalidAPIParameters('Unknown client role')
        return await User.load_all(
            info.context,
            domain_name=domain_name,
            group_id=group_id,
            is_active=is_active,
            status=status,
            limit=100)

    @staticmethod
    async def resolve_user_list(
        executor: AsyncioExecutor,
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
        client_role = ctx.user['role']
        client_domain = ctx.user['domain_name']
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
            raise InvalidAPIParameters('Unknown client role')
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
    @scoped_query(autofill_user=True, user_key='access_key')
    async def resolve_keypair(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        *,
        domain_name: str = None,
        access_key: AccessKey = None,
    ) -> KeyPair:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            'KeyPair.by_ak',
            domain_name=domain_name,
        )
        return await loader.load(access_key)

    @staticmethod
    @scoped_query(autofill_user=False, user_key='email')
    async def resolve_keypairs(
        executor: AsyncioExecutor,
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
                'KeyPair.by_email',
                domain_name=domain_name,
                is_active=is_active,
            )
            return await loader.load(email)

    @staticmethod
    @scoped_query(autofill_user=False, user_key='email')
    async def resolve_keypair_list(
        executor: AsyncioExecutor,
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
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        name: str = None,
    ) -> KeyPairResourcePolicy:
        ctx: GraphQueryContext = info.context
        client_access_key = ctx.access_key
        if name is None:
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'KeyPairResourcePolicy.by_ak',
            )
            return await loader.load(client_access_key)
        else:
            loader = ctx.dataloader_manager.get_loader(
                ctx, 'KeyPairResourcePolicy.by_name',
            )
            return await loader.load(name)

    @staticmethod
    async def resolve_keypair_resource_policies(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
    ) -> Sequence[KeyPairResourcePolicy]:
        ctx: GraphQueryContext = info.context
        client_role = ctx.user['role']
        client_access_key = ctx.access_key
        if client_role == UserRole.SUPERADMIN:
            return await KeyPairResourcePolicy.load_all(info.context)
        elif client_role == UserRole.ADMIN:
            # TODO: filter resource policies by domains?
            return await KeyPairResourcePolicy.load_all(info.context)
        elif client_role == UserRole.USER:
            return await KeyPairResourcePolicy.load_all_user(
                info.context, client_access_key,
            )
        else:
            raise InvalidAPIParameters('Unknown client role')

    @staticmethod
    async def resolve_resource_preset(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        name: str,
    ) -> ResourcePreset:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, 'ResourcePreset.by_name')
        return await loader.load(name)

    @staticmethod
    async def resolve_resource_presets(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
    ) -> Sequence[ResourcePreset]:
        return await ResourcePreset.load_all(info.context)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_group(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        name: str,
    ) -> ScalingGroup:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(
            ctx, 'ScalingGroup.by_name',
        )
        return await loader.load(name)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_all(info.context, is_active=is_active)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups_for_domain(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        domain: str,
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_by_domain(
            info.context, domain, is_active=is_active,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups_for_group(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        user_group,
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_by_group(
            info.context, user_group, is_active=is_active,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_scaling_groups_for_keypair(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        access_key: AccessKey,
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        return await ScalingGroup.load_by_keypair(
            info.context, access_key, is_active=is_active,
        )

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_storage_volume(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        id: str,
    ) -> StorageVolume:
        return await StorageVolume.load_by_id(info.context, id)

    @staticmethod
    @privileged_query(UserRole.SUPERADMIN)
    async def resolve_storage_volume_list(
        executor: AsyncioExecutor,
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
    @scoped_query(autofill_user=False, user_key='user_id')
    async def resolve_vfolder_list(
        executor: AsyncioExecutor,
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
            group_id=group_id,        # scope
            user_id=user_id,          # scope
            filter=filter,
        )
        items = await VirtualFolder.load_slice(
            info.context,
            limit,
            offset,
            domain_name=domain_name,  # scope
            group_id=group_id,        # scope
            user_id=user_id,          # scope
            filter=filter,
            order=order,
        )
        return VirtualFolderList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key='access_key')
    async def resolve_compute_container_list(
        executor: AsyncioExecutor,
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
            session_id,               # filter (mandatory)
            cluster_role=role,        # filter
            domain_name=domain_name,  # scope
            group_id=group_id,        # scope
            access_key=access_key,    # scope
            filter=filter,
        )
        items = await ComputeContainer.load_slice(
            info.context,
            limit, offset,            # slice
            session_id,               # filter (mandatory)
            cluster_role=role,        # filter
            domain_name=domain_name,  # scope
            group_id=group_id,        # scope
            access_key=access_key,    # scope
            filter=filter,
            order=order,
        )
        return ComputeContainerList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key='access_key')
    async def resolve_compute_container(
        executor: AsyncioExecutor,
        info: graphene.ResolveInfo,
        container_id: str,
    ) -> ComputeContainer:
        # We need to check the group membership of the designated kernel,
        # but practically a user cannot guess the IDs of kernels launched
        # by other users and in other groups.
        # Let's just protect the domain/user boundary here.
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, 'ComputeContainer.detail')
        return await loader.load(container_id)

    @staticmethod
    @scoped_query(autofill_user=False, user_key='access_key')
    async def resolve_compute_session_list(
        executor: AsyncioExecutor,
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
            status=status,            # filter
            domain_name=domain_name,  # scope
            group_id=group_id,        # scope
            access_key=access_key,    # scope
            filter=filter,
        )
        items = await ComputeSession.load_slice(
            info.context,
            limit, offset,            # slice
            status=status,            # filter
            domain_name=domain_name,  # scope
            group_id=group_id,        # scope
            access_key=access_key,    # scope
            filter=filter,
            order=order,
        )
        return ComputeSessionList(items, total_count)

    @staticmethod
    @scoped_query(autofill_user=False, user_key='access_key')
    async def resolve_compute_session(
        executor: AsyncioExecutor,
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
            'ComputeSession.detail',
            domain_name=domain_name,
            access_key=access_key,
        )
        return await loader.load(id)

    @staticmethod
    @scoped_query(autofill_user=False, user_key='access_key')
    async def resolve_legacy_compute_session_list(
        executor: AsyncioExecutor,
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
    @scoped_query(autofill_user=False, user_key='access_key')
    async def resolve_legacy_compute_session(
        executor: AsyncioExecutor,
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
            'LegacyComputeSession.detail',
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


class GQLMutationPrivilegeCheckMiddleware:

    def resolve(self, next, root, info: graphene.ResolveInfo, **args) -> Any:
        graph_ctx: GraphQueryContext = info.context
        if info.operation.operation == 'mutation' and len(info.path) == 1:
            mutation_cls = getattr(Mutations, info.path[0]).type
            # default is allow nobody.
            allowed_roles = getattr(mutation_cls, 'allowed_roles', [])
            if graph_ctx.user['role'] not in allowed_roles:
                return mutation_cls(False, f"no permission to execute {info.path[0]}")
        return next(root, info, **args)
