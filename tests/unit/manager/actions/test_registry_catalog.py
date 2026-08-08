"""The wiring-time spec catalog vs the v2 actions defined in the import closure.

Constructing a v2-wired package accumulates every wired spec on its registry, and
recursing ``__subclasses__()`` from the five v2 action bases finds every concrete
v2 action class defined. The two sets matching is what catches an action that was
defined but never wired. A new v2 wiring extends this guard by being imported and
constructed here.

The same sweep also holds every action to the audit identity contract: the
``(entity_type, operation, action_name)`` triple must be unique and the name must
be a lowercase snake_case phrase, so recorded rows stay distinguishable and
filterable.
"""

from __future__ import annotations

import inspect
import re
from typing import Any
from unittest.mock import MagicMock

from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry import ProcessorDependencies, ProcessorRegistry
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.app_config_allow_list.processors import (
    AppConfigAllowListProcessors,
)
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors

_V2_ACTION_BASES: tuple[type[Any], ...] = (
    BaseSingleEntityAction,
    BaseBulkAction,
    BaseScopeAction,
    BaseGlobalAction,
    BaseLookupAction,
)

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def _concrete_v2_action_classes() -> set[type[Any]]:
    """Every non-abstract v2 action class defined in the imported manager modules.

    Filtered to the manager package so action classes defined locally by other test
    modules in the same process cannot leak into the sweep.
    """
    found: set[type[Any]] = set()
    stack: list[type[Any]] = list(_V2_ACTION_BASES)
    while stack:
        cls = stack.pop()
        for subclass in cls.__subclasses__():
            stack.append(subclass)
            if not inspect.isabstract(subclass) and subclass.__module__.startswith(
                "ai.backend.manager."
            ):
                found.add(subclass)
    return found


def _ops_registry() -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
            repository=OpsRepository(MagicMock()),
        )
    )


def test_every_defined_v2_action_is_wired() -> None:
    allow_list_registry = _ops_registry()
    AppConfigAllowListProcessors(allow_list_registry)
    resource_slot_registry = _ops_registry()
    ResourceSlotProcessors(MagicMock(), [], MagicMock(), resource_slot_registry.group())

    wired = sorted(
        spec.type()
        for registry in (allow_list_registry, resource_slot_registry)
        for spec in registry.wired_specs()
    )
    defined = sorted(cls.spec().type() for cls in _concrete_v2_action_classes())

    assert wired == defined


def test_action_names_follow_the_snake_case_convention() -> None:
    for cls in _concrete_v2_action_classes():
        name = cls.action_name()
        assert _SNAKE_CASE.fullmatch(name), (
            f"{cls.__module__}.{cls.__qualname__} declares action_name()={name!r}, "
            "which is not a lowercase snake_case phrase."
        )


def test_identity_triple_is_unique_across_v2_actions() -> None:
    """Audit rows identify the run by (entity_type, operation, action_name).

    Two actions sharing all three would be indistinguishable once recorded — the
    ambiguity ``action_name`` exists to prevent.
    """
    seen: dict[tuple[str, str, str], type[Any]] = {}
    for cls in _concrete_v2_action_classes():
        triple = (str(cls.entity_type()), str(cls.operation_type()), cls.action_name())
        holder = seen.setdefault(triple, cls)
        assert holder is cls, (
            f"{cls.__module__}.{cls.__qualname__} and {holder.__module__}.{holder.__qualname__} "
            f"both record as {triple}; declare a distinct action_name() on one of them."
        )
