import os
from pathlib import Path

__version__ = (Path(__file__).parent / "VERSION").read_text().strip()

# Every `ip`/`iptables`/`nsenter` child execs at once and never uses gRPC, while a containerd
# node keeps a gRPC stream in flight; the fork handlers would only log at each fork. Read by
# gRPC's core on first import, which nothing under this package does before now.
os.environ.setdefault("GRPC_ENABLE_FORK_SUPPORT", "false")
