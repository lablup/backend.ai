"""Retiring, restoring and purging a domain."""

from __future__ import annotations

import pytest
from bai_kit.manager.personas import MEMBER, OTHER_MEMBER
from bai_kit.manager.typed_runner import TypedRunner
from bai_kit.manager.wiring.domain import (
    DomainScenario,
    admin_delete,
    admin_purge,
    admin_restore,
    already_there,
)

from ai.backend.common.dto.manager.v2.domain.request import (
    DeleteDomainInput,
    PurgeDomainInput,
    RestoreDomainInput,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
    at,
)

SCENARIOS: list[DomainScenario] = [
    TypedScenario.ok(
        "superadmin-retires-a-domain",
        given=[already_there("to-delete")],
        when=admin_delete(DeleteDomainInput(name="to-delete")),
        then=at(lambda p: p.deleted, True),
    ),
    TypedScenario.ok(
        "restoring-answers-that-it-restored",
        given=[already_there("to-restore")],
        when=admin_restore(RestoreDomainInput(name="to-restore")),
        then=at(lambda p: p.restored, True),
    ),
    TypedScenario.ok(
        "purging-a-domain-nothing-else-refers-to-succeeds",
        given=[already_there("to-purge")],
        when=admin_purge(PurgeDomainInput(name="to-purge")),
        then=at(lambda p: p.purged, True),
    ),
    TypedScenario.error(
        "retiring-a-name-nothing-answers-to-is-not-found",
        when=admin_delete(DeleteDomainInput(name="no-such-domain")),
        then=EntityNotFoundError,
    ),
    TypedScenario.error(
        "a-member-may-not-retire-a-domain",
        actor=MEMBER,
        given=[already_there("member-cannot-delete")],
        when=admin_delete(DeleteDomainInput(name="member-cannot-delete")),
        then=NotEnoughPermission,
    ),
    TypedScenario.error(
        "a-member-outside-everything-may-not-purge-a-domain",
        actor=OTHER_MEMBER,
        given=[already_there("stranger-cannot-purge")],
        when=admin_purge(PurgeDomainInput(name="stranger-cannot-purge")),
        then=NotEnoughPermission,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
async def test_retiring(scenario: DomainScenario, run: TypedRunner) -> None:
    await run(scenario)
