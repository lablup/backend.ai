import asyncio

from ai.backend.agent.probe.monitor import ProbeResult, ProbeStatus


async def _check_mountpoint(mountpoint_dir: str, timeout: int):
    """
    Check mountpoint_dir is mounted.

    :param mountpoint_dir: The path of mountpoint directory.
    :param timeout: The timeout of the check.
    """
    try:
        proc = await asyncio.create_subprocess_exec(*[
            "mountpoint",
            f"{mountpoint_dir}",
        ])
        exit_code = await asyncio.wait_for(proc.wait(), timeout=timeout)
        if exit_code < 0:
            raise RuntimeError(f"mountpoint check {mountpoint_dir} failed")
    except asyncio.TimeoutError:
        # no need to wait for the process to finish
        proc.kill()
        raise TimeoutError(f"Timeout after {timeout} seconds while checking {mountpoint_dir}")


class MountpointProbe:
    def __init__(self, mountpoint_dir: str):
        self._mountpoint_dir = mountpoint_dir

    async def check(self, timeout: int):
        try:
            await _check_mountpoint(self._mountpoint_dir, timeout)
            return ProbeResult(ProbeStatus.SUCCESS, "mountpoint is successfully checked")
        except TimeoutError as e:
            return ProbeResult(ProbeStatus.TIMEOUT, f"mountpoint check timeout: {e}")
        except Exception as e:
            return ProbeResult(ProbeStatus.FAILURE, f"mountpoint check failed: {e}")
