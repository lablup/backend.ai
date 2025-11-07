from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Self

import strawberry

if TYPE_CHECKING:
    from ai.backend.common.data.error.types import ErrorCodeData, ErrorData


@strawberry.type(
    name="ErrorCode",
    description="Structured error code representing domain, operation and error detail",
)
class ErrorCode:
    domain: str = strawberry.field(description="Error domain (e.g., 'api', 'kernel', 'session')")
    operation: str = strawberry.field(
        description="Operation where error occurred (e.g., 'create', 'delete', 'update')"
    )
    error_detail: str = strawberry.field(
        description="Specific error detail (e.g., 'not-found', 'timeout', 'forbidden')"
    )

    @classmethod
    def from_dataclass(cls, error_code: ErrorCodeData) -> ErrorCode:
        """
        Create a GraphQL ErrorCode from an ErrorCode dataclass.
        """
        return cls(
            domain=error_code.domain,
            operation=error_code.operation,
            error_detail=error_code.error_detail,
        )


@strawberry.type(description="Structured error information from Backend.AI API")
class BackendAIGQLError:
    error_code: ErrorCode = strawberry.field(
        description="Structured error code with domain, operation, and error detail"
    )
    title: str = strawberry.field(description="Human-readable error title")
    message: Optional[str] = strawberry.field(
        default=None, description="Additional error message with context"
    )
    error_type: Optional[str] = strawberry.field(
        default=None, description="RFC-7807 error type URL"
    )

    @classmethod
    def from_dataclass(cls, error_data: ErrorData) -> Self:
        """
        Create a GraphQL BackendAIError from an ErrorData.
        """
        return cls(
            error_code=ErrorCode(
                domain=error_data.error_code.domain,
                operation=error_data.error_code.operation,
                error_detail=error_data.error_code.error_detail,
            ),
            title=error_data.title,
            message=error_data.message,
            error_type=error_data.error_type,
        )
