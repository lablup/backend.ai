"""Hand host paths over to another uid/gid from an agent that is not root.

A root agent chowns the scratch directly. A rootless one cannot: ``chown`` to an id it does not own
needs ``CAP_CHOWN``, which is the privilege rootless gives up. The kernel offers the same result
through a user namespace instead -- inside one the agent is root, and ``newuidmap``/``newgidmap``
(setuid-root) will write a map for it, but only over the ranges ``/etc/subuid`` and ``/etc/subgid``
delegate to it. The boundary an operator writes in those files is what bounds this, not the agent.

The map covers the one id being handed over rather than the whole delegated range::

    uid_map:  0 <agent uid>  1     the agent itself, so the child is root inside the namespace
              1 <target uid> 1     the id the files must end up owned by

The child chowns to ns id 1, which the kernel translates back to the target host id on the way out.
Measured with ``/etc/subuid`` delegating ``5000:65536``: a 0600 file owned by the agent (1000) comes
out owned by 5001, and an id outside the delegation is refused by ``newuidmap`` ("uid range [1-2) ->
[4999-5000) not allowed") rather than silently substituted.

An id that is already the agent's own needs no second map line -- it is ns 0 -- and asking for one
would put the same host id in the map twice, which the kernel rejects with EINVAL.
"""

from __future__ import annotations

import logging
import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("chown_via_userns",)

# The setuid-root helpers that write a map on behalf of an unprivileged process, checking it against
# /etc/subuid and /etc/subgid. Any rootless container runtime already requires them.
_NEWUIDMAP = "newuidmap"
_NEWGIDMAP = "newgidmap"

# Both the helpers and the child's chowns are local operations on already-resolved paths. A wait
# this long means something is wedged, not slow.
_TIMEOUT = 30.0


class IdMapError(RuntimeError):
    """The namespace could not be mapped, or a chown inside it failed."""


def _map_spec(agent_id: int, target_id: int) -> tuple[list[str], int]:
    """The ``new[ug]idmap`` arguments for handing something to ``target_id``, and the namespace id
    to chown to.

    ``0 <agent_id> 1`` is always present: it is what makes the child root inside the namespace,
    which is where its CAP_CHOWN comes from. The second line is skipped when the target *is* the
    agent -- the same host id twice is an invalid map.
    """
    own = ["0", str(agent_id), "1"]
    if target_id == agent_id:
        return own, 0
    return [*own, "1", str(target_id), "1"], 1


def _write_maps(pid: int, uid_args: Sequence[str], gid_args: Sequence[str]) -> None:
    for helper, args in ((_NEWUIDMAP, uid_args), (_NEWGIDMAP, gid_args)):
        try:
            proc = subprocess.run(
                [helper, str(pid), *args],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT,
            )
        except (OSError, subprocess.SubprocessError) as e:
            raise IdMapError(f"could not run {helper}: {e!r}") from e
        if proc.returncode != 0:
            # The helper names the range it refused, which is the one thing that identifies a
            # misconfigured /etc/subuid; keep it verbatim.
            raise IdMapError(f"{helper} failed: {(proc.stderr or proc.stdout).strip()}")


def chown_via_userns(
    paths: Sequence[Path],
    uid: int,
    gid: int,
    *,
    agent_uid: int,
    agent_gid: int,
) -> None:
    """Chown every path to ``uid``/``gid`` without being root, through a transient user namespace.

    One identity for all paths: the namespace carries a single mapping, so a caller with more than
    one target groups its paths and calls once per group.

    The paths are expected to be the agent's own -- this hands the scratch it just wrote to the
    identity the container will run as. Asking for the agent's own ids is therefore a no-op rather
    than a way to take ownership back: the map would not carry whoever holds the paths now, and the
    kernel does not extend a namespace's root powers over an owner it cannot see.

    Raises ``IdMapError`` if the namespace could not be mapped -- an id outside what /etc/subuid
    delegates, or missing helpers -- or if a chown inside it failed.
    """
    if not paths:
        return
    uid_args, ns_uid = _map_spec(agent_uid, uid)
    gid_args, ns_gid = _map_spec(agent_gid, gid)
    if ns_uid == 0 and ns_gid == 0:
        # Already the agent's own identity, which is what the files carry: nothing to hand over.
        return

    # The child cannot map itself -- that is what the setuid helpers are for -- so it unshares, tells
    # the parent it is ready, and blocks until the map is written. Pipes rather than signals, so a
    # parent that dies closes the gate instead of leaving the child waiting for a go that never
    # comes.
    ready_r, ready_w = os.pipe()
    go_r, go_w = os.pipe()
    pid = os.fork()
    if pid == 0:  # child: async-signal-safe calls only, and never returns
        code = 1
        try:
            os.close(ready_r)
            os.close(go_w)
            os.unshare(os.CLONE_NEWUSER)
            os.write(ready_w, b"r")
            os.close(ready_w)
            if os.read(go_r, 1) == b"g":
                for path in paths:
                    os.chown(path, ns_uid, ns_gid)
                code = 0
        except BaseException:
            code = 1
        finally:
            os._exit(code)

    os.close(ready_w)
    os.close(go_r)
    try:
        if os.read(ready_r, 1) != b"r":
            raise IdMapError("the mapping child exited before it unshared")
        _write_maps(pid, uid_args, gid_args)
        os.write(go_w, b"g")
    finally:
        os.close(ready_r)
        os.close(go_w)
        _, status = os.waitpid(pid, 0)
    if not (os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0):
        raise IdMapError(f"the mapping child could not chown {len(paths)} path(s) to {uid}:{gid}")
