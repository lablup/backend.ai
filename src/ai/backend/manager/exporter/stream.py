"""CSV export stream reader for streaming responses."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import override

from ai.backend.common.types import StreamReader

from .csv import CSVExporter


class CSVExportStreamReader(StreamReader):
    """StreamReader wrapper for CSVExporter.

    Wraps CSVExporter to implement the StreamReader interface
    for use with stream_api_handler.
    """

    _exporter: CSVExporter

    def __init__(self, exporter: CSVExporter) -> None:
        self._exporter = exporter

    @override
    async def read(self) -> AsyncIterator[bytes]:
        """Yield CSV data chunks."""
        async for chunk in self._exporter.export():
            yield chunk

    @override
    def content_type(self) -> str:
        """Return CSV content type."""
        return "text/csv; charset=utf-8"
