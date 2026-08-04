import json
import os
import re

from .errors import EmptySecret, PolicyError

PLACEHOLDER = re.compile(rb"@@([A-Za-z0-9_./-]+)@@")


def render(template_dir, template, fetch):
    path = os.path.join(template_dir, template)
    if os.path.relpath(path, template_dir).startswith(".."):
        raise PolicyError(f"template {template!r} escapes {template_dir}")
    with open(path, "rb") as f:
        body = f.read()
    if not body.strip():
        raise EmptySecret(f"template {template} is empty")

    def substitute(match):
        resource = match.group(1).decode("ascii")
        value = fetch(resource)
        if not value:
            raise EmptySecret(resource)
        return json.dumps(value.decode("utf-8").strip())[1:-1].encode("utf-8")

    rendered = PLACEHOLDER.sub(substitute, body)
    if PLACEHOLDER.search(rendered):
        raise PolicyError(f"template {template} left an unresolved placeholder")
    return rendered
