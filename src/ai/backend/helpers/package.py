import site
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

import pkg_resources

Package = namedtuple("Package", "name version is_user")

__all__ = ("install",)


def install(pkgname: str, force_install: bool = False) -> None:
    """
    Install a Python package from pypi.org or the given index server.
    The package is installed inside the user site directory.
    """

    if not force_install:
        if site.USER_SITE is None:
            raise RuntimeError("USER_SITE is not available")
        user_path = Path(site.USER_SITE).resolve()
        installed_pkgs = []
        for pkg in pkg_resources.working_set:
            if pkg.location is None:
                continue
            pkg_path = Path(pkg.location).resolve()
            is_user = user_path in pkg_path.parents
            installed_pkgs.append(Package(pkg.key, pkg.version, is_user))

        for installed_pkg in installed_pkgs:
            if pkgname.lower() == installed_pkg.name.lower():
                print(
                    f"'{installed_pkg.name}' is already installed (version: {installed_pkg.version})."
                )
                return

    sys.stdout.flush()
    cmdargs = [sys.executable, "-m", "pip", "install", "--user"]
    if force_install:
        cmdargs.append("-I")
    cmdargs.append(pkgname)
    subprocess.run(cmdargs)
    sys.stdout.flush()

    # Ensure the user site directory to be in sys.path
    if site.USER_SITE is not None and site.USER_SITE not in sys.path:
        sys.path.insert(0, site.USER_SITE)
