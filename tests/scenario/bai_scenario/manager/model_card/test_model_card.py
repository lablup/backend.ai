"""Model card scenarios: the second domain the adapter runner was tried on."""

from __future__ import annotations

from uuid import UUID

import pytest
from bai_kit.manager.personas import MEMBER
from bai_kit.manager.wiring.model_card import model_card_wiring

from ai.backend.common.dto.manager.v2.model_card.request import SearchModelCardsInput
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.testutils.scenario import Call, Runner, Scenario, has, length, scenario_id

WIRING = model_card_wiring

SCENARIOS = [
    Scenario.ok(
        "an-empty-world-holds-no-model-cards",
        when=SearchModelCardsInput(),
        then=has(items=length(0), total_count=0),
    ),
    Scenario.error(
        "member-cannot-search-every-model-card",
        actor=MEMBER,
        when=SearchModelCardsInput(),
        then=InsufficientPrivilege,
    ),
    Scenario.error(
        "get-unknown-card-is-not-found",
        when=Call("get", UUID(int=0)),
        then=EntityNotFoundError,
    ),
]


@pytest.mark.parametrize("s", SCENARIOS, ids=scenario_id)
async def test_model_card(s: Scenario, run: Runner) -> None:
    await run(s)
