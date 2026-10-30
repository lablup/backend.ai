from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.relation import RelationGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.relation.processor import RelationActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.services.project.actions.bulk_get import BulkGetProjectsAction
from ai.backend.manager.services.project.actions.clear_default_registry import (
    ClearProjectDefaultRegistryAction,
    ClearProjectDefaultRegistryActionResult,
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
from ai.backend.manager.services.project.actions.partial_bulk_delete_projects import (
    PartialBulkDeleteProjectsAction,
)
from ai.backend.manager.services.project.actions.partial_bulk_restore_projects import (
    PartialBulkRestoreProjectsAction,
)
from ai.backend.manager.services.project.actions.partial_bulk_update_projects import (
    PartialBulkUpdateProjectsAction,
)
from ai.backend.manager.services.project.actions.purge_project import (
    PurgeProjectAction,
    PurgeProjectActionResult,
)
from ai.backend.manager.services.project.actions.restore_project import RestoreProjectAction
from ai.backend.manager.services.project.actions.scoped_search import (
    ScopedSearchProjectsAction,
)
from ai.backend.manager.services.project.actions.search_projects import (
    GetProjectAction,
    GlobalSearchProjectsAction,
)
from ai.backend.manager.services.project.actions.switch_default_registry import (
    SwitchProjectDefaultRegistryAction,
    SwitchProjectDefaultRegistryActionResult,
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
    switch_default_registry: RelationActionProcessor[
        SwitchProjectDefaultRegistryAction, SwitchProjectDefaultRegistryActionResult
    ]
    clear_default_registry: RelationActionProcessor[
        ClearProjectDefaultRegistryAction, ClearProjectDefaultRegistryActionResult
    ]
    lookup: LookupActionProcessor[LookupProjectAction, LookupOpsResult[ProjectID]]
    get_project: SingleEntityActionProcessor[GetProjectAction, EntityOpsResult[ProjectData]]
    bulk_get: PartialBulkActionProcessor[BulkGetProjectsAction, ProjectData]
    global_search: GlobalActionProcessor[GlobalSearchProjectsAction, BatchOpsResult[ProjectData]]
    scoped_search: ScopeActionProcessor[
        ScopedSearchProjectsAction, ScopedBatchOpsResult[ProjectData]
    ]
    create_project: ScopeActionProcessor[CreateProjectAction, CreatedEntityOpsResult[ProjectData]]
    delete_project: SingleEntityActionProcessor[DeleteProjectAction, EntityOpsResult[ProjectData]]
    restore_project: SingleEntityActionProcessor[RestoreProjectAction, EntityOpsResult[ProjectData]]
    update_project: SingleEntityActionProcessor[UpdateProjectAction, UpdateProjectActionResult]
    purge_project: SingleEntityActionProcessor[PurgeProjectAction, PurgeProjectActionResult]
    partial_bulk_update: PartialBulkActionProcessor[PartialBulkUpdateProjectsAction, ProjectData]
    partial_bulk_delete: PartialBulkActionProcessor[PartialBulkDeleteProjectsAction, ProjectData]
    partial_bulk_restore: PartialBulkActionProcessor[PartialBulkRestoreProjectsAction, ProjectData]
    usage_per_month: GlobalActionProcessor[UsagePerMonthAction, UsagePerMonthActionResult]
    usage_per_period: GlobalActionProcessor[UsagePerPeriodAction, UsagePerPeriodActionResult]
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
        relation_group: RelationGroup,
        group_service: ProjectService,
    ) -> None:
        self.switch_default_registry = relation_group.relation(
            SwitchProjectDefaultRegistryAction, group_service.switch_default_registry
        )
        self.clear_default_registry = relation_group.relation(
            ClearProjectDefaultRegistryAction, group_service.clear_default_registry
        )
        self.lookup = group.public_lookup_ops(LookupProjectAction)
        self.get_project = group.single_get_ops(GetProjectAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetProjectsAction)
        self.global_search = group.global_searcher_ops(GlobalSearchProjectsAction)
        self.scoped_search = group.scoped_search_ops(ScopedSearchProjectsAction)
        self.create_project = group.scope(CreateProjectAction, group_service.create_project)
        self.delete_project = group.single_delete_ops(DeleteProjectAction)
        self.restore_project = group.single_restore_ops(RestoreProjectAction)
        self.update_project = group.single_entity(UpdateProjectAction, group_service.update_group)
        self.purge_project = group.single_entity(PurgeProjectAction, group_service.purge_group)
        self.partial_bulk_update = group.partial_bulk(
            PartialBulkUpdateProjectsAction, group_service.partial_bulk_update
        )
        self.partial_bulk_delete = group.partial_bulk_delete_ops(PartialBulkDeleteProjectsAction)
        self.partial_bulk_restore = group.partial_bulk_restore_ops(PartialBulkRestoreProjectsAction)
        self.usage_per_month = group.global_scope(
            UsagePerMonthAction, group_service.usage_per_month
        )
        self.usage_per_period = group.global_scope(
            UsagePerPeriodAction, group_service.usage_per_period
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
