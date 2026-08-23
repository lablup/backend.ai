"""Shared machinery for the rootless, daemonless container runtimes (enroot, singularity).

Both run session containers as an unprivileged user in a user namespace, with no daemon to
delegate to. That leaves each of them owing the agent the same set of things a daemon would
otherwise provide — cgroup confinement, a restart-survivable container journal, log rotation,
container-death events, the two-phase attachable-netns gate, and a seccomp filter — none of which
is specific to how the image is stored or how the runtime binary is invoked.

`base.RootlessOciRuntime` implements all of it once; a backend subclasses it and supplies only
what genuinely differs: its image format and its launch command line.
"""
