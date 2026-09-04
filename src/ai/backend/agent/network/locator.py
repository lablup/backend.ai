"""What the privnet needs to know about containers -- and deliberately nothing else.

The privnet is a privileged daemon: it holds CAP_NET_ADMIN so the unprivileged agent does not have
to. Which container a request may act on is therefore a security question, not a convenience one,
and the answer must come from something the agent cannot forge. That "something" is the container
runtime, and this is the only shape of it the privnet is allowed to see.

What it may ask, and nothing else:

* ``container_pid`` -- the netns to attach to, resolved from the runtime rather than taken from the
  request. This is the load-bearing one; see PrivNetServer._attach for what it is worth per backend.
* ``live_sessions`` -- which containers the node still runs, whose session each belongs to and
  which agent placed it, so a restart can rebuild its state and drop what is gone. One listing
  rather than two: "every kernel container here" and "the ones this agent owns" are different
  questions, and answering them from one snapshot is what keeps them consistent with each other.
* ``cgroup_path`` -- only the rootless backends ask the privnet to create a cgroup for them; a
  runtime that places its own containers (containerd, Docker) never reaches this.

(``open``/``close`` are the connection to whatever answers those, and complete the list.)

Keeping it this narrow is what lets the privnet drive a backend it was not written for. It began
tied to containerd's OciRuntime -- a 20-method interface of image pulls, exec and commit, none of
which a network daemon has any business holding -- and adding another backend meant implementing all
of it. Now a backend implements five, of which one is optional.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

__all__ = ("OWNER_AGENT_LABEL", "SESSION_ID_LABEL", "ContainerLocator", "LiveContainer")

# The label a container carries to say which session it belongs to. It lives here, next to the one
# interface that reads it across backends, because every backend that wants the privnet must set it
# -- containerd through its OCI spec, the rootless runtimes through their own journals.
SESSION_ID_LABEL: Final = "ai.backend.session-id"
#: And which agent placed it. A node can run more than one agent (the multi-backend layout), so
#: "is this container mine" is not answered by "is it on this node".
OWNER_AGENT_LABEL: Final = "ai.backend.owner"


@dataclass(frozen=True)
class LiveContainer:
    """A running kernel container, as much of it as the network layer needs."""

    session_id: str
    #: None when the backend does not record one — the container is then nobody's to reclaim.
    owner_agent_id: str | None


class ContainerLocator(ABC):
    """The runtime, as the privnet is allowed to see it."""

    @abstractmethod
    async def open(self) -> None:
        """Connect to whatever the backend needs connecting to. Called once, before the privnet
        serves its socket, so a backend that cannot be reached fails at startup rather than on the
        first attach."""
        raise NotImplementedError

    async def close(self) -> None:
        """Release whatever ``open`` acquired. Not abstract: a locator that holds nothing has
        nothing to release, and the privnet calls this on the way out of ``serve_forever``."""

    @abstractmethod
    async def container_pid(self, container_id: str) -> int | None:
        """PID 1 of the container, or None if it is not running.

        The privnet resolves the netns from this rather than from the request, and re-reads it after
        pinning to close the PID-reuse window.
        """
        raise NotImplementedError

    @abstractmethod
    async def live_sessions(self) -> Mapping[str, LiveContainer]:
        """``{container_id: LiveContainer}`` for the containers this node still runs.

        Used to rebuild state after a restart: a session with no live container is one whose data
        plane can be torn down, and one whose containers are all another agent's is not this
        agent's to reclaim.
        """
        raise NotImplementedError

    def cgroup_path(self, container_id: str) -> Path:
        """Where this container's cgroup lives, for the backends that ask the privnet to create it.

        Not abstract: a runtime that places its own containers has nothing to say here, and saying
        the wrong thing is worse than refusing -- the privnet writes to this path as root.
        """
        raise NotImplementedError(
            f"{type(self).__name__} places its own cgroups; the privnet must not create one"
        )
