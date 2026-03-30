"""CSV exporter for data export."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import AsyncIterator
from typing import Any

from ai.backend.manager.repositories.base.export import ExportDataStream


class CSVExporter:
    """Converts ExportDataStream to CSV bytes stream."""

    _data_stream: ExportDataStream
    _encoding: str

    def __init__(
        self,
        data_stream: ExportDataStream,
        encoding: str = "utf-8",
    ) -> None:
        self._data_stream = data_stream
        self._encoding = encoding

    async def export(self) -> AsyncIterator[bytes]:
        """Export data as CSV bytes stream.

        Yields:
            bytes: CSV data chunks including BOM (for UTF-8), header, and data rows
        """
        # UTF-8 BOM for Excel compatibility (only for UTF-8)
        if self._encoding.lower().replace("-", "") == "utf8":
            yield b"\xef\xbb\xbf"

        # CSV header
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self._data_stream.field_names)
        yield output.getvalue().encode(self._encoding)

        # CSV rows (streaming per partition)
        async for partition in self._data_stream.reader:
            output = io.StringIO()
            writer = csv.writer(output)
            for row_values in partition:
                row = [self._format_value(v) for v in row_values]
                writer.writerow(row)
            yield output.getvalue().encode(self._encoding)

    def _format_value(self, value: Any) -> str:
        """Convert value to CSV string."""
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, default=str, ensure_ascii=False)
        return str(value)
