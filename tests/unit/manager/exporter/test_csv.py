"""Unit tests for CSVExporter."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

import pytest

from ai.backend.manager.exporter.csv import CSVExporter
from ai.backend.manager.repositories.base.export import ExportDataStream


async def _to_async_iter(
    partitions: list[Sequence[Sequence[Any]]],
) -> AsyncIterator[Sequence[Sequence[Any]]]:
    """Convert list of partitions to async iterator."""
    for partition in partitions:
        yield partition


@pytest.fixture
def single_row_stream() -> ExportDataStream:
    """Single row data stream."""
    return ExportDataStream(
        field_names=["ID", "Name", "Value"],
        reader=_to_async_iter([[["id-1", "name-1", 100]]]),
    )


@pytest.fixture
def empty_data_stream() -> ExportDataStream:
    """Empty data stream (header only)."""
    return ExportDataStream(
        field_names=["ID", "Name", "Value"],
        reader=_to_async_iter([[]]),
    )


@pytest.fixture
def multi_row_stream() -> ExportDataStream:
    """Multiple rows in single partition."""
    return ExportDataStream(
        field_names=["ID", "Name", "Value"],
        reader=_to_async_iter([
            [
                ["id-1", "name-1", 100],
                ["id-2", "name-2", 200],
            ],
        ]),
    )


@pytest.fixture
def multi_partition_stream() -> ExportDataStream:
    """Multiple partitions with one row each."""
    return ExportDataStream(
        field_names=["ID", "Name"],
        reader=_to_async_iter([
            [["id-1", "name-1"]],
            [["id-2", "name-2"]],
            [["id-3", "name-3"]],
        ]),
    )


@pytest.fixture
def none_value_stream() -> ExportDataStream:
    """Data stream containing None value."""
    return ExportDataStream(
        field_names=["ID", "Name", "Value"],
        reader=_to_async_iter([[["id-1", None, 100]]]),
    )


@pytest.fixture
def dict_value_stream() -> ExportDataStream:
    """Data stream containing dict value."""
    return ExportDataStream(
        field_names=["ID", "Data", "Value"],
        reader=_to_async_iter([[["id-1", {"key": "value"}, 100]]]),
    )


@pytest.fixture
def list_value_stream() -> ExportDataStream:
    """Data stream containing list value."""
    return ExportDataStream(
        field_names=["ID", "Data", "Value"],
        reader=_to_async_iter([[["id-1", [1, 2, 3], 100]]]),
    )


@pytest.fixture
def korean_text_stream() -> ExportDataStream:
    """Data stream containing Korean text."""
    return ExportDataStream(
        field_names=["ID", "Name", "Value"],
        reader=_to_async_iter([[["id-1", "한글테스트", 100]]]),
    )


class TestCSVExporter:
    """Tests for CSVExporter class."""

    @pytest.mark.asyncio
    async def test_export_with_utf8_bom(self, single_row_stream: ExportDataStream) -> None:
        """Test that UTF-8 BOM is included for utf-8 encoding."""
        exporter = CSVExporter(single_row_stream, encoding="utf-8")
        chunks = [chunk async for chunk in exporter.export()]

        assert chunks[0] == b"\xef\xbb\xbf"

    @pytest.mark.asyncio
    async def test_export_without_bom_for_euc_kr(self, single_row_stream: ExportDataStream) -> None:
        """Test that BOM is not included for non-UTF-8 encoding."""
        exporter = CSVExporter(single_row_stream, encoding="euc-kr")
        chunks = [chunk async for chunk in exporter.export()]

        assert chunks[0] != b"\xef\xbb\xbf"
        assert b"ID" in chunks[0]

    @pytest.mark.asyncio
    async def test_export_header_row(self, empty_data_stream: ExportDataStream) -> None:
        """Test that header row contains field names."""
        exporter = CSVExporter(empty_data_stream)
        chunks = [chunk async for chunk in exporter.export()]

        header = chunks[1].decode("utf-8")  # After BOM
        assert "ID" in header
        assert "Name" in header
        assert "Value" in header

    @pytest.mark.asyncio
    async def test_export_data_rows(self, multi_row_stream: ExportDataStream) -> None:
        """Test that data rows are correctly formatted."""
        exporter = CSVExporter(multi_row_stream)
        chunks = [chunk async for chunk in exporter.export()]

        data = chunks[2].decode("utf-8")  # After BOM and header
        assert "id-1" in data
        assert "name-1" in data
        assert "100" in data
        assert "id-2" in data

    @pytest.mark.asyncio
    async def test_export_multiple_partitions(
        self, multi_partition_stream: ExportDataStream
    ) -> None:
        """Test that multiple partitions produce multiple data chunks."""
        exporter = CSVExporter(multi_partition_stream)
        chunks = [chunk async for chunk in exporter.export()]

        # BOM + header + 3 data partitions = 5 chunks
        assert len(chunks) == 5

    @pytest.mark.asyncio
    async def test_format_none_value(self, none_value_stream: ExportDataStream) -> None:
        """Test that None values are formatted as empty string."""
        exporter = CSVExporter(none_value_stream)
        chunks = [chunk async for chunk in exporter.export()]

        data = chunks[2].decode("utf-8")
        assert "id-1" in data
        assert "100" in data

    @pytest.mark.asyncio
    async def test_format_dict_value(self, dict_value_stream: ExportDataStream) -> None:
        """Test that dict values are JSON serialized."""
        exporter = CSVExporter(dict_value_stream)
        chunks = [chunk async for chunk in exporter.export()]

        data = chunks[2].decode("utf-8")
        assert "key" in data
        assert "value" in data

    @pytest.mark.asyncio
    async def test_format_list_value(self, list_value_stream: ExportDataStream) -> None:
        """Test that list values are JSON serialized."""
        exporter = CSVExporter(list_value_stream)
        chunks = [chunk async for chunk in exporter.export()]

        data = chunks[2].decode("utf-8")
        assert "[1, 2, 3]" in data

    @pytest.mark.asyncio
    async def test_encoding_euc_kr(self, korean_text_stream: ExportDataStream) -> None:
        """Test that euc-kr encoding works for Korean characters."""
        exporter = CSVExporter(korean_text_stream, encoding="euc-kr")
        chunks = [chunk async for chunk in exporter.export()]

        header = chunks[0].decode("euc-kr")  # No BOM
        assert "ID" in header

        data = chunks[1].decode("euc-kr")
        assert "한글테스트" in data
