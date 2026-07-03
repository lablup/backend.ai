"""Valkey-backed reconciler flag implementation."""

from __future__ import annotations

from typing import override

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.manager.sokovan.reconciler.coordinator import ReconcilerFlag


class ValkeyReconcilerFlag(ReconcilerFlag):
    """Reconciler flag backed by the valkey schedule client's needed marks."""

    _valkey_schedule: ValkeyScheduleClient

    def __init__(self, valkey_schedule: ValkeyScheduleClient) -> None:
        self._valkey_schedule = valkey_schedule

    @override
    async def check_mark_needed(self, reconcile_type: str) -> bool:
        return await self._valkey_schedule.load_and_delete_schedule_mark(reconcile_type)
