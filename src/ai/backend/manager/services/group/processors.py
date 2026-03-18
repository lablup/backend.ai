from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.group.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.group.actions.delete_group import (
    DeleteGroupAction,
    DeleteGroupActionResult,
)
from ai.backend.manager.services.group.actions.modify_group import (
    ModifyGroupAction,
    ModifyGroupActionResult,
)
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
)
from ai.backend.manager.services.group.actions.search_projects import (
    GetProjectAction,
    GetProjectActionResult,
    ScopedSearchProjectsActionResult,
    SearchProjectsAction,
    SearchProjectsActionResult,
    SearchProjectsByDomainAction,
    SearchProjectsByUserAction,
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


class GroupProcessors(AbstractProcessorPackage):
    create_group: ScopeActionProcessor[CreateGroupAction, CreateGroupActionResult]
    modify_group: SingleEntityActionProcessor[ModifyGroupAction, ModifyGroupActionResult]
    delete_group: SingleEntityActionProcessor[DeleteGroupAction, DeleteGroupActionResult]
    purge_group: SingleEntityActionProcessor[PurgeGroupAction, PurgeGroupActionResult]
    usage_per_month: ActionProcessor[UsagePerMonthAction, UsagePerMonthActionResult]
    usage_per_period: ActionProcessor[UsagePerPeriodAction, UsagePerPeriodActionResult]
    search_projects: ActionProcessor[SearchProjectsAction, SearchProjectsActionResult]
    search_projects_by_domain: ScopeActionProcessor[
        SearchProjectsByDomainAction, ScopedSearchProjectsActionResult
    ]
    search_projects_by_user: ScopeActionProcessor[
        SearchProjectsByUserAction, ScopedSearchProjectsActionResult
    ]
    get_project: SingleEntityActionProcessor[GetProjectAction, GetProjectActionResult]

    def __init__(
        self,
        group_service: GroupService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create_group = ScopeActionProcessor(group_service.create_group, action_monitors)
        self.modify_group = SingleEntityActionProcessor(group_service.modify_group, action_monitors)
        self.delete_group = SingleEntityActionProcessor(group_service.delete_group, action_monitors)
        self.purge_group = SingleEntityActionProcessor(group_service.purge_group, action_monitors)
        self.usage_per_month = ActionProcessor(group_service.usage_per_month, action_monitors)
        self.usage_per_period = ActionProcessor(group_service.usage_per_period, action_monitors)
        self.search_projects = ActionProcessor(group_service.search_projects, action_monitors)
        self.search_projects_by_domain = ScopeActionProcessor(
            group_service.search_projects_by_domain, action_monitors
        )
        self.search_projects_by_user = ScopeActionProcessor(
            group_service.search_projects_by_user, action_monitors
        )
        self.get_project = SingleEntityActionProcessor(group_service.get_project, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateGroupAction.spec(),
            ModifyGroupAction.spec(),
            DeleteGroupAction.spec(),
            PurgeGroupAction.spec(),
            UsagePerMonthAction.spec(),
            UsagePerPeriodAction.spec(),
            SearchProjectsAction.spec(),
            SearchProjectsByDomainAction.spec(),
            SearchProjectsByUserAction.spec(),
            GetProjectAction.spec(),
        ]
