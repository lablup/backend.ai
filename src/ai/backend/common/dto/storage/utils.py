from __future__ import annotations

import urllib.parse

from aiohttp import hdrs


def build_attachment_headers(
    filename: str,
    content_type: str | None = None,
) -> dict[str, str]:
    """Build RFC-compliant attachment headers with UTF-8 filename support.

    Args:
        filename: The filename to include in Content-Disposition header.
        content_type: MIME type for Content-Type header. Defaults to application/octet-stream.

    Returns:
        Dictionary containing Content-Type and Content-Disposition headers.

    Note:
        This function generates headers compliant with:
        - RFC-2616 sec2.2: Basic filename in ASCII
        - RFC-5987: Extended filename with UTF-8 encoding for international characters
    """
    ascii_filename = filename.encode("ascii", errors="ignore").decode("ascii").replace('"', r"\"")
    encoded_filename = urllib.parse.quote(filename, encoding="utf-8")
    return {
        hdrs.CONTENT_TYPE: content_type or "application/octet-stream",
        hdrs.CONTENT_DISPOSITION: " ".join([
            f'attachment;filename="{ascii_filename}";',
            f"filename*=UTF-8''{encoded_filename}",
        ]),
    }
