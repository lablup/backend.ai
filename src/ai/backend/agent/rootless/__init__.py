"""Shared machinery for the rootless container runtimes.

Every rootless backend runs session containers as an unprivileged user in a user namespace, and
owes the agent the same contract: where it keeps its state, which uid the kernel drops to, where
privileged work goes when the agent cannot do it itself. That is `runtime.RootlessOciRuntime`, and
it is all a rootless backend must implement.

What varies is *who holds the running container*:

* enroot and apptainer have no monitor at all — the kernel process is a child of the agent — so
  everything a daemon would otherwise provide has to be done by the agent: cgroup confinement, a
  restart-survivable container journal, log rotation, container-death events, the two-phase
  attachable-netns gate, and a seccomp filter. `base.SelfHostedRootlessRuntime` implements all of
  it once, and a backend subclasses it to supply only its image format and launch command line.
* A runtime that brings its own monitor (podman's conmon) owns that machinery itself and
  implements the contract directly, beside `SelfHostedRootlessRuntime` rather than under it.
"""
