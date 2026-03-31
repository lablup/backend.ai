from __future__ import annotations

from enum import StrEnum


class RuntimeVariantPresetOrderField(StrEnum):
    NAME = "name"
    RANK = "rank"
    CREATED_AT = "created_at"


class PresetTarget(StrEnum):
    ENV = "env"
    ARGS = "args"


class PresetValueType(StrEnum):
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
