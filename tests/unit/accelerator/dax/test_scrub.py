import errno
import json
import mmap
from pathlib import Path
from typing import Any, NoReturn

import pytest

from ai.backend.accelerator.dax import scrub
from ai.backend.accelerator.dax.scrub import main

from .conftest import FakeSysfs

SCRUB_ALIGN = 65536
UNITS = 4


class FlakyMapping:
    """A real mapping whose stores or `flush()` raise a fixed error."""

    _mm: mmap.mmap
    _flush_error: OSError | None
    _write_error: OSError | None

    def __init__(
        self, mm: mmap.mmap, flush_error: OSError | None, write_error: OSError | None
    ) -> None:
        self._mm = mm
        self._flush_error = flush_error
        self._write_error = write_error

    def __enter__(self) -> "FlakyMapping":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._mm.close()

    def __setitem__(self, key: slice, value: Any) -> None:
        if self._write_error is not None:
            raise self._write_error
        self._mm[key] = value

    def __getitem__(self, key: slice) -> bytes:
        return self._mm[key]

    def flush(self) -> None:
        if self._flush_error is not None:
            raise self._flush_error


class FakeMmapModule:
    """Stands in for `mmap` inside `scrub`, handing out `FlakyMapping` wrappers."""

    MAP_SHARED: int = mmap.MAP_SHARED
    PROT_READ: int = mmap.PROT_READ

    _flush_error: OSError | None
    _write_error: OSError | None

    def __init__(
        self, *, flush_error: OSError | None = None, write_error: OSError | None = None
    ) -> None:
        self._flush_error = flush_error
        self._write_error = write_error

    def mmap(self, fileno: int, length: int, **kwargs: Any) -> FlakyMapping:
        return FlakyMapping(
            mmap.mmap(fileno, length, **kwargs), self._flush_error, self._write_error
        )


def _records(capsys: pytest.CaptureFixture[str]) -> list[dict[str, Any]]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines()]


def _make_device(fake_sysfs: FakeSysfs, dev_dir: Path, name: str, region: str) -> Path:
    fake_sysfs.add_non_cxl_device(name, region=region, size=UNITS * SCRUB_ALIGN, align=SCRUB_ALIGN)
    path = dev_dir / name
    path.write_bytes(b"\xff" * (UNITS * SCRUB_ALIGN))
    return path


@pytest.fixture
def dev_dir(tmp_path: Path) -> Path:
    path = tmp_path / "dev"
    path.mkdir()
    return path


@pytest.fixture
def device(fake_sysfs: FakeSysfs, dev_dir: Path) -> Path:
    return _make_device(fake_sysfs, dev_dir, "dax0.0", "hmem0")


@pytest.fixture
def in_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the thread-pool fallback so that patches of `scrub` reach `zero_range`."""

    def unavailable(*args: Any, **kwargs: Any) -> NoReturn:
        raise OSError("process pool disabled for this test")

    monkeypatch.setattr(scrub, "ProcessPoolExecutor", unavailable)


class TestScrub:
    def test_full_scrub_zeroes_the_device(
        self, fake_sysfs: FakeSysfs, device: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main([str(device), "--sysfs-root", str(fake_sysfs.root), "--workers", "2"])

        assert exit_code == 0
        assert device.read_bytes() == bytes(UNITS * SCRUB_ALIGN)
        [record] = _records(capsys)
        assert record["result"] == "ok"
        assert record["error"] is None
        assert record["verified"] is True
        assert record["mode"] == "full"
        assert record["path"] == str(device)
        assert record["device_id"] == "dax-dax0.0"
        assert record["serials"] == []
        assert (record["size"], record["align"]) == (UNITS * SCRUB_ALIGN, SCRUB_ALIGN)
        assert record["bytes_written"] == UNITS * SCRUB_ALIGN
        assert set(record) >= {"time_utc", "seconds", "bytes_per_sec", "tool_revision"}

    def test_header_only_zeroes_first_align(
        self, fake_sysfs: FakeSysfs, device: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main([str(device), "--header-only", "--sysfs-root", str(fake_sysfs.root)])

        assert exit_code == 0
        content = device.read_bytes()
        assert content[:SCRUB_ALIGN] == bytes(SCRUB_ALIGN)
        assert content[SCRUB_ALIGN:] == b"\xff" * ((UNITS - 1) * SCRUB_ALIGN)
        [record] = _records(capsys)
        assert (record["result"], record["mode"], record["verified"]) == ("ok", "header-only", True)
        assert record["bytes_written"] == SCRUB_ALIGN

    def test_unknown_path_is_an_error_record(
        self, fake_sysfs: FakeSysfs, dev_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main([str(dev_dir / "dax7.0"), "--sysfs-root", str(fake_sysfs.root)])

        assert exit_code != 0
        [record] = _records(capsys)
        assert record["result"] == "error"
        assert record["error"]
        assert record["verified"] is False

    def test_full_scrub_completes_when_flush_is_unsupported(
        self,
        fake_sysfs: FakeSysfs,
        device: Path,
        in_process: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            scrub,
            "mmap",
            FakeMmapModule(flush_error=OSError(errno.EINVAL, "Invalid argument")),
        )

        exit_code = main([str(device), "--sysfs-root", str(fake_sysfs.root), "--workers", "2"])

        assert exit_code == 0
        assert device.read_bytes() == bytes(UNITS * SCRUB_ALIGN)
        [record] = _records(capsys)
        assert (record["result"], record["verified"], record["error"]) == ("ok", True, None)
        assert record["bytes_written"] == UNITS * SCRUB_ALIGN

    def test_other_flush_errors_are_not_swallowed(
        self,
        fake_sysfs: FakeSysfs,
        device: Path,
        in_process: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            scrub,
            "mmap",
            FakeMmapModule(flush_error=OSError(errno.EIO, "Input/output error")),
        )

        exit_code = main([str(device), "--sysfs-root", str(fake_sysfs.root)])

        assert exit_code != 0
        [record] = _records(capsys)
        assert (record["result"], record["verified"]) == ("error", False)
        assert record["bytes_written"] == 0
        assert record["error"]

    def test_write_failure_is_an_error_record(
        self,
        fake_sysfs: FakeSysfs,
        device: Path,
        in_process: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            scrub,
            "mmap",
            FakeMmapModule(write_error=OSError(errno.EIO, "Input/output error")),
        )

        exit_code = main([str(device), "--sysfs-root", str(fake_sysfs.root)])

        assert exit_code != 0
        assert device.read_bytes() == b"\xff" * (UNITS * SCRUB_ALIGN)
        [record] = _records(capsys)
        assert (record["result"], record["verified"]) == ("error", False)
        assert record["bytes_written"] == 0

    def test_each_path_gets_one_record(
        self,
        fake_sysfs: FakeSysfs,
        device: Path,
        dev_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        second = _make_device(fake_sysfs, dev_dir, "dax1.0", "hmem1")

        exit_code = main([str(device), str(second), "--sysfs-root", str(fake_sysfs.root)])

        assert exit_code == 0
        records = _records(capsys)
        assert [r["path"] for r in records] == [str(device), str(second)]
        assert all(r["result"] == "ok" for r in records)
