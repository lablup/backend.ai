import tomllib

from .errors import PolicyError

CLASSES = ("resource", "render", "identity")
UNIT_MARKER = "/unit/"


class Entry:
    __slots__ = ("unit", "name", "kind", "value", "part", "subject", "sans")

    def __init__(self, unit, name, kind, value, part, subject, sans):
        self.unit = unit
        self.name = name
        self.kind = kind
        self.value = value
        self.part = part
        self.subject = subject
        self.sans = sans


def load(path):
    with open(path, "rb") as f:
        doc = tomllib.load(f)
    broker = doc["broker"]
    for required in ("url", "client", "socket", "template_dir", "identity_dir"):
        if not broker.get(required):
            raise PolicyError(f"broker.{required} is empty")
    table = {}
    for raw in doc.get("credential", ()):
        unit = raw.get("unit")
        name = raw.get("name")
        if not unit or not name or "/" in unit or "/" in name:
            raise PolicyError(f"malformed credential entry {raw!r}")
        kinds = [k for k in CLASSES if raw.get(k)]
        if len(kinds) != 1:
            raise PolicyError(f"{unit}/{name} must declare exactly one of {CLASSES}")
        kind = kinds[0]
        part = raw.get("part", "chain")
        if kind == "identity" and part not in ("key", "chain"):
            raise PolicyError(f"{unit}/{name} has unknown identity part {part!r}")
        key = (unit, name)
        if key in table:
            raise PolicyError(f"{unit}/{name} declared twice")
        table[key] = Entry(
            unit,
            name,
            kind,
            raw[kind],
            part,
            raw.get("subject", ""),
            tuple(raw.get("sans", ())),
        )
    if not table:
        raise PolicyError("policy table is empty")
    return broker, table


def peer_credential(peer):
    if isinstance(peer, bytes):
        peer = peer.decode("utf-8", "replace")
    peer = peer.lstrip("\x00")
    marker = peer.find(UNIT_MARKER)
    if marker < 0:
        return None
    parts = peer[marker + len(UNIT_MARKER) :].split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return (parts[0], parts[1])
