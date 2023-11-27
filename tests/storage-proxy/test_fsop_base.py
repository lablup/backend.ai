import tempfile
from pathlib import Path

import pytest

from ai.backend.storage.vfs import BaseFSOpModel


@pytest.fixture
def dummy_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create some dummy files and dirs
        (tmpdir_path / "a.txt").write_bytes(b"123")
        (tmpdir_path / "b.txt").write_bytes(b"456")
        (tmpdir_path / "c.txt").write_bytes(b"789")
        (tmpdir_path / "inner1").mkdir()
        (tmpdir_path / "inner1" / "d.txt").write_bytes(b"qwer")
        (tmpdir_path / "inner2").mkdir()
        (tmpdir_path / "inner2" / "inner3").mkdir()
        (tmpdir_path / "inner2" / "inner3" / "e.txt").write_bytes(b"asdf")
        (tmpdir_path / "x.txt").write_bytes(b"zzz")

        yield tmpdir_path


@pytest.mark.asyncio
async def test_scan_tree(dummy_path) -> None:
    fsop_model = BaseFSOpModel(dummy_path, 10)

    result = []
    async for item in fsop_model.scan_tree(dummy_path, recursive=True):
        result.append(item)
    names = {item.name for item in result}
    assert "a.txt" in names
    assert "b.txt" in names
    assert "c.txt" in names
    assert "inner1" in names
    assert "inner2" in names
    assert "inner3" in names
    assert "d.txt" in names
    assert "e.txt" in names
    assert "x.txt" in names

    result = []
    async for item in fsop_model.scan_tree(dummy_path, recursive=False):
        result.append(item)
    names = {item.name for item in result}
    assert "a.txt" in names
    assert "b.txt" in names
    assert "c.txt" in names
    assert "inner1" in names
    assert "inner2" in names
    assert "inner3" not in names
    assert "d.txt" not in names
    assert "e.txt" not in names
    assert "x.txt" in names


@pytest.mark.asyncio
async def test_scan_tree_with_limit(dummy_path) -> None:
    fsop_model = BaseFSOpModel(dummy_path, 5)

    result = []
    async for item in fsop_model.scan_tree(dummy_path, recursive=True):
        result.append(item)
    # There is no guaranteed ordering of os.scandir(), so we cannot
    # deterministically test which file/dir is included or not.
    assert len(result) == 5

    result = []
    async for item in fsop_model.scan_tree(dummy_path, recursive=False):
        result.append(item)
    assert len(result) == 5
