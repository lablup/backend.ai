from pathlib import Path

from ai.backend.common.types import KernelId


class ScratchUtil:
    @classmethod
    def scratch_dir(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (scratch_root / str(kernel_id)).resolve()

    @classmethod
    def scratch_file(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (cls.scratch_dir(scratch_root, kernel_id) / f"{kernel_id}.img").resolve()

    @classmethod
    def tmp_dir(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (scratch_root / f"{kernel_id}_tmp").resolve()

    @classmethod
    def work_dir(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (cls.scratch_dir(scratch_root, kernel_id) / "work").resolve()

    @classmethod
    def config_dir(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (cls.scratch_dir(scratch_root, kernel_id) / "config").resolve()
