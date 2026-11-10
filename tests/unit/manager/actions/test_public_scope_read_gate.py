"""The reads of the publicly readable catalogs are answered at the public singleton.

Each processor is built from the production wiring with the group validators replaced by
one that refuses everything, so a refusal proves the search went through a gated factory
and names the scope it is checked in.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from typing import Any, override
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.common.data.entity.login_client_type import LoginClientTypeEntityType
from ai.backend.common.data.entity.prometheus_query_preset import (
    PrometheusQueryPresetEntityType,
)
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryEntityType,
)
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.global_scope.validator.refusing import (
    RefusingGlobalActionValidator,
)
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.data.permission.global_entity import GlobalEntityIDCache, global_entity_id
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.login_client_type.scopes import PublicLoginClientTypeTarget
from ai.backend.manager.models.login_client_type.searchers import LoginClientTypeSearcher
from ai.backend.manager.models.prometheus_query_preset.scopes import (
    PublicPrometheusQueryPresetTarget,
)
from ai.backend.manager.models.prometheus_query_preset.searchers import (
    PrometheusQueryPresetSearcher,
)
from ai.backend.manager.models.prometheus_query_preset_category.scopes import (
    PublicPrometheusQueryPresetCategoryTarget,
)
from ai.backend.manager.models.prometheus_query_preset_category.searchers import (
    PrometheusQueryPresetCategorySearcher,
)
from ai.backend.manager.models.resource_slot.scopes import PublicResourceSlotTypeTarget
from ai.backend.manager.models.resource_slot.searchers import ResourceSlotTypeSearcher
from ai.backend.manager.models.runtime_variant.scopes import PublicRuntimeVariantTarget
from ai.backend.manager.models.runtime_variant.searchers import RuntimeVariantSearcher
from ai.backend.manager.models.runtime_variant_preset.scopes import (
    PublicRuntimeVariantPresetTarget,
)
from ai.backend.manager.models.runtime_variant_preset.searchers import (
    RuntimeVariantPresetSearcher,
)
from ai.backend.manager.models.scopes import ScopeTarget
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.login_client_type.actions.scoped_search import (
    ScopedSearchLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.processors import LoginClientTypeProcessors
from ai.backend.manager.services.prometheus_query_preset.actions.scoped_search import (
    ScopedSearchPresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions.scoped_search import (
    ScopedSearchCategoriesAction,
)
from ai.backend.manager.services.prometheus_query_preset_category.processors import (
    PrometheusQueryPresetCategoryProcessors,
)
from ai.backend.manager.services.resource_slot.actions.scoped_search_resource_slot_types import (
    ScopedSearchResourceSlotTypesAction,
)
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.runtime_variant.actions.scoped_search import (
    ScopedSearchRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.processors import RuntimeVariantProcessors
from ai.backend.manager.services.runtime_variant_preset.actions.scoped_search import (
    ScopedSearchRuntimeVariantPresetsAction,
)
from ai.backend.manager.services.runtime_variant_preset.processors import (
    RuntimeVariantPresetProcessors,
)

type BuildSearch = Callable[
    [ProcessorRegistry[Any]], tuple[ScopeActionProcessor[Any, Any], BaseScopeAction]
]


class _DenyingScopeValidator(ScopeActionValidator):
    def __init__(self) -> None:
        self.seen: list[BaseScopeAction] = []

    @override
    async def validate(self, action: BaseScopeAction, meta: ActionTriggerMeta) -> None:
        self.seen.append(action)
        raise NotEnoughPermission(f"denied at scopes {action.scope_targets()}")


def _scoped[TAction: ScopedSearchOpsAction[Any, Any]](
    action_cls: type[TAction], target: ScopeTarget, searcher: Any
) -> TAction:
    return action_cls(
        searcher=ScopedSearcher(scopes=[target], used_by=(), searcher=searcher),
    )


def _runtime_variant(
    registry: ProcessorRegistry[Any],
) -> tuple[ScopeActionProcessor[Any, Any], BaseScopeAction]:
    processors = RuntimeVariantProcessors(
        registry.group(GroupMeta(RuntimeVariantEntityType())), MagicMock()
    )
    return processors.scoped_search, _scoped(
        ScopedSearchRuntimeVariantsAction,
        PublicRuntimeVariantTarget(),
        RuntimeVariantSearcher(pagination=NoPagination()),
    )


def _runtime_variant_preset(
    registry: ProcessorRegistry[Any],
) -> tuple[ScopeActionProcessor[Any, Any], BaseScopeAction]:
    processors = RuntimeVariantPresetProcessors(
        registry.group(GroupMeta(RuntimeVariantPresetEntityType())), MagicMock()
    )
    return processors.scoped_search, _scoped(
        ScopedSearchRuntimeVariantPresetsAction,
        PublicRuntimeVariantPresetTarget(),
        RuntimeVariantPresetSearcher(pagination=NoPagination()),
    )


def _prometheus_query_preset(
    registry: ProcessorRegistry[Any],
) -> tuple[ScopeActionProcessor[Any, Any], BaseScopeAction]:
    processors = PrometheusQueryPresetProcessors(
        registry.group(GroupMeta(PrometheusQueryPresetEntityType())), MagicMock()
    )
    return processors.scoped_search_presets, _scoped(
        ScopedSearchPresetsAction,
        PublicPrometheusQueryPresetTarget(),
        PrometheusQueryPresetSearcher(pagination=NoPagination()),
    )


def _prometheus_query_preset_category(
    registry: ProcessorRegistry[Any],
) -> tuple[ScopeActionProcessor[Any, Any], BaseScopeAction]:
    processors = PrometheusQueryPresetCategoryProcessors(
        registry.group(GroupMeta(PrometheusQueryPresetCategoryEntityType()))
    )
    return processors.scoped_search_categories, _scoped(
        ScopedSearchCategoriesAction,
        PublicPrometheusQueryPresetCategoryTarget(),
        PrometheusQueryPresetCategorySearcher(pagination=NoPagination()),
    )


def _login_client_type(
    registry: ProcessorRegistry[Any],
) -> tuple[ScopeActionProcessor[Any, Any], BaseScopeAction]:
    processors = LoginClientTypeProcessors(registry.group(GroupMeta(LoginClientTypeEntityType())))
    return processors.scoped_search, _scoped(
        ScopedSearchLoginClientTypesAction,
        PublicLoginClientTypeTarget(),
        LoginClientTypeSearcher(pagination=NoPagination()),
    )


def _resource_slot_type(
    registry: ProcessorRegistry[Any],
) -> tuple[ScopeActionProcessor[Any, Any], BaseScopeAction]:
    processors = ResourceSlotProcessors(
        registry.group(GroupMeta(ResourceSlotTypeEntityType())),
        registry.group(GroupMeta(SessionEntityType())),
        registry.group(GroupMeta(AgentEntityType())),
        MagicMock(),
    )
    return processors.scoped_search_resource_slot_types, _scoped(
        ScopedSearchResourceSlotTypesAction,
        PublicResourceSlotTypeTarget(),
        ResourceSlotTypeSearcher(pagination=NoPagination()),
    )


@pytest.fixture
def public_singleton() -> Iterator[GlobalEntityID]:
    ids = {name: GlobalEntityID(uuid.uuid4()) for name in GlobalEntityName}
    GlobalEntityIDCache.fill(ids)
    try:
        yield ids[GlobalEntityName.PUBLIC]
    finally:
        GlobalEntityIDCache.clear()


@pytest.fixture
def denying_scope() -> _DenyingScopeValidator:
    return _DenyingScopeValidator()


@pytest.fixture
def registry(denying_scope: _DenyingScopeValidator) -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(
                scope=[denying_scope],
                global_scope=[RefusingGlobalActionValidator()],
            ),
            repository=OpsRepository(MagicMock()),
        )
    )


@pytest.mark.parametrize(
    "build",
    [
        _runtime_variant,
        _runtime_variant_preset,
        _prometheus_query_preset,
        _prometheus_query_preset_category,
        _login_client_type,
        _resource_slot_type,
    ],
)
async def test_catalog_search_is_answered_at_the_public_singleton(
    registry: ProcessorRegistry[Any],
    denying_scope: _DenyingScopeValidator,
    public_singleton: GlobalEntityID,
    build: BuildSearch,
) -> None:
    processor, action = build(registry)

    with pytest.raises(NotEnoughPermission):
        await processor.run(action)

    assert [seen.scope_targets() for seen in denying_scope.seen] == [[public_singleton]]
    assert global_entity_id(GlobalEntityName.PUBLIC) == public_singleton
