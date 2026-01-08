from __future__ import annotations

from typing import override

from ai.backend.manager.actions.action import BaseAction


class AuditLogAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "audit_log"
