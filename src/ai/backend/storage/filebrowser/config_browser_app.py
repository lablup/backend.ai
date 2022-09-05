import json
from pathlib import Path

import aiofiles


async def prepare_filebrowser_app_config(
    settings_path: Path,
    service_port: int,
) -> None:
    filebrowser_config = {
        "settings": {
            "key": (
                "cdsnV117a7KLMN3GAbNWIB/b4w/P1zsVxmAZxAU"
                "AKidhZG9418Fn5wjE+Zcv6C9eCEDlajcINFkvV+BFSWtVZw=="
            ),
            "signup": False,
            "createUserDir": False,
            "defaults": {
                "scope": ".",
                "locale": "en",
                "viewMode": "list",
                "singleClick": False,
                "sorting": {
                    "by": "name",
                    "asc": False,
                },
                "perm": {
                    "admin": True,
                    "execute": True,
                    "create": True,
                    "rename": True,
                    "modify": True,
                    "delete": True,
                    "share": True,
                    "download": True,
                },
                "commands": [],
                "hideDotfiles": False,
            },
            "authMethod": "noauth",
            "branding": {
                "name": "BACKEND.AI Web Browser",
                "disableExternal": True,
                "files": "/filebrowser_dir/branding/",
                "theme": "",
            },
            "commands": {
                "after_copy": [],
                "after_delete": [],
                "after_rename": [],
                "after_save": [],
                "after_upload": [],
                "before_copy": [],
                "before_delete": [],
                "before_rename": [],
                "before_save": [],
                "before_upload": [],
            },
            "shell": [],
            "rules": [],
        },
        "server": {
            "root": "/data/",
            "baseURL": "",
            "socket": "",
            "tlsKey": "",
            "tlsCert": "",
            "port": str(service_port),
            "address": "",
            "log": "stdout",
            "enableThumbnails": False,
            "resizePreview": False,
            "enableExec": False,
        },
        "auther": {"recaptcha": None},
    }

    async with aiofiles.open(settings_path / "config.json", mode="w") as file:
        await file.write(json.dumps(filebrowser_config))

    filebrowser_app_settings = {
        "port": service_port,
        "baseURL": "",
        "address": "",
        "log": "stdout",
        "database": f"/filebrowser_dir/filebrowser_{service_port}.db",
        "root": "/data/",
    }
    async with aiofiles.open(settings_path / "settings.json", mode="w") as file:
        await file.write(json.dumps(filebrowser_app_settings))
