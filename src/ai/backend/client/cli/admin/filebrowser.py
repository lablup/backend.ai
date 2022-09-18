from __future__ import annotations

from . import admin


@admin.group()
def filebrowser() -> None:
    """
    FileBrowser administration commands.
    """
