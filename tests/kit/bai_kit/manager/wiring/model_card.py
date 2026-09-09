"""Model card wiring.

Second of the shapes tried after domain. The adapter reads two processor groups, and a
scenario that stays away from deployment only needs one, so the other is left unwired
and says so if a scenario reaches it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    SearchModelCardsInput,
    UpdateModelCardInput,
)
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.repositories.model_card.repository import ModelCardRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.model_card.processors import ModelCardProcessors
from ai.backend.manager.services.model_card.service import ModelCardService
from bai_kit.manager.fakes.storage_proxy import (
    FakeStorageProxyManagerFacingClient,
    FakeStorageSessionManager,
)
from bai_kit.manager.runner import Wired, WiringDeps
from bai_kit.manager.unwired import unwired

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors  # pants: no-infer-dep


@dataclass
class ModelCardAdapterProcessors:
    """The two groups ``ModelCardAdapter`` reads. Only ``deploy`` touches deployment."""

    model_card: ModelCardProcessors
    deployment: DeploymentProcessors


DISPATCH: dict[type, str] = {
    CreateModelCardInput: "create",
    SearchModelCardsInput: "admin_search",
    # update takes the id beside the body, get takes an id: name them with Call(...).
    UpdateModelCardInput: "update",
}

STORAGE_EXTRA = "storage"


def model_card_wiring(deps: WiringDeps) -> Wired:
    storage = deps.extras.get(STORAGE_EXTRA) or FakeStorageProxyManagerFacingClient()
    provider = V2DBOpsProvider(deps.engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=deps.monitors,
            validators=deps.v2_validators,
            repository=OpsRepository(provider),
        )
    )
    service = ModelCardService(
        ModelCardRepository(provider),
        FakeStorageSessionManager({"local": storage}),
    )
    model_card = ModelCardProcessors(registry.group(GroupMeta(MODEL_CARD_ENTITY_TYPE)), service)
    adapter = ModelCardAdapter(
        cast(
            "Processors",
            ModelCardAdapterProcessors(
                model_card=model_card,
                deployment=unwired(DeploymentProcessors, "only deploy() reaches it"),
            ),
        )
    )
    return Wired(
        adapter=adapter,
        dispatch=DISPATCH,
        client_attr="model_card",
        extras={STORAGE_EXTRA: storage},
    )
