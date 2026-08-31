"""A gated lookup answers both of its failures the same way.

A key naming nothing and a key the caller may not reach reach the caller as one
exception, so the status code says nothing about whether the key exists. The audit
record still carries the real cause.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerByKeyOpsAction
from ai.backend.manager.actions.v2.lookup.base import (
    BaseLookupAction,
    BaseLookupActionResult,
    LookupKey,
)
from ai.backend.manager.actions.v2.lookup.monitor.base import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.lookup.result import LookupActionProcessResult
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupAccessTokenDeploymentAction,
    LookupAutoScalingRuleDeploymentAction,
    LookupRevisionDeploymentAction,
    LookupRouteDeploymentAction,
)
from ai.backend.manager.services.resource_slot.actions.lookup_kernel_owner import (
    LookupKernelOwnerAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair import LookupKeypairByAccessKeyAction
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupKeypairOwnerByAccessKeyAction,
)

_ACCESS_KEY = AccessKey("AKIAIOSFODNN7EXAMPLE")
_SECRET_ENTITY_TYPE = EntityType("image")


class _ImageID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return _SECRET_ENTITY_TYPE


_RESOLVED = _ImageID(uuid.uuid4())


@dataclass(frozen=True)
class _CanonicalKey(LookupKey):
    canonical: str

    @override
    def kind(self) -> str:
        return "canonical"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"canonical": self.canonical}


@dataclass
class _Action(BaseLookupAction):
    key: _CanonicalKey

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _SECRET_ENTITY_TYPE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "lookup_image"

    @override
    def lookup_key(self) -> LookupKey:
        return self.key


@dataclass
class _Result(BaseLookupActionResult):
    @override
    def entity_id(self) -> EntityIdentifier:
        return _RESOLVED


class _DenyingValidator(SingleEntityActionValidator):
    @override
    async def validate(self, meta: SingleEntityActionTriggerMeta) -> None:
        raise NotEnoughPermission(
            f"User lacks permission on {meta.entity.entity_type()} {meta.entity}"
        )


class _PassingValidator(SingleEntityActionValidator):
    @override
    async def validate(self, meta: SingleEntityActionTriggerMeta) -> None:
        return


class _RecordingMonitor(LookupActionMonitor):
    def __init__(self) -> None:
        self.done_results: list[LookupActionProcessResult] = []

    @override
    async def prepare(self, action: BaseLookupAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseLookupAction, result: LookupActionProcessResult) -> None:
        self.done_results.append(result)


@pytest.fixture
def authenticated_user() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def action() -> _Action:
    return _Action(key=_CanonicalKey(canonical="lablup/python:3.13"))


async def _missing(_: _Action) -> _Result:
    raise EntityNotFoundError("No Row matches the given key")


async def _resolved(_: _Action) -> _Result:
    return _Result()


def _processor(
    func: Any, monitor: _RecordingMonitor, post_validators: Any
) -> LookupActionProcessor[_Action, _Result]:
    return LookupActionProcessor[_Action, _Result](
        func=func, monitors=[monitor], post_validators=post_validators
    )


async def test_a_missing_key_and_a_denied_key_raise_the_same_thing(
    action: _Action, authenticated_user: UserData
) -> None:
    monitor = _RecordingMonitor()
    missing = _processor(_missing, monitor, [_PassingValidator()])
    denied = _processor(_resolved, monitor, [_DenyingValidator()])

    with with_user(authenticated_user):
        with pytest.raises(GenericBadRequest) as missing_error:
            await missing.run(action)
        with pytest.raises(GenericBadRequest) as denied_error:
            await denied.run(action)

    assert str(missing_error.value) == str(denied_error.value)
    assert missing_error.value.error_code() == denied_error.value.error_code()
    assert missing_error.value.status_code == denied_error.value.status_code


async def test_the_merged_answer_names_neither_the_key_nor_the_id(
    action: _Action, authenticated_user: UserData
) -> None:
    monitor = _RecordingMonitor()
    denied = _processor(_resolved, monitor, [_DenyingValidator()])

    with with_user(authenticated_user):
        with pytest.raises(GenericBadRequest) as error:
            await denied.run(action)

    message = str(error.value)
    assert action.key.canonical not in message
    assert str(_RESOLVED) not in message


async def test_the_audit_record_keeps_the_two_causes_apart(
    action: _Action, authenticated_user: UserData
) -> None:
    missing_monitor = _RecordingMonitor()
    denied_monitor = _RecordingMonitor()

    with with_user(authenticated_user):
        with pytest.raises(GenericBadRequest):
            await _processor(_missing, missing_monitor, [_PassingValidator()]).run(action)
        with pytest.raises(GenericBadRequest):
            await _processor(_resolved, denied_monitor, [_DenyingValidator()]).run(action)

    missing_meta = missing_monitor.done_results[0].meta
    denied_meta = denied_monitor.done_results[0].meta
    assert missing_meta.status is OperationStatus.ERROR
    assert denied_meta.status is OperationStatus.DENIED
    assert missing_meta.error_code != denied_meta.error_code
    assert "No Row matches the given key" in missing_meta.description
    assert str(_RESOLVED) in denied_meta.description


async def test_an_ungated_lookup_still_reports_the_miss(
    action: _Action, authenticated_user: UserData
) -> None:
    """``public_lookup_ops`` wires no post-validators: the key is public, so nothing is
    hidden by merging."""
    monitor = _RecordingMonitor()

    with with_user(authenticated_user):
        with pytest.raises(EntityNotFoundError):
            await _processor(_missing, monitor, []).run(action)

    assert monitor.done_results[0].meta.status is OperationStatus.ERROR


async def test_a_failure_that_is_neither_is_raised_unchanged(
    action: _Action, authenticated_user: UserData
) -> None:
    class _Unreachable(Exception):
        pass

    async def run(_: _Action) -> _Result:
        raise _Unreachable("the database is gone")

    monitor = _RecordingMonitor()

    with with_user(authenticated_user):
        with pytest.raises(_Unreachable):
            await _processor(run, monitor, [_PassingValidator()]).run(action)


_KEY_OWNER_LOOKUP_ACTIONS: list[tuple[LookupFieldOwnerByKeyOpsAction[Any], EntityIdentifier]] = [
    (LookupKeypairOwnerByAccessKeyAction(access_key=_ACCESS_KEY), UserID(uuid.uuid4())),
    (LookupKernelOwnerAction(kernel_id=KernelID(uuid.uuid4())), SessionID(uuid.uuid4())),
    (
        LookupAutoScalingRuleDeploymentAction(rule_id=uuid.uuid4()),
        DeploymentID(uuid.uuid4()),
    ),
    (
        LookupAccessTokenDeploymentAction(access_token_id=uuid.uuid4()),
        DeploymentID(uuid.uuid4()),
    ),
    (LookupRouteDeploymentAction(route_id=uuid.uuid4()), DeploymentID(uuid.uuid4())),
    (LookupRevisionDeploymentAction(revision_id=uuid.uuid4()), DeploymentID(uuid.uuid4())),
]


def _no_database() -> Any:
    """A provider no lookup reaches: the repository method under test is replaced
    before it runs."""
    return object()


def _group(
    validators: ActionValidators, monitor: _RecordingMonitor, action: BaseLookupAction
) -> ProcessorGroup[Any]:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(lookup=[monitor]),
            validators=validators,
            repository=OpsRepository(_no_database()),
        )
    )
    return registry.group(GroupMeta(action.entity_type()))


@pytest.mark.parametrize(
    ("action", "owner_id"), _KEY_OWNER_LOOKUP_ACTIONS, ids=lambda v: type(v).__name__
)
async def test_a_key_owner_lookup_merges_both_failures(
    action: LookupFieldOwnerByKeyOpsAction[Any],
    owner_id: EntityIdentifier,
    authenticated_user: UserData,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_monitor = _RecordingMonitor()
    denied_monitor = _RecordingMonitor()

    async def missing(*_: Any) -> EntityIdentifier:
        raise EntityNotFoundError("No field row matches the given key")

    async def found(*_: Any) -> EntityIdentifier:
        return owner_id

    missing_group = _group(
        ActionValidators(single_entity=[_PassingValidator()]), missing_monitor, action
    )
    denied_group = _group(
        ActionValidators(single_entity=[_DenyingValidator()]), denied_monitor, action
    )
    monkeypatch.setattr(OpsRepository, "field_owner_by_key", missing)
    missing_processor = missing_group.key_owner_lookup_ops(type(action))
    denied_processor = denied_group.key_owner_lookup_ops(type(action))

    with with_user(authenticated_user):
        with pytest.raises(GenericBadRequest) as missing_error:
            await missing_processor.run(action)
        monkeypatch.setattr(OpsRepository, "field_owner_by_key", found)
        with pytest.raises(GenericBadRequest) as denied_error:
            await denied_processor.run(action)

    assert str(missing_error.value) == str(denied_error.value)
    assert missing_error.value.status_code == denied_error.value.status_code
    assert str(owner_id) not in str(denied_error.value)
    assert missing_monitor.done_results[0].meta.status is OperationStatus.ERROR
    assert denied_monitor.done_results[0].meta.status is OperationStatus.DENIED


async def test_a_key_field_lookup_merges_both_failures(
    authenticated_user: UserData, monkeypatch: pytest.MonkeyPatch
) -> None:
    action = LookupKeypairByAccessKeyAction(access_key=_ACCESS_KEY)
    owner_id = UserID(uuid.uuid4())
    field_id = KeyPairID(uuid.uuid4())
    missing_monitor = _RecordingMonitor()
    denied_monitor = _RecordingMonitor()

    async def missing(*_: Any) -> tuple[KeyPairID, UserID]:
        raise EntityNotFoundError("No field row matches the given key")

    async def found(*_: Any) -> tuple[KeyPairID, UserID]:
        return field_id, owner_id

    missing_processor = _group(
        ActionValidators(single_entity=[_PassingValidator()]), missing_monitor, action
    ).key_field_lookup_ops(LookupKeypairByAccessKeyAction)
    denied_processor = _group(
        ActionValidators(single_entity=[_DenyingValidator()]), denied_monitor, action
    ).key_field_lookup_ops(LookupKeypairByAccessKeyAction)

    with with_user(authenticated_user):
        monkeypatch.setattr(OpsRepository, "field_by_key", missing)
        with pytest.raises(GenericBadRequest) as missing_error:
            await missing_processor.run(action)
        monkeypatch.setattr(OpsRepository, "field_by_key", found)
        with pytest.raises(GenericBadRequest) as denied_error:
            await denied_processor.run(action)

    assert str(missing_error.value) == str(denied_error.value)
    assert missing_error.value.status_code == denied_error.value.status_code
    assert str(field_id) not in str(denied_error.value)
    assert str(_ACCESS_KEY) not in str(denied_error.value)
    assert missing_monitor.done_results[0].meta.status is OperationStatus.ERROR
    assert denied_monitor.done_results[0].meta.status is OperationStatus.DENIED
