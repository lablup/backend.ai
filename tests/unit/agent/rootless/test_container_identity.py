"""A per-user container uid a rootless backend cannot give, refused instead of substituted.

``users.container_uid`` names the host identity a session's files must carry -- the point of it is
a shared filesystem where the organisation's own POSIX ids are what other tools see. A rootless
agent cannot produce them: the kernel lets it map only its own uid and the range /etc/subuid
delegates to it (measured: `newuidmap: uid range [0-1) -> [5001-5002) not allowed`).

Before this, all three backends overwrote the request with 0 and started anyway, so the session ran
under the node's kernel uid and wrote files owned by the wrong user -- on a shared filesystem, the
kind of wrong that is expensive to notice and expensive to undo.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.enroot.runtime import EnrootRuntime
from ai.backend.agent.errors.agent import ContainerUserMappingUnsupportedError
from ai.backend.agent.podman.runtime import PodmanRuntime
from ai.backend.agent.singularity.runtime import SingularityRuntime

_KERNEL_UID = 1000
_KERNEL_GID = 1000
#: An id from the organisation's own numbering -- outside anything /etc/subuid delegates.
_ORG_UID = 5001

_BACKENDS = [EnrootRuntime, PodmanRuntime, SingularityRuntime]


def _runtime(cls: Any, tmp_path: Path) -> Any:
    return cls(
        data_path=tmp_path / "data",
        cache_path=tmp_path / "cache",
        runtime_path=tmp_path / "run",
        state_path=tmp_path / "state",
        kernel_uid=_KERNEL_UID,
        kernel_gid=_KERNEL_GID,
    )


class TestWhatTheBackendCanGive:
    @pytest.mark.parametrize("cls", _BACKENDS)
    def test_the_container_runs_as_container_root(self, cls: Any, tmp_path: Path) -> None:
        """Every rootless runtime here maps container-root to the host kernel uid, which owns the
        scratch. A non-zero id inside is a different host id that cannot read it."""
        rt = _runtime(cls, tmp_path)

        assert rt._container_identity_env({}) == {"LOCAL_USER_ID": "0", "LOCAL_GROUP_ID": "0"}

    @pytest.mark.parametrize("cls", _BACKENDS)
    def test_asking_for_the_nodes_own_kernel_uid_is_not_a_conflict(
        self, cls: Any, tmp_path: Path
    ) -> None:
        """This is what a UID_MATCH image gets, and container-root already maps to exactly that id
        -- the files land under the requested identity either way, so there is nothing to refuse."""
        rt = _runtime(cls, tmp_path)
        spec = {"env": {"LOCAL_USER_ID": str(_KERNEL_UID), "LOCAL_GROUP_ID": str(_KERNEL_GID)}}

        assert rt._container_identity_env(spec) == {"LOCAL_USER_ID": "0", "LOCAL_GROUP_ID": "0"}


class TestWhatItRefuses:
    @pytest.mark.parametrize("cls", _BACKENDS)
    def test_a_per_user_uid_it_cannot_produce_stops_the_session(
        self, cls: Any, tmp_path: Path
    ) -> None:
        rt = _runtime(cls, tmp_path)
        spec = {"env": {"LOCAL_USER_ID": str(_ORG_UID)}}

        with pytest.raises(ContainerUserMappingUnsupportedError, match=str(_ORG_UID)):
            rt._container_identity_env(spec)

    @pytest.mark.parametrize("cls", _BACKENDS)
    def test_the_group_is_checked_too(self, cls: Any, tmp_path: Path) -> None:
        """`container_main_gid` is set by the same operator for the same reason; honouring the uid
        and quietly dropping the gid would leave files unreadable by the user's own group."""
        rt = _runtime(cls, tmp_path)
        spec = {"env": {"LOCAL_GROUP_ID": str(_ORG_UID)}}

        with pytest.raises(ContainerUserMappingUnsupportedError):
            rt._container_identity_env(spec)

    @pytest.mark.parametrize("cls", _BACKENDS)
    def test_the_refusal_says_what_would_fix_it(self, cls: Any, tmp_path: Path) -> None:
        """The operator configured this deliberately; a bare "cannot" would send them looking in
        the wrong place."""
        rt = _runtime(cls, tmp_path)

        with pytest.raises(ContainerUserMappingUnsupportedError) as caught:
            rt._container_identity_env({"env": {"LOCAL_USER_ID": str(_ORG_UID)}})

        message = str(caught.value)
        assert "containerd" in message
        assert str(_KERNEL_UID) in message

    @pytest.mark.parametrize("cls", _BACKENDS)
    def test_a_value_we_did_not_write_is_left_alone(self, cls: Any, tmp_path: Path) -> None:
        """Only an id is a mapping request. Refusing on anything else would turn a malformed
        environment into an unstartable node."""
        rt = _runtime(cls, tmp_path)

        assert rt._container_identity_env({"env": {"LOCAL_USER_ID": "not-a-number"}}) == {
            "LOCAL_USER_ID": "0",
            "LOCAL_GROUP_ID": "0",
        }


class TestTheLaunchArgvItself:
    """End to end on the one thing the container actually sees."""

    def test_podman_passes_container_root_and_nothing_else(self, tmp_path: Path) -> None:
        rt = _runtime(PodmanRuntime, tmp_path)
        spec = {"env": {"LOCAL_USER_ID": str(_KERNEL_UID), "BACKENDAI_KERNEL_ID": "k1"}}

        argv = rt._create_argv("c1", "img:1", ["/bin/true"], spec, rt._gate_dir("c1"))

        assert "LOCAL_USER_ID=0" in argv
        assert f"LOCAL_USER_ID={_KERNEL_UID}" not in argv
        assert "BACKENDAI_KERNEL_ID=k1" in argv

    def test_podman_refuses_before_building_a_command_line(self, tmp_path: Path) -> None:
        rt = _runtime(PodmanRuntime, tmp_path)
        spec = {"env": {"LOCAL_USER_ID": str(_ORG_UID)}}

        with pytest.raises(ContainerUserMappingUnsupportedError):
            rt._create_argv("c1", "img:1", ["/bin/true"], spec, rt._gate_dir("c1"))


def test_the_fixture_uids_are_not_this_hosts_by_accident() -> None:
    """The refusal turns on `requested != kernel_uid`; if the test runner happened to be uid 5001
    the interesting case would quietly become the uninteresting one."""
    assert os.geteuid() != _ORG_UID
