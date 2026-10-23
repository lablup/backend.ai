from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import DanglingFieldType, FieldIdentifier, FieldType

__all__ = ("BootstrapScriptRevisionFieldType", "BootstrapScriptRevisionID")


class BootstrapScriptRevisionFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "bootstrap_script_revision"

    @override
    @classmethod
    def description(cls) -> str:
        return "One write of a bootstrap script's content, numbered within that script."


class BootstrapScriptRevisionID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return BootstrapScriptRevisionFieldType()
