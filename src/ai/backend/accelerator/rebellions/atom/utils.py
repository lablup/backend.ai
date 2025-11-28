from pathlib import Path


async def host_pid_to_container_pid(container_id: str, host_pid: int) -> int:
    try:
        for p in Path("/sys/fs/cgroup/pids/docker").iterdir():
            if not p.is_dir():
                continue
            tasks_path = p / "tasks"
            cgtasks = [*map(int, tasks_path.read_text().splitlines())]
            if host_pid not in cgtasks:
                continue
            if p.name == container_id:
                proc_path = Path(f"/proc/{host_pid}/status")
                proc_status = {
                    k: v
                    for k, v in map(
                        lambda line: line.split(":\t"), proc_path.read_text().splitlines()
                    )
                }
                nspids = [*map(int, proc_status["NSpid"].split())]
                return nspids[1]  # in the given container
            return -2  # in other container
        return -1  # in host
    except (ValueError, KeyError, IOError):
        return -1  # in host
