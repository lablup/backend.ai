"""Base action class for export operations."""

from __future__ import annotations

from typing import override

from ai.backend.manager.actions.action import BaseAction


class ExportAction(BaseAction):
    """Base class for export-related actions."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "export"
