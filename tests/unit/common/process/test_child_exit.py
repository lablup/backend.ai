from __future__ import annotations

import pytest

from ai.backend.common.process.child_exit import ChildExitMonitor, ChildStatus


class TestChildExitMonitorRaiseSystemExit:
    def test_passes_when_every_child_shut_down_cleanly(self) -> None:
        statuses = tuple(ChildStatus() for _ in range(2))
        for status in statuses:
            status.mark_clean_shutdown()

        ChildExitMonitor(statuses).raise_system_exit()

    def test_fails_when_a_child_did_not_shut_down(self) -> None:
        statuses = (ChildStatus(), ChildStatus())
        statuses[0].mark_clean_shutdown()

        with pytest.raises(SystemExit) as exc_info:
            ChildExitMonitor(statuses).raise_system_exit()

        assert exc_info.value.code == 1

    def test_fails_when_a_child_initialization_failed(self) -> None:
        # A child whose initialization failed still runs its shutdown routines.
        status = ChildStatus()
        status.mark_init_failed()
        status.mark_clean_shutdown()

        with pytest.raises(SystemExit) as exc_info:
            ChildExitMonitor((status,)).raise_system_exit()

        assert exc_info.value.code == 1

    def test_passes_without_children(self) -> None:
        ChildExitMonitor(()).raise_system_exit()
