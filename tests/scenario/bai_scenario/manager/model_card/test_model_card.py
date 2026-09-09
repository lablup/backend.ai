"""What the model card adapter does, said as a request, an actor, and an answer.

A model card lives in a project, so the personas divide by the seat they hold: the
member is on the shared project's roster and the other member is not.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from bai_kit.manager.config import base_config_dict
from bai_kit.manager.db import TemplateDatabase
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.personas import DOMAIN_ADMIN, MEMBER, OTHER_MEMBER
from bai_kit.manager.typed_runner import TypedRunner
from bai_kit.manager.wiring.model_card import (
    get_model_card,
    model_card_wiring,
    search_model_cards,
)

from ai.backend.common.dto.manager.v2.model_card.request import SearchModelCardsInput
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.testutils.typed_scenario import TypedScenario, at

type ModelCardScenario = TypedScenario[ModelCardAdapter, ManagerUnifiedConfig]

SCENARIOS: list[ModelCardScenario] = [
    TypedScenario.ok(
        "an-untouched-world-holds-no-model-cards",
        when=search_model_cards(SearchModelCardsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.error(
        "reading-a-card-nothing-answers-to-is-not-found",
        when=get_model_card(UUID(int=0)),
        then=EntityNotFoundError,
    ),
    TypedScenario.error(
        "a-member-may-not-search-every-model-card",
        actor=MEMBER,
        when=search_model_cards(SearchModelCardsInput()),
        then=InsufficientPrivilege,
    ),
    TypedScenario.error(
        "the-domain-admin-may-not-search-every-model-card-either",
        actor=DOMAIN_ADMIN,
        when=search_model_cards(SearchModelCardsInput()),
        then=InsufficientPrivilege,
    ),
    TypedScenario.error(
        "a-member-outside-the-project-may-not-search-every-model-card",
        actor=OTHER_MEMBER,
        when=search_model_cards(SearchModelCardsInput()),
        then=InsufficientPrivilege,
    ),
]


@pytest.fixture
def run(
    world_template: TemplateDatabase,
    test_db: str,
    engine: Any,
    recorder: ActionRecorder,
) -> TypedRunner:
    return TypedRunner(
        wiring=model_card_wiring,
        engine=engine,
        world=world_template.world,
        base_config=base_config_dict(world_template.addr, test_db, None),
        recorder=recorder,
    )


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
async def test_model_card(scenario: ModelCardScenario, run: TypedRunner) -> None:
    await run(scenario)
