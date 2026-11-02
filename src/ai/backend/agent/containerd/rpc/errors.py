"""Errors of the client; callers map them to their own error types."""

from __future__ import annotations


class ContainerdError(Exception):
    """Base class of every error the client raises."""


class ContainerdUnavailable(ContainerdError):
    """The daemon is not reachable, or the client is not connected."""


class ContainerdNotFound(ContainerdError):
    """A required object is missing; the subclass names which."""


class ImageNotFound(ContainerdNotFound):
    """The image is not in the namespace."""


class BlobNotFound(ContainerdNotFound):
    """A blob the image refers to is missing from the content store."""


class SnapshotParentNotFound(ContainerdNotFound):
    """The image is not unpacked for the snapshotter."""


class ContainerdCallFailed(ContainerdError):
    """Any other failed call; `code` is the gRPC status name ("DEADLINE_EXCEEDED" on timeout)."""

    op: str
    code: str
    details: str

    def __init__(self, op: str, code: str, details: str) -> None:
        super().__init__(f"{op}: {code}: {details}")
        self.op = op
        self.code = code
        self.details = details
