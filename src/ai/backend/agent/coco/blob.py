import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import MeasuredBlobCorrupted, MeasuredBlobUnavailable

_SLUG = re.compile(r"[^0-9a-zA-Z]+")


def _slug(digest: str) -> str:
    return _SLUG.sub("-", digest.strip()).lower()


@dataclass(frozen=True)
class MeasuredBlob:
    content_address: str
    data: bytes

    @property
    def annotation_value(self) -> str:
        return self.data.decode("ascii")


class MeasuredBlobStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    def select(self, image_digest: str) -> MeasuredBlob:
        if not image_digest:
            raise MeasuredBlobUnavailable(extra_msg="the image digest is empty")
        index = self._root / "by-image" / _slug(image_digest)
        try:
            content_address = index.read_text().strip()
        except OSError:
            raise MeasuredBlobUnavailable(
                extra_msg=f"no index entry at {index} for image digest {image_digest}"
            ) from None
        blob_path = self._root / "blobs" / _slug(content_address)
        try:
            data = blob_path.read_bytes()
        except OSError:
            raise MeasuredBlobUnavailable(
                extra_msg=f"index {index} points at missing blob {blob_path}"
            ) from None
        observed = "sha256:" + hashlib.sha256(data).hexdigest()
        if observed != content_address:
            raise MeasuredBlobCorrupted(
                extra_msg=f"{blob_path} hashes to {observed}, indexed as {content_address}"
            )
        return MeasuredBlob(content_address, data)
