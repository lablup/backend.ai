"""Actions and results for Fair Share Service.

A fair share row keys on the pair (resource group, entity) and has no id of its own,
so nothing here names an entity: every operation happens inside a resource group, and
the reads that span resource groups are global.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.fair_share import (
    DOMAIN_FAIR_SHARE_ENTITY_TYPE,
    PROJECT_FAIR_SHARE_ENTITY_TYPE,
    USER_FAIR_SHARE_ENTITY_TYPE,
)
from ai.backend.common.data.entity.resource_group import (
    RESOURCE_GROUP_SCOPE_TYPE,
    ResourceGroupID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.specs.pagination import QueryPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.fair_share.types import (
    DomainFairShareOperationScope,
    ProjectFairShareOperationScope,
    UserFairShareOperationScope,
)


@dataclass(frozen=True)
class _FairShareScopeResult(BaseScopeActionResult):
    """A fair share row is not an entity, so a run names none."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()


@dataclass(frozen=True)
class DomainFairShareAction(BaseScopeAction):
    """Base for a domain fair share operation, scoped to its resource group."""

    resource_group_id: ResourceGroupID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_FAIR_SHARE_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=self.resource_group_id),)


@dataclass(frozen=True)
class GetDomainFairShareAction(DomainFairShareAction):
    """Read one domain's fair share weight."""

    domain_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_domain_fair_share"


@dataclass(frozen=True)
class GetDomainFairShareActionResult(_FairShareScopeResult):
    data: DomainFairShareData


@dataclass(frozen=True)
class GlobalSearchDomainFairSharesAction(BaseGlobalAction):
    """Page through domain fair shares across every resource group."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_FAIR_SHARE_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_domain_fair_shares"


@dataclass(frozen=True)
class GlobalSearchDomainFairSharesActionResult:
    items: list[DomainFairShareData]
    total_count: int


@dataclass(frozen=True)
class SearchRGDomainFairSharesAction(DomainFairShareAction):
    """Page through the domain fair shares of a resource group, defaults filled in."""

    scope: DomainFairShareOperationScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_domain_fair_shares"


@dataclass(frozen=True)
class SearchRGDomainFairSharesActionResult(_FairShareScopeResult):
    items: list[DomainFairShareData]
    total_count: int


@dataclass(frozen=True)
class UpsertDomainFairShareWeightAction(DomainFairShareAction):
    """Write one domain's fair share weight."""

    resource_group: str
    domain_name: str
    weight: Decimal | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upsert_domain_fair_share_weight"


@dataclass(frozen=True)
class UpsertDomainFairShareWeightActionResult(_FairShareScopeResult):
    data: DomainFairShareData


@dataclass(frozen=True)
class DomainWeightInput:
    """One entry of a bulk weight write."""

    domain_name: str
    weight: Decimal | None


@dataclass(frozen=True)
class BulkUpsertDomainFairShareWeightAction(DomainFairShareAction):
    """Write several domain fair share weights in one resource group."""

    resource_group: str
    inputs: list[DomainWeightInput]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_upsert_domain_fair_share_weights"


@dataclass(frozen=True)
class BulkUpsertDomainFairShareWeightActionResult(_FairShareScopeResult):
    upserted_count: int


@dataclass(frozen=True)
class ProjectFairShareAction(BaseScopeAction):
    """Base for a project fair share operation, scoped to its resource group."""

    resource_group_id: ResourceGroupID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_FAIR_SHARE_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=self.resource_group_id),)


@dataclass(frozen=True)
class GetProjectFairShareAction(ProjectFairShareAction):
    """Read one project's fair share weight."""

    project_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_project_fair_share"


@dataclass(frozen=True)
class GetProjectFairShareActionResult(_FairShareScopeResult):
    data: ProjectFairShareData


@dataclass(frozen=True)
class GlobalSearchProjectFairSharesAction(BaseGlobalAction):
    """Page through project fair shares across every resource group."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_FAIR_SHARE_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_project_fair_shares"


@dataclass(frozen=True)
class GlobalSearchProjectFairSharesActionResult:
    items: list[ProjectFairShareData]
    total_count: int


@dataclass(frozen=True)
class SearchRGProjectFairSharesAction(ProjectFairShareAction):
    """Page through the project fair shares of a resource group, defaults filled in."""

    scope: ProjectFairShareOperationScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_project_fair_shares"


@dataclass(frozen=True)
class SearchRGProjectFairSharesActionResult(_FairShareScopeResult):
    items: list[ProjectFairShareData]
    total_count: int


@dataclass(frozen=True)
class UpsertProjectFairShareWeightAction(ProjectFairShareAction):
    """Write one project's fair share weight."""

    resource_group: str
    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upsert_project_fair_share_weight"


@dataclass(frozen=True)
class UpsertProjectFairShareWeightActionResult(_FairShareScopeResult):
    data: ProjectFairShareData


@dataclass(frozen=True)
class ProjectWeightInput:
    """One entry of a bulk weight write."""

    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None


@dataclass(frozen=True)
class BulkUpsertProjectFairShareWeightAction(ProjectFairShareAction):
    """Write several project fair share weights in one resource group."""

    resource_group: str
    inputs: list[ProjectWeightInput]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_upsert_project_fair_share_weights"


@dataclass(frozen=True)
class BulkUpsertProjectFairShareWeightActionResult(_FairShareScopeResult):
    upserted_count: int


@dataclass(frozen=True)
class UserFairShareAction(BaseScopeAction):
    """Base for a user fair share operation, scoped to its resource group."""

    resource_group_id: ResourceGroupID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_FAIR_SHARE_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=self.resource_group_id),)


@dataclass(frozen=True)
class GetUserFairShareAction(UserFairShareAction):
    """Read one user's fair share weight."""

    project_id: uuid.UUID
    user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_user_fair_share"


@dataclass(frozen=True)
class GetUserFairShareActionResult(_FairShareScopeResult):
    data: UserFairShareData


@dataclass(frozen=True)
class GlobalSearchUserFairSharesAction(BaseGlobalAction):
    """Page through user fair shares across every resource group."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_FAIR_SHARE_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_user_fair_shares"


@dataclass(frozen=True)
class GlobalSearchUserFairSharesActionResult:
    items: list[UserFairShareData]
    total_count: int


@dataclass(frozen=True)
class SearchRGUserFairSharesAction(UserFairShareAction):
    """Page through the user fair shares of a resource group, defaults filled in."""

    scope: UserFairShareOperationScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_fair_shares"


@dataclass(frozen=True)
class SearchRGUserFairSharesActionResult(_FairShareScopeResult):
    items: list[UserFairShareData]
    total_count: int


@dataclass(frozen=True)
class UpsertUserFairShareWeightAction(UserFairShareAction):
    """Write one user's fair share weight."""

    resource_group: str
    project_id: uuid.UUID
    user_uuid: uuid.UUID
    domain_name: str
    weight: Decimal | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upsert_user_fair_share_weight"


@dataclass(frozen=True)
class UpsertUserFairShareWeightActionResult(_FairShareScopeResult):
    data: UserFairShareData


@dataclass(frozen=True)
class UserWeightInput:
    """One entry of a bulk weight write."""

    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None


@dataclass(frozen=True)
class BulkUpsertUserFairShareWeightAction(UserFairShareAction):
    """Write several user fair share weights in one resource group."""

    resource_group: str
    inputs: list[UserWeightInput]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_upsert_user_fair_share_weights"


@dataclass(frozen=True)
class BulkUpsertUserFairShareWeightActionResult(_FairShareScopeResult):
    upserted_count: int
