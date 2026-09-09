"""The domain scenario table. Two test modules run it: the adapter and the HTTP round trip."""

from __future__ import annotations

from bai_kit.manager.personas import MEMBER
from bai_kit.manager.wiring.domain import create_input, domain_wiring, seed_domain

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DeleteDomainInput,
    DomainFilter,
    PurgeDomainInput,
    RestoreDomainInput,
    UpdateDomainInput,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.testutils.scenario import (
    Call,
    Scenario,
    Setup,
    Step,
    each,
    has,
    snapshot,
)

WIRING = domain_wiring

ENFORCEMENT_OFF = Setup(config={"manager.rbac.enforcement_enabled": False})

SCENARIOS = [
    # --- create ---------------------------------------------------------------
    Scenario.ok(
        "superadmin-creates-domain",
        when=create_input(name="d1", description="first"),
        then=has(
            domain=has(
                basic_info=has(name="d1", description="first"),
                lifecycle=has(is_active=True, is_default=False),
                registry=has(allowed_docker_registries=[]),
            )
        ),
    ),
    Scenario.error(
        "create-rejects-duplicate-name",
        given=[seed_domain("dup")],
        when=create_input(name="dup"),
        then=(InvalidAPIParameters, "already exists"),
    ),
    Scenario.error(
        "create-rejects-blank-name",
        when=create_input(name="   "),
        then=InvalidAPIParameters,
    ),
    Scenario.error(
        "member-cannot-create-domain",
        actor=MEMBER,
        when=create_input(name="d2"),
        then=InsufficientPrivilege,
    ),
    Scenario.error(
        "enforcement-off-still-blocks-member-create",
        actor=MEMBER,
        setup=ENFORCEMENT_OFF,
        when=create_input(name="d3"),
        then=InsufficientPrivilege,
    ),
    # --- get ------------------------------------------------------------------
    Scenario.ok(
        "superadmin-gets-domain-by-name",
        given=[seed_domain("d-get", description="to read")],
        when=Call("get", "d-get"),
        then=has(basic_info=has(name="d-get", description="to read")),
    ),
    Scenario.error(
        "get-unknown-domain-is-not-found",
        when=Call("get", "no-such-domain"),
        then=EntityNotFoundError,
    ),
    Scenario.error(
        "member-cannot-get-foreign-domain",
        actor=MEMBER,
        given=[seed_domain("d-foreign")],
        when=Call("get", "d-foreign"),
        then=NotEnoughPermission,
    ),
    Scenario.ok(
        "enforcement-off-lets-member-get-domain",
        actor=MEMBER,
        setup=ENFORCEMENT_OFF,
        given=[seed_domain("d-open")],
        when=Call("get", "d-open"),
        then=has(basic_info=has(name="d-open")),
    ),
    # --- search ---------------------------------------------------------------
    Scenario.ok(
        "superadmin-sees-only-the-world-domain",
        when=AdminSearchDomainsInput(),
        then=has(total_count=1, items=each(has(basic_info=has(name="default")))),
    ),
    Scenario.ok(
        "search-filters-by-exact-name",
        given=[seed_domain("alpha"), seed_domain("beta")],
        when=AdminSearchDomainsInput(filter=DomainFilter(name=StringFilter(equals="alpha"))),
        then=has(total_count=1, items=each(has(basic_info=has(name="alpha")))),
    ),
    Scenario.error(
        "member-cannot-search-domains",
        actor=MEMBER,
        when=AdminSearchDomainsInput(),
        then=InsufficientPrivilege,
    ),
    # --- update ---------------------------------------------------------------
    Scenario.ok(
        "superadmin-updates-description",
        given=[seed_domain("d-upd")],
        when=Call("admin_update", "d-upd", UpdateDomainInput(description="edited")),
        then=has(domain=has(basic_info=has(name="d-upd", description="edited"))),
    ),
    Scenario.ok(
        "update-deactivates-domain",
        given=[seed_domain("d-off")],
        when=Call("admin_update", "d-off", UpdateDomainInput(is_active=False)),
        then=has(domain=has(lifecycle=has(is_active=False))),
    ),
    Scenario.error(
        "member-cannot-update-domain",
        actor=MEMBER,
        given=[seed_domain("d-locked")],
        when=Call("admin_update", "d-locked", UpdateDomainInput(description="x")),
        then=NotEnoughPermission,
    ),
    Scenario.ok(
        "enforcement-off-lets-member-update-domain",
        actor=MEMBER,
        setup=ENFORCEMENT_OFF,
        given=[seed_domain("d-open-upd")],
        when=Call("admin_update", "d-open-upd", UpdateDomainInput(description="by member")),
        then=has(domain=has(basic_info=has(description="by member"))),
        # The route is superadmin_required: over HTTP the member never reaches the adapter.
        variants={"http": InsufficientPrivilege},
    ),
    # --- delete / restore / purge --------------------------------------------
    Scenario.ok(
        "superadmin-soft-deletes-domain",
        given=[seed_domain("d-del")],
        when=DeleteDomainInput(name="d-del"),
        then=has(deleted=True),
    ),
    Scenario.error(
        "member-cannot-delete-domain",
        actor=MEMBER,
        given=[seed_domain("d-keep")],
        when=DeleteDomainInput(name="d-keep"),
        then=NotEnoughPermission,
    ),
    Scenario.ok(
        "enforcement-off-lets-member-delete-domain",
        actor=MEMBER,
        setup=ENFORCEMENT_OFF,
        given=[seed_domain("d-open-del")],
        when=DeleteDomainInput(name="d-open-del"),
        then=has(deleted=True),
        variants={"http": InsufficientPrivilege},
    ),
    Scenario.flow(
        "delete-then-restore-reactivates",
        given=[seed_domain("d-flow")],
        steps=[
            Step(DeleteDomainInput(name="d-flow"), has(deleted=True)),
            Step(Call("get", "d-flow"), has(lifecycle=has(is_active=False))),
            Step(RestoreDomainInput(name="d-flow"), has(restored=True)),
            Step(Call("get", "d-flow"), has(lifecycle=has(is_active=True))),
        ],
    ),
    Scenario.flow(
        "purge-removes-domain",
        given=[seed_domain("d-purge")],
        steps=[
            Step(PurgeDomainInput(name="d-purge"), has(purged=True)),
            Step(Call("get", "d-purge"), EntityNotFoundError),
        ],
    ),
    # --- then alternative: snapshot ------------------------------------------
    Scenario.ok(
        "create-domain-snapshot",
        when=create_input(name="snap"),
        then=snapshot(
            {
                "domain": {
                    "basic_info": {"name": "snap", "description": None, "integration_name": None},
                    "registry": {"allowed_docker_registries": []},
                    "lifecycle": {"is_active": True, "is_default": False},
                }
            },
            volatile=("domain.id", "domain.lifecycle.created_at", "domain.lifecycle.modified_at"),
        ),
    ),
]
