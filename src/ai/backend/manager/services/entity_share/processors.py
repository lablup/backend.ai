from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
<<<<<<< HEAD
=======
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
>>>>>>> 8afffbf6 (fix(BA-9055): answer an entity share addressed to a project as that project (#17162))
from ai.backend.manager.actions.v2.ops.result import (
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.services.entity_share.actions.answer import (
    AcceptEntityShareAction,
    CancelEntityShareAction,
    CancelEntityShareActionResult,
    EntityShareAnswerResult,
    LeaveEntityShareAction,
    RejectEntityShareAction,
    RevokeEntityShareAction,
    RevokeEntityShareActionResult,
)
from ai.backend.manager.services.entity_share.actions.create import (
    CreateEntityShareAction,
    CreateEntityShareActionResult,
)
from ai.backend.manager.services.entity_share.actions.get import GetEntityShareAction
from ai.backend.manager.services.entity_share.actions.lookup_answering_scope import (
    LookupEntityShareAnsweringScopeAction,
    LookupEntityShareAnsweringScopeActionResult,
)
from ai.backend.manager.services.entity_share.actions.search import (
    SearchEntitySharesAction,
)
from ai.backend.manager.services.entity_share.service import EntityShareService


class EntityShareProcessors:
    """Creating and reading run against ops; the three answers keep a service, each
    settling a row behind a guard, and so does resolving the scope that answers.

    One search for every side: which side a read comes in through is a value, and the
    scope it is answered for travels with the rows it selects."""

    create: ScopeActionProcessor[CreateEntityShareAction, CreateEntityShareActionResult]
    get: SingleEntityActionProcessor[GetEntityShareAction, EntityOpsResult[EntityShareData]]
    search: ScopeActionProcessor[SearchEntitySharesAction, ScopedBatchOpsResult[EntityShareData]]
    lookup_answering_scope: LookupActionProcessor[
        LookupEntityShareAnsweringScopeAction, LookupEntityShareAnsweringScopeActionResult
    ]
    accept: ScopeActionProcessor[AcceptEntityShareAction, EntityShareAnswerResult]
    reject: ScopeActionProcessor[RejectEntityShareAction, EntityShareAnswerResult]
    cancel: SingleEntityActionProcessor[CancelEntityShareAction, CancelEntityShareActionResult]
    revoke: SingleEntityActionProcessor[RevokeEntityShareAction, RevokeEntityShareActionResult]
    leave: ScopeActionProcessor[LeaveEntityShareAction, EntityShareAnswerResult]

    def __init__(
        self,
        group: ProcessorGroup[EntityShareData],
        service: EntityShareService,
    ) -> None:
        self.create = group.scope(CreateEntityShareAction, service.create)
        self.get = group.single_get_ops(GetEntityShareAction)
        self.search = group.scoped_search_ops(SearchEntitySharesAction)
        self.lookup_answering_scope = group.lookup(
            LookupEntityShareAnsweringScopeAction, service.lookup_answering_scope
        )
        self.accept = group.scope(AcceptEntityShareAction, service.accept)
        self.reject = group.scope(RejectEntityShareAction, service.reject)
        self.cancel = group.single_entity(CancelEntityShareAction, service.cancel)
        self.revoke = group.single_entity(RevokeEntityShareAction, service.revoke)
        self.leave = group.scope(LeaveEntityShareAction, service.leave)
