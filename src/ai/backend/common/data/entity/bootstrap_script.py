from __future__ import annotations

import re
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
    """Script text with LF line breaks and no surrounding whitespace."""

    @classmethod
    def from_text(cls, text: str) -> BootstrapScript:
        return cls(re.sub(r"\r\n?", "\n", text).strip())

    @classmethod
    def empty(cls) -> BootstrapScript:
        return cls("")
