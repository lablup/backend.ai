import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from ai.backend.storage.volumes.vfs import BaseFSOpModel


@pytest.fixture
def dummy_path() -> Iterator[Path]:
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


async def test_scan_tree(dummy_path: Path) -> None:
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


async def test_scan_tree_with_limit(dummy_path: Path) -> None:
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


async def test_copy_tree_keeps_symlinks(dummy_path: Path, tmp_path: Path) -> None:
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_file = outside_dir / "target.txt"
    outside_file.write_bytes(b"outside content")
    (dummy_path / "file_link.txt").symlink_to(outside_file)
    (dummy_path / "inner1" / "dir_link").symlink_to(outside_dir)
    (dummy_path / "dangling_link.txt").symlink_to(outside_dir / "missing.txt")
    (dummy_path / "relative_link.txt").symlink_to("a.txt")
    dst_path = tmp_path / "dst"
    dst_path.mkdir()

    await BaseFSOpModel(dummy_path, 10).copy_tree(dummy_path, dst_path)

    assert (dst_path / "a.txt").read_bytes() == b"123"
    assert not (dst_path / "a.txt").is_symlink()
    assert (dst_path / "inner2" / "inner3" / "e.txt").read_bytes() == b"asdf"
    assert (dst_path / "file_link.txt").readlink() == outside_file
    assert (dst_path / "inner1" / "dir_link").readlink() == outside_dir
    assert (dst_path / "dangling_link.txt").readlink() == outside_dir / "missing.txt"
    assert (dst_path / "relative_link.txt").readlink() == Path("a.txt")
