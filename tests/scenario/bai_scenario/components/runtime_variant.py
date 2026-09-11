"""What a runtime variant scenario table says besides the call.

A variant is created in no scope and reached afterwards by id or by name. A table needs
the caller, and the variant or variants the call reads. The presets a variant owns have
tables of their own.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.runtime_variant.runtime_variant import SeedRuntimeVariant

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    DeleteRuntimeVariantPayload,
    DeleteRuntimeVariantsPayload,
    RuntimeVariantModelDefinitionInfo,
    RuntimeVariantNode,
    SearchRuntimeVariantsPayload,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)

DESCRIBED = "심어둔 런타임 변형"
"""시드가 심는 변형의 설명. 시나리오가 기대값으로 다시 쓰므로 한 자리에 둔다."""

FIXED_MODEL_DEFINITION = RuntimeVariantModelDefinitionInfo.model_validate(
    DefaultModelDefinition(), from_attributes=True
)
"""만들기가 못박는 모델 정의. 요청은 이 값을 줄 수 없다."""


@dataclass(frozen=True)
class AVariantAndACaller:
    """변형 하나와, 그것을 부를 사람."""

    variant: RuntimeVariantData
    caller: UserData


@dataclass(frozen=True)
class ManyVariantsAndACaller:
    """훑을 변형 여럿과, 훑을 사람. ``named``는 그중 골라낼 하나다."""

    laid: tuple[RuntimeVariantData, ...]
    named: RuntimeVariantData
    caller: UserData


@dataclass(frozen=True)
class AVariantAndSomeone(Given[Any, AVariantAndACaller]):
    """변형 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    described: str | None = DESCRIBED

    @override
    def describe(self) -> str:
        return f"런타임 변형 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> AVariantAndACaller:
        variant = await seeding.creating(SeedRuntimeVariant(description=self.described))
        caller = await lay_a_caller(seeding, self.role)
        return AVariantAndACaller(seeding.made(variant), seeding.made(caller))


@dataclass(frozen=True)
class ManyVariantsAndSomeone(Given[Any, ManyVariantsAndACaller]):
    """변형 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"런타임 변형 {self.besides + 1}개와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyVariantsAndACaller:
        wanted = await seeding.creating(SeedRuntimeVariant(name_hint="wanted"))
        others = [
            await seeding.creating(SeedRuntimeVariant(name_hint="other"))
            for _ in range(self.besides)
        ]
        caller = await lay_a_caller(seeding, self.role)
        return ManyVariantsAndACaller(
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


def variant_verdicts(
    at: str,
    node: RuntimeVariantNode,
    *,
    named: str,
    described: str | None,
    written: WrittenByThisRun,
) -> list[Verdict]:
    """Every place of one variant node, prefixed for a node inside a list."""
    return [
        Skipped(f"{at}id", "데이터베이스가 만든다"),
        Same(f"{at}name", node.name, named),
        Same(f"{at}description", node.description, described),
        Same(f"{at}reads_vfolder_config_files", node.reads_vfolder_config_files, False),
        Same(
            f"{at}default_model_definition", node.default_model_definition, FIXED_MODEL_DEFINITION
        ),
        Held(f"{at}created_at", node.created_at, written),
        Held(f"{at}updated_at", node.updated_at, written),
    ]


@dataclass(frozen=True)
class TheNewVariantNode(Then[Any, RuntimeVariantNode]):
    """방금 만든 변형이 통째로 온다. 이름과 설명은 시나리오가 정한 것이다."""

    started: datetime
    named: str
    described: str | None

    @override
    def says(self) -> str:
        return "만든 변형 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[RuntimeVariantNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return variant_verdicts(
            "",
            node,
            named=self.named,
            described=self.described,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheVariantNode(Then[AVariantAndACaller, RuntimeVariantNode]):
    """심은 변형이 통째로 온다. 바꾸는 요청은 바뀌어야 하는 자리만 인자로 준다."""

    started: datetime
    named: str | Kept = KEPT
    described: str | None | Kept = KEPT

    @override
    def says(self) -> str:
        return "심은 변형 전체가 온다"

    @override
    def look(
        self, laid: AVariantAndACaller, answered: Answered[RuntimeVariantNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        named = laid.variant.name if isinstance(self.named, Kept) else self.named
        described = laid.variant.description if isinstance(self.described, Kept) else self.described
        return variant_verdicts(
            "", node, named=named, described=described, written=WrittenByThisRun(self.started)
        )


@dataclass(frozen=True)
class EveryLaidVariantIsCounted(Then[ManyVariantsAndACaller, SearchRuntimeVariantsPayload]):
    """심은 것이 모두 세어진다."""

    @override
    def says(self) -> str:
        return "심은 변형이 모두 세어진다"

    @override
    def look(
        self, laid: ManyVariantsAndACaller, answered: Answered[SearchRuntimeVariantsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.name for one in page.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedVariantIsLeft(Then[ManyVariantsAndACaller, SearchRuntimeVariantsPayload]):
    """걸러낸 그 하나만 남는다."""

    @override
    def says(self) -> str:
        return "걸러낸 그 변형 하나만 남는다"

    @override
    def look(
        self, laid: ManyVariantsAndACaller, answered: Answered[SearchRuntimeVariantsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("items", [one.name for one in page.items], [laid.named.name]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheFirstPageOfVariants(Then[ManyVariantsAndACaller, SearchRuntimeVariantsPayload]):
    """크기를 대지 않은 첫 쪽. 기본 크기만큼 오고 다음 쪽이 있다고 답한다."""

    size: int

    @override
    def says(self) -> str:
        return "기본 크기의 첫 쪽이 온다"

    @override
    def look(
        self, laid: ManyVariantsAndACaller, answered: Answered[SearchRuntimeVariantsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("len(items)", len(page.items), self.size),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheVariantsInTheOrderAsked(
    Then[ManyVariantsAndACaller, list[RuntimeVariantNode | Exception | None]]
):
    """준 순서대로 한 자리씩 온다. 심은 것은 노드로, 없는 id는 빈 자리로."""

    started: datetime

    @override
    def says(self) -> str:
        return "준 순서대로, 없는 id 자리는 비어서 온다"

    @override
    def look(
        self,
        laid: ManyVariantsAndACaller,
        answered: Answered[list[RuntimeVariantNode | Exception | None]],
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        for i, expected in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if not isinstance(got, RuntimeVariantNode):
                seen.append(Same(f"items[{i}]", got, "노드"))
                continue
            seen.extend(
                variant_verdicts(
                    f"items[{i}].",
                    got,
                    named=expected.name,
                    described=expected.description,
                    written=written,
                )
            )
        last = items[asked - 1] if len(items) >= asked else "없음"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class TheDeletedVariantId(Then[AVariantAndACaller, DeleteRuntimeVariantPayload]):
    """지운 변형의 id를 실은 답."""

    @override
    def says(self) -> str:
        return "지운 변형의 id가 온다"

    @override
    def look(
        self, laid: AVariantAndACaller, answered: Answered[DeleteRuntimeVariantPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held[UUID]("id", payload.id, SameAs[UUID](laid.variant.id, "심은 변형"))]


@dataclass(frozen=True)
class TheCountAsked(Then[ManyVariantsAndACaller, DeleteRuntimeVariantsPayload]):
    """요청한 id의 수를 그대로 답한다."""

    @override
    def says(self) -> str:
        return "요청한 id의 수가 온다"

    @override
    def look(
        self, laid: ManyVariantsAndACaller, answered: Answered[DeleteRuntimeVariantsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("deleted_count", payload.deleted_count, len(laid.laid))]
