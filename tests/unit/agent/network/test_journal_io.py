"""Unit tests for crash-atomic journal writes (BEP-1062).

These pin the two properties the LOCAL-network allocators depend on: a claim file is never left
empty/partial (which replay would read as an owner of ``""``), and exclusivity still raises on an
existing target (the "another writer owns this node" signal).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.agent.network.journal_io import atomic_exclusive_write, atomic_write


class TestAtomicExclusiveWrite:
    def test_writes_the_complete_content(self, tmp_path: Path) -> None:
        atomic_exclusive_write(tmp_path / "claim", "cid/eth0")
        assert (tmp_path / "claim").read_text() == "cid/eth0"

    def test_rejects_and_preserves_an_existing_target(self, tmp_path: Path) -> None:
        (tmp_path / "claim").write_text("first")
        with pytest.raises(FileExistsError):
            atomic_exclusive_write(tmp_path / "claim", "second")
        assert (tmp_path / "claim").read_text() == "first"  # left untouched

    def test_leaves_no_temp_file_behind(self, tmp_path: Path) -> None:
        atomic_exclusive_write(tmp_path / "claim", "cid/eth0")
        assert sorted(p.name for p in tmp_path.iterdir()) == ["claim"]

    def test_a_rejected_write_leaves_no_temp_file(self, tmp_path: Path) -> None:
        (tmp_path / "claim").write_text("first")
        with pytest.raises(FileExistsError):
            atomic_exclusive_write(tmp_path / "claim", "second")
        assert sorted(p.name for p in tmp_path.iterdir()) == ["claim"]


class TestAtomicWrite:
    def test_overwrites_and_leaves_no_temp(self, tmp_path: Path) -> None:
        atomic_write(tmp_path / "layout", "172.30.0.0/16 26")
        atomic_write(tmp_path / "layout", "10.0.0.0/8 24")
        assert (tmp_path / "layout").read_text() == "10.0.0.0/8 24"
        assert sorted(p.name for p in tmp_path.iterdir()) == ["layout"]
