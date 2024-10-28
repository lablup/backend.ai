import asyncio
from subprocess import CalledProcessError


async def create_scratch_filesystem(scratch_dir, size):
    """
    Create scratch folder size quota by using tmpfs filesystem.

    :param scratch_dir: The path of scratch directory.

    :param size: The quota size of scratch directory.
                 Size parameter is must be MiB(mebibyte).
    """

    proc = await asyncio.create_subprocess_exec(*[
        "mount",
        "-t",
        "tmpfs",
        "-o",
        f"size={size}M",
        "tmpfs",
        f"{scratch_dir}",
    ])
    exit_code = await proc.wait()

    if exit_code < 0:
        raise CalledProcessError(proc.returncode, proc.args, output=proc.stdout, stderr=proc.stderr)


async def check_scratch_filesystem(scratch_dir: str, timeout: int):
    """
    Check the scratch folder is mounted or not.

    :param scratch_dir: The path of scratch directory.
    :param timeout: The timeout for the process in seconds.
    """
    try:
        proc = await asyncio.create_subprocess_exec(*[
            "mountpoint",
            f"{scratch_dir}",
        ])
        exit_code = await asyncio.wait_for(proc.wait(), timeout=timeout)
        if exit_code < 0:
            raise RuntimeError("mountpoint check failed")
    except asyncio.TimeoutError:
        # no need to wait for the process to finish
        proc.kill()
        raise TimeoutError(f"Timeout after {timeout} seconds while checking {scratch_dir}")


async def destroy_scratch_filesystem(scratch_dir):
    """
    Destroy scratch folder size quota by using tmpfs filesystem.

    :param scratch_dir: The path of scratch directory.
    """
    proc = await asyncio.create_subprocess_exec(*[
        "umount",
        f"{scratch_dir}",
    ])
    exit_code = await proc.wait()

    if exit_code < 0:
        raise CalledProcessError(proc.returncode, proc.args, output=proc.stdout, stderr=proc.stderr)
