from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.sealed import (
    remove_spec_dir,
    spec_jws_mount,
    spec_signature,
    write_spec_jws,
)
from ai.backend.agent.errors.containerd import SealedSpecMissing
from ai.backend.common.types import KernelCreationConfig


@pytest.fixture
def kernel_config() -> KernelCreationConfig:
    return cast(KernelCreationConfig, {})


def _config(base: KernelCreationConfig, **extra: Any) -> KernelCreationConfig:
    return cast(KernelCreationConfig, {**base, **extra})


class TestSpecSignature:
    def test_no_confidential_key_is_unsealed(self, kernel_config: KernelCreationConfig) -> None:
        assert spec_signature(kernel_config) is None

    def test_signature_is_returned(self, kernel_config: KernelCreationConfig) -> None:
        config = _config(kernel_config, confidential={"signature": "aaa.bbb.ccc"})

        assert spec_signature(config) == "aaa.bbb.ccc"

    @pytest.mark.parametrize(
        "confidential",
        [{}, {"signature": ""}, {"signature": 7}, {"signature": "aé"}, "a"],
        ids=["absent", "empty", "int", "non-ascii", "string"],
    )
    def test_sealed_without_a_usable_signature_is_refused(
        self, kernel_config: KernelCreationConfig, confidential: Any
    ) -> None:
        with pytest.raises(SealedSpecMissing):
            spec_signature(_config(kernel_config, confidential=confidential))


class TestWriteSpecJws:
    def test_write_is_exact_and_read_only_and_remove_is_idempotent(self, tmp_path: Path) -> None:
        path = tmp_path / "k1" / "spec.jws"

        write_spec_jws(path, "aaa.bbb.ccc")

        assert path.read_bytes() == b"aaa.bbb.ccc"
        assert stat.S_IMODE(path.stat().st_mode) == 0o444

        remove_spec_dir(tmp_path, "k1")
        remove_spec_dir(tmp_path, "k1")

        assert not path.parent.exists()


class TestSpecJwsMount:
    def test_exact_entry(self, tmp_path: Path) -> None:
        assert spec_jws_mount(tmp_path / "spec.jws") == {
            "destination": "/run/bai/spec.jws",
            "type": "bind",
            "source": str(tmp_path / "spec.jws"),
            "options": ["rbind", "ro", "rprivate"],
        }
