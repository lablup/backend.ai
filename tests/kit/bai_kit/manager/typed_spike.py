"""What the type checker catches on the typed surface, written as checked mistakes.

Every ``type: ignore`` below is a mistake the text-keyed surface accepts silently. This
repository runs mypy in strict mode, where an ignore that catches nothing is itself an
error — so this file passing is the evidence that each mistake is caught, and each
mistake left without an ignore is the evidence that it is not.

The mistakes are written inside a scenario table on purpose. An accessor's parameter
type comes from the position it sits in, so the same expression is checked in the table
and unchecked when written on its own.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.manager.errors.auth import InsufficientPrivilege
from bai_kit.manager.typed import (
    TypedScenario,
    TypedSetup,
    all_of_typed,
    at,
    config_of,
    every,
    holds,
    op,
)

manager_config = config_of(ManagerUnifiedConfig)

# The operations this domain exposes, bound from the adapter's own methods.
get_domain = op(DomainAdapter.get)
create_domain = op(DomainAdapter.admin_create)
search_domains = op(DomainAdapter.admin_search)
delete_domain = op(DomainAdapter.admin_delete)

type DomainScenario = TypedScenario[DomainAdapter, ManagerUnifiedConfig]


def _actor() -> UserInfo:
    raise NotImplementedError("supplied by the runner")


# ---------------------------------------------------------------------------
# Accepted: what a scenario table looks like with nothing named as text
# ---------------------------------------------------------------------------

ACCEPTED: list[DomainScenario] = [
    TypedScenario.ok(
        "get-returns-the-named-domain",
        when=get_domain("d1"),
        then=at(lambda node: node.basic_info.name, "d1"),
    ),
    TypedScenario.ok(
        "create-fills-the-node",
        when=create_domain(CreateDomainInput(name="d1"), _actor()),
        then=all_of_typed(
            at(lambda p: p.domain.basic_info.name, "d1"),
            at(lambda p: p.domain.lifecycle.is_active, True),
            holds(lambda p: p.domain.registry.allowed_docker_registries, lambda rs: rs == []),
        ),
    ),
    TypedScenario.ok(
        "search-answers-one-row",
        when=search_domains(AdminSearchDomainsInput()),
        then=all_of_typed(
            at(lambda p: p.total_count, 1),
            every(lambda p: p.items, at(lambda n: n.lifecycle.is_active, True)),
        ),
    ),
    TypedScenario.ok(
        "delete-answers-true",
        when=delete_domain(DeleteDomainInput(name="d1")),
        then=at(lambda p: p.deleted, True),
        setup=TypedSetup(
            config=[manager_config.set(lambda c: c.manager.rbac.enforcement_enabled, False)]
        ),
    ),
    TypedScenario.error(
        "member-is-refused",
        when=create_domain(CreateDomainInput(name="d1"), _actor()),
        then=InsufficientPrivilege,
    ),
]


# ---------------------------------------------------------------------------
# Refused inside the table. Each ignore is the proof that it is refused.
# ---------------------------------------------------------------------------

REFUSED: list[DomainScenario] = [
    TypedScenario.ok(
        "field-that-does-not-exist",
        when=get_domain("d1"),
        then=at(lambda node: node.basic_info.nmae, "d1"),  # type: ignore[attr-defined]
    ),
    TypedScenario.ok(
        "matcher-over-the-wrong-payload",
        # ``admin_delete`` answers a DeleteDomainPayload, which has no ``domain``.
        when=delete_domain(DeleteDomainInput(name="d1")),
        then=at(lambda p: p.domain.basic_info.name, "d1"),  # type: ignore[attr-defined]
    ),
    TypedScenario.ok(
        "expected-of-the-wrong-type",
        when=get_domain("d1"),
        # The value fixes the field type; the accessor is then the mismatch reported.
        then=at(lambda node: node.basic_info.name, 1),  # type: ignore[arg-type, return-value]
    ),
    TypedScenario.ok(
        "config-path-that-does-not-exist",
        when=get_domain("d1"),
        setup=TypedSetup(
            config=[
                manager_config.set(lambda c: c.manager.rbac.enforcment_enabled, False)  # type: ignore[attr-defined]
            ]
        ),
    ),
    TypedScenario.ok(
        "config-value-of-the-wrong-type",
        when=get_domain("d1"),
        setup=TypedSetup(
            config=[
                manager_config.set(lambda c: c.manager.rbac.enforcement_enabled, "no")  # type: ignore[arg-type, return-value]
            ]
        ),
    ),
]


def _misspelled_method() -> None:
    op(DomainAdapter.gett)  # type: ignore[attr-defined]


def _wrong_argument_type() -> None:
    get_domain(123)  # type: ignore[arg-type]


def _missing_argument() -> None:
    create_domain(CreateDomainInput(name="d1"))  # type: ignore[call-arg]


def _wrong_input_dto() -> None:
    create_domain(DeleteDomainInput(name="d1"), _actor())  # type: ignore[arg-type]


def _accessor_written_outside_a_table() -> None:
    """Outside a scenario the accessor's parameter has nothing to bind to, so the field
    name is unchecked. Matchers are always written in ``then=``, so this is a rule about
    where they may be written rather than a hole in the table."""
    at(lambda node: node.basic_info.nmae, "d1")


def _the_node_type_is_what_get_answers(node: DomainNode) -> None:
    """``get`` answers a node, not a payload: the table above reads ``basic_info``
    directly rather than through ``domain``."""
    assert node.basic_info is not None
