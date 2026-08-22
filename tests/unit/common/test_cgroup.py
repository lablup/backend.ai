from pathlib import Path
from typing import Literal
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.common.cgroup import (
    CgroupController,
    CgroupResolutionFailed,
    CgroupVersion,
    get_container_cgroup_path,
    get_container_id_of_cgroup,
    get_container_pids,
)
from ai.backend.common.types import PID, ContainerId

CONTAINER_ID = "cd458569541d4a337965ba2be53c3685a0eea188e3c362e9c8fd5de499e4d62d"


class TestGetContainerIdOfCgroup:
    @pytest.mark.parametrize(
        ("cgroup", "description"),
        [
            (f"docker/{CONTAINER_ID}", "docker with the cgroupfs driver"),
            (f"system.slice/docker-{CONTAINER_ID}.scope", "docker with the systemd driver"),
            (f"machine.slice/libpod-{CONTAINER_ID}.scope", "rootful podman"),
            (
                f"machine.slice/libpod-{CONTAINER_ID}.scope/container",
                "podman with a container leaf",
            ),
            (f"machine.slice/libpod-{CONTAINER_ID}.scope/conmon", "podman with a conmon leaf"),
            (
                f"user.slice/user-1000.slice/session-1.scope/libpod-payload-{CONTAINER_ID}",
                "podman with split cgroups",
            ),
            (f"/system.slice/docker-{CONTAINER_ID}.scope", "a leading slash"),
            (f"crio-{CONTAINER_ID}.scope", "cri-o"),
        ],
    )
    def test_extracts_container_id(self, cgroup: str, description: str) -> None:
        assert get_container_id_of_cgroup(cgroup) == CONTAINER_ID

    @pytest.mark.parametrize(
        ("cgroup", "description"),
        [
            ("system.slice/sshd.service", "a cgroup owned by a host service"),
            ("/", "the root cgroup"),
            ("", "an empty cgroup path"),
            ("machine.slice/libpod-not-a-hex-id.scope", "a non-hexadecimal identifier"),
            ("machine.slice/libpod-abc.scope", "an identifier shorter than 12 characters"),
            ("container", "only an interposed leaf name"),
        ],
    )
    def test_returns_none_for_non_container_cgroup(self, cgroup: str, description: str) -> None:
        assert get_container_id_of_cgroup(cgroup) is None


class TestGetContainerCgroupPath:
    async def test_joins_mount_point_with_the_cgroup_of_the_main_process(self) -> None:
        with (
            patch(
                "ai.backend.common.cgroup.get_container_main_pid",
                AsyncMock(return_value=PID(1234)),
            ),
            patch(
                "ai.backend.common.cgroup.get_cgroup_mount_point",
                return_value=Path("/sys/fs/cgroup"),
            ),
            patch(
                "ai.backend.common.cgroup.get_cgroup_of_pid",
                return_value=f"machine.slice/libpod-{CONTAINER_ID}.scope",
            ),
        ):
            resolved = await get_container_cgroup_path(
                "2", CgroupController.MEMORY, ContainerId(CONTAINER_ID)
            )

        assert resolved == Path(f"/sys/fs/cgroup/machine.slice/libpod-{CONTAINER_ID}.scope")

    async def test_passes_the_controller_through_to_both_lookups(self) -> None:
        with (
            patch(
                "ai.backend.common.cgroup.get_container_main_pid",
                AsyncMock(return_value=PID(1234)),
            ),
            patch(
                "ai.backend.common.cgroup.get_cgroup_mount_point",
                return_value=Path("/sys/fs/cgroup"),
            ) as mount_point_mock,
            patch("ai.backend.common.cgroup.get_cgroup_of_pid", return_value="docker/x") as of_pid,
        ):
            await get_container_cgroup_path("1", CgroupController.BLKIO, ContainerId(CONTAINER_ID))

        mount_point_mock.assert_called_once_with("1", CgroupController.BLKIO)
        of_pid.assert_called_once_with(CgroupController.BLKIO, PID(1234))

    async def test_propagates_resolution_failure(self) -> None:
        with patch(
            "ai.backend.common.cgroup.get_container_main_pid",
            AsyncMock(side_effect=CgroupResolutionFailed("no running process")),
        ):
            with pytest.raises(CgroupResolutionFailed):
                await get_container_cgroup_path(
                    "2", CgroupController.MEMORY, ContainerId(CONTAINER_ID)
                )


class TestGetContainerPids:
    @pytest.mark.parametrize(
        ("version", "driver", "procs_filename"),
        [
            ("2", "systemd", "cgroup.procs"),
            ("2", "cgroupfs", "cgroup.procs"),
            ("1", "systemd", "tasks"),
            ("1", "cgroupfs", "tasks"),
        ],
    )
    async def test_reads_the_pid_list_of_the_resolved_cgroup(
        self,
        tmp_path: Path,
        version: Literal["1", "2"],
        driver: Literal["systemd", "cgroupfs"],
        procs_filename: str,
    ) -> None:
        (tmp_path / procs_filename).write_text("101\n202\n303\n")
        with (
            patch(
                "ai.backend.common.cgroup.get_docker_cgroup_version",
                AsyncMock(return_value=CgroupVersion(version, driver)),
            ),
            patch(
                "ai.backend.common.cgroup.get_container_cgroup_path",
                AsyncMock(return_value=tmp_path),
            ),
        ):
            pids = await get_container_pids(ContainerId(CONTAINER_ID))

        assert pids == [101, 202, 303]

    async def test_resolves_the_cgroup_with_the_pids_controller(self, tmp_path: Path) -> None:
        (tmp_path / "cgroup.procs").write_text("")
        with (
            patch(
                "ai.backend.common.cgroup.get_docker_cgroup_version",
                AsyncMock(return_value=CgroupVersion("2", "systemd")),
            ),
            patch(
                "ai.backend.common.cgroup.get_container_cgroup_path",
                AsyncMock(return_value=tmp_path),
            ) as cgroup_path_mock,
        ):
            await get_container_pids(ContainerId(CONTAINER_ID))

        cgroup_path_mock.assert_called_once_with(
            "2", CgroupController.PIDS, ContainerId(CONTAINER_ID)
        )
