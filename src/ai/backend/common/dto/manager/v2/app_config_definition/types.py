"""Enum types for app_config_definition v2 DTOs."""

from __future__ import annotations

from enum import StrEnum

__all__ = ("AppConfigDefinitionOrderField",)


class AppConfigDefinitionOrderField(StrEnum):
    CONFIG_NAME = "config_name"
    CREATED_AT = "created_at"
