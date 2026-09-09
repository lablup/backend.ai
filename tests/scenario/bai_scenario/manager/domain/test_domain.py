"""Domain scenarios through the transport-agnostic adapter."""

from __future__ import annotations

from typing import Any

import pytest
from bai_kit.manager.wiring.domain import domain_wiring
from bai_scenario.manager.domain.scenarios import SCENARIOS

from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.scenario import Call, Runner, Scenario, has, scenario_id

WIRING = domain_wiring


@pytest.mark.parametrize("s", SCENARIOS, ids=scenario_id)
async def test_domain(s: Scenario, run: Runner) -> None:
    await run(s)


# --- given, alternative 2: a pytest fixture instead of a lazy seed --------------------
# The row lands the same way; what differs is where the reader looks. A fixture is
# shared by name across tests and hides which scenario needs it; a Seed sits on the
# scenario line. Kept as one example for the comparison.


@pytest.fixture
async def fixture_domain(engine: Any) -> DomainData:
    ops: OpsRepository[Any] = OpsRepository(V2DBOpsProvider(engine))
    data: DomainData = await ops.create_role_managed_global_entity(DomainCreator(name="fx-domain"))
    return data


async def test_get_with_fixture_given(fixture_domain: DomainData, run: Runner) -> None:
    await run(
        Scenario.ok(
            "fixture-given",
            when=Call("get", "fx-domain"),
            then=has(basic_info=has(name="fx-domain")),
        )
    )
