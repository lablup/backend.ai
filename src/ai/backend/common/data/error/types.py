from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ErrorCodeData(BaseModel):
    """Structured error code representing domain, operation and error detail"""

    domain: str
    operation: str
    error_detail: str


class ErrorData(BaseModel):
    """Structured error information for data/API layer (domain-agnostic)"""

    error_code: ErrorCodeData
    title: str
    message: Optional[str] = None
    error_type: Optional[str] = None
    status_code: int = 500
