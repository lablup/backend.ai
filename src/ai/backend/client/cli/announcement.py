import hashlib
import json
from pathlib import Path

import appdirs
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style

_printed_announcement = False


def announce(msg: str, only_once: bool = True) -> None:
    global _printed_announcement
    if only_once and _printed_announcement:
        return
    local_state_path = Path(appdirs.user_state_dir("backend.ai", "Lablup"))
    local_state_path.mkdir(parents=True, exist_ok=True)
    try:
        with open(local_state_path / "announcement.json", "rb") as f_current:
            last_state = json.load(f_current)
    except IOError:
        last_state = {"hash": "", "dismissed": False}

    hasher = hashlib.sha256()
    hasher.update(msg.encode("utf8"))
    msg_hash = hasher.hexdigest()

    if not (last_state["hash"] == msg_hash and last_state["dismissed"]):
        console = Console(stderr=True)
        doc = Markdown(msg)
        console.print(
            Panel(
                doc,
                title="Server Announcement",
                border_style=Style(color="cyan", bold=True),
                width=min(console.size.width, 82),
            ),
        )
    _printed_announcement = True

    last_state["hash"] = msg_hash
    with open(local_state_path / "announcement.json", "w") as f_new:
        json.dump(last_state, f_new)
