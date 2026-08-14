import json
import re
import urllib.parse
from collections.abc import Callable
from pathlib import Path

from ai.backend.cc_broker.errors import EmptySecret, PolicyError

PLACEHOLDER = re.compile(rb"@@(?:(url):)?([A-Za-z0-9_./-]+)@@")


def render(template_dir: str, template: str, fetch: Callable[[str], bytes]) -> bytes:
    root = Path(template_dir).resolve()
    path = (root / template).resolve()
    if not path.is_relative_to(root):
        raise PolicyError(f"template {template!r} escapes {template_dir}")
    body = path.read_bytes()
    if not body.strip():
        raise EmptySecret(f"template {template} is empty")

    def substitute(match: re.Match[bytes]) -> bytes:
        mode, resource = match.group(1), match.group(2).decode("ascii")
        value = fetch(resource)
        if not value:
            raise EmptySecret(resource)
        text = value.decode("utf-8").strip()
        if mode == b"url":
            return urllib.parse.quote(text, safe="").encode("utf-8")
        return json.dumps(text)[1:-1].encode("utf-8")

    rendered = PLACEHOLDER.sub(substitute, body)
    if PLACEHOLDER.search(rendered):
        raise PolicyError(f"template {template} left an unresolved placeholder")
    return rendered
