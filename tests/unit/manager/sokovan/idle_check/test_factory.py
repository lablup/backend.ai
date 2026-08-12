from __future__ import annotations

from unittest.mock import MagicMock

from ai.backend.manager.sokovan.stages.factory import build_reconciler_coordinator


class TestFactoryRegistration:
    def test_idle_check_stages_are_not_registered(self) -> None:
        # The idle-check stages stay unregistered on 26.8 (BA-7344).
        _, task_specs = build_reconciler_coordinator(
            replica_group_repository=MagicMock(),
            valkey_schedule=MagicMock(),
            lock_factory=MagicMock(),
            config_provider=MagicMock(),
        )

        assert {
            "idle_check_assignment_sync",
            "idle_check_initial_grace_period",
            "idle_check_judgment",
            "idle_check_sweep",
        }.isdisjoint({task_spec.reconcile_type for task_spec in task_specs})
