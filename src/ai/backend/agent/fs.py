import asyncio
from subprocess import CalledProcessError


async def create_scratch_filesystem(scratch_dir, size) -> None:
    """
    Create scratch folder size quota by using tmpfs filesystem.

    :param scratch_dir: The path of scratch directory.

    :param size: The quota size of scratch directory.
                 Size parameter is must be MiB(mebibyte).
    """

    cmd = [
        "mount",
        "-t",
        "tmpfs",
        "-o",
        f"size={size}M",
        "tmpfs",
        f"{scratch_dir}",
    ]
    proc = await asyncio.create_subprocess_exec(*cmd)
    exit_code = await proc.wait()

    if exit_code < 0:
        if proc.returncode is None:
            raise RuntimeError("Process returncode is None")
        raise CalledProcessError(proc.returncode, cmd)


async def destroy_scratch_filesystem(scratch_dir) -> None:
    """
    Destroy scratch folder size quota by using tmpfs filesystem.

    :param scratch_dir: The path of scratch directory.
    """
    cmd = [
        "umount",
        f"{scratch_dir}",
    ]
    proc = await asyncio.create_subprocess_exec(*cmd)
    exit_code = await proc.wait()

    if exit_code < 0:
        if proc.returncode is None:
            raise RuntimeError("Process returncode is None")
        raise CalledProcessError(proc.returncode, cmd)
