"""
Unit tests for the TUS upload session state model.

These tests cover the pure data-layer behavior of ``TusSessionState``:
computing the contiguous prefix offset, finding records by offset, gap
analysis (``missing_ranges``), and progress reporting. Nothing here touches
the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai.backend.common.types import TusSessionId
from ai.backend.storage.services.upload.types import (
    ChunkMetadata,
    TusSessionState,
)


def _make_chunk_metadata(offset: int, length: int, sha256: str = "x") -> ChunkMetadata:
    return ChunkMetadata(offset=offset, length=length, sha256=sha256)


@dataclass(frozen=True)
class _CommittedOffsetCase:
    records: list[ChunkMetadata]
    expected_prefix: int


@dataclass(frozen=True)
class _MissingRangesCase:
    total_size: int
    records: list[ChunkMetadata]
    expected: list[tuple[int, int]]


@dataclass(frozen=True)
class _ProgressPercentCase:
    total_size: int
    records: list[ChunkMetadata]
    expected_percent: float


class TestTusSessionStatePrefix:
    @pytest.mark.parametrize(
        "case",
        [
            # Empty session: nothing received yet, prefix is at 0.
            _CommittedOffsetCase(records=[], expected_prefix=0),
            # Single chunk at the start fills offsets [0, 100).
            _CommittedOffsetCase(
                records=[_make_chunk_metadata(0, 100)],
                expected_prefix=100,
            ),
            # Two adjacent chunks form a contiguous prefix [0, 150).
            _CommittedOffsetCase(
                records=[_make_chunk_metadata(0, 100), _make_chunk_metadata(100, 50)],
                expected_prefix=150,
            ),
            # Gap after a contiguous prefix: prefix ends at the gap, not at the
            # last entry's end.
            _CommittedOffsetCase(
                records=[_make_chunk_metadata(0, 100), _make_chunk_metadata(200, 50)],
                expected_prefix=100,
            ),
            # No chunk covers byte 0: there is no prefix to report.
            _CommittedOffsetCase(
                records=[_make_chunk_metadata(50, 100)],
                expected_prefix=0,
            ),
        ],
    )
    def test_committed_offset(self, case: _CommittedOffsetCase) -> None:
        state = TusSessionState(
            session_id=TusSessionId("s"), total_size=1024, committed_chunks=list(case.records)
        )
        assert state.committed_offset == case.expected_prefix


class TestFindAtOffset:
    def test_returns_record_at_matching_offset(self) -> None:
        rec = _make_chunk_metadata(100, 50)
        state = TusSessionState(
            session_id=TusSessionId("s"),
            total_size=1024,
            committed_chunks=[_make_chunk_metadata(0, 100, "a"), rec],
        )
        assert state.find_at_offset(100) == rec

    def test_returns_none_when_offset_not_present(self) -> None:
        state = TusSessionState(
            session_id=TusSessionId("s"),
            total_size=1024,
            committed_chunks=[_make_chunk_metadata(0, 100, "a")],
        )
        assert state.find_at_offset(500) is None


class TestMissingRanges:
    @pytest.mark.parametrize(
        "case",
        [
            # Empty session: the whole declared size is missing.
            _MissingRangesCase(
                total_size=1000,
                records=[],
                expected=[(0, 1000)],
            ),
            # Single chunk at the start: only the trailing range is missing.
            _MissingRangesCase(
                total_size=1000,
                records=[_make_chunk_metadata(0, 400)],
                expected=[(400, 600)],
            ),
            # Single chunk in the middle: leading and trailing ranges are
            # missing.
            _MissingRangesCase(
                total_size=1000,
                records=[_make_chunk_metadata(200, 300)],
                expected=[(0, 200), (500, 500)],
            ),
            # Adjacent chunks form a contiguous prefix; only the tail is
            # missing.
            _MissingRangesCase(
                total_size=1000,
                records=[_make_chunk_metadata(0, 400), _make_chunk_metadata(400, 100)],
                expected=[(500, 500)],
            ),
            # Two disjoint chunks leave one inner gap and one trailing gap.
            _MissingRangesCase(
                total_size=1000,
                records=[_make_chunk_metadata(0, 200), _make_chunk_metadata(500, 300)],
                expected=[(200, 300), (800, 200)],
            ),
            # Fully complete (single chunk covers the entire declared size).
            _MissingRangesCase(
                total_size=500,
                records=[_make_chunk_metadata(0, 500)],
                expected=[],
            ),
            # Overlapping chunks are coalesced before computing gaps.
            _MissingRangesCase(
                total_size=1000,
                records=[_make_chunk_metadata(0, 600), _make_chunk_metadata(400, 200)],
                expected=[(600, 400)],
            ),
            # A record extending past `total_size` is clipped to the declared
            # size — beyond-end bytes do NOT count as covered, the rest does.
            _MissingRangesCase(
                total_size=1000,
                records=[_make_chunk_metadata(800, 500)],
                expected=[(0, 800)],
            ),
        ],
    )
    def test_missing_ranges(self, case: _MissingRangesCase) -> None:
        state = TusSessionState(
            session_id=TusSessionId("s"),
            total_size=case.total_size,
            committed_chunks=list(case.records),
        )
        assert state.missing_ranges() == case.expected


class TestProgressPercent:
    @pytest.mark.parametrize(
        "case",
        [
            # Empty session: 0% of the declared size received.
            _ProgressPercentCase(
                total_size=1000,
                records=[],
                expected_percent=0.0,
            ),
            # A single chunk at the start covers 25% of the declared size.
            _ProgressPercentCase(
                total_size=1000,
                records=[_make_chunk_metadata(0, 250)],
                expected_percent=25.0,
            ),
            # Two adjacent chunks fully cover the declared size → 100%.
            _ProgressPercentCase(
                total_size=1000,
                records=[_make_chunk_metadata(0, 500), _make_chunk_metadata(500, 500)],
                expected_percent=100.0,
            ),
            # Chunk in the middle without a prefix from byte 0: progress is 0%
            # because only the contiguous prefix counts.
            _ProgressPercentCase(
                total_size=1000,
                records=[_make_chunk_metadata(500, 500)],
                expected_percent=0.0,
            ),
            # Zero-size sessions are degenerate and always reported as 100%.
            _ProgressPercentCase(
                total_size=0,
                records=[],
                expected_percent=100.0,
            ),
        ],
    )
    def test_progress_percent(self, case: _ProgressPercentCase) -> None:
        state = TusSessionState(
            session_id=TusSessionId("s"),
            total_size=case.total_size,
            committed_chunks=list(case.records),
        )
        assert state.progress_percent() == case.expected_percent
