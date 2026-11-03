# 서버 측 CSV 로 내보내기 API

## 관련 이슈

- JIRA: BA-2922 (Epic), BA-3823 (BEP Task), BA-3818~BA-3822 (Implementation Stories)
- GitHub: #6583

## 동기

현재 CSV 로 내보내기 기능은 클라이언트에서 모든 페이지를 순회해 데이터를 받아 온 뒤 CSV 파일을 생성한다.
데이터가 큰 경우(수만 건 이상) 이 방식에는 다음과 같은 문제가 있다.

1. **성능 문제**: 수백 번의 API 요청을 순차로 실행해야 한다
2. **메모리 문제**: 모든 데이터를 브라우저 메모리에 적재해야 한다
3. **UX 문제**: UI 가 멈추거나 브라우저가 타임아웃되거나 충돌할 위험이 있다
4. **네트워크 비효율**: 페이지네이션 비용이 누적된다

이 문제를 해결하려고 서버 측 CSV 로 내보내기를 구현한다.

## 현재 설계

### 클라이언트 측 CSV 로 내보내기 (현재)

```typescript
// react/src/components/UserResourcePolicyList.tsx:246-274
const handleExportCSV = () => {
  // 1. Collect data by iterating through all pages (multiple API calls)
  // 2. Transform data on the client
  const responseData = _.map(user_resource_policies, (policy) => {
    return _.pick(policy, columnKeys.map((key) => key as keyof UserResourcePolicies));
  });
  // 3. Generate and download CSV file
  exportCSVWithFormattingRules(responseData, 'user-resource-policies', formatRules);
};
```

### 기존 repository 패턴

```python
# repositories/base/querier.py
@dataclass
class BatchQuerier:
    pagination: QueryPagination
    conditions: list[QueryCondition] = field(default_factory=list)
    orders: list[QueryOrder] = field(default_factory=list)

async def execute_batch_querier(
    db_sess: SASession,
    query: sa.sql.Select,
    querier: BatchQuerier,
) -> BatchQuerierResult[Row]:
    # Returns page-sized data with a single query
    ...
```

### 기존 스트리밍 패턴

```python
# repositories/schedule/repository.py - Example of db_sess.stream() usage
async for row in await db_sess.stream(comprehensive_query):
    result.append(SessionResourcePolicyData(...))
```

## 제안 설계

### 1. 설정

`ManagerUnifiedConfig` 에 내보내기 관련 설정을 추가한다. 기존 설정 패턴(`BaseConfigSchema`, `BackendAIConfigMeta`)을 따른다.

```python
# Add to manager/config/unified.py

class ExportConfig(BaseConfigSchema):
    """Export-related configuration.

    Example in manager.toml:
    ```toml
    [export]
    max-rows = 100000
    statement-timeout-sec = 300
    max-concurrent-exports = 3
    ```
    """

    max_rows: Annotated[
        int,
        Field(
            default=100_000,
            ge=1000,
            le=1_000_000,
            validation_alias=AliasChoices("max-rows", "max_rows"),
            serialization_alias="max-rows",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of rows per export request. "
                "Limits the amount of data that can be exported in a single request "
                "to prevent memory exhaustion and timeout issues."
            ),
            added_version="26.1.0",
            example=ConfigExample(local="100000", prod="100000"),
        ),
    ]

    statement_timeout_sec: Annotated[
        int,
        Field(
            default=300,
            ge=60,
            le=3600,
            validation_alias=AliasChoices("statement-timeout-sec", "statement_timeout_sec"),
            serialization_alias="statement-timeout-sec",
        ),
        BackendAIConfigMeta(
            description=(
                "Database statement timeout in seconds for export queries. "
                "Long-running export queries will be cancelled after this duration."
            ),
            added_version="26.1.0",
            example=ConfigExample(local="300", prod="300"),
        ),
    ]

    max_concurrent_exports: Annotated[
        int,
        Field(
            default=3,
            ge=1,
            le=10,
            validation_alias=AliasChoices("max-concurrent-exports", "max_concurrent_exports"),
            serialization_alias="max-concurrent-exports",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of concurrent export requests allowed. "
                "Prevents system overload from too many simultaneous export operations."
            ),
            added_version="26.1.0",
            example=ConfigExample(local="3", prod="3"),
        ),
    ]


# Add to ManagerUnifiedConfig
class ManagerUnifiedConfig(BaseConfigSchema):
    # ... existing fields ...
    export: Annotated[
        ExportConfig,
        Field(default_factory=ExportConfig),
        BackendAIConfigMeta(
            description="Export API configuration.",
            added_version="26.1.0",
            composite=CompositeType.FIELD,
        ),
    ]
```

### 2. 핵심 타입

#### 2.1 StreamingExportQuery

스트리밍 내보내기의 질의 조건을 정의한다. 설정 값은 호출 시점에 전달한다.

```python
# repositories/base/export.py

from dataclasses import dataclass, field

from .types import QueryCondition, QueryOrder


@dataclass(frozen=True)
class StreamingExportQuery:
    """Query definition for streaming export.

    Similar to BatchQuerier but streams all data without pagination.
    Limits export size with max_rows.

    Attributes:
        conditions: WHERE clause conditions
        orders: ORDER BY clause sort conditions
        max_rows: Maximum export row count (passed from config.export.max_rows)
        statement_timeout_sec: DB statement timeout (passed from config.export.statement_timeout_sec)
    """

    conditions: list[QueryCondition] = field(default_factory=list)
    orders: list[QueryOrder] = field(default_factory=list)
    max_rows: int  # Passed from config, no default value
    statement_timeout_sec: int  # Passed from config, no default value


class ExportLimitExceeded(Exception):
    """Raised when export row limit is exceeded."""
    pass
```

#### 2.2 내보내기 field 정의

내보낼 수 있는 field 를 정의한다. 내부 정의에는 dataclass 를, API 입력과 출력에는 Mapping 을 사용한다.

```python
# repositories/base/export.py

from dataclasses import dataclass
from enum import StrEnum


class ExportFieldType(StrEnum):
    """Export field type."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    UUID = "uuid"
    JSON = "json"


# Formatter type definition
type ExportFormatter = Callable[[Any], str]


@dataclass(frozen=True)
class ExportFieldDef:
    """Export field definition.

    Informs clients which fields can be selected,
    and used for actual data transformation.
    """
    key: str                    # Field identifier (used in API requests)
    name: str                   # Name displayed in CSV header
    description: str            # Field description (displayed in client UI)
    field_type: ExportFieldType # Field type
    accessor: str               # Attribute name to get value from Row
    is_default: bool = True     # Whether to include in default export
    formatter: ExportFormatter | None = None  # Custom formatter (None uses default conversion)
```

#### 2.3 ReportDefinition

여러 테이블을 조합한 report 를 정의한다.

```python
# repositories/base/export.py

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import sqlalchemy as sa


@dataclass
class ReportDef:
    """Export report definition.

    Defines single table or composite reports with multiple table JOINs.
    """
    report_key: str                                   # Report identifier (e.g., "audit-logs")
    name: str                                         # Report name
    description: str                                  # Report description
    fields: list[ExportFieldDef]                      # Available field list
    base_query_builder: Callable[[], sa.sql.Select]   # Base query builder

    def get_field(self, key: str) -> ExportFieldDef | None:
        """Find field definition by key."""
        for f in self.fields:
            if f.key == key:
                return f
        return None

    def get_default_field_keys(self) -> list[str]:
        """Return default field key list."""
        return [f.key for f in self.fields if f.is_default]

    def get_field_keys(self) -> set[str]:
        """Return all field keys."""
        return {f.key for f in self.fields}

    def validate_field_keys(self, requested_keys: list[str]) -> list[str]:
        """Return invalid field keys."""
        valid_keys = self.get_field_keys()
        return [k for k in requested_keys if k not in valid_keys]
```

### 3. Repository 계층: 범용 내보내기 함수

범용 `execute_streaming_export` 함수를 제공하고, 각 도메인이 테이블과 field 를 지정해 호출한다.

#### 3.1 공통 스트리밍 내보내기 함수

```python
# repositories/base/export.py

from collections.abc import AsyncIterator
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession


async def execute_streaming_export(
    db_sess: SASession,
    query: StreamingExportQuery,
    base_query: sa.sql.Select,
    report: ReportDef,
    selected_keys: list[str],
) -> AsyncIterator[dict[str, Any]]:
    """Common function for streaming export execution.

    Uses db_sess.stream() for server-side cursor data streaming.
    Uses only async for, no manual chunking.

    Args:
        db_sess: DB session
        query: Export query conditions (conditions, orders, max_rows, statement_timeout_sec)
        base_query: Base SELECT query (table/JOIN definition)
        report: ReportDef (includes field definitions)
        selected_keys: Selected field key list

    Yields:
        dict[str, Any]: Row data containing only selected fields
    """
    # Apply conditions
    for condition in query.conditions:
        base_query = base_query.where(condition())

    # Apply ordering
    for order in query.orders:
        base_query = base_query.order_by(order)

    # Apply max_rows LIMIT
    base_query = base_query.limit(query.max_rows)

    # Set statement timeout
    await db_sess.execute(
        sa.text(f"SET statement_timeout = '{query.statement_timeout_sec}s'")
    )

    # Server-side cursor streaming
    result = await db_sess.stream(base_query)

    # Iterate rows with async for (db_sess.stream handles internally)
    async for row in result:
        yield _transform_row(row, report, selected_keys)


def _transform_row(
    row: Any,
    report: ReportDef,
    selected_keys: list[str],
) -> dict[str, Any]:
    """Transform row to dict containing only selected fields."""
    result: dict[str, Any] = {}
    for key in selected_keys:
        field_def = report.get_field(key)
        if field_def is None:
            continue
        value = _get_value(row, field_def.accessor)
        # Apply custom formatter if present
        if field_def.formatter is not None:
            value = field_def.formatter(value)
        result[key] = value
    return result


def _get_value(obj: Any, accessor: str) -> Any:
    """Get value by accessor path (supports dot notation)."""
    parts = accessor.split(".")
    value = obj
    for part in parts:
        if value is None:
            return None
        if hasattr(value, part):
            value = getattr(value, part)
        elif isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value
```

#### 3.2 도메인별 report 정의 예시 (감사 로그)

```python
# repositories/export/reports/audit_log.py

import sqlalchemy as sa

from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    ReportDef,
)


def _build_audit_log_query() -> sa.sql.Select:
    """Base query for audit log export."""
    return sa.select(AuditLogRow)


# Field definitions (dataclass list)
AUDIT_LOG_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="id",
        name="ID",
        description="Unique identifier of the audit log entry",
        field_type=ExportFieldType.UUID,
        accessor="id",
    ),
    ExportFieldDef(
        key="action_id",
        name="Action ID",
        description="ID of the action that triggered this log",
        field_type=ExportFieldType.UUID,
        accessor="action_id",
    ),
    ExportFieldDef(
        key="entity_type",
        name="Entity Type",
        description="Type of entity affected (e.g., session, user)",
        field_type=ExportFieldType.STRING,
        accessor="entity_type",
    ),
    ExportFieldDef(
        key="entity_id",
        name="Entity ID",
        description="ID of the affected entity",
        field_type=ExportFieldType.STRING,
        accessor="entity_id",
    ),
    ExportFieldDef(
        key="operation",
        name="Operation",
        description="Type of operation performed",
        field_type=ExportFieldType.STRING,
        accessor="operation",
    ),
    ExportFieldDef(
        key="status",
        name="Status",
        description="Operation status (success, failure, etc.)",
        field_type=ExportFieldType.STRING,
        accessor="status",
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Timestamp when the log was created",
        field_type=ExportFieldType.DATETIME,
        accessor="created_at",
    ),
    ExportFieldDef(
        key="description",
        name="Description",
        description="Human-readable description of the action",
        field_type=ExportFieldType.STRING,
        accessor="description",
        is_default=False,
    ),
    ExportFieldDef(
        key="request_id",
        name="Request ID",
        description="ID of the API request that triggered this action",
        field_type=ExportFieldType.STRING,
        accessor="request_id",
        is_default=False,
    ),
    ExportFieldDef(
        key="triggered_by",
        name="Triggered By",
        description="User or system that triggered this action",
        field_type=ExportFieldType.STRING,
        accessor="triggered_by",
        is_default=False,
    ),
]


# Report definition
AUDIT_LOG_REPORT = ReportDef(
    report_key="audit-logs",
    name="Audit Logs",
    description="System audit log records for compliance and monitoring",
    fields=AUDIT_LOG_FIELDS,
    base_query_builder=_build_audit_log_query,
)
```

#### 3.3 Report registry

```python
# repositories/export/registry.py

from collections.abc import Mapping

from ai.backend.manager.repositories.base.export import ReportDef

from .reports.audit_log import AUDIT_LOG_REPORT
# from .reports.session import SESSION_REPORT
# from .reports.user import USER_REPORT
# from .reports.project import PROJECT_REPORT


# Register all reports (report_key → ReportDef)
EXPORT_REPORTS: Mapping[str, ReportDef] = {
    AUDIT_LOG_REPORT.report_key: AUDIT_LOG_REPORT,
    # SESSION_REPORT.report_key: SESSION_REPORT,
    # USER_REPORT.report_key: USER_REPORT,
    # PROJECT_REPORT.report_key: PROJECT_REPORT,
}


def get_report(report_key: str) -> ReportDef | None:
    """Get ReportDef by report_key."""
    return EXPORT_REPORTS.get(report_key)


def list_reports() -> list[ReportDef]:
    """Return all report list."""
    return list(EXPORT_REPORTS.values())
```

### 4. Service 계층

```python
# services/export/service.py

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.export import (
    execute_streaming_export,
    ReportDef,
    StreamingExportQuery,
)
from ai.backend.manager.repositories.export.registry import (
    get_report,
    list_reports as list_all_reports,
)
from .csv_stream import CSVExportStreamReader


class TooManyConcurrentExports(Exception):
    """Concurrent export request limit exceeded."""
    pass


class ExportService:
    """CSV Export service."""

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        max_concurrent_exports: int,
    ) -> None:
        self._db = db
        self._semaphore = asyncio.Semaphore(max_concurrent_exports)

    def get_report(self, report_key: str) -> ReportDef | None:
        """Get ReportDef by report_key."""
        return get_report(report_key)

    def list_reports(self) -> list[ReportDef]:
        """List all available reports."""
        return list_all_reports()

    async def export_csv(
        self,
        report_key: str,
        query: StreamingExportQuery,
        field_keys: list[str] | None = None,
    ) -> CSVExportStreamReader:
        """Export report to CSV.

        Args:
            report_key: Report identifier
            query: Export query conditions (passed with config values populated)
            field_keys: Field key list to select (None uses default fields)

        Returns:
            CSVExportStreamReader: CSV streaming reader

        Raises:
            ValueError: Invalid report_key or field_keys
            TooManyConcurrentExports: Concurrent export limit exceeded
        """
        report = self.get_report(report_key)
        if report is None:
            raise ValueError(f"Unknown report: {report_key}")

        # Field selection
        if field_keys is None:
            selected_keys = report.get_default_field_keys()
        else:
            invalid_keys = report.validate_field_keys(field_keys)
            if invalid_keys:
                raise ValueError(f"Invalid field keys: {invalid_keys}")
            selected_keys = field_keys

        # Check concurrent export limit (non-blocking)
        if self._semaphore.locked():
            raise TooManyConcurrentExports(
                "Too many concurrent export requests. Please try again later."
            )

        filename = f"{report_key}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

        return CSVExportStreamReader(
            data_iterator=self._stream_with_semaphore(report, query, selected_keys),
            report=report,
            selected_keys=selected_keys,
            filename=filename,
        )

    async def _stream_with_semaphore(
        self,
        report: ReportDef,
        query: StreamingExportQuery,
        selected_keys: list[str],
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream with semaphore limiting concurrent exports."""
        async with self._semaphore:
            async with self._db.begin_readonly_session() as db_sess:
                base_query = report.base_query_builder()
                async for row_data in execute_streaming_export(
                    db_sess, query, base_query, report, selected_keys
                ):
                    yield row_data
```

### 5. HTTP Trailer 를 사용하는 CSV StreamReader

스트리밍 도중 에러가 발생하면 HTTP Trailer 로 에러 상태를 클라이언트에 전달한다.
HTTP Trailer 는 chunked transfer encoding 에서 body 전송이 끝난 뒤 추가 메타데이터를 보내는 표준 방식이다.


```python
# services/export/csv_stream.py

import csv
import io
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.api_handlers import StreamReader
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.base.export import ReportDef

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ExportStatus:
    """Export result status."""
    success: bool
    error_message: str | None = None
    rows_exported: int = 0


class CSVExportStreamReader(StreamReader):
    """CSV export StreamReader with HTTP Trailer support.

    Converts data to CSV format for streaming.
    Since execute_streaming_export yields dict per row,
    this converts them to CSV rows for streaming.

    When an error occurs during streaming, the error status is conveyed via HTTP Trailer.
    Clients check the Trailer header to determine export success.
    """

    def __init__(
        self,
        data_iterator: AsyncIterator[dict[str, Any]],
        report: ReportDef,
        selected_keys: list[str],
        filename: str,
    ) -> None:
        self._data_iterator = data_iterator
        self._report = report
        self._selected_keys = selected_keys
        self._filename = filename
        self._status = ExportStatus(success=True)

    @override
    def content_type(self) -> Optional[str]:
        return "text/csv; charset=utf-8"

    def content_disposition(self) -> str:
        return f'attachment; filename="{self._filename}"'

    def get_trailer_headers(self) -> dict[str, str]:
        """Return HTTP Trailer headers.

        Called after streaming completes to return final status.
        Clients check these headers to determine export success.

        Returns:
            X-Export-Status: "success" or "error"
            X-Export-Error: Error message (only on error)
            X-Export-Rows: Number of successfully exported rows
        """
        headers = {
            "X-Export-Status": "success" if self._status.success else "error",
            "X-Export-Rows": str(self._status.rows_exported),
        }
        if self._status.error_message:
            headers["X-Export-Error"] = self._status.error_message
        return headers

    @override
    async def read(self) -> AsyncIterator[bytes]:
        # UTF-8 BOM for Excel compatibility
        yield b'\xef\xbb\xbf'

        # CSV header (use name of selected fields)
        output = io.StringIO()
        writer = csv.writer(output)
        header = []
        for key in self._selected_keys:
            field_def = self._report.get_field(key)
            header.append(field_def.name if field_def else key)
        writer.writerow(header)
        yield output.getvalue().encode('utf-8')

        # CSV rows (streaming per row)
        try:
            async for row_data in self._data_iterator:
                output = io.StringIO()
                writer = csv.writer(output)
                row = [
                    self._format_value(row_data.get(key))
                    for key in self._selected_keys
                ]
                writer.writerow(row)
                yield output.getvalue().encode('utf-8')
                self._status.rows_exported += 1
        except Exception as e:
            # Update status on streaming error
            self._status.success = False
            self._status.error_message = str(e)
            log.error("Export streaming error: {}", e)
            # Already transmitted data remains valid on error
            # Client checks Trailer to determine partial completion

    def _format_value(self, value: Any) -> str:
        """Convert value to CSV string.

        Performs only type-based default conversion.
        Custom formatters are applied in _transform_row.
        """
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            import json
            return json.dumps(value, default=str, ensure_ascii=False)
        return str(value)
```

#### 5.1 HTTP Trailer 적용 (API 응답)


```python
# api/export.py - Modified _export_csv method

async def _export_csv(
    self,
    request: web.Request,
    report_key: str,
    field_keys: Optional[list[str]],
    filter_obj: Optional[...],
    order_obj: Optional[ExportOrder],
) -> web.StreamResponse:
    """Common CSV export logic (with HTTP Trailer support)."""
    # ... (existing logic) ...

    csv_stream = await service.export_csv(
        report_key=report_key,
        query=export_query,
        field_keys=field_keys,
    )

    # StreamResponse with Trailer support
    response = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": csv_stream.content_type(),
            "Content-Disposition": csv_stream.content_disposition(),
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
            # Trailer header declaration (informs client that Trailer will follow)
            "Trailer": "X-Export-Status, X-Export-Error, X-Export-Rows",
        },
    )
    await response.prepare(request)

    # Stream CSV data
    async for chunk in csv_stream.read():
        await response.write(chunk)

    # Write trailer headers (may need custom implementation if aiohttp doesn't support directly)
    # Or use approach of including status info in the last chunk
    trailer_headers = csv_stream.get_trailer_headers()
    # Check if aiohttp's write_eof() supports trailers
    # If not supported, alternative: include status as JSON in last line

    await response.write_eof()
    return response
```

#### 5.2 클라이언트의 Trailer 처리


```python
# client/func/export.py - download_csv method

async def download_csv(
    self,
    report_key: str,
    output_path: Path,
    *,
    fields: Optional[Sequence[str]] = None,
    filter_: Optional[dict[str, Any]] = None,
    order: Optional[dict[str, str]] = None,
    chunk_size: int = 8192,
) -> tuple[Path, ExportStatus]:
    """Download report as CSV (with HTTP Trailer status check).

    Returns:
        tuple[Path, ExportStatus]: (saved file path, export status)
    """
    # ... (existing logic) ...

    async with rqst.fetch() as resp:
        with open(output_path, "wb") as f:
            async for chunk in resp.content.iter_chunked(chunk_size):
                f.write(chunk)

        # Check Trailer headers (if aiohttp supports)
        # If aiohttp doesn't support trailers, use alternative approach
        export_status = ExportStatus(
            success=resp.headers.get("X-Export-Status") == "success",
            error_message=resp.headers.get("X-Export-Error"),
            rows_exported=int(resp.headers.get("X-Export-Rows", 0)),
        )

    return output_path, export_status
```

> **참고**: HTTP Trailer 는 표준 기능이지만 모든 HTTP 클라이언트와 proxy 가 지원하지는 않는다.
> aiohttp 클라이언트의 trailer 지원을 확인하고, 지원하지 않으면 응답 끝에 구분자와 함께 JSON 상태를 넣는
> 대안을 검토한다.

### 6. API 계층

Notification API 패턴을 따라 POST 요청으로 복잡한 filter 와 정렬을 지원한다.

#### 6.1 DTO 정의 (common/dto)


```python
# common/dto/manager/export/request.py

from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import Field

from ai.backend.common.dto.base import BaseRequestModel
from ai.backend.common.dto.common import OrderDirection, StringFilter


class DateTimeFilter(BaseRequestModel):
    """Date/time filter.

    Uses the same fields as existing GQL DateTimeFilter (api/gql/base.py).
    Multiple conditions are combined with AND.

    Example:
        # After specific time
        {"after": "2024-01-01T00:00:00Z"}

        # Range specification
        {"after": "2024-01-01T00:00:00Z", "before": "2024-02-01T00:00:00Z"}

        # Exact match (equals)
        {"equals": "2024-01-15T12:00:00Z"}
    """
    before: Optional[datetime] = Field(
        default=None,
        description="Before this point (<)",
    )
    after: Optional[datetime] = Field(
        default=None,
        description="After this point (>)",
    )
    equals: Optional[datetime] = Field(
        default=None,
        description="Exact match (=)",
    )
    not_equals: Optional[datetime] = Field(
        default=None,
        description="Not equal (!=)",
    )


class ExportOrderField(StrEnum):
    """Export sort field (common)."""
    CREATED_AT = "created_at"
    ID = "id"


class ExportOrder(BaseRequestModel):
    """Export sort criteria."""
    field: ExportOrderField = Field(default=ExportOrderField.CREATED_AT)
    direction: OrderDirection = Field(default=OrderDirection.DESC)


# === Audit Log Export ===

class AuditLogFilter(BaseRequestModel):
    """Audit Log export filter."""
    entity_type: Optional[StringFilter] = Field(default=None)
    entity_id: Optional[StringFilter] = Field(default=None)
    operation: Optional[StringFilter] = Field(default=None)
    status: Optional[StringFilter] = Field(default=None)
    triggered_by: Optional[StringFilter] = Field(default=None)
    created_at: Optional[DateTimeFilter] = Field(default=None)


class ExportAuditLogsRequest(BaseRequestModel):
    """Audit Log CSV export request."""
    fields: Optional[list[str]] = Field(
        default=None,
        description="Field key list to export. None uses default fields",
    )
    filter: Optional[AuditLogFilter] = Field(default=None)
    order: Optional[ExportOrder] = Field(default=None)


# === Session Export ===

class SessionFilter(BaseRequestModel):
    """Session export filter."""
    name: Optional[StringFilter] = Field(default=None)
    status: Optional[list[str]] = Field(default=None)
    access_key: Optional[StringFilter] = Field(default=None)
    domain_name: Optional[StringFilter] = Field(default=None)
    group_id: Optional[str] = Field(default=None)
    created_at: Optional[DateTimeFilter] = Field(default=None)


class ExportSessionsRequest(BaseRequestModel):
    """Session CSV export request."""
    fields: Optional[list[str]] = Field(default=None)
    filter: Optional[SessionFilter] = Field(default=None)
    order: Optional[ExportOrder] = Field(default=None)


# === User Export ===

class UserFilter(BaseRequestModel):
    """User export filter."""
    email: Optional[StringFilter] = Field(default=None)
    username: Optional[StringFilter] = Field(default=None)
    domain_name: Optional[StringFilter] = Field(default=None)
    status: Optional[list[str]] = Field(default=None)
    role: Optional[list[str]] = Field(default=None)


class ExportUsersRequest(BaseRequestModel):
    """User CSV export request."""
    fields: Optional[list[str]] = Field(default=None)
    filter: Optional[UserFilter] = Field(default=None)
    order: Optional[ExportOrder] = Field(default=None)


# === Project Export ===

class ProjectFilter(BaseRequestModel):
    """Project export filter."""
    name: Optional[StringFilter] = Field(default=None)
    domain_name: Optional[StringFilter] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class ExportProjectsRequest(BaseRequestModel):
    """Project CSV export request."""
    fields: Optional[list[str]] = Field(default=None)
    filter: Optional[ProjectFilter] = Field(default=None)
    order: Optional[ExportOrder] = Field(default=None)
```


```python
# common/dto/manager/export/response.py

from pydantic import Field

from ai.backend.common.dto.base import BaseResponseModel


class FieldInfo(BaseResponseModel):
    """Export field information."""
    key: str
    name: str
    description: str
    field_type: str
    is_default: bool


class ReportInfo(BaseResponseModel):
    """Export report information."""
    report_key: str
    name: str
    description: str


class ListReportsResponse(BaseResponseModel):
    """Report list response."""
    reports: list[ReportInfo]


class ReportFieldsResponse(BaseResponseModel):
    """Report field list response."""
    report_key: str
    name: str
    description: str
    fields: list[FieldInfo]
```

#### 6.2 API handler (POST 기반)


```python
# api/export.py

from collections.abc import Iterable
from http import HTTPStatus
from typing import Optional

import aiohttp_cors
from aiohttp import web
from pydantic import BaseModel

from ai.backend.common.api_handlers import (
    APIResponse,
    APIStreamResponse,
    BodyParam,
    PathParam,
    api_handler,
    stream_api_handler,
)
from ai.backend.common.dto.manager.export.request import (
    AuditLogFilter,
    ExportAuditLogsRequest,
    ExportOrder,
    ExportOrderField,
    ExportProjectsRequest,
    ExportSessionsRequest,
    ExportUsersRequest,
    ProjectFilter,
    SessionFilter,
    UserFilter,
)
from ai.backend.common.dto.manager.export.response import (
    FieldInfo,
    ListReportsResponse,
    ReportFieldsResponse,
    ReportInfo,
)
from ai.backend.manager.repositories.base.export import StreamingExportQuery
from ai.backend.manager.repositories.base.types import QueryCondition, QueryOrder

from .auth import admin_required, auth_required
from .context import RootContext
from .types import CORSOptions, WebMiddleware


class ReportPathParams(BaseModel):
    """Report path parameters."""
    report_key: str


class ExportAPIHandler:
    """Export API Handler."""

    @auth_required
    @api_handler
    async def list_reports(
        self,
        request: web.Request,
    ) -> APIResponse:
        """List available reports.

        GET /export/reports
        """
        root_ctx: RootContext = request.app["_root.context"]
        service = root_ctx.export_service
        reports = service.list_reports()

        response = ListReportsResponse(
            reports=[
                ReportInfo(
                    report_key=r.report_key,
                    name=r.name,
                    description=r.description,
                )
                for r in reports
            ]
        )

        return APIResponse.build(status_code=HTTPStatus.OK, response_model=response)

    @auth_required
    @api_handler
    async def get_report_fields(
        self,
        request: web.Request,
        path: PathParam[ReportPathParams],
    ) -> APIResponse:
        """List available fields for a report.

        GET /export/reports/{report_key}/fields

        Clients use this API to check which fields can be selected.
        """
        root_ctx: RootContext = request.app["_root.context"]
        report_key = path.parsed.report_key
        service = root_ctx.export_service

        report = service.get_report(report_key)
        if report is None:
            raise web.HTTPNotFound(reason=f"Report not found: {report_key}")

        default_keys = set(report.get_default_field_keys())

        response = ReportFieldsResponse(
            report_key=report.report_key,
            name=report.name,
            description=report.description,
            fields=[
                FieldInfo(
                    key=field_def.key,
                    name=field_def.name,
                    description=field_def.description,
                    field_type=field_def.field_type.value,
                    is_default=field_def.key in default_keys,
                )
                for field_def in report.fields
            ],
        )

        return APIResponse.build(status_code=HTTPStatus.OK, response_model=response)

    @admin_required
    @stream_api_handler
    async def export_audit_logs_csv(
        self,
        request: web.Request,
        body: BodyParam[ExportAuditLogsRequest],
    ) -> APIStreamResponse:
        """Export Audit Log to CSV.

        POST /export/reports/audit-logs/csv
        """
        return await self._export_csv(
            request,
            report_key="audit-logs",
            field_keys=body.parsed.fields,
            filter_obj=body.parsed.filter,
            order_obj=body.parsed.order,
        )

    @admin_required
    @stream_api_handler
    async def export_sessions_csv(
        self,
        request: web.Request,
        body: BodyParam[ExportSessionsRequest],
    ) -> APIStreamResponse:
        """Export Session to CSV.

        POST /export/reports/sessions/csv
        """
        return await self._export_csv(
            request,
            report_key="sessions",
            field_keys=body.parsed.fields,
            filter_obj=body.parsed.filter,
            order_obj=body.parsed.order,
        )

    @admin_required
    @stream_api_handler
    async def export_users_csv(
        self,
        request: web.Request,
        body: BodyParam[ExportUsersRequest],
    ) -> APIStreamResponse:
        """Export User to CSV.

        POST /export/reports/users/csv
        """
        return await self._export_csv(
            request,
            report_key="users",
            field_keys=body.parsed.fields,
            filter_obj=body.parsed.filter,
            order_obj=body.parsed.order,
        )

    @admin_required
    @stream_api_handler
    async def export_projects_csv(
        self,
        request: web.Request,
        body: BodyParam[ExportProjectsRequest],
    ) -> APIStreamResponse:
        """Export Project to CSV.

        POST /export/reports/projects/csv
        """
        return await self._export_csv(
            request,
            report_key="projects",
            field_keys=body.parsed.fields,
            filter_obj=body.parsed.filter,
            order_obj=body.parsed.order,
        )

    async def _export_csv(
        self,
        request: web.Request,
        report_key: str,
        field_keys: Optional[list[str]],
        filter_obj: Optional[AuditLogFilter | SessionFilter | UserFilter | ProjectFilter],
        order_obj: Optional[ExportOrder],
    ) -> APIStreamResponse:
        """Common CSV export logic."""
        root_ctx: RootContext = request.app["_root.context"]
        service = root_ctx.export_service
        config = root_ctx.config.export

        # Build conditions/orders (can delegate to per-report adapters)
        conditions = self._build_conditions(report_key, filter_obj)
        orders = self._build_orders(report_key, order_obj)

        export_query = StreamingExportQuery(
            conditions=conditions,
            orders=orders,
            max_rows=config.max_rows,
            statement_timeout_sec=config.statement_timeout_sec,
        )

        csv_stream = await service.export_csv(
            report_key=report_key,
            query=export_query,
            field_keys=field_keys,
        )

        return APIStreamResponse(
            body=csv_stream,
            status=HTTPStatus.OK,
            headers={
                "Content-Type": csv_stream.content_type(),
                "Content-Disposition": csv_stream.content_disposition(),
                "Cache-Control": "no-cache",
            },
        )

    def _build_conditions(
        self,
        report_key: str,
        filter_obj: Optional[AuditLogFilter | SessionFilter | UserFilter | ProjectFilter],
    ) -> list[QueryCondition]:
        """Generate QueryCondition list from Filter object.

        Follows the notification API adapter pattern.
        Define Adapter class per report to perform Filter DTO → QueryCondition conversion.
        """
        if filter_obj is None:
            return []

        # Get per-report Adapter and convert
        adapter = FILTER_ADAPTERS.get(report_key)
        if adapter is None:
            return []
        return adapter.to_conditions(filter_obj)

    def _build_orders(
        self,
        report_key: str,
        order_obj: Optional[ExportOrder],
    ) -> list[QueryOrder]:
        """Generate QueryOrder list from Order object."""
        if order_obj is None:
            return []

        adapter = ORDER_ADAPTERS.get(report_key)
        if adapter is None:
            return []
        return adapter.to_orders(order_obj)


# === Filter/Order Adapters ===
# Implemented following the notification API adapter pattern.
# Each adapter handles Filter DTO → QueryCondition, Order DTO → QueryOrder conversion per report.

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import sqlalchemy as sa

from ai.backend.manager.models.audit_log import AuditLogRow


TFilter = TypeVar("TFilter")


class FilterAdapter(ABC, Generic[TFilter]):
    """Abstract class for Filter DTO → QueryCondition conversion."""

    @abstractmethod
    def to_conditions(self, filter_obj: TFilter) -> list[QueryCondition]:
        raise NotImplementedError


class OrderAdapter:
    """Order DTO → QueryOrder conversion."""

    def __init__(self, table: type) -> None:
        self._table = table

    def to_orders(self, order_obj: ExportOrder) -> list[QueryOrder]:
        column = getattr(self._table, order_obj.field.value, None)
        if column is None:
            return []
        if order_obj.direction == OrderDirection.DESC:
            return [sa.desc(column)]
        return [sa.asc(column)]


class AuditLogFilterAdapter(FilterAdapter[AuditLogFilter]):
    """AuditLogFilter → QueryCondition conversion."""

    def to_conditions(self, filter_obj: AuditLogFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        # StringFilter handling
        if filter_obj.entity_type:
            conditions.extend(
                _string_filter_to_conditions(AuditLogRow.entity_type, filter_obj.entity_type)
            )
        if filter_obj.entity_id:
            conditions.extend(
                _string_filter_to_conditions(AuditLogRow.entity_id, filter_obj.entity_id)
            )
        if filter_obj.operation:
            conditions.extend(
                _string_filter_to_conditions(AuditLogRow.operation, filter_obj.operation)
            )
        if filter_obj.status:
            conditions.extend(
                _string_filter_to_conditions(AuditLogRow.status, filter_obj.status)
            )
        if filter_obj.triggered_by:
            conditions.extend(
                _string_filter_to_conditions(AuditLogRow.triggered_by, filter_obj.triggered_by)
            )

        # DateTimeFilter handling
        if filter_obj.created_at:
            conditions.extend(
                _datetime_filter_to_conditions(AuditLogRow.created_at, filter_obj.created_at)
            )

        return conditions


def _string_filter_to_conditions(
    column: sa.Column,
    filter_obj: StringFilter,
) -> list[QueryCondition]:
    """StringFilter → QueryCondition conversion helper."""
    conditions: list[QueryCondition] = []
    if filter_obj.equals is not None:
        conditions.append(lambda col=column, val=filter_obj.equals: col == val)
    if filter_obj.contains is not None:
        conditions.append(lambda col=column, val=filter_obj.contains: col.ilike(f"%{val}%"))
    if filter_obj.starts_with is not None:
        conditions.append(lambda col=column, val=filter_obj.starts_with: col.ilike(f"{val}%"))
    if filter_obj.ends_with is not None:
        conditions.append(lambda col=column, val=filter_obj.ends_with: col.ilike(f"%{val}"))
    return conditions


def _datetime_filter_to_conditions(
    column: sa.Column,
    filter_obj: DateTimeFilter,
) -> list[QueryCondition]:
    """DateTimeFilter → QueryCondition conversion helper.

    Uses same field names as GQL DateTimeFilter (api/gql/base.py):
    - before: < (less than)
    - after: > (greater than)
    - equals: = (equal)
    - not_equals: != (not equal)
    """
    conditions: list[QueryCondition] = []
    if filter_obj.before is not None:
        conditions.append(lambda col=column, val=filter_obj.before: col < val)
    if filter_obj.after is not None:
        conditions.append(lambda col=column, val=filter_obj.after: col > val)
    if filter_obj.equals is not None:
        conditions.append(lambda col=column, val=filter_obj.equals: col == val)
    if filter_obj.not_equals is not None:
        conditions.append(lambda col=column, val=filter_obj.not_equals: col != val)
    return conditions


# Adapter Registry
FILTER_ADAPTERS: dict[str, FilterAdapter] = {
    "audit-logs": AuditLogFilterAdapter(),
    # "sessions": SessionFilterAdapter(),
    # "users": UserFilterAdapter(),
    # "projects": ProjectFilterAdapter(),
}

ORDER_ADAPTERS: dict[str, OrderAdapter] = {
    "audit-logs": OrderAdapter(AuditLogRow),
    # "sessions": OrderAdapter(SessionRow),
    # "users": OrderAdapter(UserRow),
    # "projects": OrderAdapter(GroupRow),
}


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Initialize Export API."""
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "export"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    handler = ExportAPIHandler()

    # Report list (GET)
    cors.add(app.router.add_route(
        "GET", "/reports", handler.list_reports
    ))

    # Report fields list (GET)
    cors.add(app.router.add_route(
        "GET", "/reports/{report_key}/fields", handler.get_report_fields
    ))

    # CSV Export (POST - individual endpoint per report)
    cors.add(app.router.add_route(
        "POST", "/reports/audit-logs/csv", handler.export_audit_logs_csv
    ))
    cors.add(app.router.add_route(
        "POST", "/reports/sessions/csv", handler.export_sessions_csv
    ))
    cors.add(app.router.add_route(
        "POST", "/reports/users/csv", handler.export_users_csv
    ))
    cors.add(app.router.add_route(
        "POST", "/reports/projects/csv", handler.export_projects_csv
    ))

    return app, []
```

### 7. 클라이언트 SDK

클라이언트 SDK 는 common/dto 에 정의한 Request DTO 를 받아 async iterator 를 반환한다.
클라이언트는 이 iterator 로 데이터를 스트리밍 처리한다.


```python
# client/func/export.py

from collections.abc import AsyncIterator
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Optional

from ai.backend.client.request import Request
from ai.backend.client.func.base import api_function
from ai.backend.common.dto.manager.export.request import (
    ExportAuditLogsRequest,
    ExportSessionsRequest,
    ExportUsersRequest,
    ExportProjectsRequest,
)


@dataclass
class FieldInfo:
    """Field information."""
    key: str
    name: str
    description: str
    field_type: str
    is_default: bool


@dataclass
class ReportInfo:
    """Report information."""
    report_key: str
    name: str
    description: str
    fields: list[FieldInfo] = dataclass_field(default_factory=list)


@dataclass
class ExportStatus:
    """Export result status (extracted from HTTP Trailer)."""
    success: bool
    error_message: str | None = None
    rows_exported: int = 0


class CSVStreamReader:
    """CSV streaming reader.

    Reads CSV data chunk by chunk via async for.

    Example:
        reader = await export.export_audit_logs(request)
        async for chunk in reader:
            file.write(chunk)
        status = reader.get_status()
    """

    def __init__(self, response) -> None:
        self._response = response
        self._status: ExportStatus | None = None

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Yield CSV data chunk by chunk."""
        async for chunk in self._response.content.iter_chunked(8192):
            yield chunk

        # Extract status from Trailer after streaming completes
        self._status = ExportStatus(
            success=self._response.headers.get("X-Export-Status") == "success",
            error_message=self._response.headers.get("X-Export-Error"),
            rows_exported=int(self._response.headers.get("X-Export-Rows", 0)),
        )

    def get_status(self) -> ExportStatus | None:
        """Return status after export completes (None before streaming completes)."""
        return self._status

    async def save_to_file(self, output_path: Path) -> ExportStatus:
        """Save CSV data to file and return status."""
        with open(output_path, "wb") as f:
            async for chunk in self:
                f.write(chunk)
        return self._status or ExportStatus(success=False, error_message="Unknown error")


class Export:
    """Export API client.

    Receives Request DTOs defined in common/dto and returns CSVStreamReader.
    """

    @api_function
    async def list_reports(self) -> list[ReportInfo]:
        """List available reports."""
        rqst = Request("GET", "/export/reports")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return [
                ReportInfo(
                    report_key=r["report_key"],
                    name=r["name"],
                    description=r["description"],
                )
                for r in data["reports"]
            ]

    @api_function
    async def get_report_fields(self, report_key: str) -> ReportInfo:
        """List fields for a report."""
        rqst = Request("GET", f"/export/reports/{report_key}/fields")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ReportInfo(
                report_key=data["report_key"],
                name=data["name"],
                description=data["description"],
                fields=[
                    FieldInfo(
                        key=f["key"],
                        name=f["name"],
                        description=f["description"],
                        field_type=f["field_type"],
                        is_default=f["is_default"],
                    )
                    for f in data["fields"]
                ],
            )

    @api_function
    async def export_audit_logs(
        self,
        request: ExportAuditLogsRequest,
    ) -> CSVStreamReader:
        """Export Audit Log to CSV (Request DTO based).

        Args:
            request: ExportAuditLogsRequest DTO (defined in common/dto)

        Returns:
            CSVStreamReader: Supports chunk-by-chunk streaming via async for

        Example:
            from ai.backend.common.dto.manager.export.request import (
                ExportAuditLogsRequest, AuditLogFilter, DateTimeFilter, StringFilter
            )
            from datetime import datetime

            request = ExportAuditLogsRequest(
                fields=["id", "entity_type", "created_at"],
                filter=AuditLogFilter(
                    entity_type=StringFilter(equals="session"),
                    created_at=DateTimeFilter(
                        after=datetime(2024, 1, 1),
                        before=datetime(2024, 2, 1),
                    ),
                ),
            )

            reader = await export.export_audit_logs(request)

            # Option 1: Process via streaming
            async for chunk in reader:
                process_chunk(chunk)

            # Option 2: Save to file
            status = await reader.save_to_file(Path("audit.csv"))
            print(f"Exported {status.rows_exported} rows")
        """
        rqst = Request(
            "POST",
            "/export/reports/audit-logs/csv",
            json=request.model_dump(exclude_none=True),
        )
        resp = await rqst.fetch().__aenter__()
        return CSVStreamReader(resp)

    @api_function
    async def export_sessions(
        self,
        request: ExportSessionsRequest,
    ) -> CSVStreamReader:
        """Export Session to CSV."""
        rqst = Request(
            "POST",
            "/export/reports/sessions/csv",
            json=request.model_dump(exclude_none=True),
        )
        resp = await rqst.fetch().__aenter__()
        return CSVStreamReader(resp)

    @api_function
    async def export_users(
        self,
        request: ExportUsersRequest,
    ) -> CSVStreamReader:
        """Export User to CSV."""
        rqst = Request(
            "POST",
            "/export/reports/users/csv",
            json=request.model_dump(exclude_none=True),
        )
        resp = await rqst.fetch().__aenter__()
        return CSVStreamReader(resp)

    @api_function
    async def export_projects(
        self,
        request: ExportProjectsRequest,
    ) -> CSVStreamReader:
        """Export Project to CSV."""
        rqst = Request(
            "POST",
            "/export/reports/projects/csv",
            json=request.model_dump(exclude_none=True),
        )
        resp = await rqst.fetch().__aenter__()
        return CSVStreamReader(resp)
```

### 8. CLI


```python
# client/cli/admin/export.py

import json
import click
from pathlib import Path
from datetime import datetime

from ai.backend.client.session import Session
from ai.backend.common.dto.manager.export.request import (
    ExportAuditLogsRequest,
    ExportSessionsRequest,
    ExportUsersRequest,
    ExportProjectsRequest,
    ExportOrder,
    ExportOrderField,
    AuditLogFilter,
    SessionFilter,
    UserFilter,
    ProjectFilter,
)
from ai.backend.common.dto.common import OrderDirection


@click.group()
def export():
    """Export data to CSV files."""
    pass


@export.command("list")
def list_reports():
    """List available export reports."""
    with Session() as session:
        reports = session.Export().list_reports()

        click.echo("Available Reports:")
        click.echo("-" * 60)
        for r in reports:
            click.echo(f"  {r.report_key}")
            click.echo(f"    Name: {r.name}")
            click.echo(f"    Description: {r.description}")
            click.echo()


@export.command("fields")
@click.argument("report_key")
def show_fields(report_key: str):
    """Show available fields for a report."""
    with Session() as session:
        report = session.Export().get_report_fields(report_key)

        click.echo(f"Report: {report.name}")
        click.echo(f"Description: {report.description}")
        click.echo()
        click.echo("Available Fields:")
        click.echo("-" * 80)
        click.echo(f"{'Key':<20} {'Name':<20} {'Type':<10} {'Default':<8} Description")
        click.echo("-" * 80)

        for f in report.fields or []:
            default = "Yes" if f.is_default else "No"
            click.echo(f"{f.key:<20} {f.name:<20} {f.field_type:<10} {default:<8} {f.description}")


# Request DTO builder (JSON → Request DTO conversion)
FILTER_CLASSES = {
    "audit-logs": AuditLogFilter,
    "sessions": SessionFilter,
    "users": UserFilter,
    "projects": ProjectFilter,
}

REQUEST_CLASSES = {
    "audit-logs": ExportAuditLogsRequest,
    "sessions": ExportSessionsRequest,
    "users": ExportUsersRequest,
    "projects": ExportProjectsRequest,
}

EXPORT_METHODS = {
    "audit-logs": "export_audit_logs",
    "sessions": "export_sessions",
    "users": "export_users",
    "projects": "export_projects",
}


def _build_request(
    report_key: str,
    fields_list: list[str] | None,
    filter_dict: dict | None,
    order_by: str,
    order_dir: str,
):
    """Create Request DTO from JSON input."""
    filter_class = FILTER_CLASSES.get(report_key)
    request_class = REQUEST_CLASSES.get(report_key)

    if not filter_class or not request_class:
        raise click.BadParameter(f"Unknown report: {report_key}")

    filter_obj = filter_class(**filter_dict) if filter_dict else None
    order_obj = ExportOrder(
        field=ExportOrderField(order_by),
        direction=OrderDirection(order_dir),
    )

    return request_class(
        fields=fields_list,
        filter=filter_obj,
        order=order_obj,
    )


@export.command("csv")
@click.argument("report_key")
@click.option(
    "-o", "--output",
    type=click.Path(),
    default=None,
    help="Output file path. Default: {report_key}-YYYYMMDD-HHMMSS.csv",
)
@click.option(
    "--fields",
    default=None,
    help="Comma-separated list of field keys to export",
)
@click.option(
    "--filter",
    "filter_json",
    default=None,
    help="Filter conditions as JSON string (e.g., '{\"entity_type\": {\"equals\": \"session\"}}')",
)
@click.option(
    "--order-by",
    default="created_at",
    help="Field to order by (default: created_at)",
)
@click.option(
    "--order-dir",
    type=click.Choice(["asc", "desc"]),
    default="desc",
    help="Order direction (default: desc)",
)
def download_csv(
    report_key: str,
    output: str | None,
    fields: str | None,
    filter_json: str | None,
    order_by: str,
    order_dir: str,
) -> None:
    """Export a report to CSV file.

    Examples:
        # Export audit logs with default fields
        backend.ai export csv audit-logs

        # Export with specific fields
        backend.ai export csv audit-logs --fields=id,entity_type,created_at

        # Export with StringFilter (JSON format)
        backend.ai export csv audit-logs --filter='{"entity_type": {"equals": "session"}}'

        # Export with DateTimeFilter (range query, using before/after)
        backend.ai export csv audit-logs --filter='{"created_at": {"after": "2024-01-01T00:00:00Z", "before": "2024-02-01T00:00:00Z"}}'

        # Export with combined filters
        backend.ai export csv audit-logs --filter='{"entity_type": {"equals": "session"}, "created_at": {"after": "2024-01-01T00:00:00Z"}}'

        # Export with ordering
        backend.ai export csv sessions --order-by=created_at --order-dir=desc
    """
    if output is None:
        output = f"{report_key}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

    output_path = Path(output)
    fields_list = [f.strip() for f in fields.split(",")] if fields else None

    # Parse filter JSON
    filter_dict = None
    if filter_json:
        try:
            filter_dict = json.loads(filter_json)
        except json.JSONDecodeError as e:
            raise click.BadParameter(f"Invalid JSON filter: {e}")

    # Build Request DTO
    request = _build_request(
        report_key=report_key,
        fields_list=fields_list,
        filter_dict=filter_dict,
        order_by=order_by,
        order_dir=order_dir,
    )

    # Export using the appropriate method
    export_method = EXPORT_METHODS.get(report_key)
    if not export_method:
        raise click.BadParameter(f"Unknown report: {report_key}")

    with Session() as session:
        click.echo(f"Exporting {report_key}...")
        export_func = getattr(session.Export(), export_method)
        reader = export_func(request)

        # Save to file and get status
        status = reader.save_to_file(output_path)

        if status.success:
            click.echo(f"Exported {status.rows_exported} rows to: {output_path}")
        else:
            click.echo(f"Export completed with error: {status.error_message}")
            click.echo(f"Partial data ({status.rows_exported} rows) saved to: {output_path}")
```

### 9. 전체 계층 구조


```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLI Layer                                   │
│  backend.ai export list                                                 │
│  backend.ai export fields audit-logs                                    │
│  backend.ai export csv audit-logs --fields=id,created_at --filter='{}'  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Client SDK Layer                                │
│  session.Export().list_reports()                                        │
│  session.Export().get_report_fields("audit-logs")                       │
│  session.Export().export_audit_logs(ExportAuditLogsRequest) → Reader    │
│                                                                         │
│  CSVStreamReader: async for chunk support, save_to_file(), get_status() │
│  Request DTO: import from common/dto (ExportAuditLogsRequest, ...)      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             API Layer                                    │
│  GET  /export/reports                    → Report list                   │
│  GET  /export/reports/{key}/fields       → Field list                    │
│  POST /export/reports/{key}/csv          → CSV streaming (body: filter)  │
│                                                                         │
│  DTO: ExportXxxRequest, XxxFilter, DateTimeFilter (notification API)    │
│  Filter/Order Adapter: FilterAdapter → QueryCondition conversion         │
│  StreamingExportQuery creation (reads max_rows, timeout from config)    │
│  HTTP Trailer: X-Export-Status, X-Export-Rows (error status delivery)   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Service Layer                                  │
│  ExportService(db, max_concurrent_exports)                              │
│    .list_reports() → list[ReportDef]                                    │
│    .get_report(key) → ReportDef                                         │
│    .export_csv(key, query, field_keys) → CSVExportStreamReader          │
│                                                                         │
│  CSVExportStreamReader: HTTP Trailer support, ExportStatus tracking     │
│  Concurrent export limit (semaphore)                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Repository Layer                                  │
│  execute_streaming_export(db_sess, query, base_query, report, keys)     │
│    → AsyncIterator[dict[str, Any]] (per row)                            │
│                                                                         │
│  Report Registry: EXPORT_REPORTS (Mapping[str, ReportDef])              │
│    - AUDIT_LOG_REPORT, SESSION_REPORT, USER_REPORT, PROJECT_REPORT      │
│                                                                         │
│  ReportDef (dataclass): report_key, fields, base_query_builder          │
│  ExportFieldDef (dataclass): key, name, description, accessor, formatter│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Database Layer                                   │
│  db_sess.stream(query.limit(max_rows))                                  │
│  SET statement_timeout = '300s'                                         │
│  async for row in result → yield per row                                │
│  (Server-side cursor, transaction consistency)                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 이전 / 호환성

### 하위 호환성

- 기존 클라이언트 측 CSV 로 내보내기 기능은 그대로 유지한다
- 서버 측 내보내기는 별도 API 엔드포인트로 추가한다
- 프런트엔드는 새 API 로 점진적으로 이전한다

### 호환성을 깨는 변경

- 없음 (API 추가)

## 구현 계획

### 1단계: 기반 구조 (BA-3818)

1. `ManagerUnifiedConfig` 에 `ExportConfig` 추가 (`config/unified.py`)
2. 핵심 타입 구현 (`repositories/base/export.py`):
   - `StreamingExportQuery` (dataclass, frozen)
   - `ExportFieldDef` (dataclass, frozen): formatter callback 포함
   - `ExportFieldType` (StrEnum)
   - `ReportDef` (dataclass)
   - `execute_streaming_export()` 공통 함수
3. DTO 정의 (`common/dto/manager/export/`):
   - 요청: `ExportAuditLogsRequest`, `AuditLogFilter`, `ExportOrder` 등
   - 응답: `ListReportsResponse`, `ReportFieldsResponse`, `FieldInfo`, `ReportInfo`
   - 공통 filter: `StringFilter`, `DateTimeFilter`
4. `CSVExportStreamReader` 구현 (`services/export/csv_stream.py`)
   - HTTP Trailer 지원 (`get_trailer_headers()`)
   - `ExportStatus` dataclass
5. `ExportService` 구현 (`services/export/service.py`)
6. filter 와 정렬 adapter 구현 (`api/export.py`):
   - `FilterAdapter`, `OrderAdapter` 추상 클래스
   - `_string_filter_to_conditions()`, `_datetime_filter_to_conditions()` helper
   - `FILTER_ADAPTERS`, `ORDER_ADAPTERS` registry
7. API handler 구현 (`api/export.py`): report 별 POST 엔드포인트
8. 단위 테스트

### 2단계: 도메인 구현

도메인별로 병렬 진행할 수 있다.

**BA-3819: 프로젝트 내보내기**
- `PROJECT_FIELDS`, `PROJECT_REPORT` 정의 (`repositories/export/reports/project.py`)
- registry 에 등록

**BA-3820: 사용자 내보내기**
- `USER_FIELDS`, `USER_REPORT` 정의 (`repositories/export/reports/user.py`)
- registry 에 등록

**BA-3821: 세션 / 세션 이력 내보내기**
- `SESSION_FIELDS`, `SESSION_REPORT` 정의
- `SESSION_HISTORY_FIELDS`, `SESSION_HISTORY_REPORT` 정의
- registry 에 등록

**BA-3822: 감사 로그 내보내기**
- `AUDIT_LOG_FIELDS`, `AUDIT_LOG_REPORT` 정의 (`repositories/export/reports/audit_log.py`)
- registry 에 등록

### 3단계: 클라이언트와 CLI

- 클라이언트 SDK (`client/func/export.py`)
- CLI (`client/cli/admin/export.py`)

### 4단계: 프런트엔드 통합

- 프런트엔드에서 새 내보내기 API 사용
- field 선택 UI 구현
- 기존 클라이언트 측 내보내기 교체

## 열린 질문

1. ~~**field 선택 방식**: query parameter 와 request body 중 선택~~ → POST request body (복잡한 filter 지원)

2. ~~**중첩 field 표현**: 점 표기와 밑줄 평탄화 중 선택~~ → 점 표기 (accessor 에서 사용)

3. **복합 report**: 여러 테이블 JOIN 이 필요한 복합 report 를 정의하는 방법
   - 현재 제안: `base_query_builder` 에서 JOIN 질의를 생성한다

4. ~~**filter 확장**: report 별 filter(예: status, entity_type) 정의~~ → Notification API 패턴 적용
   - report 마다 개별 POST 엔드포인트
   - report 마다 filter DTO 정의 (예: `AuditLogFilter`, `SessionFilter`)
   - StringFilter 로 유연한 문자열 필터링 (equals, contains, starts_with 등)
   - DateTimeFilter 로 날짜와 시간 범위 필터링 (before, after, equals, not_equals)
     - field 이름은 기존 GQL DateTimeFilter 와 같다 (api/gql/base.py)

5. ~~**스트리밍 에러 처리**: 스트리밍 도중 에러를 클라이언트에 알리는 방법~~ → HTTP Trailer 사용
   - `X-Export-Status`, `X-Export-Error`, `X-Export-Rows` header 를 Trailer 로 보낸다
   - 클라이언트는 Trailer 를 확인해 내보내기 완료 상태를 판단한다

6. ~~**filter DTO → QueryCondition 변환**: 구현 방법~~ → adapter 패턴 적용
   - Notification API adapter 패턴을 참고한다
   - `FilterAdapter`, `OrderAdapter` 추상 클래스 정의
   - report 마다 adapter 구현 (예: `AuditLogFilterAdapter`)
   - `FILTER_ADAPTERS`, `ORDER_ADAPTERS` registry 로 관리

7. ~~**field 타입 서식**: 별도 서식이 필요한 field 처리 방법~~ → formatter callback 사용
   - `ExportFieldDef.formatter` 에 `Callable[[Any], str]` 타입 formatter 정의
   - `_transform_row` 에서 formatter 적용

8. ~~**클라이언트 SDK 반환 타입**: 저장할 파일 경로를 받는 방식과 iterator 반환 방식 중 선택~~ → CSVStreamReader (async iterator) 반환
   - common/dto 의 Request DTO 를 그대로 받는다 (ExportAuditLogsRequest 등)
   - `async for` 를 지원하는 `CSVStreamReader` 반환
   - 파일 저장용 `save_to_file()` helper method 제공
   - HTTP Trailer 기반 ExportStatus 조회용 `get_status()`

## 참고

- [BA-2922: Implement Server-Side CSV Export](https://lablup.atlassian.net/browse/BA-2922)
- [GitHub Issue #6583](https://github.com/lablup/backend.ai/issues/6583)
- [aiohttp StreamResponse](https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.StreamResponse)
- [SQLAlchemy Streaming Results](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
