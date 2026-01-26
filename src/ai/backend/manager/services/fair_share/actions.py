"""Actions and results for Fair Share Service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder, QueryPagination

# Domain Fair Share


@dataclass
class DomainFairShareAction(BaseAction):
    """Base action for domain fair share operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "domain_fair_share"


@dataclass
class GetDomainFairShareAction(DomainFairShareAction):
    """Action to get a domain fair share record."""

    resource_group: str
    domain_name: str

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:{self.domain_name}"


@dataclass
class GetDomainFairShareActionResult(BaseActionResult):
    """Result of getting a domain fair share record."""

    data: DomainFairShareData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)


@dataclass
class SearchDomainFairSharesAction(DomainFairShareAction):
    """Action to search domain fair shares."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchDomainFairSharesActionResult(BaseActionResult):
    """Result of searching domain fair shares."""

    items: list[DomainFairShareData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None


# Project Fair Share


@dataclass
class ProjectFairShareAction(BaseAction):
    """Base action for project fair share operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "project_fair_share"


@dataclass
class GetProjectFairShareAction(ProjectFairShareAction):
    """Action to get a project fair share record."""

    resource_group: str
    project_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:{self.project_id}"


@dataclass
class GetProjectFairShareActionResult(BaseActionResult):
    """Result of getting a project fair share record."""

    data: ProjectFairShareData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)


@dataclass
class SearchProjectFairSharesAction(ProjectFairShareAction):
    """Action to search project fair shares."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchProjectFairSharesActionResult(BaseActionResult):
    """Result of searching project fair shares."""

    items: list[ProjectFairShareData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None


# User Fair Share


@dataclass
class UserFairShareAction(BaseAction):
    """Base action for user fair share operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "user_fair_share"


@dataclass
class GetUserFairShareAction(UserFairShareAction):
    """Action to get a user fair share record."""

    resource_group: str
    project_id: uuid.UUID
    user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:{self.project_id}:{self.user_uuid}"


@dataclass
class GetUserFairShareActionResult(BaseActionResult):
    """Result of getting a user fair share record."""

    data: UserFairShareData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)


@dataclass
class SearchUserFairSharesAction(UserFairShareAction):
    """Action to search user fair shares."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchUserFairSharesActionResult(BaseActionResult):
    """Result of searching user fair shares."""

    items: list[UserFairShareData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None


# Upsert Actions for Fair Share Weight


@dataclass
class UpsertDomainFairShareWeightAction(DomainFairShareAction):
    """Action to upsert a domain fair share weight."""

    resource_group: str
    domain_name: str
    weight: Decimal | None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "upsert_weight"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:{self.domain_name}"


@dataclass
class UpsertDomainFairShareWeightActionResult(BaseActionResult):
    """Result of upserting a domain fair share weight."""

    data: DomainFairShareData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)


@dataclass
class UpsertProjectFairShareWeightAction(ProjectFairShareAction):
    """Action to upsert a project fair share weight."""

    resource_group: str
    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "upsert_weight"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:{self.project_id}"


@dataclass
class UpsertProjectFairShareWeightActionResult(BaseActionResult):
    """Result of upserting a project fair share weight."""

    data: ProjectFairShareData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)


@dataclass
class UpsertUserFairShareWeightAction(UserFairShareAction):
    """Action to upsert a user fair share weight."""

    resource_group: str
    project_id: uuid.UUID
    user_uuid: uuid.UUID
    domain_name: str
    weight: Decimal | None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "upsert_weight"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:{self.project_id}:{self.user_uuid}"


@dataclass
class UpsertUserFairShareWeightActionResult(BaseActionResult):
    """Result of upserting a user fair share weight."""

    data: UserFairShareData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)


# Bulk Upsert Actions for Fair Share Weight


@dataclass
class DomainWeightInput:
    """Input for a single domain weight in bulk upsert."""

    domain_name: str
    weight: Decimal | None


@dataclass
class BulkUpsertDomainFairShareWeightAction(DomainFairShareAction):
    """Action to bulk upsert domain fair share weights."""

    resource_group: str
    inputs: list[DomainWeightInput]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "bulk_upsert_weight"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:[{len(self.inputs)} domains]"


@dataclass
class BulkUpsertDomainFairShareWeightActionResult(BaseActionResult):
    """Result of bulk upserting domain fair share weights."""

    upserted_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return f"[{self.upserted_count} domains]"


@dataclass
class ProjectWeightInput:
    """Input for a single project weight in bulk upsert."""

    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None


@dataclass
class BulkUpsertProjectFairShareWeightAction(ProjectFairShareAction):
    """Action to bulk upsert project fair share weights."""

    resource_group: str
    inputs: list[ProjectWeightInput]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "bulk_upsert_weight"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:[{len(self.inputs)} projects]"


@dataclass
class BulkUpsertProjectFairShareWeightActionResult(BaseActionResult):
    """Result of bulk upserting project fair share weights."""

    upserted_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return f"[{self.upserted_count} projects]"


@dataclass
class UserWeightInput:
    """Input for a single user weight in bulk upsert."""

    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None


@dataclass
class BulkUpsertUserFairShareWeightAction(UserFairShareAction):
    """Action to bulk upsert user fair share weights."""

    resource_group: str
    inputs: list[UserWeightInput]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "bulk_upsert_weight"

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.resource_group}:[{len(self.inputs)} users]"


@dataclass
class BulkUpsertUserFairShareWeightActionResult(BaseActionResult):
    """Result of bulk upserting user fair share weights."""

    upserted_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return f"[{self.upserted_count} users]"
