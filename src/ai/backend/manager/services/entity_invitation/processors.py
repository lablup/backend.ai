from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.services.entity_invitation.actions.answer import (
    AcceptEntityInvitationAction,
    CancelEntityInvitationAction,
    CancelEntityInvitationActionResult,
    EntityInvitationAnswerResult,
    RejectEntityInvitationAction,
)
from ai.backend.manager.services.entity_invitation.actions.create import (
    CreateEntityInvitationAction,
)
from ai.backend.manager.services.entity_invitation.actions.get import GetEntityInvitationAction
from ai.backend.manager.services.entity_invitation.actions.search import (
    SearchEntityInvitationsAction,
)
from ai.backend.manager.services.entity_invitation.service import EntityInvitationService


class EntityInvitationProcessors:
    """Creating and reading run against ops; the three answers keep a service, each
    settling a row behind a guard.

    One search for every side: which side a read comes in through is a value, and the
    scope it is answered for travels with the rows it selects."""

    create: ScopeActionProcessor[
        CreateEntityInvitationAction, CreatedEntityOpsResult[EntityInvitationData]
    ]
    get: SingleEntityActionProcessor[
        GetEntityInvitationAction, EntityOpsResult[EntityInvitationData]
    ]
    search: ScopeActionProcessor[
        SearchEntityInvitationsAction, ScopedBatchOpsResult[EntityInvitationData]
    ]
    accept: ScopeActionProcessor[AcceptEntityInvitationAction, EntityInvitationAnswerResult]
    reject: ScopeActionProcessor[RejectEntityInvitationAction, EntityInvitationAnswerResult]
    cancel: SingleEntityActionProcessor[
        CancelEntityInvitationAction, CancelEntityInvitationActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[EntityInvitationData],
        service: EntityInvitationService,
    ) -> None:
        self.create = group.entity_create_ops(CreateEntityInvitationAction)
        self.get = group.single_get_ops(GetEntityInvitationAction)
        self.search = group.scope_search_ops(SearchEntityInvitationsAction)
        self.accept = group.scope(AcceptEntityInvitationAction, service.accept)
        self.reject = group.scope(RejectEntityInvitationAction, service.reject)
        self.cancel = group.single_entity(CancelEntityInvitationAction, service.cancel)
