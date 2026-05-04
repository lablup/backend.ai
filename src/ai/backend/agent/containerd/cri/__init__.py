"""CRI (Container Runtime Interface) gRPC client for the containerd backend.

The agent talks to the host's containerd via the standardized CRI gRPC
API rather than containerd's native API, so the same client surface
would also work against any other CRI-compliant runtime (cri-o, etc.)
in the future. We use ``grpc.aio`` for true async I/O.

Generated stubs live in ``cri.generated`` and are vendored into the
repository (see ``cri/proto/README.md`` for regeneration steps).
"""
