"""Update specs for error logs."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater


@dataclass
class ErrorLogSoftDeleteUpdater(DataUpdater[ErrorLogRow, ErrorLogData]):
    """Clear one error log.

    ``is_cleared`` is the column this domain deletes by. The value is constant rather
    than an argument, so the transition cannot be written backwards.
    """

    log_id: uuid.UUID

    @property
    @override
    def row_class(self) -> type[ErrorLogRow]:
        return ErrorLogRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.log_id

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_cleared": True}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: ErrorLogRow) -> ErrorLogData:
        return row.to_dataclass()
