"""A scope-shaped create writes its audit row under the entity it created.

The scope the request covered is attached to that row, not used in its place.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor.audit_log import ScopeActionAuditLogMonitor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.models.audit_log.creators import AuditLogScopeCreator
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.repositories.client_ip_masking.repository import ClientIPMaskingRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.create_legacy_deployment import (
    CreateLegacyDeploymentAction,
    CreateLegacyDeploymentActionResult,
)
from ai.backend.manager.services.session.actions.create_cluster import (
    CreateClusterAction,
    CreateClusterActionResult,
)
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionResult,
)
from ai.backend.manager.services.session.actions.create_from_template import (
    CreateFromTemplateAction,
    CreateFromTemplateActionResult,
)
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    EnqueueSessionActionResult,
)
from ai.backend.manager.services.template.actions.create_cluster_template import (
    CreateClusterTemplateAction,
    CreateClusterTemplateActionResult,
)
from ai.backend.manager.services.template.actions.create_task_template import (
    CreatedTaskTemplateItem,
    CreateTaskTemplateAction,
    CreateTaskTemplateActionResult,
)
from ai.backend.manager.services.vfolder.actions.create import (
    CreateVFolderAction,
    CreateVFolderActionResult,
)

_PROJECT_ID = ProjectID(uuid.uuid4())
_SESSION_UUID = uuid.uuid4()
_DEPLOYMENT_ID = DeploymentID(uuid.uuid4())
_VFOLDER_ID = VFolderUUID(uuid.uuid4())
_TEMPLATE_UUIDS = (uuid.uuid4(), uuid.uuid4())


@dataclass(frozen=True)
class _Case:
    action: BaseScopeAction
    result: BaseScopeActionResult
    expected_entity_ids: Sequence[EntityIdentifier]


def _session_create_kwargs() -> dict[str, Any]:
    return {
        "project_id": _PROJECT_ID,
        "params": MagicMock(),
        "user_id": uuid.uuid4(),
        "user_role": UserRole.USER,
        "sudo_session_enabled": False,
        "requester_access_key": AccessKey("AKTEST"),
        "keypair_resource_policy": None,
    }


def _template_create_kwargs() -> dict[str, Any]:
    return {
        "requesting_project": _PROJECT_ID,
        "domain_name": "default",
        "requester_uuid": uuid.uuid4(),
        "requester_access_key": "AKTEST",
        "requester_role": UserRole.USER,
        "requester_domain": "default",
        "owner_access_key": None,
    }


def _vfolder_creator() -> MagicMock:
    creator = MagicMock()
    creator.scope_targets.return_value = (_PROJECT_ID,)
    return creator


_CASES: dict[str, _Case] = {
    "create_from_params": _Case(
        action=CreateFromParamsAction(**_session_create_kwargs()),
        result=CreateFromParamsActionResult(session_id=_SESSION_UUID, result={}),
        expected_entity_ids=(SessionID(_SESSION_UUID),),
    ),
    "create_from_template": _Case(
        action=CreateFromTemplateAction(**_session_create_kwargs()),
        result=CreateFromTemplateActionResult(session_id=_SESSION_UUID, result={}),
        expected_entity_ids=(SessionID(_SESSION_UUID),),
    ),
    "create_cluster": _Case(
        action=CreateClusterAction(
            project_id=_PROJECT_ID,
            session_name="s",
            user_id=uuid.uuid4(),
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            template_id=uuid.uuid4(),
            session_type=MagicMock(),
            group_name="default",
            domain_name="default",
            resource_group_name="default",
            requester_access_key=AccessKey("AKTEST"),
            owner_access_key=AccessKey("AKTEST"),
            tag="",
            enqueue_only=False,
            keypair_resource_policy=None,
            max_wait_seconds=0,
        ),
        result=CreateClusterActionResult(session_id=_SESSION_UUID, result={}),
        expected_entity_ids=(SessionID(_SESSION_UUID),),
    ),
    "enqueue_session": _Case(
        action=EnqueueSessionAction(
            project_id=_PROJECT_ID,
            session_name="s",
            session_type=MagicMock(),
            image_id=uuid.uuid4(),
            resource=MagicMock(),
            scheduling=MagicMock(),
        ),
        result=EnqueueSessionActionResult(session_data=MagicMock(id=_SESSION_UUID)),
        expected_entity_ids=(SessionID(_SESSION_UUID),),
    ),
    "create_deployment": _Case(
        action=CreateDeploymentAction(
            project_id=_PROJECT_ID, creator=MagicMock(), auto_activate=True
        ),
        result=CreateDeploymentActionResult(data=MagicMock(id=_DEPLOYMENT_ID)),
        expected_entity_ids=(_DEPLOYMENT_ID,),
    ),
    "create_legacy_deployment": _Case(
        action=CreateLegacyDeploymentAction(project_id=_PROJECT_ID, draft=MagicMock()),
        result=CreateLegacyDeploymentActionResult(data=MagicMock(id=_DEPLOYMENT_ID)),
        expected_entity_ids=(_DEPLOYMENT_ID,),
    ),
    "create_cluster_template": _Case(
        action=CreateClusterTemplateAction(**_template_create_kwargs(), template_data={}),
        result=CreateClusterTemplateActionResult(id=_TEMPLATE_UUIDS[0].hex, user="u"),
        expected_entity_ids=(SessionTemplateID(_TEMPLATE_UUIDS[0]),),
    ),
    "create_task_template": _Case(
        action=CreateTaskTemplateAction(**_template_create_kwargs()),
        result=CreateTaskTemplateActionResult(
            created=[CreatedTaskTemplateItem(id=u.hex, user="u") for u in _TEMPLATE_UUIDS]
        ),
        expected_entity_ids=tuple(SessionTemplateID(u) for u in _TEMPLATE_UUIDS),
    ),
    "create_vfolder": _Case(
        action=CreateVFolderAction(creator=_vfolder_creator()),
        result=CreateVFolderActionResult(vfolder=MagicMock(id=_VFOLDER_ID)),
        expected_entity_ids=(_VFOLDER_ID,),
    ),
}


@pytest.fixture
def audit_repository() -> MagicMock:
    return MagicMock(spec=OpsRepository)


@pytest.fixture
def monitor(audit_repository: MagicMock) -> ScopeActionAuditLogMonitor:
    masking = MagicMock(spec=ClientIPMaskingRepository)
    masking.mask.return_value = None
    return ScopeActionAuditLogMonitor(audit_repository, AuditLogPolicy([]), masking)


class TestScopeCreateAuditTarget:
    @pytest.mark.parametrize("case", _CASES.values(), ids=_CASES.keys())
    async def test_create_audit_row_is_owned_by_the_created_entity(
        self,
        case: _Case,
        monitor: ScopeActionAuditLogMonitor,
        audit_repository: MagicMock,
    ) -> None:
        async def _run(_: BaseScopeAction) -> BaseScopeActionResult:
            return case.result

        processor: ScopeActionProcessor[BaseScopeAction, BaseScopeActionResult] = (
            ScopeActionProcessor(_run, monitors=[monitor])
        )
        await processor.run(case.action)

        audit_repository.atomic_create_dangling_fields_with_nested.assert_not_called()
        creations, nested = audit_repository.atomic_create_fields_with_nested.call_args.args
        owner_ids = [c.owner_id for c in creations]
        assert owner_ids == list(case.expected_entity_ids)
        assert [type(o) for o in owner_ids] == [type(e) for e in case.expected_entity_ids]
        assert [
            (n.scope_type, n.scope_id) for n in nested if isinstance(n, AuditLogScopeCreator)
        ] == [(_PROJECT_ID.entity_type(), _PROJECT_ID)]
