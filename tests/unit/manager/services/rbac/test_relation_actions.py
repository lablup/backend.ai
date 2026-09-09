"""A relation action names both ends of every pair, and a run leaves one audit row.

One wiring serves every relation — which relation a run is about travels on the spec —
so what is checked here is that the pairs the action carries become the scopes the
permission is asked of, and that the row recorded names no entity.

The shape's own guarantee, that every named scope has to permit the run, is held by
``tests/unit/manager/actions/test_relation_processor.py``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.container_registry import (
    CONTAINER_REGISTRY_SCOPE_TYPE,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.idle_checker import (
    IdleCheckerID,
)
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.actions.v2.relation.monitor.audit_log import RelationActionAuditLogMonitor
from ai.backend.manager.actions.v2.relation.result import (
    RelationActionProcessResult,
    RelationActionResultMeta,
)
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta
from ai.backend.manager.models.audit_log.creators import RelationAuditLogCreator
from ai.backend.manager.models.container_registry.creators import ContainerRegistryProjectCreator
from ai.backend.manager.models.container_registry.purgers import ContainerRegistryProjectPurger
from ai.backend.manager.models.idle_checker.updaters import (
    IdleCheckerAssignmentDisabler,
    IdleCheckerAssignmentEnabler,
)
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupForDomainRelationCreator,
    ResourceGroupForKeypairRelationCreator,
    ResourceGroupForProjectRelationCreator,
)
from ai.backend.manager.models.resource_group.purgers import (
    ResourceGroupForDomainRelationPurger,
    ResourceGroupForKeypairRelationPurger,
    ResourceGroupForProjectRelationPurger,
)
from ai.backend.manager.services.rbac.actions.relation.base import RelationPair
from ai.backend.manager.services.rbac.actions.relation.create import CreateRelationAction
from ai.backend.manager.services.rbac.actions.relation.purge import PurgeRelationAction
from ai.backend.manager.services.rbac.actions.relation.switch import (
    DeleteRelationAction,
    RestoreRelationAction,
)

_PROJECT_ID = ProjectID(uuid.uuid4())
_DOMAIN_ID = DomainID(uuid.uuid4())
_REGISTRY_ID = ContainerRegistryID(uuid.uuid4())
_RESOURCE_GROUP_ID = ResourceGroupID(uuid.uuid4())
_USER_ID = UserID(uuid.uuid4())
_IDLE_CHECKER_ID = IdleCheckerID(uuid.uuid4())
_ACCESS_KEY = AccessKey("AKTESTRELATION0001")


class TestEveryPairBecomesTheRunsScopes:
    """The relations this system writes, each through the same two wirings."""

    @pytest.mark.parametrize(
        ("action", "operation", "expected"),
        [
            (
                CreateRelationAction(
                    pairs=[RelationPair(scope=_PROJECT_ID, target=_REGISTRY_ID)],
                    creator=ContainerRegistryProjectCreator(),
                ),
                ActionOperationType.CREATE,
                [
                    _PROJECT_ID,
                    _REGISTRY_ID,
                ],
            ),
            (
                PurgeRelationAction(
                    pairs=[RelationPair(scope=_PROJECT_ID, target=_REGISTRY_ID)],
                    purger=ContainerRegistryProjectPurger(),
                ),
                ActionOperationType.DELETE,
                [
                    _PROJECT_ID,
                    _REGISTRY_ID,
                ],
            ),
            (
                CreateRelationAction(
                    pairs=[RelationPair(scope=_PROJECT_ID, target=_RESOURCE_GROUP_ID)],
                    creator=ResourceGroupForProjectRelationCreator(),
                ),
                ActionOperationType.CREATE,
                [
                    _PROJECT_ID,
                    _RESOURCE_GROUP_ID,
                ],
            ),
            (
                PurgeRelationAction(
                    pairs=[RelationPair(scope=_PROJECT_ID, target=_RESOURCE_GROUP_ID)],
                    purger=ResourceGroupForProjectRelationPurger(),
                ),
                ActionOperationType.DELETE,
                [
                    _PROJECT_ID,
                    _RESOURCE_GROUP_ID,
                ],
            ),
            (
                CreateRelationAction(
                    pairs=[RelationPair(scope=_DOMAIN_ID, target=_RESOURCE_GROUP_ID)],
                    creator=ResourceGroupForDomainRelationCreator(),
                ),
                ActionOperationType.CREATE,
                [
                    _DOMAIN_ID,
                    _RESOURCE_GROUP_ID,
                ],
            ),
            (
                PurgeRelationAction(
                    pairs=[RelationPair(scope=_DOMAIN_ID, target=_RESOURCE_GROUP_ID)],
                    purger=ResourceGroupForDomainRelationPurger(),
                ),
                ActionOperationType.DELETE,
                [
                    _DOMAIN_ID,
                    _RESOURCE_GROUP_ID,
                ],
            ),
            (
                CreateRelationAction(
                    pairs=[RelationPair(scope=_USER_ID, target=_RESOURCE_GROUP_ID)],
                    creator=ResourceGroupForKeypairRelationCreator(access_key=_ACCESS_KEY),
                ),
                ActionOperationType.CREATE,
                [
                    _USER_ID,
                    _RESOURCE_GROUP_ID,
                ],
            ),
            (
                PurgeRelationAction(
                    pairs=[RelationPair(scope=_USER_ID, target=_RESOURCE_GROUP_ID)],
                    purger=ResourceGroupForKeypairRelationPurger(),
                ),
                ActionOperationType.DELETE,
                [
                    _USER_ID,
                    _RESOURCE_GROUP_ID,
                ],
            ),
            (
                DeleteRelationAction(
                    pairs=[RelationPair(scope=_PROJECT_ID, target=_IDLE_CHECKER_ID)],
                    updater=IdleCheckerAssignmentDisabler(),
                ),
                ActionOperationType.DELETE,
                [
                    _PROJECT_ID,
                    _IDLE_CHECKER_ID,
                ],
            ),
            (
                RestoreRelationAction(
                    pairs=[RelationPair(scope=_PROJECT_ID, target=_IDLE_CHECKER_ID)],
                    updater=IdleCheckerAssignmentEnabler(),
                ),
                ActionOperationType.RESTORE,
                [
                    _PROJECT_ID,
                    _IDLE_CHECKER_ID,
                ],
            ),
        ],
    )
    def test_scope_targets_and_operation(
        self,
        action: BaseRelationAction,
        operation: ActionOperationType,
        expected: list[EntityIdentifier],
    ) -> None:
        assert list(action.scope_targets()) == expected
        assert action.operation_type() is operation

    def test_a_run_over_several_pairs_names_every_entity_once(self) -> None:
        """A registry linked to three projects is one run: the registry is named once
        and each project once, so the permission is asked of four scopes, not six."""
        projects = [ProjectID(uuid.uuid4()) for _ in range(3)]
        action = CreateRelationAction(
            pairs=[RelationPair(scope=project, target=_REGISTRY_ID) for project in projects],
            creator=ContainerRegistryProjectCreator(),
        )

        assert list(action.scope_targets()) == [
            projects[0],
            _REGISTRY_ID,
            projects[1],
            projects[2],
        ]


class TestARelationRunIsRecordedOnItsOwn:
    async def test_the_audit_row_names_no_entity_and_carries_both_scopes(self) -> None:
        """A link is recorded under the relation's own action name, with the pair on the
        run's scopes and no entity kind — what it wrote is neither of the two."""
        repository = MagicMock()
        repository.atomic_create_dangling_fields_with_nested = AsyncMock()
        client_ip_masking = MagicMock()
        client_ip_masking.mask = AsyncMock(return_value=None)
        monitor = RelationActionAuditLogMonitor(
            repository, AuditLogPolicy(record_read_operations=[]), client_ip_masking
        )
        action: CreateRelationAction[Any, Any, Any] = CreateRelationAction(
            pairs=[RelationPair(scope=_PROJECT_ID, target=_REGISTRY_ID)],
            creator=ContainerRegistryProjectCreator(),
        )
        started_at = datetime.now(UTC)
        meta = RelationActionTriggerMeta(
            action_id=uuid.uuid4(),
            started_at=started_at,
            scope_targets=action.scope_targets(),
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

        await monitor.done(
            meta,
            RelationActionProcessResult(
                meta=RelationActionResultMeta(
                    status=OperationStatus.SUCCESS,
                    description="ok",
                    ended_at=started_at,
                    duration=timedelta(0),
                    error_code=None,
                )
            ),
        )

        creators, scopes = repository.atomic_create_dangling_fields_with_nested.call_args.args
        assert isinstance(creators[0], RelationAuditLogCreator)
        assert creators[0].entity_type is None
        assert creators[0].action_name == "create_relation"
        assert {(s.scope_type, s.scope_id) for s in scopes} == {
            (str(PROJECT_SCOPE_TYPE), _PROJECT_ID),
            (str(CONTAINER_REGISTRY_SCOPE_TYPE), _REGISTRY_ID),
        }
