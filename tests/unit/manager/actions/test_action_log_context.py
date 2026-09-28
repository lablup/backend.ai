"""Every v2 processor run opens a log scope with the run and the entity it targets."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.contexts.request_id import with_request_context
from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.actions.v2.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta

LOGGER_NAME = "tests.manager.actions.action_log_context"
PROCESSOR_LOGGER_NAME = "ai.backend.manager.actions.v2.single_entity.processor"

_REGISTRY_ID = ContainerRegistryID(uuid.uuid5(uuid.NAMESPACE_OID, "registry"))


@dataclass
class _GetRegistryAction(BaseSingleEntityAction):
    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @classmethod
    @override
    def action_name(cls) -> str:
        return "get_registry"

    @override
    def entity_id(self) -> EntityIdentifier:
        return _REGISTRY_ID


class _RecordingMonitor(SingleEntityActionMonitor):
    action_ids: list[uuid.UUID]

    def __init__(self) -> None:
        self.action_ids = []

    @override
    async def prepare(self, meta: SingleEntityActionTriggerMeta) -> None:
        self.action_ids.append(meta.action_id)

    @override
    async def done(
        self, meta: SingleEntityActionTriggerMeta, result: SingleEntityActionProcessResult
    ) -> None:
        return


class _FailingMonitor(SingleEntityActionMonitor):
    @override
    async def prepare(self, meta: SingleEntityActionTriggerMeta) -> None:
        raise RuntimeError("monitor failed")

    @override
    async def done(
        self, meta: SingleEntityActionTriggerMeta, result: SingleEntityActionProcessResult
    ) -> None:
        return


@pytest.fixture
def log() -> StructuredLogger:
    return StructuredLogger(logging.getLogger(LOGGER_NAME))


@pytest.fixture
def capture(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    with (
        caplog.at_level(logging.INFO, logger=LOGGER_NAME),
        caplog.at_level(logging.INFO, logger=PROCESSOR_LOGGER_NAME),
    ):
        yield caplog


def _user() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


class TestActionLogContext:
    async def test_logs_inside_the_action_carry_the_run(
        self, log: StructuredLogger, capture: pytest.LogCaptureFixture
    ) -> None:
        monitor = _RecordingMonitor()

        async def run(_: _GetRegistryAction) -> None:
            log.info("inside action")

        processor = SingleEntityActionProcessor[_GetRegistryAction, None](run, monitors=[monitor])
        await processor.run(_GetRegistryAction())

        (record,) = [r for r in capture.records if r.name == LOGGER_NAME]
        assert record.__dict__["log_tag_action_id"] == str(monitor.action_ids[0])
        assert record.__dict__["log_tag_action_name"] == "get_registry"
        assert record.__dict__["log_tag_entity_type"] == str(_REGISTRY_ID.entity_type())
        assert record.__dict__["log_tag_entity_id"] == str(_REGISTRY_ID)

    async def test_request_and_user_scope_reach_the_action(
        self, log: StructuredLogger, capture: pytest.LogCaptureFixture
    ) -> None:
        user = _user()

        async def run(_: _GetRegistryAction) -> None:
            log.info("inside action")

        processor = SingleEntityActionProcessor[_GetRegistryAction, None](run)
        with with_request_context("req-1"), with_user_context(user, user):
            await processor.run(_GetRegistryAction())

        (record,) = [r for r in capture.records if r.name == LOGGER_NAME]
        assert record.__dict__["log_tag_request_id"] == "req-1"
        assert record.__dict__["log_tag_user_id"] == str(user.user_id)
        assert record.__dict__["log_tag_action_name"] == "get_registry"
        assert "log_tag_action_id" in record.__dict__

    async def test_monitor_failure_log_carries_the_run(
        self, capture: pytest.LogCaptureFixture
    ) -> None:
        async def run(_: _GetRegistryAction) -> None:
            return

        processor = SingleEntityActionProcessor[_GetRegistryAction, None](
            run, monitors=[_FailingMonitor()]
        )
        await processor.run(_GetRegistryAction())

        (record,) = [r for r in capture.records if r.name == PROCESSOR_LOGGER_NAME]
        assert record.getMessage() == "action monitor prepare failed"
        assert record.__dict__["log_tag_action_name"] == "get_registry"

    async def test_unexpected_failure_is_not_logged_by_the_processor(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        async def run(_: _GetRegistryAction) -> None:
            raise RuntimeError("unexpected")

        processor = SingleEntityActionProcessor[_GetRegistryAction, None](run)
        with (
            caplog.at_level(logging.DEBUG, logger="ai.backend.manager.actions"),
            pytest.raises(RuntimeError),
        ):
            await processor.run(_GetRegistryAction())

        assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []
