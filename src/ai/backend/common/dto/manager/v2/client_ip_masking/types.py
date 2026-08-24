"""Shared enums for the client IP masking DTO v2."""

from __future__ import annotations

import enum

__all__ = (
    "ClientIPMaskingMode",
    "ClientIPMaskingPolicyOrderField",
    "ClientIPMaskingTarget",
)


class ClientIPMaskingTarget(enum.StrEnum):
    """Which recorded client IP a policy row governs.

    ``DEFAULT`` is the fallback the other targets inherit; it is a target value rather
    than a column so a row exists for each and no row has to be singled out.
    """

    DEFAULT = "default"
    LOGIN_HISTORY = "login_history"


class ClientIPMaskingMode(enum.StrEnum):
    NONE = "none"
    TRUNCATE = "truncate"
    DROP = "drop"


class ClientIPMaskingPolicyOrderField(enum.StrEnum):
    TARGET_TYPE = "target_type"
    MODE = "mode"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
