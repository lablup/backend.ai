"""Errors of `PartialRecord` (`common/data/partial.py`). Each one is a code defect."""

from __future__ import annotations

from ai.backend.common.exception import UnreachableError


class NotSelectedError(UnreachableError):
    error_type = "https://api.backend.ai/probs/partial-record-field-not-selected"
    error_title = "The field was not selected for this partial record."


class InvalidPartialRecordError(UnreachableError):
    """A partial record declared or constructed with fields its class does not allow."""

    error_type = "https://api.backend.ai/probs/invalid-partial-record"
    error_title = "Invalid partial record."


class FrozenPartialRecordError(UnreachableError):
    error_type = "https://api.backend.ai/probs/frozen-partial-record"
    error_title = "A partial record cannot be changed."
