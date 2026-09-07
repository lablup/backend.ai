from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.idle_checker.actions.admin_search import (
    AdminSearchIdleCheckersAction,
)
from ai.backend.manager.services.idle_checker.actions.create import CreateIdleCheckerAction
from ai.backend.manager.services.idle_checker.actions.exclude_sessions import (
    ExcludeSessionIdleChecksAction,
    ExcludeSessionIdleChecksActionResult,
)
from ai.backend.manager.services.idle_checker.actions.include_sessions import (
    IncludeSessionIdleChecksAction,
    IncludeSessionIdleChecksActionResult,
)
from ai.backend.manager.services.idle_checker.actions.purge import BulkPurgeIdleCheckersAction
from ai.backend.manager.services.idle_checker.actions.update import UpdateIdleCheckerAction
from ai.backend.manager.services.idle_checker.service import IdleCheckerService


class IdleCheckerProcessors:
    """The two writes that validate against a preset go through the service; the
    catalog's purge and search run straight against ops.

    Two groups: the checker definition is the entity of the first, and the session
    lists the second edits are answered for by the session.
    """

    admin_search: GlobalActionProcessor[
        AdminSearchIdleCheckersAction, BatchOpsResult[IdleCheckerData]
    ]
    create: GlobalActionProcessor[CreateIdleCheckerAction, CreatedEntityOpsResult[IdleCheckerData]]
    update: GlobalActionProcessor[UpdateIdleCheckerAction, EntityOpsResult[IdleCheckerData]]
    bulk_purge: PartialBulkActionProcessor[BulkPurgeIdleCheckersAction, IdleCheckerData]
    exclude_sessions: BulkActionProcessor[
        ExcludeSessionIdleChecksAction,
        ExcludeSessionIdleChecksActionResult,
    ]
    include_sessions: BulkActionProcessor[
        IncludeSessionIdleChecksAction,
        IncludeSessionIdleChecksActionResult,
    ]

    def __init__(
        self,
        group: ProcessorGroup[IdleCheckerData],
        session_group: ProcessorGroup[SessionData],
        service: IdleCheckerService,
    ) -> None:
        self.admin_search = group.global_search_ops(AdminSearchIdleCheckersAction)
        self.create = group.global_scope(CreateIdleCheckerAction, service.create)
        self.update = group.global_scope(UpdateIdleCheckerAction, service.update)
        self.bulk_purge = group.global_partial_bulk_purge_ops(BulkPurgeIdleCheckersAction)
        self.exclude_sessions = session_group.legacy_partial_bulk(
            ExcludeSessionIdleChecksAction, service.exclude_sessions
        )
        self.include_sessions = session_group.legacy_partial_bulk(
            IncludeSessionIdleChecksAction, service.include_sessions
        )
