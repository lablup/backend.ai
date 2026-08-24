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
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.services.project.actions.assign_users_to_project import (
    AssignUsersToProjectAction,
    AssignUsersToProjectActionResult,
)
from ai.backend.manager.services.project.actions.create_project import CreateProjectAction
from ai.backend.manager.services.project.actions.create_project_dotfile import (
    CreateProjectDotfileAction,
    CreateProjectDotfileActionResult,
)
from ai.backend.manager.services.project.actions.delete_project import DeleteProjectAction
from ai.backend.manager.services.project.actions.delete_project_dotfile import (
    DeleteProjectDotfileAction,
    DeleteProjectDotfileActionResult,
)
from ai.backend.manager.services.project.actions.lookup import LookupProjectAction
from ai.backend.manager.services.project.actions.purge_project import (
    PurgeProjectAction,
    PurgeProjectActionResult,
)
from ai.backend.manager.services.project.actions.restore_project import RestoreProjectAction
from ai.backend.manager.services.project.actions.search_projects import (
    GetProjectAction,
    GlobalSearchProjectsAction,
    SearchProjectsByDomainAction,
    SearchProjectsByUserAction,
)
from ai.backend.manager.services.project.actions.unassign_users import (
    UnassignUsersFromProjectAction,
    UnassignUsersFromProjectActionResult,
)
from ai.backend.manager.services.project.actions.update_project import (
    UpdateProjectAction,
    UpdateProjectActionResult,
)
from ai.backend.manager.services.project.actions.update_project_dotfile import (
    UpdateProjectDotfileAction,
    UpdateProjectDotfileActionResult,
)
from ai.backend.manager.services.project.actions.usage_per_month import (
    UsagePerMonthAction,
    UsagePerMonthActionResult,
)
from ai.backend.manager.services.project.actions.usage_per_period import (
    UsagePerPeriodAction,
    UsagePerPeriodActionResult,
)
from ai.backend.manager.services.project.service import ProjectService


class ProjectProcessors:
    lookup: LookupActionProcessor[LookupProjectAction, LookupOpsResult[ProjectID]]
    get_project: SingleEntityActionProcessor[GetProjectAction, EntityOpsResult[ProjectData]]
    global_search: GlobalActionProcessor[GlobalSearchProjectsAction, BatchOpsResult[ProjectData]]
    search_projects_by_domain: ScopeActionProcessor[
        SearchProjectsByDomainAction, ScopedBatchOpsResult[ProjectData]
    ]
    search_projects_by_user: ScopeActionProcessor[
        SearchProjectsByUserAction, ScopedBatchOpsResult[ProjectData]
    ]
    create_project: ScopeActionProcessor[CreateProjectAction, CreatedEntityOpsResult[ProjectData]]
    delete_project: SingleEntityActionProcessor[DeleteProjectAction, EntityOpsResult[ProjectData]]
    restore_project: SingleEntityActionProcessor[RestoreProjectAction, EntityOpsResult[ProjectData]]
    update_project: SingleEntityActionProcessor[UpdateProjectAction, UpdateProjectActionResult]
    purge_project: SingleEntityActionProcessor[PurgeProjectAction, PurgeProjectActionResult]
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
        group: ProcessorGroup[ProjectData],
        group_service: ProjectService,
    ) -> None:
        self.lookup = group.public_lookup_ops(LookupProjectAction)
        self.get_project = group.single_get_ops(GetProjectAction)
        self.global_search = group.global_search_ops(GlobalSearchProjectsAction)
        self.search_projects_by_domain = group.scope_search_ops(SearchProjectsByDomainAction)
        self.search_projects_by_user = group.scope_search_ops(SearchProjectsByUserAction)
        self.create_project = group.role_managed_create_ops(CreateProjectAction)
        self.delete_project = group.single_guarded_delete_ops(DeleteProjectAction)
        self.restore_project = group.single_guarded_restore_ops(RestoreProjectAction)
        self.update_project = group.single_entity(UpdateProjectAction, group_service.update_group)
        self.purge_project = group.single_entity(PurgeProjectAction, group_service.purge_group)
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
