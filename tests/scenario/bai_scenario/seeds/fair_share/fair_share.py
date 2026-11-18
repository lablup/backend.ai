"""Write specs for the fair share state the scheduler keeps per resource group."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.fair_share.upserters import (
    DomainFairShareUpserter,
    ProjectFairShareUpserter,
    UserFairShareUpserter,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.scenario_steps import Language, Says
from bai_scenario.seeds.seeder import TestSeedDanglingFieldUpserter


@dataclass(frozen=True)
class FairShareState:
    """The weight the operator set and what the scheduler last calculated."""

    weight: Decimal = Decimal("2.5")
    half_life_days: int = 14
    lookback_days: int = 56
    decay_unit_days: int = 2
    fair_share_factor: Decimal = Decimal("0.5")
    total_decayed_usage: ResourceSlot = field(
        default_factory=lambda: ResourceSlot({"cpu": Decimal("4")})
    )
    normalized_usage: Decimal = Decimal("0.25")
    lookback_start: date = date(2026, 1, 1)
    lookback_end: date = date(2026, 2, 26)

    def describe(self) -> Says:
        return Says(
            (
                f"가중치 {self.weight}, 반감기 {self.half_life_days}일, 돌아볼 기간 "
                f"{self.lookback_days}일, 감쇠 단위 {self.decay_unit_days}일, 계산된 factor "
                f"{self.fair_share_factor}"
            ),
            english=(
                f"weight {self.weight}, half life {self.half_life_days} days, lookback "
                f"{self.lookback_days} days, decay unit {self.decay_unit_days} days, calculated "
                f"factor {self.fair_share_factor}"
            ),
        )

    def columns(self) -> dict[str, Any]:
        return {
            "weight": TriState.update(self.weight),
            "half_life_days": OptionalState.update(self.half_life_days),
            "lookback_days": OptionalState.update(self.lookback_days),
            "decay_unit_days": OptionalState.update(self.decay_unit_days),
            "fair_share_factor": OptionalState.update(self.fair_share_factor),
            "total_decayed_usage": OptionalState.update(self.total_decayed_usage),
            "normalized_usage": OptionalState.update(self.normalized_usage),
            "lookback_start": OptionalState.update(self.lookback_start),
            "lookback_end": OptionalState.update(self.lookback_end),
        }


@dataclass(frozen=True)
class TestSeedDomainFairShare(
    TestSeedDanglingFieldUpserter[ResourceGroupData, DomainFairShareData]
):
    """The fair share state of one domain in the resource group."""

    domain_name: str
    state: FairShareState = field(default_factory=FairShareState)

    @override
    def kind(self) -> str:
        described = self.state.describe()
        return Says(
            f"도메인 {self.domain_name}의 fair share: {described}",
            english=f"fair share of domain {self.domain_name}: {described.in_(Language.ENGLISH)}",
        )

    @override
    def owner_id(self, owner: ResourceGroupData) -> ResourceGroupData:
        return owner

    @override
    def seed(self, owner_id: ResourceGroupData) -> DomainFairShareUpserter:
        return DomainFairShareUpserter(
            resource_group=owner_id.name,
            resource_group_id=owner_id.id,
            domain_name=self.domain_name,
            **self.state.columns(),
        )


@dataclass(frozen=True)
class TestSeedProjectFairShare(
    TestSeedDanglingFieldUpserter[ResourceGroupData, ProjectFairShareData]
):
    """The fair share state of one project in the resource group."""

    project_name: str
    project_id: uuid.UUID
    domain_name: str
    state: FairShareState = field(default_factory=FairShareState)

    @override
    def kind(self) -> str:
        described = self.state.describe()
        return Says(
            f"프로젝트 {self.project_name}의 fair share: {described}",
            english=f"fair share of project {self.project_name}: {described.in_(Language.ENGLISH)}",
        )

    @override
    def owner_id(self, owner: ResourceGroupData) -> ResourceGroupData:
        return owner

    @override
    def seed(self, owner_id: ResourceGroupData) -> ProjectFairShareUpserter:
        return ProjectFairShareUpserter(
            resource_group=owner_id.name,
            resource_group_id=owner_id.id,
            project_id=self.project_id,
            domain_name=self.domain_name,
            **self.state.columns(),
        )


@dataclass(frozen=True)
class TestSeedUserFairShare(TestSeedDanglingFieldUpserter[ResourceGroupData, UserFairShareData]):
    """The fair share state of one user within one project in the resource group."""

    username: str
    user_uuid: uuid.UUID
    project_name: str
    project_id: uuid.UUID
    domain_name: str
    state: FairShareState = field(default_factory=FairShareState)

    @override
    def kind(self) -> str:
        described = self.state.describe()
        return Says(
            f"프로젝트 {self.project_name} 안 사용자 {self.username}의 fair share: {described}",
            english=(
                f"fair share of user {self.username} in project {self.project_name}: "
                f"{described.in_(Language.ENGLISH)}"
            ),
        )

    @override
    def owner_id(self, owner: ResourceGroupData) -> ResourceGroupData:
        return owner

    @override
    def seed(self, owner_id: ResourceGroupData) -> UserFairShareUpserter:
        return UserFairShareUpserter(
            resource_group=owner_id.name,
            resource_group_id=owner_id.id,
            user_uuid=self.user_uuid,
            project_id=self.project_id,
            domain_name=self.domain_name,
            **self.state.columns(),
        )
