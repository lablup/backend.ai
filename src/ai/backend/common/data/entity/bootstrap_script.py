from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import DanglingFieldType, FieldIdentifier, FieldType

__all__ = ("BootstrapScript", "BootstrapScriptFieldType", "BootstrapScriptID")


class BootstrapScriptFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "bootstrap_script"

    @override
    @classmethod
    def description(cls) -> str:
        return "The script a session runs at startup, set on an entity of any kind."


class BootstrapScriptID(FieldIdentifier):
    """One bootstrap script set on one entity."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return BootstrapScriptFieldType()


class BootstrapScript(str):
    """The text of a bootstrap script."""

    @classmethod
    def empty(cls) -> BootstrapScript:
        return cls("")
