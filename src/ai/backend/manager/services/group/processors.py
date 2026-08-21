from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.services.group.actions.assign_users_to_project import (
    AssignUsersToProjectAction,
    AssignUsersToProjectActionResult,
)
from ai.backend.manager.services.group.actions.create_group import CreateGroupAction
from ai.backend.manager.services.group.actions.create_project_dotfile import (
    CreateProjectDotfileAction,
    CreateProjectDotfileActionResult,
)
from ai.backend.manager.services.group.actions.delete_group import DeleteGroupAction
from ai.backend.manager.services.group.actions.delete_project_dotfile import (
    DeleteProjectDotfileAction,
    DeleteProjectDotfileActionResult,
)
from ai.backend.manager.services.group.actions.lookup import LookupProjectAction
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
)
from ai.backend.manager.services.group.actions.restore_group import RestoreGroupAction
from ai.backend.manager.services.group.actions.search_projects import (
    GetProjectAction,
    GlobalSearchProjectsAction,
    SearchProjectsByDomainAction,
    SearchProjectsByUserAction,
)
from ai.backend.manager.services.group.actions.unassign_users import (
    UnassignUsersFromProjectAction,
    UnassignUsersFromProjectActionResult,
)
from ai.backend.manager.services.group.actions.update_group import (
    UpdateGroupAction,
    UpdateGroupActionResult,
)
from ai.backend.manager.services.group.actions.update_project_dotfile import (
    UpdateProjectDotfileAction,
    UpdateProjectDotfileActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_month import (
    UsagePerMonthAction,
    UsagePerMonthActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_period import (
    UsagePerPeriodAction,
    UsagePerPeriodActionResult,
)
from ai.backend.manager.services.group.service import GroupService


class GroupProcessors:
    lookup: LookupActionProcessor[LookupProjectAction, LookupOpsResult[ProjectID]]
    get_project: SingleEntityActionProcessor[GetProjectAction, EntityOpsResult[GroupData]]
    global_search: GlobalActionProcessor[GlobalSearchProjectsAction, BatchOpsResult[GroupData]]
    search_projects_by_domain: ScopeActionProcessor[
        SearchProjectsByDomainAction, ScopedBatchOpsResult[GroupData]
    ]
    search_projects_by_user: ScopeActionProcessor[
        SearchProjectsByUserAction, ScopedBatchOpsResult[GroupData]
    ]
    create_group: ScopeActionProcessor[CreateGroupAction, CreatedEntityOpsResult[GroupData]]
    delete_group: SingleEntityActionProcessor[DeleteGroupAction, EntityOpsResult[GroupData]]
    restore_group: SingleEntityActionProcessor[RestoreGroupAction, EntityOpsResult[GroupData]]
    update_group: SingleEntityActionProcessor[UpdateGroupAction, UpdateGroupActionResult]
    purge_group: SingleEntityActionProcessor[PurgeGroupAction, PurgeGroupActionResult]
    usage_per_month: GlobalActionProcessor[UsagePerMonthAction, UsagePerMonthActionResult]
    usage_per_period: GlobalActionProcessor[UsagePerPeriodAction, UsagePerPeriodActionResult]
    assign_users_to_project: SingleEntityActionProcessor[
        AssignUsersToProjectAction, AssignUsersToProjectActionResult
    ]
    unassign_users_from_project: SingleEntityActionProcessor[
        UnassignUsersFromProjectAction, UnassignUsersFromProjectActionResult
    ]
    create_dotfile: SingleEntityActionProcessor[
        CreateProjectDotfileAction, CreateProjectDotfileActionResult
    ]
    update_dotfile: SingleEntityActionProcessor[
        UpdateProjectDotfileAction, UpdateProjectDotfileActionResult
    ]
    delete_dotfile: SingleEntityActionProcessor[
        DeleteProjectDotfileAction, DeleteProjectDotfileActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[GroupData],
        group_service: GroupService,
    ) -> None:
        self.lookup = group.public_lookup_ops(LookupProjectAction)
        self.get_project = group.single_get_ops(GetProjectAction)
        self.global_search = group.global_search_ops(GlobalSearchProjectsAction)
        self.search_projects_by_domain = group.scope_search_ops(SearchProjectsByDomainAction)
        self.search_projects_by_user = group.scope_search_ops(SearchProjectsByUserAction)
        self.create_group = group.role_managed_create_ops(CreateGroupAction)
        self.delete_group = group.single_delete_ops(DeleteGroupAction)
        self.restore_group = group.single_restore_ops(RestoreGroupAction)
        self.update_group = group.single_entity(UpdateGroupAction, group_service.update_group)
        self.purge_group = group.single_entity(PurgeGroupAction, group_service.purge_group)
        self.usage_per_month = group.global_scope(
            UsagePerMonthAction, group_service.usage_per_month
        )
        self.usage_per_period = group.global_scope(
            UsagePerPeriodAction, group_service.usage_per_period
        )
        self.assign_users_to_project = group.single_entity(
            AssignUsersToProjectAction, group_service.assign_users_to_project
        )
        self.unassign_users_from_project = group.single_entity(
            UnassignUsersFromProjectAction, group_service.unassign_users_from_project
        )
        self.create_dotfile = group.single_entity(
            CreateProjectDotfileAction, group_service.create_dotfile
        )
        self.update_dotfile = group.single_entity(
            UpdateProjectDotfileAction, group_service.update_dotfile
        )
        self.delete_dotfile = group.single_entity(
            DeleteProjectDotfileAction, group_service.delete_dotfile
        )
