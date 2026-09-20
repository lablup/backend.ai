from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from ai.backend.agent.idmap import IdMapError, _map_spec, chown_via_userns


def _delegated_id() -> int | None:
    """A host uid this user may map, or None if the machine delegates none.

    The handover only works where an operator has written /etc/subuid, so the tests that need a
    real one skip rather than fail on a machine that has not. ``getsubids`` is asked first because
    the delegation may come from libsubid rather than the file.
    """
    if not (shutil.which("newuidmap") and shutil.which("newgidmap")):
        return None
    ranges: list[tuple[int, int]] = []
    if getsubids := shutil.which("getsubids"):
        proc = subprocess.run(
            [getsubids, str(os.geteuid())], capture_output=True, text=True, check=False
        )
        for line in proc.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 4:
                try:
                    ranges.append((int(fields[-2]), int(fields[-1])))
                except ValueError:
                    continue
    if not ranges:
        try:
            content = Path("/etc/subuid").read_text()
        except OSError:
            return None
        for line in content.splitlines():
            fields = line.split(":")
            if len(fields) != 3:
                continue
            try:
                ranges.append((int(fields[1]), int(fields[2])))
            except ValueError:
                continue
    for start, count in ranges:
        if count > 0 and start != os.geteuid():
            return start
    return None


def test_map_spec_skips_a_second_line_for_the_agents_own_id() -> None:
    # The same host id twice is an invalid map (EINVAL), and ns 0 already is that id.
    args, ns_id = _map_spec(1000, 1000)
    assert args == ["0", "1000", "1"]
    assert ns_id == 0


def test_map_spec_maps_a_foreign_id_at_ns_one() -> None:
    args, ns_id = _map_spec(1000, 5001)
    assert args == ["0", "1000", "1", "1", "5001", "1"]
    assert ns_id == 1


def test_no_paths_is_a_noop() -> None:
    chown_via_userns([], 5001, 3001, agent_uid=os.geteuid(), agent_gid=os.getegid())


def test_the_agents_own_identity_is_a_noop(tmp_path: Path) -> None:
    # Every rootless backend runs the container as the agent's own uid today, so the common call is
    # one that has nothing to hand over. It must not fork, and must not need /etc/subuid.
    target = tmp_path / "scratch"
    target.mkdir()
    before = target.stat()
    chown_via_userns(
        [target], os.geteuid(), os.getegid(), agent_uid=os.geteuid(), agent_gid=os.getegid()
    )
    after = target.stat()
    assert (after.st_uid, after.st_gid) == (before.st_uid, before.st_gid)


@pytest.mark.skipif(_delegated_id() is None, reason="no subuid/subgid range is delegated here")
def test_hands_paths_to_a_delegated_id(tmp_path: Path) -> None:
    delegated = _delegated_id()
    assert delegated is not None
    # Both are direct children of tmp_path so that pytest can still clean them up afterwards: an
    # empty directory and a file are removed with write permission on their *parent*, which stays
    # ours. Nesting the file under the handed-over directory would strand the tree.
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    # 0600 is the case the handover exists for: without it the user cannot even read its own key.
    private = tmp_path / "id_cluster"
    private.touch(mode=0o600)

    chown_via_userns(
        [work_dir, private],
        delegated,
        delegated,
        agent_uid=os.geteuid(),
        agent_gid=os.getegid(),
    )

    assert work_dir.stat().st_uid == delegated
    assert private.stat().st_uid == delegated
    assert private.stat().st_mode & 0o777 == 0o600


@pytest.mark.skipif(_delegated_id() is None, reason="no subuid/subgid range is delegated here")
def test_refuses_an_id_outside_the_delegation(tmp_path: Path) -> None:
    delegated = _delegated_id()
    assert delegated is not None
    target = tmp_path / "scratch"
    target.mkdir()
    owner_before = target.stat().st_uid

    # One below the first delegated range: a real id, and not one this user may map.
    with pytest.raises(IdMapError):
        chown_via_userns(
            [target],
            delegated - 1,
            delegated,
            agent_uid=os.geteuid(),
            agent_gid=os.getegid(),
        )
    assert target.stat().st_uid == owner_before
