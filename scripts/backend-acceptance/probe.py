"""Probes that must run INSIDE the container, not merely in its netns.

The suite's other network cases enter the netns from the host (`nsenter --net`) and use the host's
tools. That answers "does the fabric carry this", but not "can the workload use it": the container
has its own resolver, its own routing table view, and its own idea of which addresses exist.

Written against nothing but the standard library, because the container has less than you expect --
the kernel image has no `ping`, and an earlier version of these checks reported every packet as
dropped when the truth was that the command did not exist.
"""

import socket
import sys


def resolve(name: str) -> None:
    """The container's own resolver, the way a workload reaches a peer."""
    print(socket.gethostbyname(name))


def pmtu(host: str) -> None:
    """Largest UDP payload that leaves unfragmented, found by bisection with DF set."""
    IP_MTU_DISCOVER, IP_PMTUDISC_DO = 10, 2
    lo, hi, best = 1, 4000, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.IPPROTO_IP, IP_MTU_DISCOVER, IP_PMTUDISC_DO)
        try:
            s.sendto(b"x" * mid, (host, 9))
            best, lo = mid, mid + 1
        except OSError:
            hi = mid - 1
        finally:
            s.close()
    print(best)


def listen(port: int, token: str) -> None:
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(1)
    conn, _ = s.accept()
    conn.sendall(token.encode())
    conn.close()


def connect(host: str, port: int) -> None:
    try:
        s = socket.create_connection((host, port), 6)
        print(s.recv(64).decode() or "empty")
        s.close()
    except Exception as e:  # noqa: BLE001 -- the failure kind is the result
        print("FAIL:" + type(e).__name__)


def egress(host: str, port: int) -> None:
    """Out of the cluster entirely, through the LOCAL bridge's NAT."""
    try:
        socket.create_connection((host, port), 6).close()
        print("ok")
    except Exception as e:  # noqa: BLE001
        print("FAIL:" + type(e).__name__)


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "resolve":
        resolve(sys.argv[2])
    elif what == "pmtu":
        pmtu(sys.argv[2])
    elif what == "listen":
        listen(int(sys.argv[2]), sys.argv[3])
    elif what == "connect":
        connect(sys.argv[2], int(sys.argv[3]))
    elif what == "egress":
        egress(sys.argv[2], int(sys.argv[3]))
