from __future__ import annotations

from unittest.mock import MagicMock

from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.stages.factory import build_reconciler_coordinator
from ai.backend.manager.sokovan.stages.idle_check import build_idle_check_stage


class TestBuildIdleCheckStage:
    def test_registration_metadata(self) -> None:
        registration = build_idle_check_stage()
        assert registration.reconcile_type == "idle_check"
        assert registration.stage.lock_id == LockID.LOCKID_IDLE_CHECK_RECONCILE
        assert registration.task_spec.reconcile_type == "idle_check"
        assert registration.task_spec.short_interval == 10.0
        assert registration.task_spec.long_interval == 60.0


class TestFactoryRegistration:
    def test_idle_check_is_registered(self) -> None:
        _, task_specs = build_reconciler_coordinator(
            replica_group_repository=MagicMock(),
            valkey_schedule=MagicMock(),
            lock_factory=MagicMock(),
            config_provider=MagicMock(),
        )
        assert "idle_check" in {task_spec.reconcile_type for task_spec in task_specs}
