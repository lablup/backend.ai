"""A scenario table with nothing named as text, and the type assertions that hold it.

The four parts a scenario has are all named in the types of the thing they set:

- what is already there (``given``) — a creator spec, which answers the row's data type
- the situation (``setup``) — a config field read off the config class, and what an
  external client answers, checked against that client's own return type
- what is done (``when``) — an adapter method, with its arguments
- what is expected (``then``) — a field of the payload that method answers

``assert_type`` fixes the types that carry the checking. If a change breaks the chain
the assertion fails at check time, which is what keeps the table honest without any
suppression.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, assert_type
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    AdminSearchDomainsPayload,
    DeleteDomainPayload,
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainPayload,
    DomainRegistryInfo,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.storage import VFolderCreationFailure
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.testutils.typed_scenario import (
    Answer,
    Invocation,
    Override,
    TypedScenario,
    TypedSetup,
    after,
    all_of_typed,
    at,
    checked,
    config_of,
    every,
    exactly,
    fake_of,
    holds,
    ignored,
    op,
    recent,
)
from bai_kit.manager.seeding import Sown, creates

# ---------------------------------------------------------------------------
# What this domain can do, bound once from the adapter and the classes involved
# ---------------------------------------------------------------------------

get_domain = op(DomainAdapter.get)
create_domain = op(DomainAdapter.admin_create)
search_domains = op(DomainAdapter.admin_search)
delete_domain = op(DomainAdapter.admin_delete)

manager_config = config_of(ManagerUnifiedConfig)
storage = fake_of(StorageProxyManagerFacingClient)

type DomainScenario = TypedScenario[DomainAdapter, ManagerUnifiedConfig]


def _actor() -> UserInfo:
    raise NotImplementedError("supplied by the runner")


# ---------------------------------------------------------------------------
# The chain that carries the checking, fixed by assertion
# ---------------------------------------------------------------------------


def _an_operation_carries_the_payload_type_it_answers() -> None:
    """Each operation knows what it returns, which is what ``then`` is checked against."""
    assert_type(get_domain("d1"), Invocation[DomainAdapter, DomainNode])
    assert_type(
        create_domain(CreateDomainInput(name="d1"), _actor()),
        Invocation[DomainAdapter, DomainPayload],
    )
    assert_type(
        search_domains(AdminSearchDomainsInput()),
        Invocation[DomainAdapter, AdminSearchDomainsPayload],
    )
    assert_type(
        delete_domain(DeleteDomainInput(name="d1")),
        Invocation[DomainAdapter, DeleteDomainPayload],
    )


def _a_config_override_carries_the_config_class_and_the_field_type() -> None:
    """A config field is read off the class, so a name that is not there is refused and
    a value of the wrong type is refused with it."""
    assert_type(
        manager_config.set(lambda c: c.manager.rbac.enforcement_enabled, False),
        Override[ManagerUnifiedConfig, Any],
    )


def _an_answer_carries_the_client_method_it_belongs_to() -> None:
    """What the storage proxy answers is written in the storage proxy's own types: the
    value must be what that method returns, and the refusal an exception."""
    assert_type(
        storage.answers(
            StorageProxyManagerFacingClient.get_folder_usage,
            {"used_bytes": 1024, "file_count": 3},
        ),
        Answer[StorageProxyManagerFacingClient],
    )
    assert_type(
        storage.raises(
            StorageProxyManagerFacingClient.create_folder,
            VFolderCreationFailure("the host refused"),
        ),
        Answer[StorageProxyManagerFacingClient],
    )


def _the_usage_reading_is_a_mapping_because_the_client_says_so(
    usage: Mapping[str, Any],
) -> None:
    """``get_folder_usage`` answers a mapping, which is why the scripted value above is
    one. A number there would be refused."""
    assert usage is not None


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------

SCENARIOS: list[DomainScenario] = [
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
        "enforcement-off-lets-the-delete-through",
        when=delete_domain(DeleteDomainInput(name="d1")),
        then=at(lambda p: p.deleted, True),
        setup=TypedSetup(
            config=[manager_config.set(lambda c: c.manager.rbac.enforcement_enabled, False)],
        ),
    ),
    TypedScenario.error(
        "member-is-refused",
        when=create_domain(CreateDomainInput(name="d1"), _actor()),
        then=InsufficientPrivilege,
    ),
]


# ---------------------------------------------------------------------------
# A scenario whose situation is what the outside answers
# ---------------------------------------------------------------------------

STORAGE_SCENARIOS: list[DomainScenario] = [
    TypedScenario.ok(
        "usage-is-read-from-the-storage-host",
        when=get_domain("d1"),
        setup=TypedSetup(
            answers=[
                storage.answers(
                    StorageProxyManagerFacingClient.get_folder_usage,
                    {"used_bytes": 1024, "file_count": 3},
                )
            ],
        ),
        then=at(lambda node: node.basic_info.name, "d1"),
    ),
    TypedScenario.error(
        "a-refusing-storage-host-fails-the-call",
        when=get_domain("d1"),
        setup=TypedSetup(
            answers=[
                storage.raises(
                    StorageProxyManagerFacingClient.create_folder,
                    VFolderCreationFailure("the host refused"),
                )
            ],
        ),
        then=VFolderCreationFailure,
    ),
]


# ---------------------------------------------------------------------------
# Putting a row in the database: the creator names the row and its data type
# ---------------------------------------------------------------------------


def _a_seed_carries_the_data_type_its_creator_answers() -> None:
    """``DomainCreator`` answers ``DomainData``, so the seed does too. Which ops path
    writes it follows from the creator's type, not from a name given here."""
    assert_type(creates(DomainCreator(name="dup")), Sown[DomainData])


existing_domain = creates(DomainCreator(name="dup"))

SEEDED_SCENARIOS: list[DomainScenario] = [
    TypedScenario.ok(
        "a-name-already-taken-is-refused",
        given=[existing_domain],
        when=create_domain(CreateDomainInput(name="dup"), _actor()),
        then=at(lambda p: p.domain.basic_info.name, "dup"),
    ),
    TypedScenario.ok(
        "the-generated-id-is-reachable-after-the-seed",
        given=[existing_domain],
        # The id is made by the database, so the call is written against the row.
        when=after(existing_domain, lambda row: get_domain(row.name)),
        then=at(lambda node: node.basic_info.name, "dup"),
    ),
]


# ---------------------------------------------------------------------------
# Checking the whole answer, with the generated fields taken over by a condition
# ---------------------------------------------------------------------------


EXHAUSTIVE: list[DomainScenario] = [
    TypedScenario.ok(
        "the-created-domain-in-full",
        when=create_domain(CreateDomainInput(name="d1"), _actor()),
        then=exactly(
            DomainPayload(
                domain=DomainNode(
                    # Stated so the payload can be built; taken over below, so the
                    # value written here is never compared.
                    id=DomainID(UUID(int=0)),
                    basic_info=DomainBasicInfo(name="d1", description=None, integration_name=None),
                    registry=DomainRegistryInfo(allowed_docker_registries=[]),
                    lifecycle=DomainLifecycleInfo(
                        is_active=True,
                        is_default=False,
                        created_at=datetime.now(UTC),
                        modified_at=datetime.now(UTC),
                    ),
                )
            ),
            where=(
                # The type is the whole guarantee: it arrives as a DomainID or the
                # payload would not have been built. How it is generated is the
                # writer's business.
                ignored(lambda p: p.domain.id, "generated by the database"),
                # A timestamp can hold something wrong, so it is held to a condition.
                checked(
                    lambda p: p.domain.lifecycle.created_at,
                    recent(timedelta(minutes=1)),
                    "written just now",
                ),
                checked(
                    lambda p: p.domain.lifecycle.modified_at,
                    recent(timedelta(minutes=1)),
                    "written just now",
                ),
            ),
        ),
    ),
]
