"""What the model card adapter does, said as a request, an actor, and an answer.

A model card lives in a project, so the personas divide by the seat they hold: the
member is on the shared project's roster and the other member is not.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from bai_scenario.infra.personas import DOMAIN_ADMIN, MEMBER, OTHER_MEMBER
from bai_scenario.runner.runner import ScenarioRunner

from ai.backend.common.dto.manager.v2.model_card.request import SearchModelCardsInput
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
    at,
    call,
)

type ModelCardScenario = TypedScenario[ModelCardAdapter, ManagerUnifiedConfig]

SCENARIOS: list[ModelCardScenario] = [
    TypedScenario.ok(
        "an-untouched-world-holds-no-model-cards",
        when=call(ModelCardAdapter.admin_search, SearchModelCardsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.error(
        "reading-a-card-nothing-answers-to-is-not-found",
        when=call(ModelCardAdapter.get, UUID(int=0)),
        then=EntityNotFoundError,
    ),
    TypedScenario.error(
        "a-member-may-not-search-every-model-card",
        actor=MEMBER,
        when=call(ModelCardAdapter.admin_search, SearchModelCardsInput()),
        then=InsufficientPrivilege,
    ),
    TypedScenario.error(
        "the-domain-admin-may-not-search-every-model-card-either",
        actor=DOMAIN_ADMIN,
        when=call(ModelCardAdapter.admin_search, SearchModelCardsInput()),
        then=InsufficientPrivilege,
    ),
    TypedScenario.error(
        "a-member-outside-the-project-may-not-search-every-model-card",
        actor=OTHER_MEMBER,
        when=call(ModelCardAdapter.admin_search, SearchModelCardsInput()),
        then=InsufficientPrivilege,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_model_card(scenario: ModelCardScenario, run: ScenarioRunner) -> None:
    await run(scenario)
