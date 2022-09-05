from pathlib import Path

import pkg_resources

p = Path(pkg_resources.resource_filename(__name__, ""))
storage_proxy_root_path_index = p.parts.index("storage-proxy")

Path(*p.parts[0:storage_proxy_root_path_index]) / "config/filebrowser"
