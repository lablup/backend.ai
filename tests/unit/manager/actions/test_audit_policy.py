"""Mutations are recorded unconditionally; reads are opt-in."""

from __future__ import annotations

import pytest

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.config.unified import AuditLogConfig


@pytest.mark.parametrize(
    "operation",
    [
        ActionOperationType.CREATE,
        ActionOperationType.UPDATE,
        ActionOperationType.DELETE,
        ActionOperationType.PURGE,
    ],
)
def test_successful_mutation_is_recorded_with_nothing_opted_in(
    operation: ActionOperationType,
) -> None:
    assert AuditLogPolicy([]).should_record(operation, OperationStatus.SUCCESS)


@pytest.mark.parametrize("operation", [ActionOperationType.GET, ActionOperationType.SEARCH])
def test_successful_read_is_not_recorded_unless_opted_in(
    operation: ActionOperationType,
) -> None:
    assert not AuditLogPolicy([]).should_record(operation, OperationStatus.SUCCESS)


def test_opting_an_operation_in_covers_every_entity_type() -> None:
    policy = AuditLogPolicy([ActionOperationType.SEARCH])

    assert policy.should_record(ActionOperationType.SEARCH, OperationStatus.SUCCESS)
    assert policy.should_record(ActionOperationType.SEARCH, OperationStatus.SUCCESS)
    # A read operation left out stays off.
    assert not policy.should_record(ActionOperationType.GET, OperationStatus.SUCCESS)


@pytest.mark.parametrize(
    "status",
    [OperationStatus.ERROR, OperationStatus.DENIED, OperationStatus.UNKNOWN],
)
def test_unsuccessful_read_is_recorded_without_opting_in(status: OperationStatus) -> None:
    assert AuditLogPolicy([]).should_record(ActionOperationType.SEARCH, status)


def test_config_rejects_mutating_operations() -> None:
    with pytest.raises(BackendAISchemaValidationFailed):
        AuditLogConfig.model_validate({"record-read-operations": ["delete"]})


def test_config_defaults_to_recording_no_reads() -> None:
    assert AuditLogConfig.model_validate({}).record_read_operations == []
