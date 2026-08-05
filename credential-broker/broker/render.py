import json
import os
import re
import urllib.parse

from .errors import EmptySecret, PolicyError

PLACEHOLDER = re.compile(rb"@@(?:(url):)?([A-Za-z0-9_./-]+)@@")


def render(template_dir, template, fetch):
    path = os.path.join(template_dir, template)
    if os.path.relpath(path, template_dir).startswith(".."):
        raise PolicyError(f"template {template!r} escapes {template_dir}")
    with open(path, "rb") as f:
        body = f.read()
    if not body.strip():
        raise EmptySecret(f"template {template} is empty")

    def substitute(match):
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
